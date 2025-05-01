"""
Test Remote Path
~~~~~~~~~~~~~~~~
"""

import os
from pathlib import (PurePath, Path)
from urllib.parse import urlparse

import pytest
import tealogger

from aioartifactory import RemotePath


ARTIFACTORY_API_KEY = os.environ.get("ARTIFACTORY_API_KEY")
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORK_PATH = Path().cwd()
SEPARATOR = "/"

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
test_logger = tealogger.get_logger("test.remotepath")


class TestRemotePath:
    """Test Remote Path"""

    def test_construct(self, path: str):
        """Test Construct"""

        remote_path = RemotePath(
            path=path,
            api_key=ARTIFACTORY_API_KEY,
        )

        test_logger.debug(f"Remote Path __str__: {str(remote_path)}")
        test_logger.debug(f"Remote Path __repr__: {repr(remote_path)}")

        assert isinstance(remote_path, PurePath)

    def test_parameter_get(self, path: str, parameter: str):
        """Test Parameter Get"""

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Parameter: {remote_path.parameter}")

        assert remote_path.parameter == parameter


    def test_parameter_set(
        self,
        path: str,
        parameter: dict,
        expect: dict,
    ):
        """Test Parameter Set"""

        test_logger.debug(f"Path: {path}")
        test_logger.debug(f"Parameter: {parameter}")
        test_logger.debug(f"Expect: {expect}")

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Parameter: {remote_path.parameter}")

        remote_path.parameter = parameter

        assert str(remote_path) == str(expect)


    def test_name_get(self, path: str, name: str):
        """Test Name Get"""

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Name: {remote_path.name}")

        assert remote_path.name == name

    def test_parent_get(self, path: str, parent: str):
        """Test Parent Get"""

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Parent: {remote_path.parent}")

        assert remote_path.parent == parent

    def test_repository_get(self, path: str, repository: str):
        """Test Repository Get"""

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Repository: {remote_path.repository}")

        assert remote_path.repository == repository

    def test_location_get(self, path: str, location: str):
        """Test Location Get"""

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Location: {remote_path.location}")

        assert remote_path.location == location

    def test_search_api_ur_get(self, path: str, search_api_url: str):
        """Test Search API URL"""

        remote_path = RemotePath(path=path)

        test_logger.debug(f"Remote Path Search API URL: {remote_path.search_api_url}")

        assert remote_path.search_api_url == search_api_url

    @pytest.mark.asyncio
    async def test_folder_get(self, path: str, folder: bool):
        """Test Folder Get"""

        test_logger.debug(f"Path: {path}, Type: {type(path)}")
        test_logger.debug(f"Folder: {folder}, Type: {type(folder)}")

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        # remote_path_folder = remote_path.folder
        # test_logger.debug(f"Remote Path Folder: {remote_path_folder}, Type: {type(remote_path_folder)}")

        assert await remote_path.folder == folder

    @pytest.mark.asyncio
    async def test_md5_get(self, path: str, md5: str):
        """Test MD5 Get"""

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        checksum_md5 = await remote_path.md5

        test_logger.debug(f"Remote Path MD5: {checksum_md5}")

        assert isinstance(checksum_md5, str)
        assert checksum_md5 == md5

    @pytest.mark.asyncio
    async def test_sha1_get(self, path: str, sha1: str):
        """Test SHA1 Get"""

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        checksum_sha1 = await remote_path.sha1

        test_logger.debug(f"Remote Path SHA1: {checksum_sha1}")

        assert isinstance(checksum_sha1, str)
        assert checksum_sha1 == sha1

    @pytest.mark.asyncio
    async def test_sha256_get(self, path: str, sha256: str):
        """Test SHA256 Get"""

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        checksum_sha256 = await remote_path.sha256

        test_logger.debug(f"Remote Path SHA256: {checksum_sha256}")

        assert isinstance(checksum_sha256, str)
        assert checksum_sha256 == sha256

    def test_get_storage_api_path(self, path: str):
        """Test Get Storage API Path"""

        remote_path = RemotePath(path=path)

        parse_url = urlparse(path)
        # Remove leading SEPARATOR and split the path with SEPARATOR
        path_list = parse_url.path.lstrip(SEPARATOR).split(SEPARATOR)

        expected_path = PurePath(
            "//",
            # Network Location and Path
            "/".join([
                parse_url.netloc,
                *path_list[:1],
                "api/storage",
                *path_list[1:],
            ]),
        )

        test_logger.debug(
            f"Storage API Path: {remote_path._get_storage_api_path()}, "
            f"Type: {type(remote_path._get_storage_api_path())}"
        )

        test_logger.debug(
            f"Expected Path: {expected_path}, "
            f"Type: {type(expected_path)}"
        )

        assert isinstance(remote_path._get_storage_api_path(), PurePath)
        assert remote_path._get_storage_api_path() == expected_path

    @pytest.mark.asyncio
    async def test_get_storage_api_url(self, path: str, scheme: str):
        """Test Get Storage API Path"""

        remote_path = RemotePath(path=path)

        storage_api_url = remote_path._get_storage_api_url()
        test_logger.debug(
            f"Storage API URL: {storage_api_url}, "
            f"Type: {type(storage_api_url)}"
        )

        parse_url = urlparse(storage_api_url)
        test_logger.debug(parse_url)

        test_logger.debug(f"Class: {self.__class__.__name__}")

        assert parse_url.scheme == scheme

    @pytest.mark.asyncio
    async def test_exists(self, path: str, expect: bool):
        """Test Exists"""

        test_logger.debug(f"Path: {path}")
        test_logger.debug(f"Expect: {expect}")

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        assert (await remote_path.exists()) == expect

    @pytest.mark.asyncio
    async def test_get_file_list(self, path: str):
        """Test Get File List"""

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        file_list = remote_path.get_file_list()
        # test_logger.debug(f"File List: {file_list}, Type: {type(file_list)}")

        # https://peps.python.org/pep-0525/
        assert file_list.__aiter__() is file_list
        assert (await file_list.__anext__()) is not None

    @pytest.mark.asyncio
    async def test_search_property_simple(
        self,
        path: str,
        property: dict,
        repository: str,
    ):
        """Test Search Property Simple"""

        test_logger.debug(f"Path: {path}")
        test_logger.debug(f"Property: {property}")
        test_logger.debug(f"Repository: {repository}")

        remote_path = RemotePath(path=path, api_key=ARTIFACTORY_API_KEY)

        artifact_list = await remote_path.search_property(
            property=property,
            repository=repository,
        )
        test_logger.debug(f"Artifact List: {artifact_list}")
