"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
from asyncio import BoundedSemaphore, Queue, TaskGroup
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from functools import partial
from pathlib import Path
from types import TracebackType

# from urllib.parse import (urlparse)
import aiofiles
import tealogger
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from .configuration import (
    DEFAULT_CONNECTION_TIMEOUT,
    # DEFAULT_ARTIFACTORY_SEARCH_USER_QUERY_LIMIT,
    DEFAULT_MAXIMUM_CONNECTION,
)
from .localpath import LocalPath
from .remotepath import RemotePath

CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()

# Configure logger
tealogger.configure(configuration=CURRENT_MODULE_PATH / "tealogger.json")
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
        **kwargs,
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

        # Secure Sockets Layer (SSL) Certification Check
        self._ssl = kwargs.get("ssl", True)

        # Retrieve Limiter
        self._retrieve_limiter = BoundedSemaphore(10)

        # Client Session
        self._client_session = None

    # ------
    # Helper
    # ------

    def _create_client_session(self) -> ClientSession:
        """Create Client Session

        Create a `ClientSession` configured with the default connection
        limit, the default connection timeout, and the Secure Sockets
        Layer (SSL) certification check of the instance.

        :return: The client session
        :rtype: ClientSession
        """

        return ClientSession(
            connector=TCPConnector(
                limit_per_host=DEFAULT_MAXIMUM_CONNECTION,
                ssl=self._ssl,
            ),
            timeout=ClientTimeout(total=DEFAULT_CONNECTION_TIMEOUT),
        )

    def _acquire_client_session(self) -> ClientSession:
        """Acquire Client Session

        Reuse the client session of the instance, when available,
        otherwise create a new one.

        :return: The client session
        :rtype: ClientSession
        """

        if self._client_session:
            return self._client_session

        return self._create_client_session()

    @staticmethod
    def _as_path_sequence(
        path: str | LocalPath | RemotePath | Sequence,
        path_type: type[LocalPath] | type[RemotePath],
    ) -> Sequence:
        """As Path Sequence

        Wrap a single path into a one item sequence, a sequence of
        path(s) pass through unchanged.

        :param path: The path(s)
        :type path: str | LocalPath | RemotePath | Sequence
        :param path_type: The path type of a single path
        :type path_type: type[LocalPath] | type[RemotePath]

        :return: The sequence of path(s)
        :rtype: Sequence
        """

        if isinstance(path, (str, path_type)):
            return [path]

        return path

    async def _run_worker(
        self,
        queue: Queue,
        worker: Callable[[], Awaitable[None]],
        work_item_list: Sequence | None = None,
    ) -> None:
        """Run Worker

        Run a group of worker task(s) consuming the `queue`. The worker
        count is the number of work item(s), or the current size of the
        `queue` when there is no `work_item_list`, capped by the default
        maximum connection.

        Enqueue the `work_item_list`, when available, then enqueue a
        `None` signal for each worker to exit.

        :param queue: The queue the worker(s) consume
        :type queue: Queue
        :param worker: The (no argument) worker callable to create the
            worker task(s) with
        :type worker: Callable[[], Awaitable[None]]
        :param work_item_list: The work item(s) to enqueue, defaults to
            None for an already populated `queue`
        :type work_item_list: Sequence, optional
        """

        # Optimize maximum connection
        worker_count = min(
            len(work_item_list) if work_item_list is not None else queue.qsize(),
            DEFAULT_MAXIMUM_CONNECTION,
        )

        async with TaskGroup() as group:
            # Create `worker_count` of worker task(s)
            for _ in range(worker_count):
                group.create_task(worker())

            # Enqueue the work item(s) to the `queue`
            for work_item in work_item_list or []:
                await queue.put(work_item)

            # Enqueue a `None` signal for worker(s) to exit
            for _ in range(worker_count):
                await queue.put(None)

    # ------
    # Deploy
    # ------

    async def deploy(
        self,
        source: str | LocalPath | Sequence[str | LocalPath],
        destination: str | RemotePath | Sequence[str | RemotePath],
        property: dict | None = None,
        recursive: bool = False,
        quiet: bool = False,
        ssl: bool = True,
    ):
        """Deploy

        Deploy (upload) artifact file(s) to Artifactory.

        :param source: The source (Local) path(s), can be relative or
            absolute path(s)
        :type source: str | LocalPath | Sequence[str | LocalPath]
        :param destination: The destination (Remote) path(s)
        :type destination: str | RemotePath | Sequence[str | RemotePath]
        :param property: The property(ies) metadata for the artifact(s),
            defaults to None
        :type property: dict, optional
        :param recursive: Whether to recursively deploy artifact(s),
            defaults to False
        :type recursive: bool, optional
        :param quiet: Whether to show deploy progress, defaults to False
        :type quiet: bool, optional
        :param ssl: Whether to check SSL certification, relax by setting
            to False, defaults to True
        :type ssl: bool, optional
        """

        # Create an `upload_queue`
        upload_queue = Queue()

        # TODO: Convert one to many...for now
        source = self._as_path_sequence(source, LocalPath)
        destination = self._as_path_sequence(destination, RemotePath)

        async with self._acquire_client_session() as session:
            return await self._deploy(
                source_list=source,
                destination_list=destination,
                property_dictionary=property,
                upload_queue=upload_queue,
                session=session,
                recursive=recursive,
                quiet=quiet,
            )

    async def _deploy(
        self,
        source_list: Sequence[str | LocalPath],
        destination_list: Sequence[str | RemotePath],
        property_dictionary: dict | None,
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
        # TODO: This need to be fixed...incorrect upload size?
        await self._run_worker(
            queue=source_queue,
            worker=partial(
                self._deploy_task,
                source_queue=source_queue,
                upload_queue=upload_queue,
                recursive=recursive,
                # session=session,
            ),
            work_item_list=source_list,
        )

        upload_list = []

        # Upload
        await self._run_worker(
            queue=upload_queue,
            worker=partial(
                self._upload_task,
                destination_list=destination_list,
                property_dictionary=property_dictionary,
                upload_queue=upload_queue,
                upload_list=upload_list,
                session=session,
            ),
        )

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

            # logger.debug(f"Source: {source}, Type: {type(source)}")

            source_path = LocalPath(path=source)
            # logger.debug(f"Source Path: {source_path}")

            # Enqueue the deploy query response
            # The `upload_queue` should be relative path
            if source_path.is_file():
                before, _, after = str(source_path).rpartition(os.sep)
                await upload_queue.put((before, after))
            else:
                for file in source_path.get_file_list(recursive=recursive):
                    relative_path = os.path.relpath(file, start=source_path)
                    # local_path = source_path / relative_path
                    # Enqueue the upload queue
                    # TODO: Is there a better way for this...?
                    await upload_queue.put((source_path, relative_path))

    async def _upload_task(
        self,
        destination_list: Sequence[str | RemotePath],
        property_dictionary: dict | None,
        upload_queue: Queue,
        upload_list: list[RemotePath],
        session: ClientSession,
    ) -> None:
        """Upload Task

        :param destination_list: The destination list
        :type destination_list: Sequence[str | RemotePath]
        :param property_dictionary: The property(ies) metadata for the
            artifact(s)
        :type property_dictionary: dict
        :param upload_queue: The upload queue
        :type upload_queue: Queue
        :param upload_list: The upload list, store what is uploaded
        :type upload_list: list[RemotePath]
        :param session: The current session
        :type session: ClientSession
        """

        while True:
            upload = await upload_queue.get()

            # The signal to exit (check at the beginning)
            if upload is None:
                break

            source_path, relative_path = upload
            upload_path: LocalPath = LocalPath(source_path) / relative_path
            # logger.debug(f"Source Path: {source_path}")
            # logger.debug(f"Relative Path: {relative_path}")

            # logger.info(f"Upload: {upload_path}, Type: {type(upload_path)}")
            # logger.debug(f"Destination List: {destination_list}")
            # logger.debug(f"Property Dictionary: {property_dictionary}")

            local_path = LocalPath(path=upload_path)
            # logger.debug(f"Local Path: {local_path}")
            # Parse the filename, account for Universal Naming Convention (UNC) path
            # local_path_name = (
            #     local_path.name
            #     if local_path.name
            #     else str(local_path.expanduser().resolve()).split("/")[-1]
            # )
            # logger.debug(f"Local Path Name: {local_path_name}")

            # Upload the file
            logger.debug(f"Uploading: {upload_path}")

            async with aiofiles.open(local_path, "rb") as file:
                for destination in destination_list:
                    logger.debug(f"Destination: {destination}")

                    remote_path = RemotePath(path=f"{destination}/{relative_path}")
                    if property_dictionary:
                        # logger.debug(f"Property Dictionary: {property_dictionary}")
                        remote_path.parameter = property_dictionary
                    remote_path = remote_path.as_posix()
                    # logger.debug(f"Remote Path: {remote_path}")

                    # Update header with checksum
                    if local_path.checksum:
                        self._header.update(
                            {
                                "X-Checksum": local_path.checksum["md5"],
                                "X-Checksum-Sha1": local_path.checksum["sha1"],
                                "X-Checksum-Sha256": local_path.checksum["sha256"],
                            }
                        )

                    async with session.put(
                        url=str(remote_path),
                        headers=self._header,
                        data=file,
                    ) as response:
                        logger.debug(f"Response: {response}")
                        if response.status != 201:
                            logger.error(f"Upload Failed: {remote_path}")
                            raise RuntimeError(f"Upload Failed: {remote_path}")

                        data = await response.json()
                        upload_list.append(data["downloadUri"])

            logger.info(f"Uploaded: {upload}")

    # --------
    # Retrieve
    # --------

    async def retrieve(
        self,
        source: str | RemotePath | Sequence[str | RemotePath],
        destination: str | LocalPath | Sequence[str | LocalPath],
        recursive: bool = False,
        output_repository: bool = False,
        quiet: bool = False,
    ) -> list[str]:
        """Retrieve

        :param source: The source (Remote) path(s)
        :type source: str | RemotePath | Sequence[str | RemotePath]
        :param destination: The destination (Local) path(s)
        :type destination: str | LocalPath | Sequence[str | LocalPath]
        :param recursive: Whether to recursively retrieve artifact(s),
            defaults to False
        :type recursive: bool, optional
        :param output_repository: Whether to include the repository name
            in the destination path, defaults to False
        :type output_repository: bool, optional
        :param quiet: Whether to show retrieve progress, defaults to False
        :type quiet: bool, optional

        :return: The list of retrieved artifact(s)
        :rtype: list[str]
        """

        # Create a `download_queue`
        download_queue = Queue()

        # TODO: Convert one to many...for now
        source = self._as_path_sequence(source, RemotePath)
        destination = self._as_path_sequence(destination, LocalPath)

        async with self._acquire_client_session() as session:
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
        source_list: Sequence[str | RemotePath],
        destination_list: Sequence[str | LocalPath],
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
        await self._run_worker(
            queue=source_queue,
            worker=partial(
                self._retrieve_task,
                source_queue=source_queue,
                download_queue=download_queue,
                recursive=recursive,
                # session=session,
            ),
            work_item_list=source_list,
        )

        download_list = []

        # Download
        await self._run_worker(
            queue=download_queue,
            worker=partial(
                self._download_task,
                destination_list=destination_list,
                download_queue=download_queue,
                download_list=download_list,
                session=session,
                output_repository=output_repository,
            ),
        )

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
            source: str = await source_queue.get()

            # The signal to exit (check at the beginning)
            if source is None:
                break

            # logger.debug(f"Source: {source}, Type: {type(source)}")
            # logger.debug(f"Source Path: {urlparse(source).path}")

            remote_path = RemotePath(
                path=source,
                api_key=self._api_key,
                ssl=self._ssl,
            )
            # logger.debug(f"Remote Path: {remote_path}")

            # Enqueue the retrieve query response
            async for file in remote_path.get_file_list(recursive=recursive):
                # logger.warning(f"File: {file}, Type: {type(file)}")
                # TODO: Need to account for file with no extension
                if file:
                    if not await remote_path.folder:
                        # logger.debug(f"Download Input: {remote_path.parent}{file}")
                        await download_queue.put(f"{remote_path.parent}{file}")
                    else:
                        # logger.debug(f"Download Input: {source.rstrip('/')}{file}")
                        await download_queue.put(f"{source.rstrip('/')}{file}")

    async def _download_task(
        self,
        destination_list: Sequence[str | LocalPath],
        download_queue: Queue,
        download_list: list[str],
        session: ClientSession,
        output_repository: bool,
    ) -> None:
        """Download Task

        :param destination_list: The destination list
        :type destination_list: Sequence[str | LocalPath]
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

            # logger.debug(f"Download: {download}, Type: {type(download)}")

            remote_path = RemotePath(
                path=download,
                api_key=self._api_key,
                ssl=self._ssl,
            )

            # Download the file
            # logger.debug(f"Downloading: {download}")

            async with session.get(
                url=str(remote_path),
                headers=self._header,
            ) as response:
                for destination in destination_list:
                    location = LocalPath(path=remote_path.location)
                    # logger.warning(f"Location: {location}")
                    if output_repository:
                        location = LocalPath(f"{remote_path.repository}/{location}")

                    destination_path = (
                        Path(destination / location).expanduser().resolve()
                    )
                    # logger.debug(f"Destination Path: {destination_path}")
                    try:
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        logger.error(f"Operating System Error: {e}")

                    async with aiofiles.open(destination_path, "wb") as file:
                        async for chunk, _ in response.content.iter_chunks():
                            await file.write(chunk)

                    download_list.append(str(destination_path))

            # logger.info(f"Completed: {destination_path}")

    # ------
    # Delete
    # ------

    async def delete(
        self,
        source: str | RemotePath | Sequence[str | RemotePath],
        recursive: bool = False,
    ) -> list[str]:
        """Delete

        Delete artifact file(s) from Artifactory.

        :param source: The source (Remote) path(s)
        :type source: str | RemotePath | Sequence[str | RemotePath]
        :param recursive: Whether to recursively delete artifact(s),
            defaults to False
        :type recursive: bool, optional
        """

        source = self._as_path_sequence(source, RemotePath)

        async with self._acquire_client_session() as session:
            return await self._delete(
                source_list=source,
                session=session,
                recursive=recursive,
            )

    async def _delete(
        self,
        source_list: Sequence[str | RemotePath],
        session: ClientSession,
        recursive: bool,
    ) -> list[str]:
        """Delete

        Delete artifact file(s) from Artifactory.
        :param source_list: The source (Remote) path(s)
        :type source_list: Sequence[str | RemotePath]
        :param session: The current session
        :type session: ClientSession
        :param recursive: Whether to recursively delete artifact(s)
        :type recursive: bool
        """

        # Create a `source_queue` to store the `source_list` to delete
        source_queue = Queue()

        query_queue = Queue()

        # Query
        await self._run_worker(
            queue=source_queue,
            worker=partial(
                self._query_remote_task,
                source_queue=source_queue,
                query_queue=query_queue,
                recursive=recursive,
            ),
            work_item_list=source_list,
        )

        # Initialize a `delete_list` to store individual artifact files deleted
        delete_list = []

        # Delete
        await self._run_worker(
            queue=query_queue,
            worker=partial(
                self._delete_task,
                source_queue=query_queue,
                delete_list=delete_list,
                session=session,
            ),
        )

        return delete_list

    async def _query_remote_task(
        self,
        source_queue: Queue,
        query_queue: Queue,
        recursive: bool,
    ):
        """Query Remote Task

        :param source_queue: The source queue
        :type source_queue: Queue
        :param query_queue: The query queue, store the query result
        :type query_queue: Queue
        :param recursive: Whether to recursively query artifact(s)
        :type recursive: bool
        """

        while True:
            source = await source_queue.get()

            # The signal to exit (check at the beginning)
            if source is None:
                break

            logger.debug(f"Query Source: {source}, Type: {type(source)}")

            # NOTE: Need To Check On This...
            remote_path = (
                source
                if isinstance(source, RemotePath)
                else RemotePath(
                    path=source,
                    api_key=self._api_key,
                    ssl=self._ssl,
                )
            )

            async for file in remote_path.get_file_list(recursive=recursive):
                if not await remote_path.folder:
                    await query_queue.put(source)
                else:
                    await query_queue.put(f"{str(source).rstrip('/')}{file}")

    async def _delete_task(
        self,
        source_queue: Queue,
        delete_list: list[str],
        session: ClientSession,
    ):
        """Delete Task

        :param source_queue: The source queue
        :type source_queue: Queue
        """
        while True:
            source = await source_queue.get()

            # The signal to exit (check at the beginning)
            if source is None:
                break

            logger.debug(f"Delete: {source}, Type: {type(source)}")

            # NOTE: Need To Check On This...
            remote_path = (
                source
                if isinstance(source, RemotePath)
                else RemotePath(
                    path=source,
                    api_key=self._api_key,
                    ssl=self._ssl,
                )
            )

            # remote_path = RemotePath(
            #     path=str(source),
            #     api_key=self._api_key,
            #     ssl=self._ssl,
            # )

            async with session.delete(
                url=str(remote_path),
                headers=self._header,
            ) as response:
                if response.status != 204:
                    logger.error(f"Delete Failed: {remote_path}")
                    raise RuntimeError(f"Delete Failed: {remote_path}")

                # TODO: Return str or RemotePath...?
                delete_list.append(str(remote_path))

                logger.info(f"Deleted: {remote_path}")

    # ------
    # Search
    # ------

    async def search_property(
        self,
        source: str,
        property: dict,
        repository: list | None = None,
    ) -> AsyncGenerator[str, None]:
        """Search Property

        Search artifact(s) by property(ies).

        :param source: The source (Remote) URL for Artifactory
        :type source: str
        :param property: The property(ies) for the artifact(s)
        :type property: dict
        :param repository: The repository name(s) to search for
            artifact(s), defaults to None
        :type repository: list, optional

        :yield: The artifact(s) found
        :rtype: AsyncGenerator[str, None]
        """

        # logger.info("Search Property")
        # logger.debug(f"Source: {source}")
        # logger.debug(f"Property: {property}")
        # logger.debug(f"Repository: {repository}")

        remote_path = RemotePath(
            path=source,
            api_key=self._api_key,
            ssl=self._ssl,
        )

        artifact_list = remote_path.search_property(
            property=property,
            repository=repository,
        )

        async for artifact in artifact_list:
            # logger.debug(f"Artifact: {artifact}")
            yield artifact

    # ----------------------------
    # Asynchronous Context Manager
    # ----------------------------

    async def __aenter__(self):
        """Asynchronous Enter"""
        # Client Session
        self._client_session = self._create_client_session()

        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        """Asynchronous Exit

        :param exception_type: The exception type
        :type exception_type: Optional[Type[BaseException]]
        :param exception_value: The exception value
        :type exception_value: Optional[BaseException]
        :param exception_traceback: The exception traceback
        :type exception_traceback: Optional[TracebackType]
        """

        if self._client_session:
            await self._client_session.close()
