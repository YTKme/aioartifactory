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
        test_logger.warning(f"Local Path MD5: {local_path.md5}")

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.md5(file.read()).hexdigest()
                test_logger.warning(f"Checksum: {checksum}")

            assert isinstance(local_path.md5, str)

        except IsADirectoryError as error:
            test_logger.warning(f"Local Path is a Directory: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None
        except PermissionError as error:
            # NOTE: Jenkins Issue
            test_logger.warning(f"Permission Denied: {path}")
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
        except PermissionError as error:
            # NOTE: Jenkins Issue
            test_logger.warning(f"Permission Denied: {path}")
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
        except PermissionError as error:
            # NOTE: Jenkins Issue
            test_logger.warning(f"Permission Denied: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None

        test_logger.debug(f"Local Path SHA256: {local_path.sha256}")
        test_logger.debug(f"SHA256 Checksum: {checksum}")

        assert local_path.sha256 == checksum

    def test_checksum(self, path: str):
        """Test Checksum"""

        test_logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)
        test_logger.debug(f"Local Path Checksum: {local_path.checksum}")

        try:
            with open(Path(path), "rb") as file:
                file_data = file.read()
                checksum = {
                    "md5": hashlib.md5(file_data).hexdigest(),
                    "sha1": hashlib.sha1(file_data).hexdigest(),
                    "sha256": hashlib.sha256(file_data).hexdigest(),
                }

            assert isinstance(local_path.checksum, dict)
            assert isinstance(local_path.checksum["md5"], str)
            assert isinstance(local_path.checksum["sha1"], str)
            assert isinstance(local_path.checksum["sha256"], str)

        except IsADirectoryError as error:
            test_logger.warning(f"Local Path is a Directory: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None
        except PermissionError as error:
            # NOTE: Jenkins Issue
            test_logger.warning(f"Permission Denied: {path}")
            test_logger.error(f"Error: {error}")
            checksum = None

        test_logger.debug(f"Local Path Checksum: {local_path.checksum}")
        test_logger.debug(f"Checksum: {checksum}")

        assert local_path.checksum == checksum

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
