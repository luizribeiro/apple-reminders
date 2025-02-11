import ctypes
import json
import sys
from typing import Dict, Any, List, Optional
from unittest.mock import patch
from uuid import uuid4

from apple_reminders import mock

# Mock Swift API Implementation
class MockSwiftAPI:
    active_pointers: Dict[int, Any] = {}  # Shared active pointers registry

    def __init__(self) -> None:
        self.lists: Dict[str, Dict[str, Any]] = {}  # Stores Reminder lists and their reminders.
        # Create and register a mock reader pointer
        self.reader_pointer = ctypes.c_void_p(id(self))
        MockSwiftAPI.active_pointers[id(self.reader_pointer)] = self.reader_pointer

    # Helper to create a c_void_p result pointer
    def _to_result_ptr(self, data: Any) -> ctypes.c_void_p:
        json_data = json.dumps(data)  # Convert data to JSON string
        buffer = ctypes.create_string_buffer(json_data.encode("utf-8"))  # Create string buffer
        return ctypes.cast(buffer, ctypes.c_void_p)  # Return as c_void_p

    # Mock CreateRemindersReader Functionality
    def CreateRemindersReader(self) -> ctypes.c_void_p:
        return self.reader_pointer

    # Mock DestroyRemindersReader Functionality
    def DestroyRemindersReader(self, pointer: Optional[ctypes.c_void_p]) -> None:
        if pointer and id(pointer) in MockSwiftAPI.active_pointers:
            del MockSwiftAPI.active_pointers[id(pointer)]  # Remove from active pointers registry

    # Mock CreateList Functionality
    def CreateList(self, _: ctypes.c_void_p, title: ctypes.c_char_p) -> ctypes.c_void_p:
        title_buffer = ctypes.cast(title, ctypes.c_char_p).value
        if title_buffer is None:
            raise ValueError("Invalid title - cannot decode None")
        title_str = title_buffer.decode("utf-8")
        list_id = str(uuid4())
        if title_str in (lst['name'] for lst in self.lists.values()):
            raise ValueError(f"List with name '{title_str}' already exists.")
        
        self.lists[list_id] = {"name": title_str, "reminders": {}}
        return self._to_result_ptr({"id": list_id})

    # Mock AddReminder Functionality
    def CreateReminder(self, _: ctypes.c_void_p, input_data: ctypes.c_char_p) -> ctypes.c_void_p:
        input_buffer = ctypes.cast(input_data, ctypes.c_char_p).value
        if input_buffer is None:
            raise ValueError("Invalid input data - cannot decode None")
        data = json.loads(input_buffer.decode("utf-8"))
        list_id = data.get("listId")
        title = data.get("title")

        if not list_id or list_id not in self.lists:
            raise ValueError("Invalid list ID.")
        if not title:
            raise ValueError("Title is required.")

        reminder_id = str(uuid4())
        self.lists[list_id]["reminders"][reminder_id] = {
            "title": title,
            "notes": data.get("notes", ""),
            "due_date": data.get("dueDate"),
            "completed": False
        }
        return self._to_result_ptr({"id": reminder_id})

    # Mock SearchReminders Functionality
    def SearchReminders(self, _: ctypes.c_void_p, query: ctypes.c_char_p) -> ctypes.c_void_p:
        query_buffer = ctypes.cast(query, ctypes.c_char_p).value
        if query_buffer is None:
            raise ValueError("Query cannot be None")
        query_str = query_buffer.decode("utf-8")  # Decode query from bytes
        results = []

        for list_id, list_data in self.lists.items():  # Ensure correct scoping for list_id
            for reminder_id, reminder in list_data["reminders"].items():
                if query_str.lower() in reminder["title"].lower():
                    results.append({
                        "id": reminder_id,
                        "title": reminder["title"],
                        "notes": reminder["notes"],
                        "due_date": reminder["due_date"],
                        "completed": reminder["completed"],
                        "priority": 5,  # Default priority value
                        "listId": list_id
                    })
        
        return self._to_result_ptr(results)

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
