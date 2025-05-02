{ pkgs, ... }: {
  name = "apple-reminders";

  env.PYTHONPATH = "./src";

  packages = with pkgs; [
    darwin.apple_sdk.frameworks.AppKit
    darwin.apple_sdk.frameworks.Foundation
    python311
    python311Packages.pip
    python311Packages.pytest
    python311Packages.pytest-cov
    python311Packages.pytest-mock
    swift
    swiftpm
    uv
  ];

  # Python configuration
  languages.python = {
    enable = true;
    package = pkgs.python311;
    venv.enable = true;
  };

  enterShell = ''
    echo "🔨 Setting up development environment..."
    
    # Initialize and activate venv if needed
    if [ ! -d .venv ]; then
      echo "📦 Creating Python virtual environment..."
      python -m venv .venv
    fi
    
    source .venv/bin/activate

    # Install dependencies with uv
    echo "📦 Installing dependencies..."
    uv pip install -e ".[dev]"
    
    echo "✨ Development environment ready!"
  '';

  processes.test.exec = "pytest";
}

