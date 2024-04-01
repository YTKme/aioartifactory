"""
Test Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import json
from pathlib import (PurePath, Path)
from urllib.parse import urlparse

import pytest
import tealogger

from aioartifactory import (AIOArtifactory, RemotePath)


tealogger.set_level(tealogger.DEBUG)


class TestRemotePath:
    """Test Remote Path
    """

    def test_construct(self, path: str):
        """Test Construct"""

        remote_path = RemotePath(
            path=path,
            api_key=API_KEY,
        )

        tealogger.debug(f'Remote Path __str__: {str(remote_path)}')
        tealogger.debug(f'Remote Path __repr__: {repr(remote_path)}')

        assert isinstance(remote_path, PurePath)

    def test_name(self, path: str):
        """Test Name"""

        remote_path = RemotePath(path=path)

        tealogger.debug(f'Remote Path Name: {remote_path.name}')

    def test_path(self, path: str):
        """Test Path"""

        remote_path = RemotePath(path=path)

        tealogger.debug(f'Remote Path Path: {remote_path.location}')

    @pytest.mark.asyncio
    async def test_sha256(self, path: str):
        """Test SHA256"""

        remote_path = RemotePath(path=path, api_key=API_KEY)

        checksum_sha256 = await remote_path.sha256

        tealogger.debug(f'Remote Path SHA256: {checksum_sha256}')

        assert isinstance(checksum_sha256, str)

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
    async def test_retrieve(self, source_list: list[str]):
        """Test Retrieve"""

        aioartifactory = AIOArtifactory(
            api_key=API_KEY
        )

        await aioartifactory.retrieve(
            source_list=source_list,
            destination_list=[Path(__file__).parent.resolve()],
            recursive=True,
        )
