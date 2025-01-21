"""
Test Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
from os import PathLike
from pathlib import (PurePath, Path)
from urllib.parse import urlparse

import pytest
import tealogger

from aioartifactory import (AIOArtifactory, RemotePath)


ARTIFACTORY_API_KEY = os.environ.get('ARTIFACTORY_API_KEY')
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORK_PATH = Path().cwd()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / 'tealogger.json'
)
test_logger = tealogger.get_logger('test.aioartifactory')


class TestRemotePath:
    """Test Remote Path
    """

    def test_construct(self, path: str):
        """Test Construct"""

        remote_path = RemotePath(
            path=path,
            api_key=ARTIFACTORY_API_KEY,
        )

        tealogger.debug(f'Remote Path __str__: {str(remote_path)}')
        tealogger.debug(f'Remote Path __repr__: {repr(remote_path)}')

        assert isinstance(remote_path, PurePath)

    def test_name(self, path: str, name: str):
        """Test Name"""

        remote_path = RemotePath(path=path)

        tealogger.debug(f'Remote Path Name: {remote_path.name}')

        assert remote_path.name == name

    def test_location(self, path: str, location: PurePath):
        """Test Location"""

        remote_path = RemotePath(path=path)

        tealogger.debug(f'Remote Path Location: {remote_path.location}')

        assert isinstance(remote_path.location, PurePath)
        assert str(remote_path.location) == str(location)

    @pytest.mark.asyncio
    async def test_sha256(self, path: str, sha256: str):
        """Test SHA256"""

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        checksum_sha256 = await remote_path.sha256

        tealogger.debug(f'Remote Path SHA256: {checksum_sha256}')

        assert isinstance(checksum_sha256, str)
        assert checksum_sha256 == sha256

    def test_get_storage_api_path(self, path: str):
        """Test Get Storage API Path"""

        remote_path = RemotePath(path=path)

        parse_url = urlparse(path)
        expected_path = PurePath(
            '//',
            # Network Location and Path
            '/'.join([
                parse_url.netloc,
                *parse_url.path.split('/')[:2],
                'api/storage',
                *parse_url.path.split('/')[2:],
            ]),
        )

        tealogger.debug(
            f'Storage API Path: {remote_path._get_storage_api_path()}, '
            f'Type: {type(remote_path._get_storage_api_path())}'
        )

        tealogger.debug(
            f'Expected Path: {expected_path}, '
            f'Type: {type(expected_path)}'
        )

        assert isinstance(remote_path._get_storage_api_path(), PurePath)
        assert remote_path._get_storage_api_path() == expected_path

    @pytest.mark.asyncio
    async def test_get_storage_api_url(self, path: str, scheme: str):
        """Test Get Storage API Path"""

        remote_path = RemotePath(path=path)

        storage_api_url = remote_path._get_storage_api_url()
        tealogger.debug(
            f'Storage API URL: {storage_api_url}, '
            f'Type: {type(storage_api_url)}'
        )

        parse_url = urlparse(storage_api_url)
        tealogger.debug(parse_url)

        tealogger.debug(f'Class: {self.__class__.__name__}')

        assert parse_url.scheme == scheme


class TestAIOArtifactory:
    """Test Asynchronous Input Output (AIO) Artifactory Class
    """

    @pytest.mark.asyncio
    async def test_host(self, host: str):
        """Test Host"""

        aioartifactory = AIOArtifactory(
            host=host,
            api_key=ARTIFACTORY_API_KEY,
        )
        test_logger.debug(f'Host: {await aioartifactory.host}')

        # assert aioartifactory.host == host

    @pytest.mark.asyncio
    async def test_retrieve_one_source(
        self,
        source_list: str,
        destination_list: PathLike,
    ):
        """Test Retrieve One Source"""

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)
        test_logger.debug(f'Destination List: {destination_list}')

        download_list = await aioartifactory.retrieve(
            source=source_list,
            destination=destination_list,
        )

        for download in download_list:
            path = urlparse(download).path.replace('/artifactory', '')
            full_path = Path('/'.join([
                str(CURRENT_WORK_PATH),
                destination_list,
                path,
            ]))
            assert full_path.exists()

    @pytest.mark.asyncio
    async def test_retrieve_one_artifact(
        self,
        source_list: str,
        destination_list: PathLike,
    ):
        """Test Retrieve One Artifact"""

        aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

        await aioartifactory.retrieve(
            source=source_list,
            destination=destination_list,
        )

#     @pytest.mark.asyncio
#     async def test_retrieve_many(
#         self,
#         source: list[str],
#         destination: list[PathLike],
#     ):
#         """Test Retrieve Many"""

#         aioartifactory = AIOArtifactory(api_key=ARTIFACTORY_API_KEY)

#         await aioartifactory.retrieve(
#             source=source,
#             destination=[Path(__file__).parent.resolve()],
#             recursive=True,
#         )

#     async def test_retrieve_destination(
#         self,
#         source_list: list[str],
#         destination_list: list[PathLike]
#     ):
#         """Test Retrieve Destination"""
#         ...
