"""Tests for the rem CLI tool."""
from datetime import datetime, timezone
import json
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch
from typing import Optional, Generator

import pytest
from click.testing import CliRunner

from apple_reminders.rem import cli
from apple_reminders import Reminder, ReminderList

@dataclass
class MockReminder:
    """Mock reminder for testing."""
    id: str = "1"
    title: str = "Test Reminder"
    due_date: Optional[datetime] = None
    completed: bool = False
    notes: Optional[str] = None
    priority: int = 0
    list_id: str = "list-1"
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None

@dataclass
class MockReminderList:
    """Mock reminder list for testing."""
    id: str = "list-1"
    title: str = "Test List"
    color: Optional[str] = "#FF0000"

@pytest.fixture
def mock_api() -> Generator[Mock, None, None]:
    """Mock RemindersAPI for testing."""
    with patch('apple_reminders.rem.RemindersAPI') as mock:
        # Create a proper instance mock that will be returned by the class mock
        instance = Mock()
        mock.return_value = instance
        
        # Setup default return values
        instance.get_all_reminders.return_value = []
        instance.get_lists.return_value = []
        instance.get_reminders_due_today.return_value = []
        instance.get_overdue_reminders.return_value = []
        instance.get_reminders_in_list.return_value = []
        instance.create_reminder.return_value = "new-reminder-id"
        instance.create_list.return_value = "new-list-id"
        
        yield instance  # Yield the instance, not the class mock

@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI runner."""
    return CliRunner()

def test_list_command_no_reminders(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test list command with no reminders."""
    result = cli_runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert "📋 All" in result.output
    assert len(result.output.strip()) > 0  # Should have some output

def test_list_command_with_reminders(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test list command with reminders."""
    mock_api.get_all_reminders.return_value = [MockReminder()]
    
    result = cli_runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert "Test Reminder" in result.output

def test_list_command_json_output(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test list command with JSON output."""
    mock_api.get_all_reminders.return_value = [MockReminder()]
    
    result = cli_runner.invoke(cli, ['list', '--format', 'json'])
    assert result.exit_code == 0
    
    # Parse JSON output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['title'] == "Test Reminder"

def test_today_command(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test today command."""
    result = cli_runner.invoke(cli, ['today'])
    assert result.exit_code == 0
    assert "No reminders" in result.output

def test_today_command_with_reminders(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test today command with reminders."""
    mock_api.get_reminders_due_today.return_value = [MockReminder()]
    
    result = cli_runner.invoke(cli, ['today'])
    assert result.exit_code == 0
    assert "Test Reminder" in result.output

def test_lists_command(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test lists command."""
    result = cli_runner.invoke(cli, ['lists'])
    assert result.exit_code == 0
    assert "No reminder lists found" in result.output

def test_lists_command_with_lists(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test lists command with lists."""
    mock_api.get_lists.return_value = [MockReminderList()]
    mock_api.get_reminders_in_list.return_value = []
    
    result = cli_runner.invoke(cli, ['lists'])
    assert result.exit_code == 0
    assert "Test List" in result.output

def test_lists_command_json_output(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test lists command with JSON output."""
    mock_api.get_lists.return_value = [MockReminderList()]
    mock_api.get_reminders_in_list.return_value = []
    
    result = cli_runner.invoke(cli, ['lists', '--format', 'json'])
    assert result.exit_code == 0
    
    # Parse JSON output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['title'] == "Test List"

def test_stats_command(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test stats command."""
    result = cli_runner.invoke(cli, ['stats'])
    assert result.exit_code == 0
    assert "Active: 0" in result.output

def test_stats_command_json_output(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test stats command with JSON output."""
    result = cli_runner.invoke(cli, ['stats', '--format', 'json'])
    assert result.exit_code == 0
    
    # Parse JSON output
    data = json.loads(result.output)
    assert isinstance(data, dict)
    assert 'active' in data
    assert 'completed' in data
    assert 'due_today' in data
    assert 'overdue' in data

from unittest.mock import Mock, patch

@patch('apple_reminders.rem.RemindersAPI')
def test_add_command(mock_api: Mock, cli_runner: CliRunner) -> None:
    """Test adding a new reminder."""
    # Mock the create_reminder method
    mock_api.return_value.create_reminder.return_value = "new-reminder-id"
    
    result = cli_runner.invoke(cli, [
        'add',
        'Test Reminder',
        '--list', 'list1',
        '--notes', 'Test Notes',
        '--due', '2023-12-31 12:00',
        '--priority', 'high'
    ])
    
    print(f"Output: {result.output}")
    print(f"Exit Code: {result.exit_code}")
    assert result.exit_code == 0
    assert "Created reminder: Test Reminder" in result.output
    
    # Verify API was called correctly
    mock_api.return_value.create_reminder.assert_called_once()
    call_args = mock_api.return_value.create_reminder.call_args[1]
    assert call_args["title"] == "Test Reminder"
    assert call_args["list_id"] == "list1"
    assert call_args["notes"] == "Test Notes"
    assert call_args["priority"] == 1  # high priority
    assert isinstance(call_args["due_date"], datetime)

from unittest.mock import Mock, patch

@patch('apple_reminders.rem.RemindersAPI')
def test_add_command_minimal(mock_api: Mock, cli_runner: CliRunner) -> None:
    """Test adding a reminder with minimal options."""
    mock_api.return_value.create_reminder.return_value = "new-reminder-id"
    
    result = cli_runner.invoke(cli, [
        'add',
        'Test Reminder',
        '--list', 'list1'
    ])
    
    assert result.exit_code == 0
    assert "Created reminder: Test Reminder" in result.output
    
    # Verify API was called with minimal args
    call_args = mock_api.return_value.create_reminder.call_args[1]
    assert call_args["title"] == "Test Reminder"
    assert call_args["list_id"] == "list1"
    assert call_args["notes"] is None
    assert call_args["priority"] is None
    assert call_args["due_date"] is None

def test_add_command_json_output(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test adding a reminder with JSON output."""
    mock_api.return_value.create_reminder.return_value = "new-reminder-id"
    
    result = cli_runner.invoke(cli, [
        'add',
        'Test Reminder',
        '--list', 'list1',
        '--format', 'json'
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["id"] == "new-reminder-id"

from unittest.mock import Mock, patch

@patch('apple_reminders.rem.RemindersAPI')
def test_add_command_error(mock_api: Mock, cli_runner: CliRunner) -> None:
    """Test error handling when adding a reminder."""
    mock_api.return_value.create_reminder.side_effect = RuntimeError("Failed to create reminder")
    
    result = cli_runner.invoke(cli, [
        'add',
        'Test Reminder',
        '--list', 'list1'
    ])
    
    assert result.exit_code == 0  # We don't exit with error to stay consistent
    assert "Error: Failed to create reminder" in result.output

from unittest.mock import Mock, patch

@patch('apple_reminders.rem.RemindersAPI')
def test_create_list_command(mock_api: Mock, cli_runner: CliRunner) -> None:
    """Test creating a new list."""
    mock_api.return_value.create_list.return_value = "new-list-id"
    
    result = cli_runner.invoke(cli, [
        'create-list',
        'Test List',
        '--color', '#FF0000'
    ])
    
    assert result.exit_code == 0
    assert "Created list: Test List" in result.output
    
    # Verify API was called correctly
    mock_api.return_value.create_list.assert_called_once_with(
        title="Test List",
        color="#FF0000"
    )

from unittest.mock import Mock, patch

@patch('apple_reminders.rem.RemindersAPI')
def test_create_list_minimal(mock_api: Mock, cli_runner: CliRunner) -> None:
    """Test creating a list with minimal options."""
    mock_api.return_value.create_list.return_value = "new-list-id"
    
    result = cli_runner.invoke(cli, [
        'create-list',
        'Test List'
    ])
    
    assert result.exit_code == 0
    assert "Created list: Test List" in result.output
    
    # Verify API was called with minimal args
    mock_api.return_value.create_list.assert_called_once_with(
        title="Test List",
        color=None
    )

def test_create_list_json_output(cli_runner: CliRunner, mock_api: Mock) -> None:
    """Test creating a list with JSON output."""
    mock_api.return_value.create_list.return_value = "new-list-id"
    
    result = cli_runner.invoke(cli, [
        'create-list',
        'Test List',
        '--format', 'json'
    ])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["id"] == "new-list-id"

from unittest.mock import Mock, patch

@patch('apple_reminders.rem.RemindersAPI')
def test_create_list_error(mock_api: Mock, cli_runner: CliRunner) -> None:
    """Test error handling when creating a list."""
    mock_api.return_value.create_list.side_effect = RuntimeError("Failed to create list")
    
    result = cli_runner.invoke(cli, [
        'create-list',
        'Test List'
    ])
    
    assert result.exit_code == 0  # We don't exit with error to stay consistent
    assert "Error: Failed to create list" in result.output