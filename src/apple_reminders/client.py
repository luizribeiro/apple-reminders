import ctypes
import json
from datetime import datetime, timezone
from typing import Any, List, Optional

from .ffi import _lib
from .types import Reminder, ReminderList


class Client:
    """Main interface for interacting with Apple Reminders."""

    def __init__(self) -> None:
        """Initialize the client."""
        self._reader = _lib.CreateRemindersReader()
        if not self._reader:
            raise RuntimeError("Failed to initialize RemindersReader")

    def cleanup(self) -> None:
        """Explicit cleanup for resources."""
        if hasattr(self, "_reader") and self._reader:
            try:
                _lib.DestroyRemindersReader(self._reader)
                self._reader = None
            except Exception as e:
                print(f"Warning during cleanup: {e}")

    def _handle_json_response(self, result_ptr: Any) -> Any:
        """Handle JSON response from Swift library.

        The response can be either:
        - A dictionary containing data or an error message
        - A list of items (for get_lists and get_reminders)
        """
        result_str = ctypes.string_at(result_ptr).decode("utf-8")
        result = json.loads(result_str)

        # If it's a dictionary, check for errors
        if isinstance(result, dict):
            if "error" in result:
                raise RuntimeError(result["error"])
            if "items" in result:
                return result["items"]
            return result

        # If it's a list, return it directly
        if isinstance(result, list):
            return result

        raise RuntimeError(f"Unexpected JSON response type: {type(result)}")

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
            _lib.GetRemindersInList(self._reader, list_id.encode("utf-8"))
        )
        return [Reminder.from_dict(r) for r in result]

    def search_reminders(self, query: str) -> List[Reminder]:
        """Search reminders by query string."""
        result = self._handle_json_response(
            _lib.SearchReminders(self._reader, query.encode("utf-8"))
        )
        return [Reminder.from_dict(r) for r in result]

    def get_incomplete_reminders(self) -> List[Reminder]:
        """Get all incomplete reminders."""
        return [r for r in self.get_all_reminders() if not r.completed]

    def get_overdue_reminders(self) -> List[Reminder]:
        """Get all overdue reminders."""
        now = datetime.now(timezone.utc)
        return [r for r in self.get_incomplete_reminders() if r.due_date and r.due_date < now]

    def get_reminders_due_today(self) -> List[Reminder]:
        """Get all reminders due today."""
        today = datetime.now(timezone.utc).date()
        return [
            r for r in self.get_incomplete_reminders() if r.due_date and r.due_date.date() == today
        ]

    def get_reminders_by_priority(self, priority: int) -> List[Reminder]:
        """Get all reminders with a specific priority."""
        return [r for r in self.get_all_reminders() if r.priority == priority]

    def get_reminder(self, reminder_id: str) -> Reminder:
        """Get a specific reminder by ID."""
        # First try native implementation if available
        try:
            result = self._handle_json_response(
                _lib.GetReminder(self._reader, reminder_id.encode("utf-8"))
            )
            return Reminder.from_dict(result)
        except (AttributeError, RuntimeError):
            # Fallback implementation if native GetReminder not available
            all_reminders = self.get_all_reminders()
            for reminder in all_reminders:
                if reminder.id == reminder_id:
                    return reminder
            raise RuntimeError(f"Reminder with ID '{reminder_id}' not found") from None

    def create_reminder(
        self,
        title: str,
        list_id: str,
        notes: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: Optional[int] = None,
    ) -> str:
        """Create a new reminder.

        Args:
            title: The title of the reminder
            list_id: The ID of the list to add the reminder to
            notes: Optional notes for the reminder
            due_date: Optional due date (must be timezone aware)
            priority: Optional priority (1=high, 5=medium, 9=low)

        Returns:
            The ID of the newly created reminder

        Raises:
            RuntimeError: If the reminder creation fails
        """
        input_data = {
            "title": title,
            "listId": list_id,
            "notes": notes,
            "dueDate": due_date.astimezone(timezone.utc).isoformat() if due_date else None,
            "priority": priority,
        }

        result = self._handle_json_response(
            _lib.CreateReminder(self._reader, json.dumps(input_data).encode("utf-8"))
        )

        reminder_id = result.get("id")
        if not isinstance(reminder_id, str):
            raise RuntimeError("Failed to create reminder: invalid ID type received")
        if not reminder_id:
            raise RuntimeError(f"Failed to create reminder, missing id: {result.get('error')}")

        return reminder_id

    def create_list(self, title: str, color: Optional[str] = None) -> str:
        """Create a new reminder list.

        Args:
            title: The title of the list
            color: Optional color in hex format (e.g., '#FF0000' for red)

        Returns:
            The ID of the newly created list

        Raises:
            RuntimeError: If the list creation fails
        """
        input_data = {"title": title, "color": color}

        result = self._handle_json_response(
            _lib.CreateList(self._reader, json.dumps(input_data).encode("utf-8"))
        )

        list_id = result.get("id")
        if not isinstance(list_id, str):
            raise RuntimeError("Failed to create list: invalid ID type received")
        if not list_id:
            raise RuntimeError(f"Failed to create list, missing id: {result.get('error')}")

        return list_id

    def complete_reminder(self, reminder_id: str) -> None:
        """Mark a reminder as completed.

        Args:
            reminder_id: The ID of the reminder to complete

        Raises:
            RuntimeError: If the operation fails
        """
        result = self._handle_json_response(
            _lib.CompleteReminder(self._reader, reminder_id.encode("utf-8"))
        )

        if not result.get("success"):
            raise RuntimeError(f"Failed to complete reminder: {result.get('error')}")

    def uncomplete_reminder(self, reminder_id: str) -> None:
        """Mark a reminder as not completed.

        Args:
            reminder_id: The ID of the reminder to mark as not completed

        Raises:
            RuntimeError: If the operation fails
        """
        result = self._handle_json_response(
            _lib.UncompleteReminder(self._reader, reminder_id.encode("utf-8"))
        )

        if not result.get("success"):
            raise RuntimeError(f"Failed to mark reminder as not completed: {result.get('error')}")
