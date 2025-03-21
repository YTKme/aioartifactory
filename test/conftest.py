"""
Configure Test
~~~~~~~~~~~~~~

This module implement test configuration for Asynchronous Input Output
(AIO) Artifactory.
"""

import json
import platform
from itertools import product
from pathlib import Path
import shutil

import pytest
from pytest import (
    Config,
    ExitCode,
    Metafunc,
    Parser,
    PytestPluginManager,
    Session
)

import tealogger


CURRENT_MODULE_PATH = Path(__file__).parent.expanduser().resolve()
CURRENT_WORKING_DIRECTORY = Path().cwd()
TEST_DATA_DIRECTORY = CURRENT_WORKING_DIRECTORY / "_test"

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
    configuration=CURRENT_MODULE_PATH.parent / "tealogger.json"
)
conftest_logger = tealogger.get_logger("test.conftest")


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
    conftest_logger.info("pytest Add Option")
    conftest_logger.debug(f"Parser: {parser}")
    conftest_logger.debug(f"Plugin Manager: {pluginmanager}")


def pytest_configure(config: Config) -> None:
    """Configure Test

    Allow perform of initial configuration.

    :param config: The pytest config object
    :type config: pytest.Config
    """
    conftest_logger.info("pytest Configure")
    conftest_logger.debug(f"Config: {config}")

    # Create the test data directory
    conftest_logger.debug(f"Create Test Data Directory: {TEST_DATA_DIRECTORY}")
    try:
        TEST_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        conftest_logger.error(f"Operating System Error: {e}")
    conftest_logger.debug("Create Test Data Directory Success")

    # Create the test file data
    setup_test_file()


def pytest_unconfigure(config: Config):
    """Unconfigure Test

    Called before test process is exited.

    NOTE: Run once

    :param config: The pytest config object
    :type config: pytest.Config
    """
    conftest_logger.info("pytest Unconfigure")
    conftest_logger.debug(f"Config: {config}")

    # Remove the test file data
    # teardown_test_file()

    # Remove the test data directory
    # conftest_logger.debug(f"Remove Test Data Directory: {TEST_DATA_DIRECTORY}")
    # if TEST_DATA_DIRECTORY.exists():
    #     try:
    #         shutil.rmtree(TEST_DATA_DIRECTORY)
    #     except OSError as e:
    #         conftest_logger.error(f"Operating System Error: {e}")
    # conftest_logger.debug(f"Remove Test Data Directory Success")


def pytest_sessionstart(session: Session) -> None:
    """Start Session

    Called after the Session object has been created and before
    performing collection and entering the run test loop.

    :param session: The pytest session object
    :type session: pytest.Session
    """
    conftest_logger.info("pytest Session Start")
    conftest_logger.debug(f"Session: {session}")

    conftest_logger.debug("Platform Information")
    conftest_logger.debug(f"Architecture: {platform.architecture()}")
    conftest_logger.debug(f"Machine: {platform.machine()}")
    conftest_logger.debug(f"Node: {platform.node()}")
    conftest_logger.debug(f"Platform: {platform.platform()}")
    conftest_logger.debug(f"Processor: {platform.processor()}")
    conftest_logger.debug(f"Python Build: {platform.python_build()}")
    conftest_logger.debug(f"Python Compiler: {platform.python_compiler()}")
    conftest_logger.debug(f"Python Branch: {platform.python_branch()}")
    conftest_logger.debug(f"Python Implementation: {platform.python_implementation()}")
    conftest_logger.debug(f"Python Revision: {platform.python_revision()}")
    conftest_logger.debug(f"Python Version: {platform.python_version()}")
    conftest_logger.debug(f"Python Version Tuple: {platform.python_version_tuple()}")
    conftest_logger.debug(f"Release: {platform.release()}")
    conftest_logger.debug(f"System: {platform.system()}")
    conftest_logger.debug(f"Version: {platform.version()}")
    conftest_logger.debug(f"Unix Name: {platform.uname()}")


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

    Example:
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

    :param metafunc: The Metafunc helper for the test function
    :type metafunc: pytest.Metafunc
    """
    conftest_logger.info("pytest Generate Test")
    conftest_logger.debug(f"Metafunc: {metafunc}")
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
    conftest_logger.debug(f"Test Data Path: {test_data_path}")

    # Inject the test data
    if test_data_path:
        try:
            with open(test_data_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            conftest_logger.warning(f"No Test Data Found: {module_name}")
            conftest_logger.error(f"Error: {error}")
            pytest.skip(f"Skip No Test Data Found: {module_name}")
        except TypeError as error:
            conftest_logger.warning(f"No Test Data Path Set: {module_name}")
            conftest_logger.error(f"Error: {error}")
            pytest.skip(f"Skip No Test Data Path Set: {module_name}")

        class_condition = [
            module_name in data,
            # Part of a class
            hasattr(metafunc, "cls"),
            # The class name is in the test data
            metafunc.cls.__name__ in data[module_name],
            # Part of a function (should always be true)
            hasattr(metafunc, "function"),
            # The function name is in the test data
            metafunc.function.__name__ in data[module_name][metafunc.cls.__name__],
        ]

        ####################
        # Class Level Test #
        ####################
        if all(class_condition):
            conftest_logger.debug("Generate Class Test")
            class_name = metafunc.cls.__name__
            function_name = metafunc.function.__name__
            # conftest_logger.debug(f"Class Name: {metafunc.cls.__name__}")
            # conftest_logger.debug(f"Function Name: {metafunc.function.__name__}")
            # conftest_logger.debug(f"Fixture Names: {metafunc.fixturenames}")
            function_data = data[module_name][class_name][function_name]
            test_data = function_data["data"]
            # conftest_logger.debug(f"Test Data: {test_data}")

            argument_name_list = test_data.keys()
            argument_value_list = test_data.values()

            strategy = function_data["strategy"]
            # conftest_logger.debug(f"Strategy: {strategy}")

            match strategy:
                case "product":
                    # Create the cartesian product of the argument value to test
                    argument_value_list = list(product(*argument_value_list))
                case _:
                    # Create a zip of the argument value to test
                    argument_value_list = list(zip(*argument_value_list))

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
                        exclude_value_list = list(product(*exclude_data.values()))

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
            )


def pytest_sessionfinish(session: Session, exitstatus: int | ExitCode):
    """Finish Session

    Called after whole test run finished, right before returning the
    exit status to the system.

    NOTE: Run once

    :param session: The pytest session object
    :type session: pytest.Session
    :param exitstatus: The status which pytest will return to the system
    :type exitstatus: Union[int, pytest.ExitCode]
    """
    conftest_logger.info("pytest Session Finish")
    conftest_logger.debug(f"Session: {session}")
    conftest_logger.debug(f"Exit Status: {exitstatus}")


@pytest.fixture(scope="function")
def function_logger():
    """Function Logger"""
    pass


@pytest.fixture(scope="class")
def class_logger():
    """Class Logger"""
    pass


def setup_test_file():
    """Setup Test File"""
    conftest_logger.info("Setup Local Path")

    try:
        for test_file in TEST_FILE_LIST:
            file_path = TEST_DATA_DIRECTORY / test_file
            conftest_logger.debug(f"Create File: {file_path}")
            if file_path.is_dir():
                file_path.mkdir(parents=True, exist_ok=True)
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
    except OSError as e:
        conftest_logger.error(f"Operating System Error: {e}")


def teardown_test_file():
    """Teardown Test File"""
    conftest_logger.info("Teardown Local Path")

    try:
        for test_file in TEST_FILE_LIST:
            file_path = TEST_DATA_DIRECTORY / test_file
            conftest_logger.debug(f"Remove File: {file_path}")
            if file_path.is_dir():
                shutil.rmtree(file_path, ignore_errors=True)
            else:
                file_path.unlink()

        parent_path = set()
        for test_file in TEST_FILE_LIST:
            directory_path = (TEST_DATA_DIRECTORY / test_file).parent
            parent_path.add(directory_path)

        for path in parent_path:
            conftest_logger.debug(f"Remove Directory: {path}")
            shutil.rmtree(path, ignore_errors=True)

    except OSError as e:
        conftest_logger.error(f"Operating System Error: {e}")
