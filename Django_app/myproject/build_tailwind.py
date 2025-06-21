#!/usr/bin/env python3
"""
Script to build Tailwind CSS for the Django project.
Usage: python build_tailwind.py [dev|build]
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(f"Error: {result.stderr}")
            return False
        print(f"Success: {result.stdout}")
        return True
    except Exception as e:
        print(f"Exception running command: {command}")
        print(f"Error: {e}")
        return False

def main():
    # Get the project root directory
    project_root = Path(__file__).parent
    theme_dir = project_root / "theme" / "static_src"
    
    if not theme_dir.exists():
        print(f"Error: Theme directory not found at {theme_dir}")
        sys.exit(1)
    
    # Check if npm is installed
    if not run_command("npm --version", cwd=theme_dir):
        print("Error: npm is not installed or not available")
        sys.exit(1)
    
    # Parse command line arguments
    mode = "build"  # default mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if mode == "dev":
        print("Starting Tailwind CSS development mode...")
        print("This will watch for changes and rebuild automatically.")
        print("Press Ctrl+C to stop.")
        run_command("npm run dev", cwd=theme_dir)
    elif mode == "build":
        print("Building Tailwind CSS for production...")
        if run_command("npm run build", cwd=theme_dir):
            print("✅ Tailwind CSS built successfully!")
        else:
            print("❌ Failed to build Tailwind CSS")
            sys.exit(1)
    else:
        print("Usage: python build_tailwind.py [dev|build]")
        print("  dev   - Start development mode with file watching")
        print("  build - Build for production (default)")
        sys.exit(1)

if __name__ == "__main__":
    main()