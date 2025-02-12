import os
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        # Only build the Swift library when building the wheel
        if self.target_name != "wheel":
            return

        root = Path(self.root)
        lib_name = "RemindersLib"
        dylib_name = f"lib{lib_name}.dylib"

        # Skip if not on macOS
        if sys.platform != "darwin":
            raise RuntimeError("This package only supports macOS")

        # Build the Swift library
        subprocess.run(["swift", "build", "-c", "release"], check=True)

        # Create the package data directory
        package_data_dir = root / "src/apple_reminders/lib"
        package_data_dir.mkdir(exist_ok=True)

        # Copy the built dylib to the package data directory
        build_dir = root / ".build/release"
        dylib_path = build_dir / dylib_name
        if not dylib_path.exists():
            raise RuntimeError(f"Failed to build Swift library: {dylib_path} not found")

        # Copy the dylib to the package directory
        target_path = package_data_dir / dylib_name
        target_path.write_bytes(dylib_path.read_bytes())

        # Add the lib directory to the wheel's data files
        build_data["pure_python"] = False
        build_data["tag"] = "macosx_11_0_arm64"  # Adjust based on your minimum macOS version