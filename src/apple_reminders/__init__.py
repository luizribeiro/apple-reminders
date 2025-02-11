"""
AppleReminders - A Python library for interacting with Apple's Reminders app.
"""

from __future__ import annotations

import ctypes
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path

# Find the library relative to the script location
SCRIPT_DIR = Path(__file__).parent.parent.parent
LIB_PATH = SCRIPT_DIR / ".build/debug/libRemindersLib.dylib"

if not LIB_PATH.exists():
    raise RuntimeError(
        f"Swift library not found at {LIB_PATH}. "
        "Make sure you've built the Swift code with 'swift build'"
    )

# Load the dynamic library
_lib = ctypes.CDLL(str(LIB_PATH))

# Define the function signatures
_lib.CreateRemindersReader.restype = ctypes.c_void_p
_lib.CreateRemindersReader.argtypes = []

_lib.DestroyRemindersReader.restype = None
_lib.DestroyRemindersReader.argtypes = [ctypes.c_void_p]

_lib.GetReminders.restype = ctypes.POINTER(ctypes.c_char)
_lib.GetReminders.argtypes = [ctypes.c_void_p]

_lib.GetReminderLists.restype = ctypes.POINTER(ctypes.c_char)
_lib.GetReminderLists.argtypes = [ctypes.c_void_p]

_lib.GetRemindersInList.restype = ctypes.POINTER(ctypes.c_char)
_lib.GetRemindersInList.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.SearchReminders.restype = ctypes.POINTER(ctypes.c_char)
_lib.SearchReminders.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

_lib.FreeString.restype = None
_lib.FreeString.argtypes = [ctypes.POINTER(ctypes.c_char)]


@dataclass
class Reminder:
    """Representation of an Apple Reminder."""
    id: str
    title: str
    due_date: Optional[datetime]
    completed: bool
    notes: Optional[str]
    priority: int
    list_id: str
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]

    @classmethod 
    def from_dict(cls, data: Dict[str, Any]) -> 'Reminder':
        """Create a Reminder instance from a dictionary."""
        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            # Parse ISO date and ensure timezone awareness
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        return cls(
            id=data['id'],
            title=data['title'],
            due_date=parse_date(data.get('dueDate')),
            completed=data['completed'],
            notes=data.get('notes'),
            priority=data['priority'],
            list_id=data['listId'],
            creation_date=parse_date(data.get('creationDate')),
            modification_date=parse_date(data.get('modificationDate'))
        )

    def __str__(self) -> str:
        status = '✓' if self.completed else '○'
        due = f", due: {self.due_date.strftime('%Y-%m-%d %H:%M')}" if self.due_date else ""
        return f"[{status}] {self.title}{due}"


@dataclass
class ReminderList:
    """Representation of an Apple Reminder List."""
    id: str
    title: str
    color: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReminderList':
        """Create a ReminderList instance from a dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            color=data.get('color')
        )

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"


class RemindersAPI:
    """Main interface for interacting with Apple Reminders."""

    def __init__(self) -> None:
        """Initialize the RemindersAPI."""
        self._reader = _lib.CreateRemindersReader()
        if not self._reader:
            raise RuntimeError("Failed to initialize RemindersReader")

    def __del__(self) -> None:
        """Clean up resources when the object is destroyed."""
        if hasattr(self, '_reader') and self._reader:
            _lib.DestroyRemindersReader(self._reader)
            self._reader = None

    def _handle_json_response(self, result_ptr: Any) -> Any:
        """Handle JSON response from the C library."""
        try:
            result_str = ctypes.string_at(result_ptr).decode('utf-8')
            result = json.loads(result_str)
            
            if isinstance(result, dict) and 'error' in result:
                raise RuntimeError(result['error'])
            
            return result
        finally:
            _lib.FreeString(result_ptr)

    def get_all_reminders(self) -> List[Reminder]:
        """Get all reminders."""
        result = self._handle_json_response(_lib.GetReminders(self._reader))
        return [Reminder.from_dict(r) for r in result]

    def get_lists(self) -> List[ReminderList]:
        """Get all reminder lists."""
        result = self._handle_json_response(_lib.GetReminderLists(self._reader))
        return [ReminderList.from_dict(r) for r in result]

    def get_reminders_in_list(self, list_id: str) -> List[Reminder]:
        """Get all reminders in a specific list."""
        result = self._handle_json_response(
            _lib.GetRemindersInList(self._reader, list_id.encode('utf-8'))
        )
        return [Reminder.from_dict(r) for r in result]

    def search_reminders(self, query: str) -> List[Reminder]:
        """Search reminders by query string."""
        result = self._handle_json_response(
            _lib.SearchReminders(self._reader, query.encode('utf-8'))
        )
        return [Reminder.from_dict(r) for r in result]

    def get_incomplete_reminders(self) -> List[Reminder]:
        """Get all incomplete reminders."""
        return [r for r in self.get_all_reminders() if not r.completed]

    def get_overdue_reminders(self) -> List[Reminder]:
        """Get all overdue reminders."""
        now = datetime.now(timezone.utc)
        return [r for r in self.get_incomplete_reminders() 
                if r.due_date and r.due_date < now]

    def get_reminders_due_today(self) -> List[Reminder]:
        """Get all reminders due today."""
        today = datetime.now(timezone.utc).date()
        return [r for r in self.get_incomplete_reminders()
                if r.due_date and r.due_date.date() == today]

    def get_reminders_by_priority(self, priority: int) -> List[Reminder]:
        """Get all reminders with a specific priority."""
        return [r for r in self.get_all_reminders() if r.priority == priority]