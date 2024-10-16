"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from asyncio import (BoundedSemaphore, Queue, TaskGroup)
import os
from os import PathLike
from pathlib import (_PosixFlavour, _WindowsFlavour, Path, PurePath)
from types import TracebackType
from typing import (AsyncGenerator, Optional, Type)
from urllib.parse import (unquote, urlparse)

import aiofiles
from aiohttp import (ClientSession, ClientTimeout, TCPConnector)
import tealogger

from aioartifactory.configuration import (
    DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT,
    DEFAULT_MAXIMUM_CONNECTION,
    DEFAULT_CONNECTION_TIMEOUT,
)


tealogger.set_level(tealogger.DEBUG)


class RemotePath(PurePath):
    """Remote Path

    :param path: The URL of the Remote Path
    :type path: str
    :param api_key: The Artifactory API Key
    :type api_key: str, optional
    """

    # NOTE: Backward compatibility for 3.11, remove in Python 3.12
    _flavour = _PosixFlavour() if os.name == 'posix' else _WindowsFlavour()

    def __new__(
        cls,
        path: str,
        api_key: Optional[str] = None,  # NOTE: 3.11
        *args,
        **kwargs
    ):
        """Create Constructor"""
        return super().__new__(cls, path, *args, **kwargs)

    def __init__(
        self,
        path: str,
        *args,
        **kwargs
    ):
        """Initialize Constructor

        :param path: The URL of the Remote Path
        :type path: str
        """
        super().__init__(*args)

        # Authentication
        if kwargs.get('api_key'):
            self._api_key = kwargs.get('api_key')
            self._header = {'X-JFrog-Art-Api': self._api_key}
        elif kwargs.get('token'):
            self._token = kwargs.get('token')
            self._header = {'Authorization': f'Bearer {self._token}'}

        self._path = path

        # TODO: Validate URL

        # Parse the URL path
        self._parse_url = urlparse(path)

    def __str__(self):
        """Informal or Nicely Printable String Representation"""
        return f'{self._path}'

    def __repr__(self):
        """Official String Representation"""
        return f'{self.__class__.__name__}({self._path!r})'

    @property
    def name(self) -> str:
        """Name"""
        return unquote(PurePath(self._parse_url.path).name)

    @property
    def location(self) -> PurePath:
        """Location

        The `location` is defined as the `path` component of the
        `urlparse` function, without the `/artifactory` prefix `part`.
        See `urllib.parse.urlparse <https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse>`_.
        """
        return PurePath(unquote(
            '/'.join(PurePath(self._parse_url.path).parts[2:])
        ))

    @property
    async def sha256(self) -> str:
        """SHA256

        Get the SHA-256 checksum of the Remote Path if available, else
        return None.

        :return: The SHA-256 checksum of the Remote Path
        :rtype: str, None
        """
        storage_api_url = self._get_storage_api_url()
        # tealogger.debug(f'Storage API URL: {storage_api_url}')

        async with ClientSession() as session:
            async with session.get(
                url=storage_api_url,
                headers=self._header,
            ) as response:
                data = await response.json()

        return data['checksums']['sha256']

    def _get_storage_api_path(
        self
    ) -> PurePath:
        """Get Storage API Path

        Get the storage API path of the Remote Path. Return it as a
        valid PurePath.

        :return: The PurePath of the storage API path
        :rtype: PurePath
        """
        return PurePath(
            '//',
            # Network Location and Path
            '/'.join([
                self._parse_url.netloc,
                *self._parse_url.path.split('/')[:2],
                'api/storage',
                *self._parse_url.path.split('/')[2:],
            ]),
        )

    def _get_storage_api_url(
        self
    ) -> str:
        """Get Storage API URL
        """

        # The rest of the element(s) for URL
        parse_url_tail = ''.join([
            # Parameter
            ';' if self._parse_url.params else '',
            self._parse_url.params,
            # Query
            '?' if self._parse_url.query else '',
            self._parse_url.query,
            # Fragment
            '#' if self._parse_url.fragment else '',
            self._parse_url.fragment,
        ])

        return (
            f'{self._parse_url.scheme}:'
            f'{self._get_storage_api_path()}'
            f'{parse_url_tail}'
        )

    async def get_file_list(
        self,
        # recursive: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Get File List

        Get a list of file(s) for the Remote Path
        """

        storage_api_url = self._get_storage_api_url()
        # tealogger.debug(f'Storage API URL: {storage_api_url}')

        # query = 'list&deep=1' if recursive else 'list'
        query = 'list&deep=1'
        query += '&listFolders=0&includeRootPath=0'

        async with ClientSession() as session:
            async with session.get(
                url=f'{storage_api_url}?{query}',
                headers=self._header,
            ) as response:
                if response.status == 400:
                    # NOTE: Need `and 'Expected a folder' in await response.text()`?
                    _, separator, after = str(self.location).partition('/')
                    yield separator + after
                    # Need to `return` to terminate
                    return

                data = await response.json()

        for file in data['files']:
            yield file['uri']


class AIOArtifactory:
    """Asynchronous Input Output (AIO) Artifactory Class
    """
    # __slots__ = ()

    def __new__(cls, *args, **kwargs):
        """Create Constructor
        """
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        """Customize Constructor

        The main Artifactory class

        :param api_key: The Artifactory API Key
        :type api_key: str, optional
        :param token: The Artifactory Token
        :type token: str, optional
        """
        # Authentication
        if kwargs.get('api_key'):
            self._api_key = kwargs.get('api_key')
            self._header = {'X-JFrog-Art-Api': self._api_key}
        elif kwargs.get('token'):
            self._token = kwargs.get('token')
            self._header = {'Authorization': f'Bearer {self._token}'}

        # Retrieve Limiter
        self._retrieve_limiter = BoundedSemaphore(10)

    async def retrieve(
        self,
        source: str | list[str],
        destination: PathLike | list[PathLike],
        maximum_connection: int = DEFAULT_MAXIMUM_CONNECTION,
        quiet: bool = False,
        recursive: bool = False,
    ):
        """Retrieve

        :param source: The source (Remote) path
        :type source: str
        :param destination: The destination (Local) path
        :type destination: str
        :param maximum_connection: The maximum parallel connection use
            to retrieve artifact(s)
        :type maximum_connection: int, optional
        :param quiet: Whether to show retrieve progress
        :type quiet: bool, optional
        :param recursive: Whether to recursively retrieve artifact(s)
        :type recursive: bool, optional
        """

        # Create a `download_queue`
        download_queue = Queue()

        # TODO: Convert one to many...for now
        if isinstance(source, str):
            source = [source]
        if isinstance(destination, str):
            destination = [destination]

        session_connector = TCPConnector(limit_per_host=maximum_connection)
        session_timeout = ClientTimeout(total=DEFAULT_CONNECTION_TIMEOUT)
        async with (
            ClientSession(
                connector=session_connector,
                timeout=session_timeout,
            ) as session,
        ):
            # Retrieve Recursive
            if recursive:
                await self._retrieve_recursive(
                    source_list=source,
                    destination_list=destination,
                    download_queue=download_queue,
                    maximum_connection=maximum_connection,
                    session=session,
                    quiet=quiet,
                )

    async def _retrieve_recursive(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
        download_queue: Queue,
        maximum_connection: int,
        session: ClientSession,
        quiet: bool,
    ):
        """Retrieve Recursive"""
        # Create a `source_queue` to store the `source_list` to retrieve
        source_queue = Queue()
        # Create a `destination_queue` to store the `destination_list` to retrieve
        destination_queue = Queue()

        async with TaskGroup() as group:
            # Optimize maximum connection
            connection_count = min(len(source_list), maximum_connection)

            # Create `connection_count` of `_retrieve_query` worker task(s)
            # Store them in a `task_list`
            _ = [
                group.create_task(
                    self._retrieve_task(
                        source_queue=source_queue,
                        download_queue=download_queue,
                        # session=session,
                    )
                ) for _ in range(connection_count)
            ]

            # Enqueue the `source` to the `source_queue`
            for source in source_list:
                await source_queue.put(source)

            # Enqueue the `destination` to the `destination_queue`
            # for destination in destination_list:
            #     await destination_queue.put(destination)

            # Enqueue a `None` signal for worker(s) to exit
            for _ in range(connection_count):
                await source_queue.put(None)

        async with TaskGroup() as group:
            # Optimize maximum connection
            connection_count = min(download_queue.qsize(), maximum_connection)

            # Create `connection_count` of `_download_query` worker task(s)
            # Store them in a `task_list`
            for count in range(connection_count):
                group.create_task(
                    self._download_task(
                        destination_list=destination_list,
                        download_queue=download_queue,
                        session=session,
                    )
                )

            # Enqueue a `None` signal for worker(s) to exit
            for _ in range(connection_count):
                await download_queue.put(None)

    # async def _retrieve_nonrecursive(
    #     self,
    #     source_list: list[str],
    #     destination_list: list[PathLike],
    # ):
    #     """Retrieve Non-Recursive"""
    #     ...

    async def _retrieve_task(
        self,
        source_queue: Queue,
        download_queue: Queue,
        # bounded_limiter: BoundedSemaphore,
        # session: ClientSession,
    ):
        """Retrieve Task

        :param source_queue: The source queue
        :type source_queue: Queue
        :param download_queue: The download queue
        :type download_queue: Queue
        """
        while True:
            source = await source_queue.get()

            # The signal to exit (check at the beginning)
            if source is None:
                break

            tealogger.debug(f'Source: {source}, Type: {type(source)}')
            tealogger.debug(f'Path: {urlparse(source).path}')

            # Enqueue the retrieve query response
            remote_path = RemotePath(path=source, api_key=self._api_key)
            async for file in remote_path.get_file_list():
                # Get partition before the last `/`
                before, _, _ = source.rpartition('/')
                tealogger.debug(f'File: {before}{file}')
                await download_queue.put(f'{before}{file}')

    async def _download_task(
        self,
        destination_list: list[PathLike],
        download_queue: Queue,
        session: ClientSession,
    ):
        """Download Task

        :param download_queue: The download queue
        :type download_queue: Queue
        :param session: The current session
        :type session: ClientSession
        """
        while True:
            download = await download_queue.get()

            # The signal to exit (check at the beginning)
            if download is None:
                break

            tealogger.debug(f'Download: {download}, Type: {type(download)}')

            remote_path = RemotePath(path=download, api_key=self._api_key)

            # Download the file
            tealogger.debug(f'Downloading: {download}')

            async with session.get(url=str(remote_path), headers=self._header) as response:
                for destination in destination_list:
                    destination_path = Path(
                        destination / remote_path.location
                    ).expanduser().resolve()
                    try:
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        tealogger.error(f'Operating System Error: {e}')

                    async with aiofiles.open(destination_path, 'wb') as file:
                        async for chunk, _ in response.content.iter_chunks():
                            await file.write(chunk)

            tealogger.info(f'Completed: {download}')

    async def __aenter__(self):
        """Asynchronous Enter
        """
        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> None:
        """Asynchronous Exit

        :param exception_type: The exception type
        :type exception_type: Optional[Type[BaseException]]
        :param exception_value: The exception value
        :type exception_value: Optional[BaseException]
        :param exception_traceback: The exception traceback
        :type exception_traceback: Optional[TracebackType]
        """
        await super()
