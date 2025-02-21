"""
Test Local Path
~~~~~~~~~~~~~~~
"""

import os
from pathlib import (PurePath, Path)

import pytest
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

        local_path = LocalPath(path=path)

        test_logger.debug(f"Local Path __str__: {str(local_path)}")
        test_logger.debug(f"Local Path __repr__: {repr(local_path)}")

        assert isinstance(local_path, PurePath)

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

