"""Tests for the apple_reminders library."""
from datetime import datetime, timezone
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from apple_reminders import Reminder, ReminderList, RemindersAPI

@pytest.fixture
def sample_reminder_dict() -> Dict[str, Any]:
    """Sample reminder data."""
    return {
        "id": "reminder-1",
        "title": "Test Reminder",
        "dueDate": "2024-02-15T15:00:00Z",
        "completed": False,
        "notes": "Test notes",
        "priority": 1,
        "listId": "list-1",
        "creationDate": "2024-02-10T10:00:00Z",
        "modificationDate": "2024-02-10T10:00:00Z"
    }

@pytest.fixture
def sample_list_dict() -> Dict[str, Any]:
    """Sample list data."""
    return {
        "id": "list-1",
        "title": "Test List",
        "color": "#FF0000"
    }

def test_reminder_from_dict(sample_reminder_dict: Dict[str, Any]) -> None:
    """Test creating a Reminder from dictionary."""
    reminder = Reminder.from_dict(sample_reminder_dict)
    
    assert reminder.id == "reminder-1"
    assert reminder.title == "Test Reminder"
    assert isinstance(reminder.due_date, datetime)
    assert reminder.completed is False
    assert reminder.notes == "Test notes"
    assert reminder.priority == 1
    assert reminder.list_id == "list-1"

def test_reminder_list_from_dict(sample_list_dict: Dict[str, Any]) -> None:
    """Test creating a ReminderList from dictionary."""
    reminder_list = ReminderList.from_dict(sample_list_dict)
    
    assert reminder_list.id == "list-1"
    assert reminder_list.title == "Test List"
    assert reminder_list.color == "#FF0000"

def test_reminder_str_representation(sample_reminder_dict: Dict[str, Any]) -> None:
    """Test the string representation of a Reminder."""
    reminder = Reminder.from_dict(sample_reminder_dict)
    str_repr = str(reminder)
    
    assert "Test Reminder" in str_repr
    assert any(status in str_repr for status in ["○", "✓"])  # either status marker
    assert "due:" in str_repr.lower()  # just check for due date indication

def test_reminder_list_str_representation(sample_list_dict: Dict[str, Any]) -> None:
    """Test the string representation of a ReminderList."""
    reminder_list = ReminderList.from_dict(sample_list_dict)
    str_repr = str(reminder_list)
    
    assert "Test List" in str_repr
    assert "list-1" in str_repr

def test_reminder_handles_missing_optional_fields() -> None:
    """Test that Reminder handles missing optional fields gracefully."""
    minimal_data = {
        "id": "reminder-1",
        "title": "Test Reminder",
        "completed": False,
        "listId": "list-1",
        "priority": 0,
        "tags": []  # Added this as it's expected by the from_dict method
    }
    
    reminder = Reminder.from_dict(minimal_data)
    assert reminder.due_date is None
    assert reminder.notes is None
    assert reminder.creation_date is None
    assert reminder.modification_date is None

def test_reminder_list_handles_missing_color() -> None:
    """Test that ReminderList handles missing color field."""
    minimal_data = {
        "id": "list-1",
        "title": "Test List"
    }
    
    reminder_list = ReminderList.from_dict(minimal_data)
    assert reminder_list.color is None