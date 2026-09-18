"""
Configure Test
~~~~~~~~~~~~~~

This module implement test configuration for Asynchronous Input Output
(AIO) Artifactory.
"""

import json
import platform
import shutil
from collections.abc import Generator
from itertools import product
from pathlib import Path

import pytest
import tealogger
from pytest import Config, ExitCode, Metafunc, Parser, PytestPluginManager, Session

CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORKING_DIRECTORY = Path().cwd()
TEST_DATA_DIRECTORY = CURRENT_WORKING_DIRECTORY / "_test"

# The (Local) destination directory for retrieve (download) test(s). It is
# deliberately outside of the seed tree, so a download can never become the
# source of a later deploy (upload), which nest the seed tree.
TEST_RETRIEVE_DIRECTORY = TEST_DATA_DIRECTORY / "retrieve"

TEST_FILE_LIST = [
    "aioartifactory/alpha.txt",
    "aioartifactory/folder/beta.txt",
    "aioartifactory/folder/subfolder/gamma.txt",
    "localpath/alpha.txt",
    "localpath/beta.txt",
    "localpath/folder/gamma.txt",
    "localpath/folder/delta.txt",
]

# Configure conftest_logger
tealogger.configure(
    configuration=CURRENT_MODULE_PATH.parent / "aioartifactory" / "tealogger.json"
)
logger = tealogger.get_logger("test.conftest")


#######################
# Initialization Hook #
#######################


def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager):
    """Register Command Line Option(s)

    Register argparse style options and ini style config values, called
    once at the beginning of a test run.

    :param parser: The parser for command line option(s)
    :type parser: pytest.Parser
    :param pluginmanager: The pytest plugin manager
    :type pluginmanager: pytest.PytestPluginManager
    """
    logger.info("pytest Add Option")
    logger.debug(f"Parser: {parser}")
    logger.debug(f"Plugin Manager: {pluginmanager}")


def pytest_configure(config: Config) -> None:
    """Configure Test

    Allow perform of initial configuration.

    :param config: The pytest config object
    :type config: pytest.Config
    """
    logger.info("pytest Configure")
    logger.debug(f"Config: {config}")

    # Create the test data directory
    logger.debug(f"Create Test Data Directory: {TEST_DATA_DIRECTORY}")
    try:
        TEST_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Operating System Error: {e}")
    logger.debug("Create Test Data Directory Success")

    # Create the test file data
    setup_test_file()


def pytest_unconfigure(config: Config):
    """Unconfigure Test

    Called before test process is exited.

    NOTE: Run once

    :param config: The pytest config object
    :type config: pytest.Config
    """
    logger.info("pytest Unconfigure")
    logger.debug(f"Config: {config}")

    # Remove the test file data
    teardown_test_file()

    # Remove the test data directory
    logger.debug(f"Remove Test Data Directory: {TEST_DATA_DIRECTORY}")
    if TEST_DATA_DIRECTORY.exists():
        try:
            shutil.rmtree(TEST_DATA_DIRECTORY, ignore_errors=True)
        except OSError as e:
            logger.error(f"Operating System Error: {e}")
    logger.debug("Remove Test Data Directory Success")


def pytest_sessionstart(session: Session) -> None:
    """Start Session

    Called after the Session object has been created and before
    performing collection and entering the run test loop.

    conftest: This hook is only called for initial conftest(s).

    :param session: The pytest session object
    :type session: pytest.Session
    """
    logger.info("pytest Session Start")
    logger.debug(f"Session: {session}")

    # Platform Information
    # https://docs.python.org/3/library/platform.html
    logger.debug("Platform Information")
    # Cross Platform
    logger.debug("Cross Platform Information")
    logger.debug(f"Architecture: {platform.architecture()}")
    logger.debug(f"Machine: {platform.machine()}")
    logger.debug(f"Node: {platform.node()}")
    logger.debug(f"Platform: {platform.platform()}")
    logger.debug(f"Processor: {platform.processor()}")
    logger.debug(f"Python Build: {platform.python_build()}")
    logger.debug(f"Python Compiler: {platform.python_compiler()}")
    logger.debug(f"Python Branch: {platform.python_branch()}")
    logger.debug(f"Python Implementation: {platform.python_implementation()}")
    logger.debug(f"Python Revision: {platform.python_revision()}")
    logger.debug(f"Python Version: {platform.python_version()}")
    logger.debug(f"Python Version Tuple: {platform.python_version_tuple()}")
    logger.debug(f"Release: {platform.release()}")
    logger.debug(f"System: {platform.system()}")
    logger.debug(f"Version: {platform.version()}")
    logger.debug(f"Unix Name: {platform.uname()}")
    # Java Platform
    logger.debug("Java Platform Information")
    logger.debug(f"Java Version: {platform.java_ver()}")
    # Windows Platform
    logger.debug("Windows Platform Information")
    logger.debug(f"Windows Version: {platform.win32_ver()}")
    logger.debug(f"Windows Edition: {platform.win32_edition()}")
    logger.debug(f"Windows IoT: {platform.win32_is_iot()}")
    # macOS Platform
    logger.debug("macOS Platform Information")
    logger.debug(f"macOS Version: {platform.mac_ver()}")
    # iOS Platform
    # logger.debug("iOS Platform Information")
    # logger.debug(f"iOS Version: {platform.ios_ver()}")
    # Unix Platform
    logger.debug("Unix Platform Information")
    logger.debug(f"Unix libc Version: {platform.libc_ver()}")
    # Linux Platform
    # logger.debug("Linux Platform Information")
    # logger.debug(f"Linux OS Release: {platform.freedesktop_os_release()}")
    # Android Platform
    # logger.debug("Android Platform Information")
    # logger.debug(f"Android Version: {platform.android_ver()}")


def pytest_sessionfinish(session: Session, exitstatus: int | ExitCode) -> None:
    """Finish Session

    Called after whole test run finished, right before returning the
    exit status to the system.

    conftest: Any conftest file can implement this hook.

    NOTE: Run once

    :param session: The pytest session object
    :type session: pytest.Session
    :param exitstatus: The status which pytest will return to the system
    :type exitstatus: Union[int, pytest.ExitCode]
    """
    logger.info("pytest Session Finish")
    logger.debug(f"Session: {session}")
    logger.debug(f"Exit Status: {exitstatus}")


###################
# Collection Hook #
###################


def pytest_generate_tests(metafunc: Metafunc):
    """Generate Test Hook

    Generate (multiple) parametrized calls to a test function.

    Dynamically parametrize test(s) using test data from a JSON
    (JavaScript Object Notation) file. The data will align with the
    class and function name of the test(s).

    conftest: Any conftest file can implement this hook. For a given
        function definition, only conftest files in the functions's
        directory and its parent directories are consulted.

    Example Class:
        {
            "module_name":
                "ClassName": {
                    "function_name": {
                        "parameter": [
                            "expression",
                            ...
                        ],
                        ...
                    },
                    ...
                },
                ...
            },
            ...
        }

    Example Function:
        {
            "module_name":
                "function_name": {
                    "parameter": [
                        "expression",
                        ...
                    ],
                    ...
                },
                ...
            },
            ...
        }

    :param metafunc: The Metafunc helper for the test function
    :type metafunc: pytest.Metafunc
    """
    logger.info("pytest Generate Test")
    logger.debug(f"Metafunc: {metafunc}")
    # conftest_logger.debug(f"Module Name: {metafunc.module.__name__}")

    # Parse metafunc module
    module_name = metafunc.module.__name__
    module_path = Path(metafunc.module.__file__).parent

    # Load the test data
    test_data_path = None
    if (module_path / f"{module_name}.json").exists():
        test_data_path = module_path / f"{module_name}.json"
    elif (module_path / "data.json").exists():
        test_data_path = module_path / "data.json"
    logger.debug(f"Test Data Path: {test_data_path}")

    # Inject the test data
    if test_data_path:
        try:
            with open(test_data_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            logger.warning(f"No Test Data Found: {module_name}")
            logger.error(f"Error: {error}")
            pytest.skip(f"Skip No Test Data Found: {module_name}")
        except TypeError as error:
            logger.warning(f"No Test Data Path Set: {module_name}")
            logger.error(f"Error: {error}")
            pytest.skip(f"Skip No Test Data Path Set: {module_name}")

        class_condition = [
            module_name in data,
            # Part of a class
            # The class name is in the test data
            metafunc.cls.__name__ in data[module_name] if metafunc.cls else False,
            # Part of a function (should always be true)
            # The function name is in the test data
            metafunc.function.__name__ in data[module_name][metafunc.cls.__name__]
            if metafunc.cls and metafunc.function
            else False,
            # metafunc.cls and metafunc.function and metafunc.function.__name__ in data[module_name][metafunc.cls.__name__]
            # if metafunc.cls and metafunc.function and metafunc.cls.__name__ in data[module_name] else False,
        ]

        ####################
        # Class Level Test #
        ####################
        if all(class_condition):
            logger.debug("Generate Class Test")
            class_name = metafunc.cls.__name__
            function_name = metafunc.function.__name__
            function_data = data[module_name][class_name][function_name]
            test_data = function_data["data"]
            # conftest_logger.debug(f"Test Data: {test_data}")

            argument_name_list = test_data.keys()
            argument_value_list = test_data.values()
            # conftest_logger.debug(f"Argument Name List: {argument_name_list}")
            # conftest_logger.debug(f"Argument Value List: {argument_value_list}")
            id_list = None
            # id_list = []
            indirect = False

            strategy = function_data.get("strategy", "auto")
            # conftest_logger.debug(f"Strategy: {strategy}")

            match strategy:
                case "product":
                    # Create the cartesian product of the argument value to test
                    argument_value_list = list(product(*argument_value_list))
                case _:
                    # Create a zip of the argument value to test
                    argument_value_list = list(zip(*argument_value_list))

            # NOTE: Default
            # for argument_value_tuple in argument_value_list:
            #     id_list.append("-".join(map(str, argument_value_tuple)))

            # NOTE: There maybe a better way for this?
            # if "name" in function_data:
            #     id_list.extend(
            #         [function_data["name"]] * len(argument_value_list)
            #     )

            # Indirect
            if "indirect" in function_data:
                indirect = function_data["indirect"]

            # Exclude
            if (
                "exclude" in function_data
                and "strategy" in function_data["exclude"]
                and "data" in function_data["exclude"]
            ):
                exclude_strategy = function_data["exclude"]["strategy"]
                exclude_data = function_data["exclude"]["data"]
                # conftest_logger.debug(f"Exclude Strategy: {exclude_strategy}")
                # conftest_logger.debug(f"Exclude Data: {exclude_data}")

                match exclude_strategy:
                    case "product":
                        # Create the cartesian product of the exclude data
                        exclude_value_list = list(product(*exclude_data.values()))
                    case _:
                        # Default
                        exclude_value_list = list(zip(*exclude_data.values()))

                # conftest_logger.debug(f"Exclude Value List: {exclude_value_list}")

                # Remove the exclude value from the argument value
                # NOTE: Not sure if this is best implementation
                argument_value_list = [
                    argument_value
                    for argument_value in argument_value_list
                    if not any(
                        set(exclude_value).issubset(set(argument_value))
                        for exclude_value in exclude_value_list
                    )
                ]

            # conftest_logger.debug(f"Argument Name List: {argument_name_list}")
            # conftest_logger.debug(f"Argument Value List: {argument_value_list}")

            # Parametrize the test(s), only if test_data is available
            metafunc.parametrize(
                argnames=argument_name_list,
                argvalues=argument_value_list,
                indirect=indirect,
                ids=id_list,
                # scope="function",
            )


@pytest.fixture(scope="function")
def function_logger():
    """Function Logger"""


@pytest.fixture(scope="class")
def class_logger():
    """Class Logger"""


@pytest.fixture(scope="function")
def retrieve_directory() -> Path:
    """Retrieve Directory

    The (Local) destination directory for retrieve (download) test(s).

    :return: The retrieve (download) directory
    :rtype: pathlib.Path
    """
    TEST_RETRIEVE_DIRECTORY.mkdir(parents=True, exist_ok=True)

    return TEST_RETRIEVE_DIRECTORY


@pytest.fixture(scope="function")
def retrieve_cleanup(retrieve_directory: Path) -> Generator[list, None, None]:
    """Retrieve Cleanup

    Track the retrieve (download) path(s) of a test, and remove each one
    of them, along with any empty parent directory, after the test. It
    keep a test run from reusing the artifact of a previous test run.

    :param retrieve_directory: The retrieve (download) directory
    :type retrieve_directory: pathlib.Path
    :return: The (mutable) list to track the retrieve (download) path(s)
    :rtype: Generator[list, None, None]
    """
    download_list = []

    yield download_list

    remove_download(download_list=download_list, directory=retrieve_directory)


def setup_test_file():
    """Setup Test File

    Create the seed (test data) file(s), along with an empty retrieve
    (download) directory. The layout is identical for every test run.
    """
    logger.info("Setup Test File")

    try:
        TEST_RETRIEVE_DIRECTORY.mkdir(parents=True, exist_ok=True)

        for test_file in TEST_FILE_LIST:
            file_path = TEST_DATA_DIRECTORY / test_file
            logger.debug(f"Create File: {file_path}")
            if test_file.endswith("/"):
                file_path.mkdir(parents=True, exist_ok=True)
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
    except OSError as e:
        logger.error(f"Operating System Error: {e}")


def teardown_test_file():
    """Teardown Test File

    Remove the seed (test data) file(s), along with any empty parent
    directory, up to (but not include) the test data directory.
    """
    logger.info("Teardown Test File")

    try:
        for test_file in TEST_FILE_LIST:
            file_path = TEST_DATA_DIRECTORY / test_file
            logger.debug(f"Remove File: {file_path}")
            if file_path.is_dir():
                shutil.rmtree(file_path, ignore_errors=True)
            else:
                file_path.unlink(missing_ok=True)

            prune_directory(directory=file_path.parent)

    except OSError as e:
        logger.error(f"Operating System Error: {e}")


def remove_download(
    download_list: list,
    directory: Path = TEST_RETRIEVE_DIRECTORY,
):
    """Remove Download

    Remove each retrieve (download) path, along with any empty parent
    directory, up to (but not include) the retrieve (download)
    directory. A path outside of the retrieve (download) directory, a
    seed (test data) file for example, is never remove.

    :param download_list: The list of retrieve (download) path(s)
    :type download_list: list
    :param directory: The retrieve (download) directory
    :type directory: pathlib.Path
    """
    logger.info("Remove Download")

    directory = Path(directory).expanduser().resolve()

    for download in download_list:
        download_path = Path(download).expanduser().resolve()

        if not download_path.is_relative_to(directory) or download_path == directory:
            logger.warning(f"Skip Remove Download Outside Directory: {download_path}")
            continue

        logger.debug(f"Remove Download: {download_path}")
        try:
            if download_path.is_dir():
                shutil.rmtree(download_path, ignore_errors=True)
            else:
                download_path.unlink(missing_ok=True)
        except OSError as e:
            logger.error(f"Operating System Error: {e}")

        prune_directory(directory=download_path.parent, root=directory)


def prune_directory(
    directory: Path,
    root: Path = TEST_DATA_DIRECTORY,
):
    """Prune Directory

    Remove the directory, along with any empty parent directory, up to
    (but not include) the root directory.

    :param directory: The directory to prune
    :type directory: pathlib.Path
    :param root: The root directory to stop the prune
    :type root: pathlib.Path
    """
    directory = Path(directory).expanduser().resolve()
    root = Path(root).expanduser().resolve()

    while directory != root and directory.is_relative_to(root):
        try:
            directory.rmdir()
        except OSError:
            # The directory is not empty, or it does not exist
            break

        logger.debug(f"Remove Directory: {directory}")
        directory = directory.parent
