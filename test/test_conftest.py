"""
Test Configure Test
~~~~~~~~~~~~~~~~~~~

This module implement test for the test data (seed) setup, teardown,
and the retrieve (download) cleanup of the test configuration. It does
not require an Artifactory server.
"""

from pathlib import Path

import pytest
import tealogger
from conftest import (
    TEST_DATA_DIRECTORY,
    TEST_FILE_LIST,
    TEST_RETRIEVE_DIRECTORY,
    prune_directory,
    remove_download,
    setup_test_file,
    teardown_test_file,
)

CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()

# Configure test_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "aioartifactory" / "tealogger.json"
)
logger = tealogger.get_logger("test.conftest.test")

# The retrieve (download) path shared between the track and the remove
# test of the `retrieve_cleanup` fixture
RETRIEVE_CLEANUP_PATH = TEST_RETRIEVE_DIRECTORY / "cleanup" / "alpha.txt"


@pytest.mark.conftest
class TestConfigureTest:
    """Test Configure Test Class"""

    ########
    # Real #
    ########

    @pytest.mark.real
    def test_setup_test_file(self):
        """Test Setup Test File

        The seed tree, and an empty retrieve (download) directory, are
        available for each test run.
        """

        for test_file in TEST_FILE_LIST:
            assert (TEST_DATA_DIRECTORY / test_file).exists()

        assert TEST_RETRIEVE_DIRECTORY.is_dir()

    @pytest.mark.real
    def test_setup_test_file_repeatable(self):
        """Test Setup Test File Repeatable

        A second (run of the) setup, after a teardown, recreate the same
        seed tree, without a nest of the previous one.
        """

        teardown_test_file()

        try:
            for test_file in TEST_FILE_LIST:
                assert not (TEST_DATA_DIRECTORY / test_file).exists()

            # The seed directory of each test file is prune
            for test_file in TEST_FILE_LIST:
                assert not (TEST_DATA_DIRECTORY / test_file).parent.exists()
        finally:
            setup_test_file()

        for test_file in TEST_FILE_LIST:
            assert (TEST_DATA_DIRECTORY / test_file).is_file()

        # No nest of a seed directory, for example `aioartifactory/aioartifactory`
        for seed_directory in {
            Path(test_file).parts[0] for test_file in TEST_FILE_LIST
        }:
            assert not (TEST_DATA_DIRECTORY / seed_directory / seed_directory).exists()

    @pytest.mark.real
    def test_remove_download(self, tmp_path: Path):
        """Test Remove Download

        :param tmp_path: The temporary directory path
        :type tmp_path: pathlib.Path
        """

        retrieve_directory = tmp_path / "retrieve"
        download_list = [
            retrieve_directory / "alpha.txt",
            retrieve_directory / "folder" / "subfolder" / "beta.txt",
        ]

        for download in download_list:
            download.parent.mkdir(parents=True, exist_ok=True)
            download.touch()

        remove_download(download_list=download_list, directory=retrieve_directory)

        for download in download_list:
            assert not download.exists()

        # The empty parent directory is prune, the retrieve directory stay
        assert not (retrieve_directory / "folder").exists()
        assert retrieve_directory.is_dir()
        assert not list(retrieve_directory.iterdir())

    @pytest.mark.real
    def test_remove_download_outside_directory(self, tmp_path: Path):
        """Test Remove Download Outside Directory

        A path outside of the retrieve (download) directory, a seed
        (test data) file for example, is never remove.

        :param tmp_path: The temporary directory path
        :type tmp_path: pathlib.Path
        """

        retrieve_directory = tmp_path / "retrieve"
        retrieve_directory.mkdir(parents=True, exist_ok=True)

        seed_path = tmp_path / "seed" / "alpha.txt"
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        seed_path.touch()

        remove_download(
            download_list=[seed_path, retrieve_directory],
            directory=retrieve_directory,
        )

        assert seed_path.is_file()
        assert retrieve_directory.is_dir()

    @pytest.mark.real
    def test_prune_directory(self, tmp_path: Path):
        """Test Prune Directory

        :param tmp_path: The temporary directory path
        :type tmp_path: pathlib.Path
        """

        directory = tmp_path / "alpha" / "beta" / "gamma"
        directory.mkdir(parents=True, exist_ok=True)

        prune_directory(directory=directory, root=tmp_path)

        assert not (tmp_path / "alpha").exists()
        assert tmp_path.is_dir()

    @pytest.mark.real
    def test_prune_directory_not_empty(self, tmp_path: Path):
        """Test Prune Directory Not Empty

        :param tmp_path: The temporary directory path
        :type tmp_path: pathlib.Path
        """

        directory = tmp_path / "alpha" / "beta"
        directory.mkdir(parents=True, exist_ok=True)
        (tmp_path / "alpha" / "gamma.txt").touch()

        prune_directory(directory=directory, root=tmp_path)

        assert not directory.exists()
        assert (tmp_path / "alpha" / "gamma.txt").is_file()

    @pytest.mark.real
    def test_retrieve_cleanup_track(
        self,
        retrieve_directory: Path,
        retrieve_cleanup: list,
    ):
        """Test Retrieve Cleanup Track

        The `retrieve_cleanup` fixture track a download path, and remove
        it after the test, without a live server.

        :param retrieve_directory: The retrieve (download) directory
        :type retrieve_directory: pathlib.Path
        :param retrieve_cleanup: The retrieve (download) path(s) to
            remove after the test
        :type retrieve_cleanup: list
        """

        assert retrieve_directory == TEST_RETRIEVE_DIRECTORY

        RETRIEVE_CLEANUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        RETRIEVE_CLEANUP_PATH.touch()

        retrieve_cleanup.append(RETRIEVE_CLEANUP_PATH)

        assert RETRIEVE_CLEANUP_PATH.is_file()

    @pytest.mark.real
    def test_retrieve_cleanup_remove(self):
        """Test Retrieve Cleanup Remove

        The download path track by the previous test is remove, along
        with its (now empty) parent directory.
        """

        assert not RETRIEVE_CLEANUP_PATH.exists()
        assert not RETRIEVE_CLEANUP_PATH.parent.exists()
        assert TEST_RETRIEVE_DIRECTORY.is_dir()
