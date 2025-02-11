import sys
from unittest.mock import patch
from apple_reminders import mock
from typing import Any  # Added missing import

class MockRemindersTestHelper:
    """
    A test utility to mock the actual `apple_reminders._lib` functionality using the MockSwiftAPI.
    This helper ensures that all Swift API calls are rerouted to our mock implementation.
    """
    def __init__(self) -> None:
        self.mock_api = mock.MockSwiftAPI()

    def __enter__(self) -> mock.MockSwiftAPI:
        """Start patching the _lib module."""
        self.patcher = patch("apple_reminders._lib", self.mock_api)
        self.patcher.start()
        return self.mock_api

    def __exit__(self, exc_type: type, exc_value: Exception, traceback: Any) -> None:
        """Stop patching the _lib module."""
        self.patcher.stop()

# Only provide the test utility if running in a test environment
if 'pytest' in sys.modules or 'unittest' in sys.modules:
    MockRemindersTestHelper