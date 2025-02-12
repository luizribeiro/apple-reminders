"""CLI interface for Apple Reminders."""

import enum
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from . import Client, Reminder, ReminderList

# Initialize rich console
console = Console()


# Utility functions for handling UUIDs
def find_minimum_length(ids: List[str]) -> int:
    """
    Find the minimum length needed to uniquely identify all IDs.
    All IDs are compared in lowercase.
    """
    if not ids:
        return 0
        
    # Convert all IDs to lowercase for comparison
    lower_ids = [id.lower() for id in ids]
    max_len = max(len(id) for id in lower_ids)
    
    # Start with length 4 as minimum for readability
    for length in range(4, max_len + 1):
        # Get prefixes of current length
        prefixes = [id[:length] for id in lower_ids]
        # If all prefixes are unique, we found our minimum length
        if len(set(prefixes)) == len(prefixes):
            return length
            
    return max_len

def shorten_id(uuid: str, all_ids: Optional[List[str]] = None) -> str:
    """
    Shorten a UUID to the minimum length needed for uniqueness.
    If all_ids is provided, finds minimum length needed for uniqueness among all IDs.
    Otherwise returns first 8 characters.
    Always returns lowercase.
    """
    if all_ids is None:
        return uuid[:8].lower()
        
    min_length = find_minimum_length(all_ids)
    return uuid[:min_length].lower()

def expand_id(partial_id: str, all_ids: List[str]) -> str:
    """
    Expand a partial ID to its full UUID.
    Case-insensitive matching is used.
    Raises ValueError if ambiguous or not found.
    """
    if not partial_id:
        raise ValueError("ID cannot be empty")
    
    # Convert input to lowercase for matching    
    partial_id = partial_id.lower()
    # Create case-mapping dict to preserve original IDs
    id_map = {id.lower(): id for id in all_ids}
    
    matches = [
        orig_id
        for lower_id, orig_id in id_map.items()
        if lower_id.startswith(partial_id)
    ]
    
    if len(matches) == 0:
        raise ValueError(f"No ID found starting with '{partial_id}'")
    if len(matches) > 1:
        matches_display = ", ".join(shorten_id(m, all_ids) for m in matches)
        raise ValueError(f"Ambiguous ID '{partial_id}' matches multiple: {matches_display}")
        
    return matches[0]


class OutputFormat(str, enum.Enum):
    """Supported output formats."""

    PRETTY = "pretty"  # Default rich text output
    JSON = "json"  # JSON output


def style_priority(priority: int) -> Text:
    """Return styled priority indicator."""
    if priority == 1:
        return Text("!", style="red")  # High priority
    elif priority == 5:
        return Text("!", style="yellow")  # Medium priority
    elif priority == 9:
        return Text("!", style="blue")  # Low priority
    return Text(" ")  # No priority


def style_date(date: Optional[datetime], show_date: bool = False) -> Text:
    """Return styled date string."""
    if not date:
        return Text("")

    now = datetime.now(timezone.utc)
    if show_date:
        date_str = date.strftime("%Y-%m-%d %H:%M")
    else:
        date_str = date.strftime("%H:%M")

    # Use Rich's Text object directly with style
    if date.date() == now.date():
        return Text(date_str, style="cyan")
    elif date < now:
        return Text(date_str, style="red")
    else:
        return Text(date_str, style="yellow")


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)


def format_color_block(hex_color: Optional[str]) -> Text:
    """Format a color as a visible circle in the terminal."""
    if not hex_color:
        return Text("●", style="dim")  # Using a dimmed circle for empty colors
    r, g, b = hex_to_rgb(hex_color)
    return Text("●", style=f"rgb({r},{g},{b})")


def format_status(completed: bool) -> Text:
    """Format the status indicator."""
    return Text("✓", style="dim") if completed else Text("○")


class OutputFormatter:
    """Handles consistent output formatting across commands."""

    @staticmethod
    def format_reminder_row(
        reminder: Reminder, all_reminders: List[Reminder], lists: Dict[str, ReminderList] = None, show_notes: bool = True, show_date: bool = False
    ) -> List[Text]:
        """Format a reminder for table display."""
        # Basic styling
        title_style = Style(dim=True) if reminder.completed else None
        title = Text(reminder.title, style=title_style if title_style else "")

        # Build columns
        # Status, priority, ID, then title
        all_ids = [r.id for r in all_reminders]
        columns: List[Text] = [
            format_status(reminder.completed),
            style_priority(reminder.priority),
            Text(shorten_id(reminder.id, all_ids), style="dim"),
            title
        ]
        
        # Due date
        if reminder.due_date:
            columns.append(style_date(reminder.due_date, show_date=show_date))

        # Add list info if available
        if lists and reminder.list_id in lists:
            reminder_list = lists[reminder.list_id]
            list_color = format_color_block(reminder_list.color)
            list_text = Text("").join([list_color, Text(" "), Text(reminder_list.title, style="dim")])
            columns.append(list_text)

        if show_notes and reminder.notes:
            notes = Text(
                reminder.notes[:50] + "..." if len(reminder.notes) > 50 else reminder.notes,
                style="dim",
            )
            columns.append(notes)

        return columns

    @staticmethod
    def format_reminders_as_table(
        reminders: List[Reminder],
        *,
        lists: Optional[Dict[str, ReminderList]] = None,
        show_notes: bool = True,
        show_date: bool = False,
        title: Optional[str] = None,
    ) -> Table:
        """Create a formatted table of reminders."""
        table = Table(
            box=None, show_header=False, pad_edge=False, padding=(0, 1), collapse_padding=True
        )

        sorted_reminders = sorted(
            reminders,
            key=lambda r: (r.completed, r.due_date or datetime.max.replace(tzinfo=timezone.utc)),
        )

        for reminder in sorted_reminders:
            table.add_row(
                *OutputFormatter.format_reminder_row(
                    reminder, sorted_reminders, lists=lists, show_notes=show_notes, show_date=show_date
                )
            )

        return table

    @staticmethod
    def format_lists_as_table(lists: List[ReminderList], reminder_counts: Dict[str, int]) -> Table:
        """Create a formatted table of reminder lists."""
        table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))

        # Get all list IDs for shortening context
        all_ids = [lst.id for lst in lists]

        for reminder_list in lists:
            active_count = reminder_counts.get(reminder_list.id, 0)
            color_block = format_color_block(reminder_list.color)
            # Add shortened ID before the title
            short_id = shorten_id(reminder_list.id, all_ids)
            
            table.add_row(
                color_block,
                Text(shorten_id(reminder_list.id, all_ids), style="dim"), 
                reminder_list.title,
                Text(f"{active_count} active", style="dim")
            )

        return table

    @staticmethod
    def output_reminders(
        reminders: List[Reminder],
        fmt: OutputFormat = OutputFormat.PRETTY,
        title: Optional[str] = None,
        show_notes: bool = True,
        show_date: bool = False,
        lists: Optional[Dict[str, ReminderList]] = None,
    ) -> None:
        """Output reminders in the specified format."""
        if fmt == OutputFormat.JSON:
            click.echo(json.dumps([asdict(r) for r in reminders], default=str))
            return

        if not reminders:
            message = title or "No reminders"
            console.print(f"\n{message}\n")
            return

        table = OutputFormatter.format_reminders_as_table(
            reminders, lists=lists, show_notes=show_notes, show_date=show_date
        )

        # Add a subtle legend if there are prioritized items
        has_priorities = any(r.priority in (1, 5, 9) for r in reminders)
        if has_priorities:
            legend = [
                Text("!", style="red") + Text(" high  "),
                Text("!", style="yellow") + Text(" medium  "),
                Text("!", style="blue") + Text(" low")
            ]
            legend_text = Text("").join(legend)

        console.print()
        if title:
            console.print(f"{title} ({len(reminders)})")
        console.print(table)
        if has_priorities:
            console.print(legend_text)
        console.print()

    @staticmethod
    def output_lists(
        lists: List[ReminderList],
        reminder_counts: Dict[str, int],
        fmt: OutputFormat = OutputFormat.PRETTY,
    ) -> None:
        """Output lists in the specified format."""
        if fmt == OutputFormat.JSON:
            output = [
                {**asdict(reminder_list), "active_reminders": reminder_counts.get(reminder_list.id, 0)} for reminder_list in lists
            ]
            click.echo(json.dumps(output, default=str))
            return

        if not lists:
            console.print("\nNo reminder lists found\n")
            return

        table = OutputFormatter.format_lists_as_table(lists, reminder_counts)
        console.print("\n📋 Lists")
        console.print(table)
        console.print()


def common_options(f: Callable) -> Callable:
    """Common options for all commands."""
    f = click.option(
        "--format",
        "output_format",
        type=click.Choice([f.value for f in OutputFormat]),
        default=OutputFormat.PRETTY,
        help="Output format",
    )(f)
    return f


class IDType(click.ParamType):
    """Custom parameter type for handling shortened IDs."""
    name = "id"  # Add name attribute for Click's help text
    
    def __init__(self, client: Optional[Client] = None, list_mode: bool = False):
        self.client = client
        self.list_mode = list_mode
        
    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        try:
            if not value:
                self.fail("ID cannot be empty")
                
            # Create client if not provided
            client = self.client or Client()
            
            # Get all valid IDs based on mode
            if self.list_mode:
                all_ids = [lst.id for lst in client.get_lists()]
            else:
                all_ids = [r.id for r in client.get_all_reminders()]
                
            # Try to expand the ID
            return expand_id(value, all_ids)
            
        except ValueError as e:
            self.fail(str(e))


@click.group()
def cli() -> None:
    """Reminders CLI"""
    pass


@cli.command()
@common_options
@click.argument("title")
@click.option("--list", "list_id", required=True, type=IDType(list_mode=True), help="List ID to create the reminder in")
@click.option("--notes", help="Optional notes for the reminder")
@click.option(
    "--due",
    "due_date",
    type=click.DateTime(
        formats=["%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    ),
    help="Due date (format: YYYY-MM-DD HH:MM)",
)
@click.option("--priority", type=click.Choice(["high", "medium", "low"]), help="Priority level")
def add(
    output_format: OutputFormat,
    title: str,
    list_id: str,
    notes: Optional[str] = None,
    due_date: Optional[datetime] = None,
    priority: Optional[str] = None,
) -> None:
    """Add a new reminder"""
    client = Client()

    # Convert priority string to number
    priority_map = {"high": 1, "medium": 5, "low": 9}
    priority_num = priority_map.get(priority) if priority else None

    # Make due date timezone aware if provided
    if due_date and due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    try:
        reminder_id = client.create_reminder(
            title=title, list_id=list_id, notes=notes, due_date=due_date, priority=priority_num
        )

        if output_format == OutputFormat.JSON:
            click.echo(json.dumps({"success": True, "id": reminder_id}))
        else:
            # Create a list with just the new reminder ID to get proper shortening
            new_reminder = client.get_reminder(reminder_id)
            all_reminders = client.get_all_reminders()
            short_id = shorten_id(reminder_id, [r.id for r in all_reminders])
            console.print(f"\n✓ Created reminder: {title} {short_id}\n")

    except RuntimeError as e:
        if output_format == OutputFormat.JSON:
            click.echo(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"\n[red]Error:[/red] {e}\n")


@cli.command("create-list")
@common_options
@click.argument("title")
@click.option("--color", help="Color in hex format (e.g., #FF0000 for red)")
def create_list(output_format: OutputFormat, title: str, color: Optional[str] = None) -> None:
    """Create a new reminder list"""
    client = Client()

    try:
        list_id = client.create_list(title=title, color=color)

        if output_format == OutputFormat.JSON:
            click.echo(json.dumps({"success": True, "id": list_id}))
        else:
            # Get all lists for proper ID shortening
            all_lists = client.get_lists()
            short_id = shorten_id(list_id, [lst.id for lst in all_lists])
            console.print(f"\n✓ Created list: {title} {short_id}\n")

    except RuntimeError as e:
        if output_format == OutputFormat.JSON:
            click.echo(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"\n[red]Error:[/red] {e}\n")


@cli.command()
@common_options
@click.option("--hide-overdue", is_flag=True, help="Hide overdue tasks")
def today(output_format: OutputFormat, hide_overdue: bool) -> None:
    """Show today's and overdue reminders"""
    client = Client()
    now = datetime.now(timezone.utc)

    # Get both today's and overdue reminders
    today_reminders = client.get_reminders_due_today()
    overdue_reminders = (
        []
        if hide_overdue
        else [
            r
            for r in client.get_overdue_reminders()
            if r.due_date
            and r.due_date.date() != now.date()  # Exclude today's reminders to avoid duplicates
        ]
    )

    # Combine and sort all reminders
    all_reminders = overdue_reminders + today_reminders

    # Get lists info for colored display
    lists = {lst.id: lst for lst in client.get_lists()}

    if output_format == OutputFormat.JSON:
        OutputFormatter.output_reminders(all_reminders, fmt=output_format)
    else:
        OutputFormatter.output_reminders(
            all_reminders, lists=lists, show_notes=False, show_date=True  # Show full date for overdue tasks
        )


@cli.command()
@common_options
@click.option("--list", "list_id", type=IDType(list_mode=True), help="Show reminders from a specific list")
@click.option("--today", is_flag=True, help="Show reminders due today")
@click.option("--overdue", is_flag=True, help="Show overdue reminders")
@click.option("--search", help="Search reminders by text")
@click.option("--all", "show_all", is_flag=True, help="Show all reminders including completed")
def list(
    output_format: OutputFormat,
    list_id: Optional[str],
    today: bool,
    overdue: bool,
    search: Optional[str],
    show_all: bool,
) -> None:
    """List reminders"""
    client = Client()

    if today:
        title = "📅 Today"
        reminders = client.get_reminders_due_today()
    elif overdue:
        title = "⏰ Overdue"
        reminders = client.get_overdue_reminders()
    elif search:
        title = f"🔍 '{search}'"
        reminders = client.search_reminders(search)
    elif list_id:
        lists = {reminder_list.id: reminder_list.title for reminder_list in client.get_lists()}
        title = f"📋 {lists.get(list_id, 'Unknown List')}"
        reminders = client.get_reminders_in_list(list_id)
    else:
        title = "📋 All"
        reminders = client.get_all_reminders()

    if not show_all:
        reminders = [r for r in reminders if not r.completed]

    # Get lists info for colored display
    lists = {lst.id: lst for lst in client.get_lists()}

    OutputFormatter.output_reminders(
        reminders, fmt=output_format, title=title, lists=lists, show_notes=True, show_date=True
    )


@cli.command()
@common_options
@click.argument("reminder_id", type=IDType())
def show(output_format: OutputFormat, reminder_id: str) -> None:
    """Show detailed information about a specific reminder"""
    client = Client()
    try:
        reminder = client.get_reminder(reminder_id)
        lists = {lst.id: lst for lst in client.get_lists()}
        
        if output_format == OutputFormat.JSON:
            click.echo(json.dumps(asdict(reminder), default=str))
            return
            
        # Format dates nicely
        created = (
            reminder.creation_date.strftime("%Y-%m-%d %H:%M")
            if reminder.creation_date
            else "unknown"
        )
        modified = (
            reminder.modification_date.strftime("%Y-%m-%d %H:%M")
            if reminder.modification_date
            else "unknown"
        )
        due = (
            reminder.due_date.strftime("%Y-%m-%d %H:%M")
            if reminder.due_date
            else "not set"
        )
        
        # Get list information
        list_info = lists.get(reminder.list_id)
        list_name = list_info.title if list_info else "Unknown List"
        list_id = shorten_id(reminder.list_id, [lst.id for lst in lists.values()])
        
        # Format priority
        priority_map = {1: "high", 5: "medium", 9: "low"}
        priority = priority_map.get(reminder.priority, "none")
        
        # Create a rich table for the details
        table = Table(show_header=False, box=None, padding=(0, 1))
        
        # Show reminder ID in context of all reminders
        all_reminders = client.get_all_reminders()
        short_id = shorten_id(reminder.id, [r.id for r in all_reminders])
        
        table.add_row(Text("ID", style="bold"), Text(short_id, style="dim"))
        table.add_row(Text("Title", style="bold"), reminder.title)
        table.add_row(Text("Status", style="bold"), 
                     Text("✓ Completed", style="dim") if reminder.completed else "○ Active")
        # Format list with color
        list_color = format_color_block(list_info.color if list_info else None)
        table.add_row(Text("List", style="bold"), 
                     Text("").join([list_color, Text(" "), Text(f"{list_name} {list_id}", style="dim")]))
        table.add_row(Text("Priority", style="bold"), 
                     Text(priority, style="red" if priority == "high" 
                          else "yellow" if priority == "medium"
                          else "blue" if priority == "low"
                          else "dim"))
        table.add_row(Text("Due", style="bold"), 
                     Text(due, style="red" if reminder.due_date and reminder.due_date < datetime.now(timezone.utc)
                          else "yellow" if reminder.due_date
                          else "dim"))
        
        if reminder.notes:
            table.add_row(Text("Notes", style="bold"), Text(reminder.notes))
            
        table.add_row(Text("Created", style="bold"), Text(created, style="dim"))
        table.add_row(Text("Modified", style="bold"), Text(modified, style="dim"))
        
        console.print("\n")
        console.print(table)
        console.print("\n")
        
    except RuntimeError as e:
        if output_format == OutputFormat.JSON:
            click.echo(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"\n[red]Error:[/red] {e}\n")


@cli.command()
@common_options
def lists(output_format: OutputFormat) -> None:
    """Show reminder lists"""
    client = Client()
    reminder_lists = client.get_lists()

    # Get counts for each list
    reminder_counts: Dict[str, int] = {}
    for reminder_list in reminder_lists:
        reminders = client.get_reminders_in_list(reminder_list.id)
        reminder_counts[reminder_list.id] = len([r for r in reminders if not r.completed])

    OutputFormatter.output_lists(reminder_lists, reminder_counts, fmt=output_format)


@cli.command()
@common_options
def stats(output_format: OutputFormat) -> None:
    """Show statistics"""
    client = Client()
    reminders = client.get_all_reminders()

    now = datetime.now(timezone.utc)
    completed = len([r for r in reminders if r.completed])
    active = len(reminders) - completed
    overdue = len([r for r in reminders if not r.completed and r.due_date and r.due_date < now])
    due_today = len(
        [r for r in reminders if not r.completed and r.due_date and r.due_date.date() == now.date()]
    )

    stats = {
        "active": active,
        "completed": completed,
        "due_today": due_today,
        "overdue": overdue,
        "total": len(reminders),
    }

    if output_format == OutputFormat.JSON:
        click.echo(json.dumps(stats))
    else:
        formatted_stats = [
            f"[cyan]Active: {active}[/cyan]",
            f"[green]Done: {completed}[/green]",
            f"[yellow]Due Today: {due_today}[/yellow]",
            f"[red]Overdue: {overdue}[/red]",
        ]
        console.print("\n" + " • ".join(formatted_stats) + "\n")


if __name__ == "__main__":
    cli()