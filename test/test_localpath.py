"""
Test Local Path
~~~~~~~~~~~~~~~
"""

import hashlib
import os
from pathlib import Path

import pytest
import tealogger
from pytest_mock import MockerFixture

from aioartifactory import LocalPath

ARTIFACTORY_API_KEY = os.environ.get("ARTIFACTORY_API_KEY")
CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORKING_DIRECTORY = Path().cwd()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "aioartifactory" / "tealogger.json"
)
logger = tealogger.get_logger("test.localpath")


@pytest.mark.localpath
class TestLocalPath:
    """Test Local Path"""

    ########
    # Real #
    ########

    @pytest.mark.real
    def test_construct(self, path: str):
        """Test Construct"""

        logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        # logger.debug(f"Local Path __str__: {str(local_path)}")
        # logger.debug(f"Local Path __repr__: {repr(local_path)}")

        assert isinstance(local_path, Path)

    @pytest.mark.real
    def test_md5(self, path: str):
        """Test MD5"""

        logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)
        logger.debug(f"Local Path MD5: {local_path.md5}")

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.md5(file.read()).hexdigest()
                logger.debug(f"Checksum: {checksum}")

            assert isinstance(local_path.md5, str)

        except IsADirectoryError as error:
            logger.warning(f"Local Path is a Directory: {path}")
            logger.error(f"Error: {error}")
            checksum = None
        except PermissionError as error:
            # NOTE: Jenkins Issue
            logger.warning(f"Permission Denied: {path}")
            logger.error(f"Error: {error}")
            checksum = None

        logger.debug(f"Local Path MD5: {local_path.md5}")
        logger.debug(f"MD5 Checksum: {checksum}")

        assert local_path.md5 == checksum

    @pytest.mark.real
    def test_sha1(self, path: str):
        """Test SHA1"""

        logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.sha1(file.read()).hexdigest()

            assert isinstance(local_path.sha1, str)

        except IsADirectoryError as error:
            logger.warning(f"Local Path is a Directory: {path}")
            logger.error(f"Error: {error}")
            checksum = None
        except PermissionError as error:
            # NOTE: Jenkins Issue
            logger.warning(f"Permission Denied: {path}")
            logger.error(f"Error: {error}")
            checksum = None

        logger.debug(f"Local Path SHA1: {local_path.sha1}")
        logger.debug(f"SHA1 Checksum: {checksum}")

        assert local_path.sha1 == checksum

    @pytest.mark.real
    def test_sha256(self, path: str):
        """Test SHA256"""

        logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)

        try:
            with open(Path(path), "rb") as file:
                checksum = hashlib.sha256(file.read()).hexdigest()

            assert isinstance(local_path.sha256, str)

        except IsADirectoryError as error:
            logger.warning(f"Local Path is a Directory: {path}")
            logger.error(f"Error: {error}")
            checksum = None
        except PermissionError as error:
            # NOTE: Jenkins Issue
            logger.warning(f"Permission Denied: {path}")
            logger.error(f"Error: {error}")
            checksum = None

        logger.debug(f"Local Path SHA256: {local_path.sha256}")
        logger.debug(f"SHA256 Checksum: {checksum}")

        assert local_path.sha256 == checksum

    @pytest.mark.real
    def test_checksum(self, path: str):
        """Test Checksum"""

        logger.debug(f"Path: {path}")

        local_path = LocalPath(path=path)
        logger.debug(f"Local Path Checksum: {local_path.checksum}")

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
            logger.warning(f"Local Path is a Directory: {path}")
            logger.error(f"Error: {error}")
            checksum = None
        except PermissionError as error:
            # NOTE: Jenkins Issue
            logger.warning(f"Permission Denied: {path}")
            logger.error(f"Error: {error}")
            checksum = None

        logger.debug(f"Local Path Checksum: {local_path.checksum}")
        logger.debug(f"Checksum: {checksum}")

        assert local_path.checksum == checksum

    @pytest.mark.real
    def test_get_file_list(self, path: str, file: str):
        """Test Get File List"""

        logger.debug(f"Path: {path}")
        logger.debug(f"File: {file}")

        local_path = LocalPath(path=path)

        file_list = list(local_path.get_file_list())
        logger.debug(f"File List: {file_list}")

        assert Path(f"{path}/{file}").expanduser().resolve() in list(file_list)

    @pytest.mark.real
    def test_get_file_list_exception(self, path: str, file: str):
        """Test Get File List"""

        logger.debug(f"Path: {path}")
        logger.debug(f"File: {file}")

        # Execute Local Path Get File List
        with pytest.raises(FileNotFoundError):
            local_path = LocalPath(
                path=f"{CURRENT_MODULE_PATH.parent}/_test/randompath/"
            )
            _ = list(local_path.get_file_list())

    ########
    # Mock #
    ########

    @pytest.mark.mock
    def test_construct_mock(self, mocker: MockerFixture):
        """Test Construct Mock"""

        # Mock Local Path Constructor
        mock_local_path_constructor = mocker.patch(
            "aioartifactory.localpath.LocalPath.__init__",
            return_value=None,
        )

        # Execute Local Path Constructor
        local_path = LocalPath(path=".")

        # logger.debug(f"Local Path __str__: {str(local_path)}")
        # logger.debug(f"Local Path __repr__: {repr(local_path)}")

        # Assert
        mock_local_path_constructor.assert_called_once_with(path=".")
        assert isinstance(local_path, Path)

    @pytest.mark.mock
    def test_md5_mock(self, mocker: MockerFixture):
        """Test MD5 Mock"""

        # Mock Local Path MD5
        mock_md5 = mocker.patch(
            "aioartifactory.localpath.LocalPath.md5",
            new_callable=mocker.PropertyMock,
        )
        mock_md5.return_value = "92c6b751585b0ff74f10f66c0534ed7a"

        # Execute Local Path MD5
        local_path = LocalPath(path=".")
        md5_checksum = local_path.md5

        # logger.debug(f"Local Path MD5: {md5_checksum}")

        # Assert
        mock_md5.assert_called_once()
        assert md5_checksum == "92c6b751585b0ff74f10f66c0534ed7a"

    @pytest.mark.mock
    def test_get_file_list_mock(
        self,
        mocker: MockerFixture,
    ):
        """Test Get File List Mock"""

        # Mock Local Path Get File List
        mock_get_file_list = mocker.patch(
            "aioartifactory.localpath.LocalPath.get_file_list"
        )
        mock_get_file_list.return_value = iter(
            [
                f"{CURRENT_MODULE_PATH.parent}/_test/localpath/alpha.txt",
                f"{CURRENT_MODULE_PATH.parent}/_test/localpath/beta.txt",
            ]
        )

        # Execute Local Path Get File List
        local_path = LocalPath(path=f"{CURRENT_MODULE_PATH.parent}/_test/localpath/")
        file_list = local_path.get_file_list()

        # logger.debug(f"File List: {file_list}")
        # logger.debug(f"Mock Get File List: {mock_get_file_list.return_value}")

        # Assert
        mock_get_file_list.assert_called_once()
        assert file_list == mock_get_file_list.return_value

    @pytest.mark.mock
    def test_get_file_list_exception_mock(
        self,
        mocker: MockerFixture,
    ):
        """Test Get File List Exception Mock"""

        # Mock Local Path Get File List
        # mock_get_file_list = mocker.patch(
        #     "aioartifactory.localpath.LocalPath.get_file_list",
        #     return_value=False,
        #     side_effect=FileNotFoundError,
        # )

        # Execute Local Path Get File List
        with pytest.raises(FileNotFoundError):
            local_path = LocalPath(
                path=f"{CURRENT_MODULE_PATH.parent}/_test/randompath/"
            )
            _ = list(local_path.get_file_list())

        # logger.debug(f"File List: {file_list}")
        # logger.debug(f"Mock Get File List: {mock_get_file_list.return_value}")

        # Assert
        # mock_get_file_list.assert_called_once()
