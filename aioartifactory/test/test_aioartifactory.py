"""
Test Asynchronous Input Output (AIO) Artifactory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from pathlib import Path

import pytest

from aioartifactory.aioartifactory import AIOArtifactory


class TestAIOArtifactory:
    """Test Asynchronous Input Output (AIO) Artifactory Class
    """

    @pytest.mark.asyncio
    async def test_retrieve(self):
        """Test Retrieve
        """

        aioartifactory = AIOArtifactory(api_key='<key>')

        await aioartifactory.retrieve(
            source='<file>',
            destination=str(Path(__file__).parent.resolve() / 'default.zip')
        )
