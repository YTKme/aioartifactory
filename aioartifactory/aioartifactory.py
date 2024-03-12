"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from asyncio import (Queue, TaskGroup)
from os import PathLike
from pathlib import PurePath
from types import TracebackType
from typing import (AsyncGenerator, Optional, Type)
from urllib.parse import urlparse

import aiofiles
from aiohttp import (ClientSession, ClientTimeout, TCPConnector)
import tealogger

from aioartifactory.configuration import (
    DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT,
    DEFAULT_MAX_CONNECTION,
)
from aioartifactory.common import progress
from aioartifactory.context import TeardownContextManager


tealogger.set_level(tealogger.DEBUG)


class RemotePath(PurePath):
    """Remote Path
    """

    def __new__(
        cls,
        *args,
        **kwargs
    ):
        """New
        """
        tealogger.debug(f'Remote Path Create Constructor')
        return super().__new__(cls, *args, **kwargs)

    def __init__(
        self,
        path: str,
        *args,
        **kwargs
    ):
        """Constructor

        :param path: The URL of the Remote
            Path
        :type path: str
        """
        tealogger.debug(f'Remote Path Initialize Constructor')
        super().__init__(*args)

        # Authentication
        if kwargs.get('api_key'):
            self._api_key = kwargs.get('api_key')
            self._header = {'X-JFrog-Art-Api': self._api_key}
        elif kwargs.get('token'):
            self._token = kwargs.get('token')
            self._header = {'Authorization': f'Bearer {self._token}'}

        # TODO: Validate URL

        # Parse the URL path
        self._parse_url = urlparse(path)
        tealogger.debug(f'Parse Result: {self._parse_url}')

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

    async def get_file_list(self) -> AsyncGenerator[str, None]:
        """Get File List

        Get a list of file(s) for the Remote Path
        """

        storage_api_url = self._get_storage_api_url()
        tealogger.debug(f'Storage API URL: {storage_api_url}')

        async with ClientSession() as session:
            async with session.get(
                url=f'{storage_api_url}?list&deep=1',
                headers=self._header,
            ) as response:
                data = await response.json()

        for file in data['files']:
            yield file['uri']


class AIOArtifactory:
    """Asynchronous Input Output (AIO) Artifactory Class
    """
    # __slots__ = ()

    def __new__(cls, *args, **kwargs):
        """New
        """
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        """Constructor

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

    # async def print_me(self, message: str):
    #     await asyncio.sleep(1)
    #     print(message)

    async def retrieve(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
        maximum_queue_size: int = DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT,
        maximum_connection: int = DEFAULT_MAX_CONNECTION,
        quiet: bool = False,
        recursive: bool = False,
    ):
        """Retrieve

        :param source: The source (Remote) path
        :type source: str
        :param destination: The destination (Local) path
        :type destination: str
        :param maximum_queue_size: The maximum queue size use to
            retrieve artifact(s)
        :type maximum_queue_size: int, optional
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

        session_connector = TCPConnector(limit=maximum_connection)
        async with (
            ClientSession(connector=session_connector) as session,
        ):
            # Retrieve Recursive
            if recursive:
                await self._retrieve_recursive(
                    source_list=source_list,
                    destination_list=destination_list,
                    download_queue=download_queue,
                    maximum_queue_size=maximum_queue_size,
                    maximum_connection=maximum_connection,
                    session=session,
                    quiet=quiet,
                )

    async def _retrieve_recursive(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
        download_queue: Queue,
        maximum_queue_size: int,
        maximum_connection: int,
        session: ClientSession,
        quiet: bool,
    ):
        """Retrieve Recursive"""
        # Create a `query_queue` to store the `source_list` to retrieve
        query_queue = Queue()

        async with TaskGroup() as group:
            # Create `maximum_connection` of `_retrieve_query` worker task(s)
            # Store them in a `task_list`
            task_list = [
                group.create_task(
                    self._retrieve_query(
                        query_queue=query_queue,
                        download_queue=download_queue,
                        session=session,
                    )
                ) for index in range(maximum_connection)
            ]

            # Enqueue the `source` to the `query_queue`
            for source in source_list:
                await query_queue.put(source)

            # Enqueue a `None` signal for worker(s) to exit
            for _ in range(maximum_connection):
                await query_queue.put(None)

    async def _retrieve_nonrecursive(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
    ):
        """Retrieve Non-Recursive"""
        ...

    async def _retrieve_query(
        self,
        query_queue: Queue,
        download_queue: Queue,
        session: ClientSession,
    ):
        """Retrieve Query
        """
        while True:
            query = await query_queue.get()

            # The signal to exit
            if query is None:
                break

            tealogger.debug(f'Query: {query}, Type: {type(query)}')
            tealogger.debug(f'Path: {urlparse(query).path}')

            remote_path = RemotePath(path=query, api_key=self._api_key)
            async for file in remote_path.get_file_list():
                # Store the result
                tealogger.info(f'File: {query.rstrip("/")}{file}')
                await download_queue.put(f'{query.rstrip("/")}{file}')

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
