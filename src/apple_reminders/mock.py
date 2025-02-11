import ctypes
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from typing_extensions import TypeAlias, TypeVar
from unittest.mock import patch
from uuid import uuid4

from apple_reminders import mock, Reminder, ReminderList


T = TypeVar("T")


def decode_char_p(ptr: Union[ctypes.c_char_p, bytes]) -> str:
    """Safely decode a c_char_p value or bytes into a string."""
    if isinstance(ptr, bytes):
        return ptr.decode("utf-8")
    if ptr.value is None:
        raise ValueError("Cannot decode None value from c_char_p")
    return ptr.value.decode("utf-8")


# Type alias that matches the library's LP_c_char type
if TYPE_CHECKING:
    LP_c_char: TypeAlias = ctypes.POINTER[ctypes.c_char]  # type: ignore
else:
    LP_c_char = ctypes.POINTER(ctypes.c_char)


# Mock Swift API Implementation
class MockSwiftAPI:
    active_pointers: Dict[int, Any] = {}  # Shared active pointers registry

    def __init__(self) -> None:
        self.lists: Dict[str, ReminderList] = {}  # Stores ReminderList objects
        self.reminders: Dict[str, Dict[str, Reminder]] = {}  # Stores Reminder objects by list_id
        # Create and register a mock reader pointer
        self.reader_pointer = ctypes.c_void_p(id(self))
        MockSwiftAPI.active_pointers[id(self.reader_pointer)] = self.reader_pointer

    # Helper to create a char pointer result
    def _to_char_ptr(self, data: Any) -> LP_c_char:
        json_data = json.dumps(data).encode("utf-8")  # Convert data to JSON bytes
        buffer = ctypes.create_string_buffer(json_data)  # Create string buffer
        ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))
        return ptr

    # Mock CreateRemindersReader Functionality
    def CreateRemindersReader(self) -> ctypes.c_void_p:
        return self.reader_pointer

    # Mock DestroyRemindersReader Functionality
    def DestroyRemindersReader(self, pointer: Optional[ctypes.c_void_p]) -> None:
        if pointer and id(pointer) in MockSwiftAPI.active_pointers:
            del MockSwiftAPI.active_pointers[id(pointer)]  # Remove from active pointers registry

    # Mock CreateList Functionality
    def CreateList(self, _: ctypes.c_void_p, title: ctypes.c_char_p) -> LP_c_char:
        data = json.loads(decode_char_p(title))
        title_str = data.get("title")
        if not title_str:
            raise ValueError("Title is required")

        list_id = str(uuid4())
        if title_str in (lst.title for lst in self.lists.values()):
            raise ValueError(f"List with name '{title_str}' already exists.")

        reminder_list = ReminderList(id=list_id, title=title_str, color=data.get("color"))
        self.lists[list_id] = reminder_list
        self.reminders[list_id] = {}  # Initialize empty reminders dict for this list

        return self._to_char_ptr({"id": list_id})

    # Mock AddReminder Functionality
    def CreateReminder(self, _: ctypes.c_void_p, input_data: ctypes.c_char_p) -> LP_c_char:
        data = json.loads(decode_char_p(input_data))
        list_id = data.get("listId")
        title = data.get("title")

        if not list_id or list_id not in self.lists:
            raise ValueError("Invalid list ID.")
        if not title:
            raise ValueError("Title is required.")

        reminder_id = str(uuid4())
        now = datetime.now(timezone.utc)

        reminder = Reminder(
            id=reminder_id,
            title=title,
            notes=data.get("notes"),
            due_date=datetime.fromisoformat(data["dueDate"]) if data.get("dueDate") else None,
            completed=False,
            priority=data.get("priority", 5),
            list_id=list_id,
            creation_date=now,
            modification_date=now,
        )

        self.reminders[list_id][reminder_id] = reminder
        return self._to_char_ptr({"id": reminder_id})

    # Mock SearchReminders Functionality
    def SearchReminders(self, _: ctypes.c_void_p, query: ctypes.c_char_p) -> LP_c_char:
        query_str = decode_char_p(query)
        results = []

        for list_id, reminders in self.reminders.items():
            for reminder in reminders.values():
                if query_str.lower() in reminder.title.lower():
                    results.append(reminder.as_dict())

        return self._to_char_ptr(results)

    def GetReminders(self, _: ctypes.c_void_p) -> LP_c_char:
        all_reminders = []
        for reminders in self.reminders.values():
            for reminder in reminders.values():
                all_reminders.append(reminder.as_dict())
        return self._to_char_ptr(all_reminders)

    def GetReminderLists(self, _: ctypes.c_void_p) -> LP_c_char:
        return self._to_char_ptr([lst.as_dict() for lst in self.lists.values()])

    def GetRemindersInList(self, _: ctypes.c_void_p, list_id: ctypes.c_char_p) -> LP_c_char:
        list_id_str = decode_char_p(list_id)
        if list_id_str not in self.reminders:
            return self._to_char_ptr([])
        return self._to_char_ptr([r.as_dict() for r in self.reminders[list_id_str].values()])

    def FreeString(self, ptr: LP_c_char) -> None:
        # No-op implementation since Python handles memory management
        pass


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
if "pytest" in sys.modules or "unittest" in sys.modules:
    MockRemindersTestHelper
