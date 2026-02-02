"""
Test Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
from pathlib import Path

import pytest
import tealogger

from aioartifactory import AIOArtifactory, LocalPath, RemotePath

ARTIFACTORY_API_KEY = os.environ.get("ARTIFACTORY_API_KEY")
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORK_PATH = Path().cwd()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "aioartifactory" / "tealogger.json"
)
test_logger = tealogger.get_logger("test.aioartifactory")


class TestAIOArtifactory:
    """Test Asynchronous Input Output (AIO) Artifactory Class"""

    # @pytest.mark.asyncio
    # async def test_host(self, host: str):
    #     """Test Host"""

    #     aioartifactory = AIOArtifactory(
    #         host=host,
    #         api_key=ARTIFACTORY_API_KEY,
    #     )
    #     test_logger.debug(f"Host: {await aioartifactory.host}")

    #     assert aioartifactory.host == host

    @pytest.mark.asyncio
    async def test_deploy_one_source_simple(
        self,
        source: str | LocalPath,
        destination: str,
    ):
        """Test Deploy One Source Simple

        Test simple deploy of one source to one destination.

        :param source: The source (Local) path(s)
        :type source: PathLike
        :param destination: The destination (Remote) path(s)
        :type destination: str
        """

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
        )
        test_logger.debug(f"Upload List: {upload_list}")

        for upload in upload_list:
            # test_logger.debug(f"Upload: {upload}")

            assert await RemotePath(path=upload, api_key=ARTIFACTORY_API_KEY).exists()

    @pytest.mark.asyncio
    async def test_deploy_one_source_recursive(
        self,
        source: str | LocalPath,
        destination: str,
    ):
        """Test Deploy One Source Recursive

        Test recursive deploy of one source to one destination.

        :param source: The source (Local) path(s)
        :type source: PathLike
        :param destination: The destination (Remote) path(s)
        :type destination: str
        """

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            recursive=True,
        )
        test_logger.debug(f"Upload List: {upload_list}")

    @pytest.mark.asyncio
    async def test_deploy_one_artifact(
        self,
        source: str | LocalPath,
        destination: str,
    ):
        """Test Deploy One Artifact"""

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
        )
        test_logger.debug(f"Upload List: {upload_list}")

        for upload in upload_list:
            remote_path = RemotePath(path=upload)
            test_logger.debug(f"Remote Path: {remote_path}")
            assert isinstance(remote_path, RemotePath)

    @pytest.mark.asyncio
    async def test_deploy_one_artifact_property(
        self,
        source: str | LocalPath,
        destination: str,
        property: dict,
    ):
        """Deploy One Artifact Property"""

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")
        test_logger.debug(f"Property: {property}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        upload_list = await aioartifactory.deploy(
            source=source,
            destination=destination,
            property=property,
        )
        test_logger.debug(f"Upload List: {upload_list}")

        for upload in upload_list:
            remote_path = RemotePath(path=upload)
            test_logger.debug(f"Remote Path: {remote_path}")
            assert isinstance(remote_path, RemotePath)

    @pytest.mark.asyncio
    async def test_retrieve_one_source_simple(
        self,
        source: str | LocalPath,
        destination: str | RemotePath,
    ):
        """Test Retrieve One Source Simple

        Test simple retrieve of one source to one destination.

        :param source: The source (Remote) path(s)
        :type source: str
        :param destination: The destination (Local) path(s)
        :type destination: PathLike
        """

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        download_list = await aioartifactory.retrieve(
            source=source,
            destination=destination,
        )

        for download in download_list:
            assert Path(download).exists()

    @pytest.mark.asyncio
    async def test_retrieve_one_source_recursive(
        self,
        source: str | LocalPath,
        destination: str | RemotePath,
    ):
        """Test Retrieve One Source Recursive

        :param source: The source (Remote) path(s)
        :type source: str
        :param destination: The destination (Local) path(s)
        :type destination: PathLike
        """

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        download_list = await aioartifactory.retrieve(
            source=source,
            destination=destination,
            recursive=True,
        )

        for download in download_list:
            assert Path(download).exists()

    @pytest.mark.asyncio
    async def test_retrieve_one_artifact(
        self,
        source: str | LocalPath,
        destination: str | RemotePath,
    ):
        """Test Retrieve One Artifact

        :param source: The source (Remote) path(s)
        :type source: str
        :param destination: The destination (Local) path(s)
        :type destination: PathLike
        """

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        download_list = await aioartifactory.retrieve(
            source=source,
            destination=destination,
        )

        test_logger.debug(f"Download List: {download_list}")

        for download in download_list:
            assert Path(download).exists()

    @pytest.mark.asyncio
    async def test_retrieve_many_artifact(
        self,
        source: list[str | LocalPath],
        destination: list[str | RemotePath],
    ):
        """Test Retrieve Many Artifact"""

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        await aioartifactory.retrieve(
            source=source,
            destination=destination,
            recursive=True,
        )

    @pytest.mark.asyncio
    async def test_search_property_simple(
        self,
        source: str,
        property: dict,
        repository: list,
        expect: list,
    ):
        """Test Search Property"""

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Property: {property}")
        test_logger.debug(f"Repository: {repository}")
        test_logger.debug(f"Expect: {expect}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        artifact_list = aioartifactory.search_property(
            source=source,
            property=property,
            repository=repository,
        )
        async for artifact in artifact_list:
            # test_logger.debug(f"Artifact: {artifact}")
            assert artifact in expect


#     async def test_retrieve_destination(
#         self,
#         source_list: list[str],
#         destination_list: list[PathLike]
#     ):
#         """Test Retrieve Destination"""
#         ...
