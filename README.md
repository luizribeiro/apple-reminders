# Apple Reminders Python Library

A Python library for interacting with Apple's Reminders app on macOS, providing both a programmable interface and a command-line utility.

## Features

### Library Features
- Full access to Apple's Reminders through EventKit
- Read reminders and lists
- Filter by due date, completion status
- Search functionality
- Rich metadata support (priorities, notes, due dates)

### Command-line Utility
The library includes `rem`, a command-line tool for quick access to your reminders:
```bash
rem today              # Show today's and overdue reminders
rem list              # List all reminders
rem list --overdue    # Show overdue reminders
rem lists             # Show all reminder lists
rem stats             # Show reminder statistics
```

## Installation

### Prerequisites
- macOS (uses Apple's EventKit)
- Python 3.9+
- [Nix with devenv](https://devenv.sh/getting-started/) for development

### User Installation
```bash
pip install apple-reminders
```

### Development Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/apple-reminders.git
cd apple-reminders
```

2. Setup development environment:
```bash
devenv shell
python -m venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Library Usage

```python
from apple_reminders import RemindersAPI

# Initialize the API
api = RemindersAPI()

# Get all reminders
reminders = api.get_all_reminders()
for reminder in reminders:
    print(f"{reminder.title} - Due: {reminder.due_date}")

# Get reminder lists
lists = api.get_lists()
for list_ in lists:
    print(f"{list_.title}: {list_.color}")

# Get today's reminders
today = api.get_reminders_due_today()

# Get overdue reminders
overdue = api.get_overdue_reminders()

# Search reminders
results = api.search_reminders("shopping")
```

## Command-line Usage

The `rem` command-line tool provides quick access to your reminders:

```bash
# Basic commands
rem today              # Show today's and overdue reminders
rem list              # List all reminders
rem lists             # Show all reminder lists
rem stats             # Show statistics

# Filtering options
rem list --overdue    # Show overdue reminders
rem list --today      # Show today's reminders
rem list --search "shopping"   # Search reminders
rem list --list "Shopping"    # Show reminders from a specific list

# Output formats
rem list --format json    # Output as JSON
rem today --format json   # JSON output for today's reminders
```

## Reminder Objects

The library provides rich objects with all reminder metadata:

```python
class Reminder:
    id: str                  # Unique identifier
    title: str              # Reminder title
    due_date: datetime      # Due date (optional)
    completed: bool         # Completion status
    notes: str             # Notes (optional)
    priority: int          # Priority (1=high, 5=medium, 9=low)
    list_id: str           # Parent list ID
    creation_date: datetime    # When created
    modification_date: datetime  # Last modified
```

## Permissions

On first use, macOS will prompt for permission to access Reminders. This is required for both the library and command-line tool to function.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on Apple's EventKit framework
- Uses Click for CLI interface
- Uses Rich for beautiful terminal output