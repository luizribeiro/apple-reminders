{ pkgs, ... }: {
  # Disable cachix warning
  cachix.enable = false;

  # Name your project
  name = "apple-reminders";

  packages = [
    pkgs.swift
    pkgs.python311
    pkgs.uv
  ];

  languages = {
    python.enable = true;
    python.package = pkgs.python311;
    python.venv.enable = true;
  };

  enterShell = ''
    echo "🔨 Setting up development environment..."
    
    # Initialize and activate venv if needed
    if [ ! -d .venv ]; then
      echo "📦 Creating Python virtual environment..."
      python -m venv .venv
    fi
    
    source .venv/bin/activate
    
    echo "✨ Development environment ready!"
  '';
}