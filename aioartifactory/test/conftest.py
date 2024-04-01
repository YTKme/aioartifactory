"""
Test Configuration
~~~~~~~~~~~~~~~~~~
"""

import json
from pathlib import Path

import pytest
import tealogger


tealogger.set_level(tealogger.DEBUG)


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """Generate Test Hook

    Dynamically parametrize test(s) using test data from a JSON
    (JavaScript Object Notation) file. The data will align with the
    class and function name of the test(s).

    Example:
        {
            "ClassName": {
                "function_name": {
                    "parameter": [
                        "expression"
                    ]
                }
            },
            ...
        }

    :param metafunc: Objects passed to the pytest_generate_tests hook
    :type metafunc: pytest.Metafunc
    """

    tealogger.debug(f'Class Name: {metafunc.cls.__name__}')
    tealogger.debug(f'Function Name: {metafunc.function.__name__}')
    tealogger.debug(f'Fixture Names: {metafunc.fixturenames}')

    # Load the test data
    with open(Path(__file__).parent / 'data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Check the class name and function name, make sure they are in the test data
    if metafunc.cls.__name__ in data and metafunc.function.__name__ in data[metafunc.cls.__name__]:
        # Loop through the test data for each class and function
        for name, value in data[metafunc.cls.__name__][metafunc.function.__name__].items():
            tealogger.debug(f'Parameter Name: {name}')
            tealogger.debug(f'Parameter Value: {value}')
            # Check the test data parameter name
            # Make sure it is part of the fixture name(s)
            if name in metafunc.fixturenames:
                # Parametrize the test(s)
                metafunc.parametrize(
                    argnames=name,
                    argvalues=value
                )
