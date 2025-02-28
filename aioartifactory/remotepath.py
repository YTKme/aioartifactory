"""
Remote Path
~~~~~~~~~~~
"""

import os
from pathlib import (_PosixFlavour, _WindowsFlavour, PurePath, Path)
from typing import (AsyncGenerator, Optional)
from urllib.parse import (unquote, urlparse)

from aiohttp import ClientSession

import tealogger


CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
SEPARATOR = "/"

# Configure logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
logger = tealogger.get_logger("remotepath")


class RemotePath(PurePath):
    """Remote Path

    The Remote Path class.
    """

    # NOTE: Backward compatibility for 3.11, remove in Python 3.12
    _flavour = _PosixFlavour() if os.name == "posix" else _WindowsFlavour()

    def __new__(
        cls,
        path: str,
        api_key: Optional[str] = None,  # NOTE: 3.11
        *args,
        **kwargs
    ):
        """Create Constructor

        :param path: The URL of the Remote Path
        :type path: str
        :param api_key: The Artifactory API Key
        :type api_key: str, optional
        """
        return super().__new__(cls, path, *args, **kwargs)

    def __init__(
        self,
        path: str,
        *args,
        **kwargs
    ):
        """Initialize Constructor

        :param path: The URL of the Remote Path
        :type path: str
        """
        super().__init__(*args)

        # Authentication
        if kwargs.get("api_key"):
            self._api_key = kwargs.get("api_key")
            self._header = {"X-JFrog-Art-Api": self._api_key}
        elif kwargs.get("token"):
            self._token = kwargs.get("token")
            self._header = {"Authorization": f"Bearer {self._token}"}

        self._path = path

        # TODO: Validate URL

        # Parse the URL path
        self._parse_url = urlparse(path)

    def __str__(self):
        """Informal or Nicely Printable String Representation"""
        return f"{self._path}"

    def __repr__(self):
        """Official String Representation"""
        return f"{self.__class__.__name__}({self._path!r})"

    @property
    def name(self) -> str:
        """Name"""
        return unquote(PurePath(self._parse_url.path).name)

    @property
    def repository(self) -> str:
        """Repository"""
        return unquote(PurePath(self._parse_url.path).parts[2])

    @property
    def location(self) -> PurePath:
        """Location

        The `location` is defined as the `path` component of the
        `urlparse` function, without the `/artifactory/<repository>`
        prefix `part`.
        See `urllib.parse.urlparse <https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse>`_.
        """
        return PurePath(unquote(
            SEPARATOR.join(PurePath(self._parse_url.path).parts[3:])
        ))

    @property
    async def sha256(self) -> str:
        """SHA256

        Get the SHA-256 checksum of the Remote Path if available, else
        return None.

        :return: The SHA-256 checksum of the Remote Path
        :rtype: str, None
        """
        storage_api_url = self._get_storage_api_url()
        # tealogger.debug(f"Storage API URL: {storage_api_url}")

        async with ClientSession() as session:
            async with session.get(
                url=storage_api_url,
                headers=self._header,
            ) as response:
                data = await response.json()

        return data["checksums"]["sha256"]

    def _get_storage_api_path(self) -> PurePath:
        """Get Storage API Path

        Get the storage API path of the Remote Path. Return it as a
        valid PurePath.

        :return: The PurePath of the storage API path
        :rtype: PurePath
        """
        return PurePath(
            "//",
            # Network Location and Path
            SEPARATOR.join([
                self._parse_url.netloc,
                *self._parse_url.path.split(SEPARATOR)[:2],
                "api/storage",
                *self._parse_url.path.split(SEPARATOR)[2:],
            ]),
        )

    def _get_storage_api_url(self) -> str:
        """Get Storage API URL
        """

        # The rest of the element(s) for URL
        parse_url_tail = "".join([
            # Parameter
            ";" if self._parse_url.params else "",
            self._parse_url.params,
            # Query
            "?" if self._parse_url.query else "",
            self._parse_url.query,
            # Fragment
            "#" if self._parse_url.fragment else "",
            self._parse_url.fragment,
        ])

        return (
            f"{self._parse_url.scheme}:"
            f"{self._get_storage_api_path()}"
            f"{parse_url_tail}"
        )

    async def exist(self) -> bool:
        """Exist

        Check if the Remote Path exist.

        :return: Whether the Remote Path exist
        :rtype: bool
        """
        storage_api_url = self._get_storage_api_url()

        async with ClientSession() as session:
            async with session.get(
                url=storage_api_url,
                headers=self._header,
            ) as response:
                return response.status == 200

    async def get_file_list(
        self,
        recursive: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Get File List

        Get a list of filename(s) with separator for the Remote Path.
        (e.g. `/file.ext`).
        """

        storage_api_url = self._get_storage_api_url()
        # logger.debug(f"Storage API URL: {storage_api_url}")

        query = "list&deep=1" if recursive else "list"
        query += "&listFolders=0&includeRootPath=0"
        # logger.debug(f"Query: {query}")

        async with ClientSession() as session:
            async with session.get(
                url=f"{storage_api_url}?{query}",
                headers=self._header,
            ) as response:
                if response.status == 400:
                    # NOTE: Need `and "Expected a folder" in await response.text()`?
                    _, _, after = str(self.location).rpartition(SEPARATOR)
                    yield SEPARATOR + after
                    # Need to `return` to terminate
                    return

                data = await response.json()

        for file in data["files"]:
            yield file["uri"]
