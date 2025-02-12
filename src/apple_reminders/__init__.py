"""
AppleReminders - A Python library for interacting with Apple's Reminders app.
"""

from __future__ import annotations

from .client import Client
from .types import Reminder, ReminderList

__all__ = ["Client", "Reminder", "ReminderList"]
