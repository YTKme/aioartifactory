"""
Local Path
~~~~~~~~~~
"""

from collections.abc import Generator
import hashlib
import os
from os import PathLike
from pathlib import Path
import sys

import tealogger


CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()

# Configure logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
logger = tealogger.get_logger("localpath")


class LocalPath(Path):
    """Local Path

    The Local Path class.
    """

    # NOTE: Backward compatibility for 3.11, remove in Python 3.12
    if sys.version_info < (3, 12):
        from pathlib import (_PosixFlavour, _WindowsFlavour)
        _flavour = _PosixFlavour() if os.name == "posix" else _WindowsFlavour()

    def __new__(
        cls,
        path: PathLike,
        *args,
        **kwargs
    ):
        """Create Constructor

        :param path: The path of the Local Path
        :type path: PathLike
        """
        return super().__new__(cls, path, *args, **kwargs)

    def __init__(
        self,
        path: PathLike,
        *args,
    ):
        """Initialize Constructor

        :param path: The path of the Local Path
        :type path: PathLike
        """
        # NOTE: Backward compatibility for 3.11, remove in Python 3.12
        if sys.version_info < (3, 12):
            super().__init__(*args)
        else:
            super().__init__(path, *args)

        self._path = path

    @property
    def md5(self) -> str:
        """MD5 Checksum

        Get the MD5 checksum of the Local Path.

        :return: The MD5 checksum of the Local Path
        :rtype: str
        """
        if Path(self._path).is_dir():
            logger.warning(f"Local Path is a Directory: {self._path}")
            return None

        with open(self._path, "rb") as file:
            checksum = hashlib.md5(file.read()).hexdigest()

        return checksum

    @property
    def sha1(self) -> str:
        """SHA1 Checksum

        Get the SHA1 checksum of the Local Path.

        :return: The SHA1 checksum of the Local Path
        :rtype: str
        """
        if Path(self._path).is_dir():
            logger.warning(f"Local Path is a Directory: {self._path}")
            return None

        with open(self._path, "rb") as file:
            checksum = hashlib.sha1(file.read()).hexdigest()

        return checksum

    @property
    def sha256(self) -> str:
        """SHA256 Checksum

        Get the SHA256 checksum of the Local Path.

        :return: The SHA256 checksum of the Local Path
        :rtype: str
        """
        if Path(self._path).is_dir():
            logger.warning(f"Local Path is a Directory: {self._path}")
            return None

        with open(self._path, "rb") as file:
            checksum = hashlib.sha256(file.read()).hexdigest()

        return checksum

    @property
    def checksum(self) -> dict:
        """Checksum

        Get the checksum(s) of the Local Path in a dictionary.

        Example:
            {
                "md5": "md5_checksum",
                "sha1": "sha1_checksum",
                "sha256": "sha256_checksum"
            }

        :return: The checksum(s) of the Local Path
        :rtype: dict
        """
        if Path(self._path).is_dir():
            logger.warning(f"Local Path is a Directory: {self._path}")
            return None

        with open(self._path, "rb") as file:
            file_data = file.read()
            checksum = {
                "md5": hashlib.md5(file_data).hexdigest(),
                "sha1": hashlib.sha1(file_data).hexdigest(),
                "sha256": hashlib.sha256(file_data).hexdigest(),
            }

        return checksum

    def get_file_list(
        self,
        recursive: bool = False,
    ) -> Generator[PathLike, None, None]:
        """Get File List

        Get the list of files in the Local Path.

        :param recursive: Whether to recursively search for file(s),
            defaults to False
        :type recursive: bool, optional

        :return: The list of file(s) in the Local Path
        :rtype: Generator[PathLike, None, None]
        """
        path = Path(self._path).expanduser().resolve()

        if not path.exists():
            logger.error(f"File Not Found: {path}")
            raise FileNotFoundError(f"File Not Found: {path}")

        if path.is_dir():
            # Directory
            stack = [path]
            while stack:
                current_path = stack.pop()
                try:
                    with os.scandir(current_path) as entry_list:
                        for entry in entry_list:
                            if entry.is_file():
                                yield Path(entry.path).expanduser().resolve()
                            elif entry.is_dir() and recursive:
                                stack.append(entry.path)
                except PermissionError:
                    logger.error(f"Permission Denied: {current_path}")
                # except FileNotFoundError:
                #     logger.error(f"File Not Found: {current_path}")
                # except OSError as error:
                #     logger.error(f"Error: {error}")
        elif path.is_file():
            # File
            yield path
        else:
            logger.error(f"Neither File Nor Directory: {path}")
            raise ValueError(f"Neither File Nor Directory: {path}")
