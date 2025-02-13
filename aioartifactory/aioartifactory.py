"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from asyncio import (BoundedSemaphore, Queue, TaskGroup)
from os import PathLike
from pathlib import Path
from types import TracebackType
from typing import (Optional, Type)
from urllib.parse import (urlparse)

import aiofiles
from aiohttp import (ClientSession, ClientTimeout, TCPConnector)
import tealogger

from aioartifactory.configuration import (
    # DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT,
    DEFAULT_MAXIMUM_CONNECTION,
    DEFAULT_CONNECTION_TIMEOUT,
)
from aioartifactory.remotepath import RemotePath


CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()

# Configure logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH / "tealogger.json"
)
logger = tealogger.get_logger("aioartifactory")


class AIOArtifactory:
    """Asynchronous Input Output (AIO) Artifactory Class
    """
    # __slots__ = ()

    def __new__(cls, *args, **kwargs):
        """Create Constructor"""
        return super().__new__(cls)

    def __init__(
        self,
        # host: str,
        # port: int = 443,
        *args,
        **kwargs
    ) -> None:
        """Customize Constructor

        The main Artifactory class

        :param host: The name of the Artifactory host
        :type host: str
        :param port: The port of the Artifactory host
        :type port: int, optional
        :param api_key: The Artifactory API Key
        :type api_key: str, optional
        :param token: The Artifactory Token
        :type token: str, optional
        """
        # self._host = host
        # self._port = port

        # Authentication
        if kwargs.get("api_key"):
            self._api_key = kwargs.get("api_key")
            self._header = {"X-JFrog-Art-Api": self._api_key}
        elif kwargs.get("token"):
            self._token = kwargs.get("token")
            self._header = {"Authorization": f"Bearer {self._token}"}

        # Retrieve Limiter
        self._retrieve_limiter = BoundedSemaphore(10)

        # Client Session
        self._client_session = None

    # @property
    # async def host(self) -> str:
    #     """Host"""
    #     return self._host

    # @property
    # def port(self) -> int:
    #     """Port"""
    #     return self._port

    async def retrieve(
        self,
        source: str | list[str],
        destination: PathLike | list[PathLike],
        recursive: bool = False,
        quiet: bool = False,
    ) -> list[str]:
        """Retrieve

        :param source: The source (Remote) path(s)
        :type source: str | list[str]
        :param destination: The destination (Local) path(s)
        :type destination: str | list[str]
        :param recursive: Whether to recursively retrieve artifact(s)
        :type recursive: bool, optional
        :param quiet: Whether to show retrieve progress
        :type quiet: bool, optional
        """

        # Create a `download_queue`
        download_queue = Queue()

        # TODO: Convert one to many...for now
        if isinstance(source, str):
            source = [source]
        if isinstance(destination, str):
            destination = [destination]

        if self._client_session:
            client_session = self._client_session
        else:
            client_session = ClientSession(
                connector=TCPConnector(limit_per_host=DEFAULT_MAXIMUM_CONNECTION),
                timeout=ClientTimeout(total=DEFAULT_CONNECTION_TIMEOUT),
            )

        async with client_session as session:
            return await self._retrieve(
                source_list=source,
                destination_list=destination,
                download_queue=download_queue,
                session=session,
                recursive=recursive,
                quiet=quiet,
            )

    async def _retrieve(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
        download_queue: Queue,
        session: ClientSession,
        recursive: bool,
        quiet: bool,
    ) -> list[str]:
        """Retrieve"""
        # Create a `source_queue` to store the `source_list` to retrieve
        source_queue = Queue()
        # Create a `destination_queue` to store the `destination_list` to retrieve
        # destination_queue = Queue()

        # Retrieve
        async with TaskGroup() as group:
            # Optimize maximum connection
            connection_count = min(len(source_list), DEFAULT_MAXIMUM_CONNECTION)

            # Create `connection_count` of `_retrieve_query` worker task(s)
            # Store them in a `task_list`
            _ = [
                group.create_task(
                    self._retrieve_task(
                        source_queue=source_queue,
                        download_queue=download_queue,
                        recursive=recursive,
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

        download_list = []

        # Download
        async with TaskGroup() as group:
            # Optimize maximum connection
            connection_count = min(download_queue.qsize(), DEFAULT_MAXIMUM_CONNECTION)

            # Create `connection_count` of `_download_query` worker task(s)
            # Store them in a `task_list`
            for count in range(connection_count):
                group.create_task(
                    self._download_task(
                        destination_list=destination_list,
                        download_queue=download_queue,
                        download_list=download_list,
                        session=session,
                    )
                )

            # Enqueue a `None` signal for worker(s) to exit
            for _ in range(connection_count):
                await download_queue.put(None)

        # logger.debug(f"Download List: {download_list}")
        return download_list

    async def _retrieve_task(
        self,
        source_queue: Queue,
        download_queue: Queue,
        recursive: bool,
        # bounded_limiter: BoundedSemaphore,
        # session: ClientSession,
    ) -> None:
        """Retrieve Task

        :param source_queue: The source queue
        :type source_queue: Queue
        :param download_queue: The download queue
        :type download_queue: Queue
        :param recursive: Whether to recursively retrieve artifact(s)
        :type recursive: bool
        """
        while True:
            source = await source_queue.get()

            # The signal to exit (check at the beginning)
            if source is None:
                break

            logger.debug(f"Source: {source}, Type: {type(source)}")
            logger.debug(f"Source Path: {urlparse(source).path}")

            # Enqueue the retrieve query response
            remote_path = RemotePath(path=source, api_key=self._api_key)
            async for file in remote_path.get_file_list(recursive=recursive):
                # Get partition before the last `/`
                before, _, _ = str(source).rpartition("/")
                logger.debug(f"Source File: {before}{file}")
                await download_queue.put(f"{before}{file}")

    async def _download_task(
        self,
        destination_list: list[PathLike],
        download_queue: Queue,
        download_list: list[str],
        session: ClientSession,
    ) -> None:
        """Download Task

        :param destination_list: The destination list
        :type destination_list: list[PathLike]
        :param download_queue: The download queue
        :type download_queue: Queue
        :param download_list: The download list store what is downloaded
        :type download_list: list[str]
        :param session: The current session
        :type session: ClientSession
        """
        while True:
            download = await download_queue.get()

            # The signal to exit (check at the beginning)
            if download is None:
                break

            logger.debug(f"Download: {download}, Type: {type(download)}")

            remote_path = RemotePath(path=download, api_key=self._api_key)

            # Download the file
            logger.debug(f"Downloading: {download}")

            async with session.get(url=str(remote_path), headers=self._header) as response:
                for destination in destination_list:
                    destination_path = Path(
                        destination / remote_path.location
                    ).expanduser().resolve()
                    try:
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        logger.error(f"Operating System Error: {e}")

                    async with aiofiles.open(destination_path, "wb") as file:
                        async for chunk, _ in response.content.iter_chunks():
                            await file.write(chunk)

            download_list.append(download)

            logger.info(f"Completed: {download}")

    async def __aenter__(self):
        """Asynchronous Enter
        """
        # Client Session
        self._client_session = ClientSession(
            connector=TCPConnector(limit_per_host=DEFAULT_MAXIMUM_CONNECTION),
            timeout=ClientTimeout(total=DEFAULT_CONNECTION_TIMEOUT),
        )

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

        if self._client_session:
            await self._client_session.close()
