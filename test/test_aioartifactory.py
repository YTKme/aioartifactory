"""
Test Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
from os import PathLike
from pathlib import Path
from urllib.parse import urlparse

import pytest
import tealogger

from aioartifactory import AIOArtifactory


ARTIFACTORY_API_KEY = os.environ.get("ARTIFACTORY_API_KEY")
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORK_PATH = Path().cwd()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
test_logger = tealogger.get_logger("test.aioartifactory")


class TestAIOArtifactory:
    """Test Asynchronous Input Output (AIO) Artifactory Class
    """

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
    async def test_deploy_one_artifact(
        self,
        source: PathLike,
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

    @pytest.mark.asyncio
    async def test_retrieve_one_source(
        self,
        source: str,
        destination: PathLike,
    ):
        """Test Retrieve One Source

        Test retrieve of one source to one destination.

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
            path = urlparse(download).path.replace("/artifactory", "")
            full_path = Path("/".join([
                str(CURRENT_WORK_PATH),
                destination,
                path,
            ]))
            assert full_path.exists()

    # @pytest.mark.asyncio
    # async def test_retrieve_one_source_recursive(
    #     self,
    #     source: str,
    #     destination: PathLike,
    # ):
    #     """Test Retrieve One Source Recursive

    #     :param source: The source (Remote) path(s)
    #     :type source: str
    #     :param destination: The destination (Local) path(s)
    #     :type destination: PathLike
    #     """

    #     test_logger.debug(f"Source: {source}")
    #     test_logger.debug(f"Destination: {destination}")

    #     aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

    #     download_list = await aioartifactory.retrieve(
    #         source=source,
    #         destination=destination,
    #         recursive=True,
    #     )

    #     for download in download_list:
    #         path = urlparse(download).path.replace("/artifactory", "")
    #         full_path = Path("/".join([
    #             str(CURRENT_WORK_PATH),
    #             destination,
    #             path,
    #         ]))
    #         assert full_path.exists()

    @pytest.mark.asyncio
    async def test_retrieve_one_artifact(
        self,
        source: str,
        destination: PathLike,
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

        for download in download_list:
            path = urlparse(download).path.replace("/artifactory", "")
            full_path = Path("/".join([
                str(CURRENT_WORK_PATH),
                destination,
                path,
            ]))
            assert full_path.exists()

    @pytest.mark.asyncio
    async def test_retrieve_many(
        self,
        source: list[str],
        destination: list[PathLike],
    ):
        """Test Retrieve Many"""

        test_logger.debug(f"Source: {source}")
        test_logger.debug(f"Destination: {destination}")

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        await aioartifactory.retrieve(
            source=source,
            destination=destination,
            recursive=True,
        )

#     async def test_retrieve_destination(
#         self,
#         source_list: list[str],
#         destination_list: list[PathLike]
#     ):
#         """Test Retrieve Destination"""
#         ...
