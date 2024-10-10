"""
Context
~~~~~~~
"""

from types import TracebackType
from typing import (
    Callable,
    Optional,
    Type,
)


class TeardownContextManager:
    """Teardown Context Manager"""

    def __init__(self):
        self._function_list = []

    def append(self, function: Callable):
        self._function_list.append(function)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ):
        for function in self._function_list:
            function()
            self._function_list.remove(function)
