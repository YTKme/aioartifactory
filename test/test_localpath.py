"""
Test Local Path
~~~~~~~~~~~~~~~
"""

import hashlib
import os
from pathlib import (PurePath, Path)

import tealogger

from aioartifactory import LocalPath


ARTIFACTORY_API_KEY = os.environ.get("ARTIFACTORY_API_KEY")
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORKING_DIRECTORY = Path().cwd()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
test_logger = tealogger.get_logger("test.localpath")


class TestLocalPath:
    """Test Local Path"""

    def test_construct(self, path: str):
        """Test Construct"""

        test_logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        test_logger.debug(f"Local Path __str__: {str(local_path)}")
        test_logger.debug(f"Local Path __repr__: {repr(local_path)}")

        assert isinstance(local_path, PurePath)

    def test_md5(self, path: str):
        """Test MD5"""

        test_logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.md5(file.read()).hexdigest()

            assert isinstance(local_path.md5, str)

        except IsADirectoryError as error:
            test_logger.warning(f"Local Path is a Directory: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None

        test_logger.debug(f"Local Path MD5: {local_path.md5}")
        test_logger.debug(f"MD5 Checksum: {checksum}")

        assert local_path.md5 == checksum

    def test_sha1(self, path: str):
        """Test SHA1"""

        test_logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.sha1(file.read()).hexdigest()

            assert isinstance(local_path.sha1, str)

        except IsADirectoryError as error:
            test_logger.warning(f"Local Path is a Directory: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None

        test_logger.debug(f"Local Path SHA1: {local_path.sha1}")
        test_logger.debug(f"SHA1 Checksum: {checksum}")

        assert local_path.sha1 == checksum

    def test_sha256(self, path: str):
        """Test SHA256"""

        test_logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.sha256(file.read()).hexdigest()

            assert isinstance(local_path.sha256, str)

        except IsADirectoryError as error:
            test_logger.warning(f"Local Path is a Directory: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None

        test_logger.debug(f"Local Path SHA256: {local_path.sha256}")
        test_logger.debug(f"SHA256 Checksum: {checksum}")

        assert local_path.sha256 == checksum

    def test_get_file_list(
        self,
        path: str,
        file: str
    ):
        """Test Get File List"""

        test_logger.debug(f"Path: {path}")
        test_logger.debug(f"File: {file}")

        local_path = LocalPath(path=path)

        file_list = list(local_path.get_file_list())
        test_logger.debug(f"File List: {file_list}")

        assert (
            Path(f"{path}/{file}").expanduser().resolve()
            in list(file_list)
        )
