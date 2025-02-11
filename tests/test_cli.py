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
        api_instance = mock.return_value
        
        # Setup default return values
        api_instance.get_all_reminders.return_value = []
        api_instance.get_lists.return_value = []
        api_instance.get_reminders_due_today.return_value = []
        api_instance.get_overdue_reminders.return_value = []
        api_instance.get_reminders_in_list.return_value = []
        
        yield api_instance

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