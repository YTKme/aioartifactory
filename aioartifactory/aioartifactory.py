"""
Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import aiofiles
import aiohttp
from pathlib import Path


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

    async def retrieve(
        self,
        source: str,
        destination: str,
    ):
        """Retrieve
        """
        transferred_size = 0
        destination_path = Path(destination).parent.resolve()

        session_connector = aiohttp.TCPConnector(limit=10)
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=10000, sock_read=10000)
        async with aiohttp.ClientSession(connector=session_connector, timeout=session_timeout) as session:
            async with session.get(source, headers=self._header) as response:
                async with aiofiles.open(file=destination, mode='wb') as file:
                    async for chunk, _ in response.content.iter_chunks():
                        await file.write(chunk)

        print('Done')


    async def __aenter__(self):
        """Asynchronous Enter
        """
        return self

    async def __aexit__(self, *args) -> None:
        """Asynchronous Exit
        """
        await self.close()
