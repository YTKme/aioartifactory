"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from asyncio import (BoundedSemaphore, Queue, TaskGroup)
import os
from os import PathLike
from pathlib import Path
from types import TracebackType
from typing import (Optional, Type)
from urllib.parse import (urlparse)

import aiofiles
from aiohttp import (ClientSession, ClientTimeout, TCPConnector)
import tealogger

from .configuration import (
    # DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT,
    DEFAULT_MAXIMUM_CONNECTION,
    DEFAULT_CONNECTION_TIMEOUT,
)
from .localpath import LocalPath
from .remotepath import RemotePath


CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()

# Configure logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
logger = tealogger.get_logger("aioartifactory")


class AIOArtifactory:
    """Asynchronous Input Output (AIO) Artifactory Class"""
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

    # ------
    # Deploy
    # ------

    async def deploy(
        self,
        source: str | list[str] | LocalPath | list[LocalPath],
        destination: str | list[str] | RemotePath | list[RemotePath],
        property: dict = dict | None,
        recursive: bool = False,
        quiet: bool = False,
    ):
        """Deploy

        :param source: The source (Local) path(s)
        :type source: str | list[str] | LocalPath | list[LocalPath]
        :param destination: The destination (Remote) path(s)
        :type destination: str | list[str] | RemotePath | list[RemotePath]
        :param property: The property(ies) metadata for the artifact(s)
        :type property: dict, optional
        :param recursive: Whether to recursively deploy artifact(s)
        :type recursive: bool, optional
        :param quiet: Whether to show deploy progress
        :type quiet: bool, optional
        """

        # Create an `upload_queue`
        upload_queue = Queue()

        # TODO: Convert one to many...for now
        if not isinstance(source, list):
            source = [source]
        if not isinstance(destination, list):
            destination = [destination]

        if self._client_session:
            client_session = self._client_session
        else:
            client_session = ClientSession(
                connector=TCPConnector(limit_per_host=DEFAULT_MAXIMUM_CONNECTION),
                timeout=ClientTimeout(total=DEFAULT_CONNECTION_TIMEOUT),
            )

        async with client_session as session:
            return await self._deploy(
                source_list=source,
                destination_list=destination,
                property=property,
                upload_queue=upload_queue,
                session=session,
                recursive=recursive,
                quiet=quiet,
            )

    async def _deploy(
        self,
        source_list: list[str] | list[LocalPath],
        destination_list: list[str] | list[RemotePath],
        property: dict,
        upload_queue: Queue,
        session: ClientSession,
        recursive: bool,
        quiet: bool,
    ) -> list[str]:
        """Deploy"""
        # Create a `source_queue` to store the `source_list` to deploy
        source_queue = Queue()
        # Create a `destination_queue` to store the `destination_list` to deploy
        # destination_queue = Queue()

        # Deploy
        async with TaskGroup() as group:
            # Optimize maximum connection
            connection_count = min(len(source_list), DEFAULT_MAXIMUM_CONNECTION)

            # Create `connection_count` of `_deploy_query` worker task(s)
            # Store them in a `task_list`

            _ = [
                group.create_task(
                    self._deploy_task(
                        source_queue=source_queue,
                        upload_queue=upload_queue,
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

        upload_list = []

        # Upload
        async with TaskGroup() as group:
            # Optimize maximum connection
            connection_count = min(upload_queue.qsize(), DEFAULT_MAXIMUM_CONNECTION)

            # Create `connection_count` of `_upload_query` worker task(s)
            # Store them in a `task_list`
            for count in range(connection_count):
                group.create_task(
                    self._upload_task(
                        destination_list=destination_list,
                        property=property,
                        upload_queue=upload_queue,
                        upload_list=upload_list,
                        session=session,
                    )
                )

            # Enqueue a `None` signal for worker(s) to exit
            for _ in range(connection_count):
                await upload_queue.put(None)

        # logger.debug(f"Upload List: {upload_list}")
        return upload_list

    async def _deploy_task(
        self,
        source_queue: Queue,
        upload_queue: Queue,
        recursive: bool,
        # bounded_limiter: BoundedSemaphore,
        # session: ClientSession,
    ) -> None:
        """Deploy Task

        :param source_queue: The source queue
        :type source_queue: Queue
        :param upload_queue: The upload queue
        :type upload_queue: Queue
        :param recursive: Whether to recursively deploy artifact(s)
        :type recursive: bool
        """
        while True:
            source = await source_queue.get()

            # The signal to exit (check at the beginning)
            if source is None:
                break

            logger.debug(f"Source: {source}, Type: {type(source)}")

            source_path = LocalPath(path=source)
            logger.debug(f"Source Path: {source_path}")

            # Enqueue the deploy query response
            # The `upload_queue` should be relative path
            if source_path.is_file():
                await upload_queue.put(source_path)
            else:
                for file in source_path.get_file_list(recursive=recursive):
                    relative_path = os.path.relpath(file, start=source_path)
                    local_path = source_path / relative_path
                    # Enqueue the upload queue
                    await upload_queue.put(local_path)

    async def _upload_task(
        self,
        destination_list: list[str] | list[RemotePath],
        property: dict,
        upload_queue: Queue,
        upload_list: list[str],
        session: ClientSession,
    ) -> None:
        """Upload Task

        :param destination_list: The destination list
        :type destination_list: list[str] | list[RemotePath]
        :param property: The property(ies) metadata for the artifact(s)
        :type property: dict
        :param upload_queue: The upload queue
        :type upload_queue: Queue
        :param upload_list: The upload list store what is uploaded
        :type upload_list: list[str]
        :param session: The current session
        :type session: ClientSession
        """

        while True:
            upload = await upload_queue.get()

            # The signal to exit (check at the beginning)
            if upload is None:
                break

            logger.info(f"Upload: {upload}, Type: {type(upload)}")
            logger.debug(f"Destination List: {destination_list}")

            logger.warning(f"Property: {property}")

            local_path = LocalPath(path=upload)
            logger.debug(f"Local Path: {local_path}")

            # Upload the file
            logger.debug(f"Uploading: {upload}")

            with open(local_path, "rb") as file:
                for destination in destination_list:
                    logger.debug(f"Destination: {destination}")

                    remote_path = RemotePath(
                        path=f"{destination}/{local_path}"
                    ).as_posix()

                    # Update header with checksum
                    local_path_checksum = local_path.checksum
                    self._header.update({
                        "X-Checksum": local_path_checksum["md5"],
                        "X-Checksum-Sha1": local_path_checksum["sha1"],
                        "X-Checksum-Sha256": local_path_checksum["sha256"],
                    })

                    async with session.put(
                        url=str(remote_path),
                        headers=self._header,
                        data=file,
                    ) as response:
                        # logger.debug(f"Response: {response}")
                        if response.status != 201:
                            logger.error(f"Upload Failed: {remote_path}")
                            raise RuntimeError(f"Upload Failed: {remote_path}")

                        data = await response.json()
                        upload_list.append(data["downloadUri"])

            logger.info(f"Completed: {upload}")

    # --------
    # Retrieve
    # --------

    async def retrieve(
        self,
        source: str | list[str],
        destination: PathLike | list[PathLike],
        recursive: bool = False,
        output_repository: bool = False,
        quiet: bool = False,
    ) -> list[str]:
        """Retrieve

        :param source: The source (Remote) path(s)
        :type source: str | list[str]
        :param destination: The destination (Local) path(s)
        :type destination: str | list[str]
        :param recursive: Whether to recursively retrieve artifact(s)
        :type recursive: bool, optional
        :param output_repository: Whether to include the repository name
            in the destination path, defaults to False
        :type output_repository: bool, optional
        :param quiet: Whether to show retrieve progress
        :type quiet: bool, optional
        """

        # Create a `download_queue`
        download_queue = Queue()

        # TODO: Convert one to many...for now
        if not isinstance(source, list):
            source = [source]
        if not isinstance(destination, list):
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
                output_repository=output_repository,
                quiet=quiet,
            )

    async def _retrieve(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
        download_queue: Queue,
        session: ClientSession,
        recursive: bool,
        output_repository: bool,
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
                        output_repository=output_repository,
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

            remote_path = RemotePath(path=source, api_key=self._api_key)

            # Enqueue the retrieve query response
            async for file in remote_path.get_file_list(recursive=recursive):
                # Get partition before the last `/`
                before, _, _ = str(source).rpartition("/")
                logger.debug(f"Remote File: {before}{file}")
                await download_queue.put(f"{before}{file}")

    async def _download_task(
        self,
        destination_list: list[PathLike],
        download_queue: Queue,
        download_list: list[str],
        session: ClientSession,
        output_repository: bool,
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
        :param output_repository: Whether to include the repository name
            in the destination path
        :type output_repository: bool
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

            async with session.get(
                url=str(remote_path),
                headers=self._header,
            ) as response:
                for destination in destination_list:
                    location = LocalPath(path=remote_path.location)
                    if output_repository:
                        location = LocalPath(
                            f"{remote_path.repository}/{location}"
                        )

                    destination_path = Path(
                        destination / location
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

    # ----------------------------
    # Asynchronous Context Manager
    # ----------------------------

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
