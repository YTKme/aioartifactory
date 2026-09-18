"""
Test Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
from asyncio import Queue, TaskGroup
from pathlib import Path

import pytest
import tealogger
from pytest_mock import MockerFixture

from aioartifactory import AIOArtifactory, LocalPath, RemotePath
from aioartifactory.configuration import DEFAULT_MAXIMUM_CONNECTION

ARTIFACTORY_API_KEY = os.environ.get("ARTIFACTORY_API_KEY")
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORK_PATH = Path().cwd()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "aioartifactory" / "tealogger.json"
)
logger = tealogger.get_logger("test.aioartifactory")


@pytest.mark.aioartifactory
class TestAIOArtifactory:
    """Test Asynchronous Input Output (AIO) Artifactory Class"""

    ########
    # Real #
    ########

    # @pytest.mark.asyncio
    # async def test_host(self, host: str):
    #     """Test Host"""

    #     aioartifactory = AIOArtifactory(
    #         host=host,
    #         api_key=ARTIFACTORY_API_KEY,
    #     )
    #     test_logger.debug(f"Host: {await aioartifactory.host}")

    #     assert aioartifactory.host == host

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_deploy_one_source_simple(
        self,
        source: str,
        destination: str,
    ):
        """Test Deploy One Source Simple

        Test simple deploy of one source to one destination.

        :param source: The source (Local) path(s)
        :type source: str
        :param destination: The destination (Remote) path(s)
        :type destination: str
        """

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            recursive=False,
        )
        # logger.debug(f"Upload List: {upload_list}")

        async with TaskGroup() as group:
            task_list = [
                group.create_task(
                    RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()
                )
                for upload in upload_list
            ]

        for task in task_list:
            assert task.result()

        # for upload in upload_list:
        #     assert await RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()
        #     # logger.debug(f"Upload Item: {upload}")

        # Clean Up
        remote_path = RemotePath(path=destination, api_key=ARTIFACTORY_API_KEY)
        delete_list = await aioartifactory.delete(source=remote_path, recursive=False)

        async with TaskGroup() as group:
            task_list = [
                group.create_task(
                    RemotePath(path=delete_item, api_key=ARTIFACTORY_API_KEY).exists()
                )
                for delete_item in delete_list
            ]

        for task in task_list:
            assert not task.result()

        # for delete_item in delete_list:
        #     logger.debug(f"Delete Item: {delete_item}")
        #     assert not await RemotePath(
        #         path=delete_item, api_key=ARTIFACTORY_API_KEY
        #     ).exists()

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_deploy_one_source_recursive(
        self,
        source: str,
        destination: str,
    ):
        """Test Deploy One Source Recursive

        Test recursive deploy of one source to one destination.

        :param source: The source (Local) path(s)
        :type source: str
        :param destination: The destination (Remote) path(s)
        :type destination: str
        """

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            recursive=True,
        )
        # logger.debug(f"Upload List: {upload_list}")

        async with TaskGroup() as group:
            task_list = [
                group.create_task(
                    RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()
                )
                for upload in upload_list
            ]

        for task in task_list:
            assert task.result()

        # for upload in upload_list:
        #     assert await RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()
        #     # logger.debug(f"Upload Item: {upload}")

        # Clean Up
        remote_path = RemotePath(path=destination, api_key=ARTIFACTORY_API_KEY)
        delete_list = await aioartifactory.delete(source=remote_path, recursive=True)

        for delete_item in delete_list:
            logger.debug(f"Delete Item: {delete_item}")
            assert not await RemotePath(
                path=delete_item, api_key=ARTIFACTORY_API_KEY
            ).exists()

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_deploy_one_artifact(
        self,
        source: str | LocalPath,
        destination: str,
    ):
        """Test Deploy One Artifact"""

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            recursive=False,
        )
        logger.debug(f"Upload List: {upload_list}")

        for upload in upload_list:
            remote_path = RemotePath(path=upload)
            logger.debug(f"Remote Path: {remote_path}")
            assert isinstance(remote_path, RemotePath)

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_deploy_one_artifact_property(
        self,
        source: str | LocalPath,
        destination: str,
        property: dict,
    ):
        """Deploy One Artifact Property"""

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")
        logger.debug(f"Property: {property}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            property=property,
        )
        logger.debug(f"Upload List: {upload_list}")

        for upload in upload_list:
            remote_path = RemotePath(path=upload)
            logger.debug(f"Remote Path: {remote_path}")
            assert isinstance(remote_path, RemotePath)

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_retrieve_one_source_simple(
        self,
        source: str | RemotePath,
        destination: str | LocalPath,
    ):
        """Test Retrieve One Source Simple

        Test simple retrieve of one source to one destination.

        :param source: The source (Remote) path(s)
        :type source: str
        :param destination: The destination (Local) path(s)
        :type destination: PathLike
        """

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        download_list = await aioartifactory.retrieve(
            source=source,
            destination=destination,
        )

        for download in download_list:
            assert Path(download).exists()

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_retrieve_one_source_recursive(
        self,
        source: str | RemotePath,
        destination: str | LocalPath,
    ):
        """Test Retrieve One Source Recursive

        :param source: The source (Remote) path(s)
        :type source: str
        :param destination: The destination (Local) path(s)
        :type destination: PathLike
        """

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        download_list = await aioartifactory.retrieve(
            source=source,
            destination=destination,
            recursive=True,
        )

        for download in download_list:
            assert Path(download).exists()

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_retrieve_one_artifact(
        self,
        source: str | RemotePath,
        destination: str | LocalPath,
    ):
        """Test Retrieve One Artifact

        :param source: The source (Remote) path(s)
        :type source: str
        :param destination: The destination (Local) path(s)
        :type destination: PathLike
        """

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        download_list = await aioartifactory.retrieve(
            source=source,
            destination=destination,
        )

        logger.debug(f"Download List: {download_list}")

        for download in download_list:
            assert Path(download).exists()

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_retrieve_many_artifact(
        self,
        source: list[str | RemotePath],
        destination: list[str | LocalPath],
    ):
        """Test Retrieve Many Artifact"""

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        await aioartifactory.retrieve(
            source=source,
            destination=destination,
            recursive=True,
        )

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_delete_one_source_simple(
        self,
        source: str,
        destination: str,
    ):
        """Test Delete One Source Simple"""

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            recursive=False,
        )
        # logger.debug(f"Upload List: {upload_list}")

        async with TaskGroup() as group:
            task_list = [
                group.create_task(
                    RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()
                )
                for upload in upload_list
            ]

        for task in task_list:
            assert task.result()

        # for upload in upload_list:
        #     assert await RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()
        #     # logger.debug(f"Upload Item: {upload}")

        remote_path = RemotePath(path=destination, api_key=ARTIFACTORY_API_KEY)
        delete_list = await aioartifactory.delete(source=remote_path, recursive=False)

        for delete_item in delete_list:
            logger.debug(f"Delete Item: {delete_item}")
            assert not await RemotePath(
                path=delete_item, api_key=ARTIFACTORY_API_KEY
            ).exists()

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_delete_one_artifact(
        self,
        source: str,
        destination: str,
    ):
        """Test Delete One Artifact"""

        logger.debug(f"Source: {source}")
        logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            recursive=False,
        )
        logger.debug(f"Upload List: {upload_list}")

        filename = source.split("/")[-1]
        logger.debug(f"Filename: {filename}")

        delete_list = await aioartifactory.delete(
            source=f"{destination}/{filename}",
            recursive=False,
        )
        logger.debug(f"Delete List: {delete_list}")

    @pytest.mark.real
    @pytest.mark.asyncio
    async def test_search_property_simple(
        self,
        source: str,
        property: dict,
        repository: list,
        expect: list,
    ):
        """Test Search Property"""

        logger.debug(f"Source: {source}")
        logger.debug(f"Property: {property}")
        logger.debug(f"Repository: {repository}")
        logger.debug(f"Expect: {expect}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        artifact_list = aioartifactory.search_property(
            source=source,
            property=property,
            repository=repository,
        )
        async for artifact in artifact_list:
            # test_logger.debug(f"Artifact: {artifact}")
            assert artifact in expect

    ########
    # Mock #
    ########

    @pytest.mark.mock
    @pytest.mark.asyncio
    async def test_delete_one_source_simple_mock(
        self,
        # source: str,
        mocker: MockerFixture,
    ):
        """Test Delete One Source Simple Mock"""

        delete_source = "https://example.com/artifactory/repository/artifact.txt"

        # Mock AIOArtifactory Delete Method
        mock_delete = mocker.patch(
            "aioartifactory.aioartifactory.AIOArtifactory.delete"
        )
        mock_delete.return_value = iter([delete_source])

        # Execute AIOArtifactory Delete Method
        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)
        _ = await aioartifactory.delete(source=delete_source)

        # logger.warning(f"Delete List: {delete_list}")
        # logger.warning(f"Mock Delete Return Value: {mock_delete.return_value}")

        # Assert
        mock_delete.assert_called_once_with(source=delete_source)
        assert delete_source in list(mock_delete.return_value)

    @pytest.mark.mock
    @pytest.mark.parametrize(
        "path, path_type",
        [
            ("./_test/aioartifactory/alpha.txt", LocalPath),
            (LocalPath("./_test/aioartifactory/alpha.txt"), LocalPath),
            ("https://example.com/artifactory/repository/alpha.txt", RemotePath),
            (
                RemotePath("https://example.com/artifactory/repository/alpha.txt"),
                RemotePath,
            ),
        ],
    )
    def test_as_path_sequence_one_path_mock(
        self,
        path: str | LocalPath | RemotePath,
        path_type: type[LocalPath] | type[RemotePath],
    ):
        """Test As Path Sequence One Path Mock

        Test one path become a one item sequence.

        :param path: The (single) path
        :type path: str | LocalPath | RemotePath
        :param path_type: The path type of a single path
        :type path_type: type[LocalPath] | type[RemotePath]
        """

        path_sequence = AIOArtifactory._as_path_sequence(path, path_type)

        assert path_sequence == [path]

    @pytest.mark.mock
    def test_as_path_sequence_many_path_mock(self):
        """Test As Path Sequence Many Path Mock

        Test a sequence of path(s) pass through unchanged.
        """

        path_list = [
            "https://example.com/artifactory/repository/alpha.txt",
            "https://example.com/artifactory/repository/beta.txt",
        ]

        assert AIOArtifactory._as_path_sequence(path_list, RemotePath) is path_list

    @pytest.mark.mock
    @pytest.mark.asyncio
    async def test_delete_client_session_reuse_mock(
        self,
        mocker: MockerFixture,
    ):
        """Test Delete Client Session Reuse Mock

        Test the client session of the instance, when available, is
        reuse instead of a new one being create.

        :param mocker: The mocker fixture
        :type mocker: MockerFixture
        """

        delete_source = "https://example.com/artifactory/repository/artifact.txt"

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)
        client_session = aioartifactory._create_client_session()
        aioartifactory._client_session = client_session

        create_client_session = mocker.spy(aioartifactory, "_create_client_session")
        mock_delete = mocker.patch.object(
            AIOArtifactory,
            "_delete",
            return_value=[delete_source],
        )

        delete_list = await aioartifactory.delete(source=delete_source)

        # Assert the client session of the instance is reuse
        create_client_session.assert_not_called()
        assert mock_delete.call_args.kwargs["session"] is client_session
        # Assert the source (single) path become a one item sequence
        assert mock_delete.call_args.kwargs["source_list"] == [delete_source]
        assert delete_list == [delete_source]

    @pytest.mark.mock
    @pytest.mark.asyncio
    async def test_delete_client_session_create_mock(
        self,
        mocker: MockerFixture,
    ):
        """Test Delete Client Session Create Mock

        Test a new client session is create, then close, when the
        instance does not have one.

        :param mocker: The mocker fixture
        :type mocker: MockerFixture
        """

        delete_source = "https://example.com/artifactory/repository/artifact.txt"

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        create_client_session = mocker.spy(aioartifactory, "_create_client_session")
        mock_delete = mocker.patch.object(
            AIOArtifactory,
            "_delete",
            return_value=[delete_source],
        )

        delete_list = await aioartifactory.delete(source=delete_source)

        # Assert a new client session is create, then close
        create_client_session.assert_called_once()
        session = mock_delete.call_args.kwargs["session"]
        assert session is create_client_session.spy_return
        assert session.closed
        assert delete_list == [delete_source]

    @pytest.mark.mock
    @pytest.mark.asyncio
    async def test_run_worker_work_item_list_mock(self):
        """Test Run Worker Work Item List Mock

        Test the worker helper run one worker per work item, capped by
        the default maximum connection, and signal each worker to exit.
        """

        work_item_list = [f"artifact-{index}.txt" for index in range(3)]
        queue = Queue()
        worker_list = []
        process_list = []

        async def worker():
            """Worker"""
            worker_list.append(worker)
            while True:
                work_item = await queue.get()
                if work_item is None:
                    break
                process_list.append(work_item)

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)
        await aioartifactory._run_worker(
            queue=queue,
            worker=worker,
            work_item_list=work_item_list,
        )

        # Assert one worker per work item, each receive a stop signal
        assert len(worker_list) == min(len(work_item_list), DEFAULT_MAXIMUM_CONNECTION)
        assert sorted(process_list) == sorted(work_item_list)
        assert queue.empty()

    @pytest.mark.mock
    @pytest.mark.asyncio
    async def test_run_worker_queue_size_mock(self):
        """Test Run Worker Queue Size Mock

        Test the worker helper run one worker per item already in the
        queue, capped by the default maximum connection.
        """

        queue = Queue()
        for index in range(DEFAULT_MAXIMUM_CONNECTION + 2):
            queue.put_nowait(f"artifact-{index}.txt")
        queue_size = queue.qsize()

        worker_list = []
        process_list = []

        async def worker():
            """Worker"""
            worker_list.append(worker)
            while True:
                work_item = await queue.get()
                if work_item is None:
                    break
                process_list.append(work_item)

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)
        await aioartifactory._run_worker(queue=queue, worker=worker)

        # Assert the worker count is cap by the default maximum connection
        assert len(worker_list) == DEFAULT_MAXIMUM_CONNECTION
        assert len(process_list) == queue_size
        assert queue.empty()


#     async def test_retrieve_destination(
#         self,
#         source_list: list[str],
#         destination_list: list[PathLike]
#     ):
#         """Test Retrieve Destination"""
#         ...
