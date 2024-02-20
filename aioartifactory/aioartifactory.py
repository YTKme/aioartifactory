"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import asyncio
from asyncio import (
    TaskGroup
)
from os import PathLike
from pathlib import Path
from types import TracebackType
from typing import (
    Optional,
    Type,
)

import aiofiles
from aiohttp import (
    ClientSession,
    ClientTimeout,
    TCPConnector,
)
import rich.progress

from aioartifactory.context import TeardownContextManager
from aioartifactory import configuration


class AIOArtifactory:
    """Asynchronous Input Output (AIO) Artifactory Class
    """
    # __slots__ = ()

    def __init__(self, *args, **kwargs):
        """Constructor

        The main Artifactory class

        :param api_key: The Artifactory API Key
        :type api_key: str, optional
        :param token: The Artifactory Token
        :type token: str, optional
        """
        if kwargs.get('api_key'):
            self._api_key = kwargs.get('api_key')
            self._header = {'X-JFrog-Art-Api': self._api_key}

        if kwargs.get('token'):
            self._token = kwargs.get('token')
            self._header = {'Authorization': f'Bearer {self._token}'}

    def __new__(cls, *args, **kwargs):
        """New
        """
        return super().__new__(cls)

    async def print_me(self, message: str):
        await asyncio.sleep(1)
        print(message)

    async def retrieve(
        self,
        source_list: list[str],
        destination_list: list[PathLike],
        recursive: bool = False,
        quiet: bool = False,
    ):
        """Retrieve

        :param source: The source (URL) path
        :type source: str
        :param destination: The destination path
        :type destination: str
        :param recursive: Whether to recursively retrieve artifact(s)
        :param quiet: Whether to show retrieve progress
        :type quiet: bool, optional
        """
        queue = asyncio.Queue()
        # async with TaskGroup() as group:
        #     for source in source_list:
        #         group.create_task(self.print_me(source))

    async def _retrieve(
        self,
        source: str,
        destination: str,
        quiet: bool = False,
    ):
        transferred_size = 0
        destination_path = Path(destination).parent.resolve()

        session_connector = TCPConnector(limit=10)
        session_timeout = ClientTimeout(total=None, sock_read=10000, sock_connect=10000)
        async with (
            ClientSession(connector=session_connector, timeout=session_timeout) as session,
            session.get(source, headers=self._header) as response,
            aiofiles.open(file=destination, mode='wb') as file,
        ):
            total = int(response.headers['Content-Length'])
            # with TeardownContextManager() as teardown:
            #     def cleanup():
            #         ...

            #     teardown.append(cleanup)

            with rich.progress.Progress(
                '[progress.percentage]{task.percentage:>3.0f}%',
                rich.progress.BarColumn(bar_width=None),
                rich.progress.DownloadColumn(),
                rich.progress.TransferSpeedColumn(),
            ) as progress:
                download_task = progress.add_task('Download', total=total)
                async for chunk, _ in response.content.iter_chunks():
                    await file.write(chunk)
                    progress.update(download_task, advance=len(chunk))

        print('Done')

    async def __aenter__(self):
        """Asynchronous Enter
        """
        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> None:
        """Asynchronous Exit

        :param exception_type: The exception type
        :type exception_type: Optional[Type[BaseException]]
        :param exception_value: The exception value
        :type exception_value: Optional[BaseException]
        :param exception_traceback: The exception traceback
        :type exception_traceback: Optional[TracebackType]
        """
        await super()
