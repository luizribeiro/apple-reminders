# 🎯 Apple Reminders CLI

A beautiful command-line interface for Apple's Reminders app, built with Python and Swift.

## ✨ Features

- 📋 List, create, and manage reminders from your terminal
- 🏷️ Filter by tags, lists, due dates, and more
- 🎨 Beautiful, colorful interface
- 📊 Reminder statistics and insights
- 🚀 Fast and efficient Swift backend

## 🛠️ Setup

### Prerequisites

1. Install Nix package manager:
```bash
sh <(curl -L https://nixos.org/nix/install)
```

2. Enable Nix Flakes:
```bash
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

3. Install devenv:
```bash
nix-channel --add https://github.com/cachix/devenv/archive/latest.tar.gz devenv 
nix-channel --update
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/apple-reminders.git
cd apple-reminders
```

2. Enter the development environment:
```bash
devenv shell
```

3. Install the package:
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## 🚀 Usage

### List Reminders

Show all reminders:
```bash
rem list
```

Show today's reminders:
```bash
rem list --today
```

Show overdue reminders:
```bash
rem list --overdue
```

Filter by tag:
```bash
rem list --tag work
```

### Add Reminders

Add a simple reminder:
```bash
rem add "Buy groceries"
```

Add with details:
```bash
rem add "Team meeting" --due "tomorrow 2pm" --notes "Prepare presentation" --tags "work,important"
```

### Manage Lists

Show all lists:
```bash
rem lists
```

### Statistics

Show reminder statistics:
```bash
rem stats
```

## 🧑‍💻 Development

### Project Structure

```
apple-reminders/
├── src/
│   └── apple_reminders/     # Python package
│       ├── __init__.py      # Core library
│       └── rem.py           # CLI interface
├── Sources/                 # Swift code
│   └── TodayReminders/
│       ├── include/
│       │   └── RemindersLib.h
│       └── RemindersLib.swift
├── tests/                   # Test suite
├── devenv.nix              # Development environment
└── pyproject.toml          # Python config
```

### Development Commands

Format code:
```bash
black .
```

Run linter:
```bash
ruff check .
```

Run tests:
```bash
pytest
```

Build Swift library:
```bash
swift build
```

### Development Flow

1. Enter development environment:
```bash
devenv shell
```

2. Make your changes

3. Format and lint:
```bash
black .
ruff check .
```

4. Run tests:
```bash
pytest
```

5. Build Swift library if needed:
```bash
swift build
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built on top of Apple's EventKit
- Uses Click for CLI interface
- Uses Rich for beautiful terminal output