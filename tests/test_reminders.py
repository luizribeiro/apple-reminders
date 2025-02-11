"""Test suite for Apple Reminders."""
import pytest
from apple_reminders import RemindersAPI, Reminder, ReminderList

def test_reminders_api_initialization() -> None:
    """Test that we can initialize the RemindersAPI."""
    api = RemindersAPI()
    assert api is not None

def test_get_lists() -> None:
    """Test that we can get reminder lists."""
    api = RemindersAPI()
    lists = api.get_lists()
    assert isinstance(lists, list)
    if lists:  # If there are any lists
        assert isinstance(lists[0], ReminderList)
        assert hasattr(lists[0], 'id')
        assert hasattr(lists[0], 'title')

def test_get_all_reminders() -> None:
    """Test that we can get all reminders."""
    api = RemindersAPI()
    reminders = api.get_all_reminders()
    assert isinstance(reminders, list)
    if reminders:  # If there are any reminders
        assert isinstance(reminders[0], Reminder)
        assert hasattr(reminders[0], 'id')
        assert hasattr(reminders[0], 'title')
        assert hasattr(reminders[0], 'completed')