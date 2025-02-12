# Apple Reminders Python Library

[![CI](https://github.com/luizribeiro/apple-reminders/actions/workflows/ci.yml/badge.svg)](https://github.com/luizribeiro/apple-reminders/actions/workflows/ci.yml)

A Python library for interacting with Apple's Reminders app on macOS, providing both a programmable interface and a command-line utility.

## Features

### Library Features
- Full access to Apple's Reminders through EventKit
- Create and manage reminder lists
- Create, read, and manage reminders
- Filter by due date, completion status
- Search functionality
- Rich metadata support (priorities, notes, due dates)

### Command-line Utility Features
The library includes `rem`, a command-line tool for quick access to your reminders with:
- View today's, overdue, and all reminders
- Create and manage reminder lists and individual reminders
- Search and filter reminders
- Show detailed statistics and reminder information
- Support for both pretty terminal output and JSON format
- Rich color and formatting support

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
```

Note: The development environment is automatically managed through `devenv`, and virtual environments are setup with `uv` and automatically loaded by `devenv`. All commands should be run from within `devenv shell`.

## Library Usage

```python
from apple_reminders import Client
from datetime import datetime, timezone

# Initialize the client
client = Client()

# Get all reminders
reminders = client.get_all_reminders()
for reminder in reminders:
    print(f"{reminder.title} - Due: {reminder.due_date}")

# Get reminder lists
lists = client.get_lists()
for list_ in lists:
    print(f"{list_.title}: {list_.color}")

# Create a new list
list_id = client.create_list(
    title="Shopping List",
    color="#FF0000"  # Optional color in hex format
)

# Create a new reminder
reminder_id = client.create_reminder(
    title="Buy milk",
    list_id=list_id,
    notes="2% milk",
    due_date=datetime.now(timezone.utc),
    priority=1  # high priority
)

# Get today's reminders
today = client.get_reminders_due_today()

# Get overdue reminders
overdue = client.get_overdue_reminders()

# Search reminders
results = client.search_reminders("shopping")
```

## Command-line Usage

The `rem` command-line tool provides quick access to your reminders:

```bash
# Basic commands
rem today             # Show today's and overdue reminders
rem list              # List all reminders
rem lists             # Show all reminder lists (and get their IDs)
rem stats             # Show statistics
rem show abc123       # Show detailed information about reminder with ID abc123

# Creating reminders and lists
rem create-list "Shopping" --color "#FF0000"    # Creates a list and returns its ID
rem add "Buy milk" --list abc123 --due "2024-03-20 15:00" --priority high --notes "2% milk"
                                                # abc123 is the list ID from create-list

# Managing reminders
rem done def456       # Mark reminder def456 as completed
rem undone def456     # Mark reminder def456 as not completed

# Filtering options
rem list --overdue             # Show overdue reminders
rem list --today               # Show today's reminders
rem list --search "shopping"   # Search reminders
rem list --list abc123         # Show reminders from list with ID abc123
rem list --all                 # Show all reminders including completed

# Output formats
rem list --format json    # Output as JSON
rem today --format json   # JSON output for today's reminders
rem add --format json     # JSON output for creation result

Note: List and reminder IDs are shown in the CLI output in a shortened form.
You can use these shortened IDs in commands as long as they uniquely identify the item.
For example, if a full ID is "1234-5678", you might be able to use just "1234"
if no other IDs start with those digits.
```

## Reminder Objects

The library provides rich objects with all reminder metadata:

```python
class Reminder:
    id: str                      # Unique identifier
    title: str                   # Reminder title
    due_date: datetime           # Due date (optional)
    completed: bool              # Completion status
    notes: str                   # Notes (optional)
    priority: int                # Priority (1=high, 5=medium, 9=low)
    list_id: str                 # Parent list ID
    creation_date: datetime      # When created
    modification_date: datetime  # Last modified
```

## List Objects

```python
class ReminderList:
    id: str                 # Unique identifier
    title: str              # List title
    color: Optional[str]    # List color in hex format (e.g., "#FF0000")
```

## Permissions

On first use, macOS will prompt for permission to access Reminders. This is required for both the library and command-line tool to function.

## Development

### Project Structure

This project combines a Swift library (using Apple's EventKit) with a Python interface:

```
apple-reminders/
├── Sources/                    # Swift source code
│   └── RemindersLib/           # Swift library using EventKit
│       ├── RemindersLib.swift  # Main Swift implementation
│       └── include/            # C-compatible header
├── src/
│   └── apple_reminders/        # Python package
│       ├── lib/                # Built Swift dylib gets packaged here
│       ├── client.py           # Main Python interface
│       ├── ffi.py              # Swift/Python FFI bindings
│       └── rem.py              # CLI implementation
├── tests/                      # Python tests
├── Package.swift               # Swift package configuration
├── pyproject.toml              # Python project configuration
├── hatch_build.py              # Custom build hooks for Hatch
└── RemindersLib.entitlements   # macOS security entitlements
```

### Architecture

The package works through several layers:

1. Swift Library (`RemindersLib`):
   - Interfaces directly with Apple's EventKit
   - Handles all direct Reminders.app interactions
   - Provides a C-compatible FFI interface

2. Python FFI Layer (`ffi.py`):
   - Uses ctypes to load and interact with the Swift library
   - Handles type conversions between Swift and Python
   - Manages library discovery and loading

3. Python Interface (`client.py`):
   - Provides a Pythonic API over the FFI layer
   - Handles data conversions and error management
   - Implements additional convenience methods

### Development Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/apple-reminders.git
cd apple-reminders
```

2. Setup development environment:
```bash
devenv shell
```

3. Build the Swift library:
```bash
swift build -c release  # Uses release build for better performance
```

4. Install in development mode:
```bash
pip install -e .
```

### Building for Distribution

The package uses Hatch for building and packaging, which handles both the Swift and Python components:

1. Build the package:
```bash
# Using hatch directly (recommended)
hatch build

# Or using pip's build module
pip install build
python -m build
```

This creates in the `dist/` directory:
- A wheel (`.whl`) containing the bundled library, ready for distribution
- A source distribution (`.tar.gz`) for development

2. Upload to PyPI (after creating an account and getting an API token):
```bash
pip install twine
twine upload dist/*
```

During the build:
- The Swift library is automatically compiled in release mode
- The dylib is bundled into the wheel package
- Platform tags are set correctly for macOS/arm64
- The package ensures it's only installed on compatible systems

Note: For development, you can install in editable mode with:
```bash
pip install -e .
```

### Platform Support

This package only works on macOS due to its dependency on Apple's EventKit framework. The package includes checks to ensure it's only installed on compatible systems.

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
- Initial CI setup and code improvements by Goose 🦢
