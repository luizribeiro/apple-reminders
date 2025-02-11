"""Test suite for Apple Reminders."""
from datetime import datetime, timezone
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

def test_create_list() -> None:
    """Test creating a new reminder list."""
    api = RemindersAPI()
    
    # Create list with all fields
    list_id = api.create_list(
        title="Test List",
        color="#FF0000"  # Red
    )
    
    assert list_id is not None
    assert isinstance(list_id, str)
    
    # Verify the list was created correctly
    lists = api.get_lists()
    new_list = next((l for l in lists if l.id == list_id), None)
    assert new_list is not None
    assert new_list.title == "Test List"
    assert new_list.color == "#FF0000"

def test_create_list_minimal() -> None:
    """Test creating a list with minimal fields."""
    api = RemindersAPI()
    
    # Create list with only required fields
    list_id = api.create_list(title="Test Minimal List")
    
    assert list_id is not None
    assert isinstance(list_id, str)
    
    # Verify the list
    lists = api.get_lists()
    new_list = next((l for l in lists if l.id == list_id), None)
    assert new_list is not None
    assert new_list.title == "Test Minimal List"
    assert new_list.color == "#007AFF"

def test_create_reminder() -> None:
    """Test creating a new reminder."""
    api = RemindersAPI()
    
    # First create a list for our reminder
    list_id = api.create_list("Test List for Reminder")
    assert list_id is not None
    assert isinstance(list_id, str)
    
    # Create reminder with all fields
    reminder_id = api.create_reminder(
        title="Test Reminder",
        list_id=list_id,
        notes="Test Notes",
        due_date=datetime.now(timezone.utc),
        priority=1  # high priority
    )
    
    assert reminder_id is not None
    assert isinstance(reminder_id, str)
    
    # Verify the reminder was created correctly
    reminders = api.get_reminders_in_list(list_id)
    assert len(reminders) > 0
    
    new_reminder = next((r for r in reminders if r.id == reminder_id), None)
    assert new_reminder is not None
    assert new_reminder.title == "Test Reminder"
    assert new_reminder.notes == "Test Notes"
    assert new_reminder.priority == 1

def test_create_reminder_minimal() -> None:
    """Test creating a reminder with minimal fields."""
    api = RemindersAPI()
    
    # Create a list
    list_id = api.create_list("Test List for Minimal Reminder")
    
    # Create reminder with only required fields
    reminder_id = api.create_reminder(
        title="Test Minimal Reminder",
        list_id=list_id
    )
    
    assert reminder_id is not None
    assert isinstance(reminder_id, str)
    
    # Verify the reminder
    reminders = api.get_reminders_in_list(list_id)
    new_reminder = next((r for r in reminders if r.id == reminder_id), None)
    assert new_reminder is not None
    assert new_reminder.title == "Test Minimal Reminder"
    assert new_reminder.notes is None
    assert new_reminder.due_date is None

def test_create_reminder_invalid_list() -> None:
    """Test creating a reminder with an invalid list ID."""
    api = RemindersAPI()
    
    with pytest.raises(RuntimeError) as exc_info:
        api.create_reminder(
            title="Test Reminder",
            list_id="invalid-list-id"
        )
    
    assert "List not found" in str(exc_info.value)