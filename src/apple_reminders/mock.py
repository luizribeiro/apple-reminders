import ctypes
import json
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from unittest.mock import patch
from uuid import uuid4

from typing_extensions import TypeAlias, TypeVar

from apple_reminders import Reminder, ReminderList, mock

T = TypeVar("T")


def decode_bytes_or_str(data: Union[bytes, str, None]) -> Optional[str]:
    """Convert bytes or string data to string."""
    if data is None:
        return None
    if isinstance(data, bytes):
        return data.decode('utf-8')
    return str(data)


def decode_char_p(ptr: Union[ctypes.c_char_p, bytes, str]) -> Optional[str]:
    """Safely decode a c_char_p value into a string."""
    if isinstance(ptr, (bytes, str)):
        return decode_bytes_or_str(ptr)
    if ptr is None or ptr.value is None:
        return None
    return decode_bytes_or_str(ptr.value)


# Type alias that matches the library's LP_c_char type
if TYPE_CHECKING:
    LP_c_char: TypeAlias = ctypes.POINTER[ctypes.c_char]  # type: ignore
else:
    LP_c_char = ctypes.POINTER(ctypes.c_char)


# Mock Swift API Implementation
class MockSwiftAPI:
    """Mock implementation of the Swift Reminders API."""
    active_pointers: Dict[int, 'MockSwiftAPI'] = {}  # Shared active pointers registry

    def __init__(self) -> None:
        self.lists: Dict[str, ReminderList] = {}  # Stores ReminderList objects
        self.reminders: Dict[str, Dict[str, Reminder]] = {}  # Stores Reminder objects by list_id
        # Register this instance in the active pointers registry
        addr = id(self)
        MockSwiftAPI.active_pointers[addr] = self

    def _get_reader_pointer(self) -> ctypes.c_void_p:
        """Get a void pointer to this instance."""
        return ctypes.c_void_p(id(self))

    def _verify_reader(self, reader: ctypes.c_void_p) -> None:
        """Verify that the reader pointer is valid."""
        if reader is None:
            raise ValueError("Reader pointer is required")
        addr = reader.value
        if addr is None or addr not in MockSwiftAPI.active_pointers:
            raise ValueError("Invalid reader pointer")

    # Helper to create a char pointer result
    def _to_char_ptr(self, data: Any) -> LP_c_char:
        """Convert data to a C-style string pointer."""
        json_data = json.dumps(data).encode("utf-8")  # Convert data to JSON bytes
        buffer = ctypes.create_string_buffer(json_data)  # Create string buffer
        ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))
        return ptr

    # Mock CreateRemindersReader Functionality
    def CreateRemindersReader(self) -> ctypes.c_void_p:
        return self._get_reader_pointer()

    # Mock DestroyRemindersReader Functionality
    def DestroyRemindersReader(self, reader: Optional[ctypes.c_void_p]) -> None:
        """Remove the instance from active pointers if the pointer matches."""
        if reader is None:
            return
        # Get the address value from the pointer
        addr = reader.value
        if addr is not None and addr in MockSwiftAPI.active_pointers:
            del MockSwiftAPI.active_pointers[addr]

    # Mock CreateList Functionality
    def CreateList(self, reader: ctypes.c_void_p, title: ctypes.c_char_p) -> LP_c_char:
        """Create a new reminder list with the given title."""
        self._verify_reader(reader)
        
        title_str = decode_char_p(title)
        if title_str is None:
            raise ValueError("Title string is required")
            
        try:
            data = json.loads(title_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in title string")
            
        title_value = data.get("title")
        if not title_value:
            raise ValueError("Title is required")

        list_id = str(uuid4())
        if title_value in (lst.title for lst in self.lists.values()):
            raise ValueError(f"List with name '{title_value}' already exists.")

        reminder_list = ReminderList(id=list_id, title=title_value, color=data.get("color"))
        self.lists[list_id] = reminder_list
        self.reminders[list_id] = {}  # Initialize empty reminders dict for this list

        return self._to_char_ptr({"id": list_id})

    # Mock AddReminder Functionality
    def CreateReminder(self, reader: ctypes.c_void_p, input_data: ctypes.c_char_p) -> LP_c_char:
        """Create a new reminder with the given data."""
        self._verify_reader(reader)
        
        data_str = decode_char_p(input_data)
        if data_str is None:
            raise ValueError("Input data string is required")
            
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in input data")

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
    def SearchReminders(self, reader: ctypes.c_void_p, query: ctypes.c_char_p) -> LP_c_char:
        """Search for reminders matching the query string."""
        self._verify_reader(reader)
        
        query_str = decode_char_p(query)
        if query_str is None:
            return self._to_char_ptr([])

        results = []
        for _, reminders in self.reminders.items():
            for reminder in reminders.values():
                if query_str.lower() in reminder.title.lower():
                    results.append(reminder.as_dict())

        return self._to_char_ptr(results)

    def GetReminders(self, reader: ctypes.c_void_p) -> LP_c_char:
        """Get all reminders."""
        self._verify_reader(reader)
        
        all_reminders = []
        for reminders in self.reminders.values():
            for reminder in reminders.values():
                all_reminders.append(reminder.as_dict())
        return self._to_char_ptr(all_reminders)

    def GetReminderLists(self, reader: ctypes.c_void_p) -> LP_c_char:
        """Get all reminder lists."""
        self._verify_reader(reader)
        return self._to_char_ptr([lst.as_dict() for lst in self.lists.values()])

    def GetRemindersInList(self, reader: ctypes.c_void_p, list_id: ctypes.c_char_p) -> LP_c_char:
        """Get all reminders in a specific list."""
        self._verify_reader(reader)
        
        list_id_str = decode_char_p(list_id)
        if not list_id_str or list_id_str not in self.reminders:
            return self._to_char_ptr([])
        return self._to_char_ptr([r.as_dict() for r in self.reminders[list_id_str].values()])

    def FreeString(self, ptr: LP_c_char) -> None:
        """Free a string pointer (no-op in Python)."""
        # No-op implementation since Python handles memory management
        pass


class MockRemindersTestHelper:
    """
    A test utility to mock the actual `apple_reminders.ffi._lib` functionality using the MockSwiftAPI.
    This helper ensures that all Swift API calls are rerouted to our mock implementation.
    """

    def __init__(self) -> None:
        self.mock_api = mock.MockSwiftAPI()

    def __enter__(self) -> mock.MockSwiftAPI:
        """Start patching the _lib module."""
        self.patcher = patch("apple_reminders.client._lib", self.mock_api)
        self.patcher.start()
        return self.mock_api

    def __exit__(self, exc_type: type, exc_value: Exception, traceback: Any) -> None:
        """Stop patching the _lib module."""
        self.patcher.stop()


# Only provide the test utility if running in a test environment
if "pytest" in sys.modules or "unittest" in sys.modules:
    # Register test helper for use in test environment
    _test_helper = MockRemindersTestHelper