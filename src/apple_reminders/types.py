from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


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
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        """Create a Reminder instance from a dictionary."""

        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            # Parse ISO date and ensure timezone awareness
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        return cls(
            id=data["id"],
            title=data["title"],
            due_date=parse_date(data.get("dueDate")),
            completed=data["completed"],
            notes=data.get("notes"),
            priority=data["priority"],
            list_id=data["listId"],
            creation_date=parse_date(data.get("creationDate")),
            modification_date=parse_date(data.get("modificationDate")),
        )

    def as_dict(self) -> Dict[str, Any]:
        """Convert the Reminder to a dictionary format suitable for JSON."""

        def format_date(dt: Optional[datetime]) -> Optional[str]:
            if not dt:
                return None
            return dt.astimezone(timezone.utc).isoformat()

        return {
            "id": self.id,
            "title": self.title,
            "dueDate": format_date(self.due_date),
            "completed": self.completed,
            "notes": self.notes,
            "priority": self.priority,
            "listId": self.list_id,
            "creationDate": format_date(self.creation_date),
            "modificationDate": format_date(self.modification_date),
        }

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        due = f", due: {self.due_date.strftime('%Y-%m-%d %H:%M')}" if self.due_date else ""
        return f"[{status}] {self.title}{due}"


@dataclass
class ReminderList:
    """Representation of an Apple Reminder List."""

    id: str
    title: str
    color: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReminderList":
        """Create a ReminderList instance from a dictionary."""
        return cls(id=data["id"], title=data["title"], color=data.get("color"))

    def as_dict(self) -> Dict[str, Any]:
        """Convert the ReminderList to a dictionary format suitable for JSON."""
        return {"id": self.id, "title": self.title, "color": self.color}

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"
