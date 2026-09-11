"""
Context
~~~~~~~
"""

from collections.abc import Callable
from types import TracebackType


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
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ):
        for function in self._function_list:
            function()
            self._function_list.remove(function)
