"""
Local Path
~~~~~~~~~~
"""

from collections.abc import Generator
import os
from os import PathLike
from pathlib import (_PosixFlavour, _WindowsFlavour, PurePath, Path)
from typing import Optional

import tealogger


CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()

# Configure logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
logger = tealogger.get_logger("localpath")


class LocalPath(PurePath):
    """Local Path

    The Local Path class.
    """

    # NOTE: Backward compatibility for 3.11, remove in Python 3.12
    _flavour = _PosixFlavour() if os.name == "posix" else _WindowsFlavour()

    def __new__(
        cls,
        path: str,
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
        super().__init__(*args)

        self._path = path

    def get_file_list(
        self,
        recursive: bool = False,
    ) -> Generator[PathLike, None, None]:
        """Get File List

        Get the list of files in the Local Path.
        """
        stack = [Path(self._path).expanduser().resolve()]
        logger.debug(f"Stack: {stack}")

        while stack:
            current_path = stack.pop()
            try:
                with os.scandir(current_path) as entry_list:
                    for entry in entry_list:
                        logger.debug(f"Entry: {entry}")
                        if entry.is_file():
                            yield Path(entry.path).expanduser().resolve()
                        elif entry.is_dir() and recursive:
                            stack.append(entry.path)
            except PermissionError:
                logger.warning(f"Permission Denied: {current_path}")
            except FileNotFoundError:
                logger.warning(f"File Not Found: {current_path}")
            except OSError as error:
                logger.error(f"Error: {error}")
