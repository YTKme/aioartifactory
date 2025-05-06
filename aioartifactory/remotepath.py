"""
Remote Path
~~~~~~~~~~~
"""

from collections.abc import AsyncGenerator
import os
from pathlib import PurePath, Path
import platform
import sys
from typing import Optional
from urllib.parse import (unquote, urlparse, urlunparse)

from aiohttp import ClientSession, TCPConnector

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
    if sys.version_info < (3, 12):
        from pathlib import (_PosixFlavour, _WindowsFlavour)
        _flavour = _PosixFlavour() if os.name == "posix" else _WindowsFlavour()

    def __new__(
        cls,
        path: str,
        api_key: Optional[str] = None,  # NOTE: 3.11
        ssl: Optional[bool] = True,
        *args,
        **kwargs
    ):
        """Create Constructor

        :param path: The URL of the Remote Path
        :type path: str
        :param api_key: The Artifactory API Key
        :type api_key: str, optional
        :param ssl: Whether to check SSL certification, relax by setting
            to False, defaults to True
        :type ssl: bool, optional
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

        # Secure Sockets Layer (SSL) Certification Check
        self._ssl = kwargs.get("ssl", True)

        # self._path = path

        # TODO: Validate URL

        # Parse the URL path
        self._parse_url = urlparse(path)

    def __str__(self):
        """Informal or Nicely Printable String Representation"""
        return f"{urlunparse(self._parse_url)}"

    def __repr__(self):
        """Official String Representation"""
        return f"{self.__class__.__name__}({urlunparse(self._parse_url)!r})"

    @property
    def parameter(self) -> str:
        """Parameter"""
        return self._parse_url.params

    @parameter.setter
    def parameter(self, value_dictionary: dict):
        """Parameter Setter"""
        # if self._parse_url.params:
        #     self._path = self._path.replace(self._parse_url.params, value)

        #
        self._parse_url = self._parse_url._replace(
            params=";".join([
                f"{key}={value}" for key, value
                in value_dictionary.items()
            ])
        )

    @property
    def name(self) -> str:
        """Name"""
        return unquote(PurePath(self._parse_url.path).name)

    @property
    def parent(self) -> str:
        """Parent"""
        parent_url = self._parse_url._replace(
            path=str(PurePath(self._parse_url.path).parent.as_posix())
        )
        # logger.debug(f"Parent: {urlunparse(parent_url)}")
        return unquote(urlunparse(parent_url))

    @property
    def repository(self) -> str:
        """Repository"""
        return unquote(PurePath(self._parse_url.path).parts[2])

    @property
    def location(self) -> str:
        """Location

        The `location` is defined as the `path` component of the
        `urlparse` function, without the `/artifactory/<repository>`
        prefix `part`.
        See `urllib.parse.urlparse <https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse>`_.
        """
        return PurePath(unquote(
            SEPARATOR.join(PurePath(self._parse_url.path).parts[3:])
        )).as_posix()

    @property
    def search_api_url(self) -> str:
        """Search API URL

        Get the Search Application Programming Interface (API) Uniform
        Resource Locator (URL) of the Remote Path.
        See `Artifactory Property Search <https://jfrog.com/help/r/jfrog-rest-apis/property-search>`_.
        """

        return unquote(
            "".join([
                self._parse_url.scheme,
                "://",
                self._parse_url.netloc,
                "/artifactory/api/search/prop",
            ])
        )

    @property
    async def folder(self) -> bool:
        """Folder

        Determine whether or not the Remote Path is a folder.

        :return: Whether or not the Remote Path is a folder
        :rtype: bool
        """
        storage_api_url = self._get_storage_api_url()
        # logger.debug(f"Storage API URL: {storage_api_url}")

        query = "list"

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            async with session.get(
                url=f"{storage_api_url}?{query}",
                headers=self._header,
            ) as response:
                # logger.debug(f"Response: {await response.json()}")
                if response.status == 400:
                    return False

        return True

    @property
    async def md5(self) -> str:
        """MD5

        Get the MD5 checksum of the Remote Path if available, else
        return None.

        :return: The MD5 checksum of the Remote Path
        :rtype: str | None
        """
        storage_api_url = self._get_storage_api_url()
        # logger.debug(f"Storage API URL: {storage_api_url}")

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            async with session.get(
                url=storage_api_url,
                headers=self._header,
            ) as response:
                # logger.warning(f"Response: {await response.json()}")
                data = await response.json()

        return data["checksums"]["md5"]

    @property
    async def sha1(self) -> str:
        """SHA1

        Get the SHA-1 checksum of the Remote Path if available, else
        return None.

        :return: The SHA-1 checksum of the Remote Path
        :rtype: str | None
        """
        storage_api_url = self._get_storage_api_url()
        # logger.debug(f"Storage API URL: {storage_api_url}")

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            async with session.get(
                url=storage_api_url,
                headers=self._header,
            ) as response:
                data = await response.json()

        return data["checksums"]["sha1"]

    @property
    async def sha256(self) -> str:
        """SHA256

        Get the SHA-256 checksum of the Remote Path if available, else
        return None.

        :return: The SHA-256 checksum of the Remote Path
        :rtype: str | None
        """
        storage_api_url = self._get_storage_api_url()
        # logger.debug(f"Storage API URL: {storage_api_url}")

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
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
        # Remove leading SEPARATOR and split the path with SEPARATOR
        path_list = self._parse_url.path.lstrip(SEPARATOR).split(SEPARATOR)

        return PurePath(
            "//",
            # Network Location and Path
            SEPARATOR.join([
                self._parse_url.netloc,
                *path_list[:1],
                "api/storage",
                *path_list[1:],
            ]),
        )

    def _get_storage_api_url(self) -> str:
        """Get Storage API URL"""

        storage_api_path = self._get_storage_api_path().as_posix()

        # NOTE: Backward compatibility for 3.11, remove in Python 3.12
        if platform.system() == "Windows" and sys.version_info < (3, 12):
            storage_api_path = f"/{storage_api_path}"

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
            f"{storage_api_path}"
            f"{parse_url_tail}"
        )

    async def exists(self) -> bool:
        """Exists

        Check if the Remote Path exists.

        :return: Whether the Remote Path exists
        :rtype: bool
        """
        storage_api_url = self._get_storage_api_url()

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            try:
                async with session.get(
                    url=storage_api_url,
                    headers=self._header,
                ) as response:
                    # logger.warning(f"Response: {await response.json()}")
                    return response.status == 200
            except OSError as error:
                logger.error(f"Error: {error}")
                return False

    async def get_file_list(
        self,
        recursive: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Get File List

        Get a list of filename(s) with separator for the Remote Path.
        (e.g. `/file.ext`).
        """

        storage_api_url = self._get_storage_api_url()
        # logger.warning(f"Storage API URL: {storage_api_url}")

        query = "list&deep=1" if recursive else "list"
        query += "&listFolders=0&includeRootPath=0"
        # logger.debug(f"Query: {query}")

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            try:
                async with session.get(
                    url=f"{storage_api_url}?{query}",
                    headers=self._header,
                ) as response:
                    # logger.debug(f"Response: {await response.json()}")
                    if response.status == 400:
                        # NOTE: Need `and "Expected a folder" in await response.text()`?
                        _, _, after = str(self.location).rpartition(SEPARATOR)
                        yield SEPARATOR + after
                        # Need to `return` to terminate
                        return
                    elif response.status == 404:
                        # NOTE: Might need some improvement
                        logger.warning(f"{response.status} {response.reason}")
                        raise FileNotFoundError(f"Could Not Find: {storage_api_url}")

                    data = await response.json()

                    for file in data["files"]:
                        yield file["uri"]
            except OSError as error:
                logger.error(f"Error: {error}")
                yield None

    # ----
    # List
    # ----

    async def list(
        self,
        recursive: bool = False,
        list_folder: bool = False,
        timestamp: bool = False,
        include_root_path: bool = False,
    ) -> AsyncGenerator[str, None]:
        """List

        List the item(s) in the Remote Path.

        :param recursive: Whether to recursively list item(s), defaults
            to False
        :type recursive: bool, optional

        :yield: The list of item(s)
        :rtype: AsyncGenerator[str, None]
        """

        storage_api_url = self._get_storage_api_url()
        # logger.warning(f"Storage API URL: {storage_api_url}")

        query = "list&deep=1" if recursive else "list"
        query += "&listFolders=1" if list_folder else "&listFolders=0"
        query += "&timestamp=1" if timestamp else "&timestamp=0"
        query += "&includeRootPath=1" if include_root_path else "&includeRootPath=0"
        # logger.debug(f"Query: {query}")

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            try:
                async with session.get(
                    url=f"{storage_api_url}?{query}",
                    headers=self._header,
                ) as response:
                    # logger.debug(f"Response: {await response.json()}")
                    if response.status == 400:
                        raise ValueError(f"Bad Request: {response.reason}")

                    data = await response.json()

                    if not data["files"]:
                        logger.warning("No Item(s) Found For The Given Query.")
                        yield None

                    for file in data["files"]:
                        yield file["uri"]
            except OSError as error:
                logger.error(f"Error: {error}")
                yield None

    # ------
    # Search
    # ------

    async def search_property(
        self,
        property: dict,
        repository: list = None,
    ) -> AsyncGenerator[str, None]:
        """Search Property

        Search artifact(s) by property(ies) for a Remote Path.

        :param property: The property(ies) for the artifact(s)
        :type property: dict
        :param repository: The repository name(s) to search for
            artifact(s), defaults to None
        :type repository: list, optional

        :yield: The list of artifact(s) found
        :rtype: AsyncGenerator[str, None]
        """

        # logger.info("Search Property")
        # logger.debug(f"Property: {property}")
        # logger.debug(f"Repository: {repository}")

        search_api_url = self.search_api_url
        # logger.debug(f"Search API URL: {search_api_url}")

        query = "?"

        # Property
        for property_name, property_value in property.items():
            query += f"{property_name}={property_value}&"

        # Repository
        if repository:
            query = f"{query}repos={','.join(repository)}"
        else:
            query = query[:-1]
        # logger.debug(f"Query: {query}")

        async with ClientSession(
            connector=TCPConnector(ssl=self._ssl)
        ) as session:
            try:
                async with session.get(
                    url=f"{search_api_url}{query}",
                    headers=self._header,
                ) as response:
                    if response.status == 400:
                        raise ValueError(f"Bad Request: {response.reason}")

                    data = await response.json()
                    # logger.debug(f"Response Data: {data}")

                    if not data["results"]:
                        logger.warning(
                            "No Artifact(s) Found For The Given Property(ies)."
                        )
                        yield None

                    for artifact in data["results"]:
                        # logger.debug(f"Artifact: {artifact}")
                        yield artifact["uri"]

            except OSError as error:
                logger.error(f"Error: {error}")
                yield None
