#!/usr/bin/env python
"""Cross-platform release script for publishing to PyPI."""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            text=True,
            capture_output=False
        )
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR: {description} failed!")
        print(f"  Exit code: {e.returncode}")
        return False


def main():
    """Main release workflow."""
    print("=" * 50)
    print("  Typer-GUI Release Script")
    print("=" * 50)

    # Clean previous builds
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("\nCleaning previous builds...")
        shutil.rmtree(dist_dir)
        print("✓ Previous builds cleaned")

    # Build the package
    if not run_command("python -m build", "Building package"):
        sys.exit(1)

    # Upload to PyPI
    print("\n" + "=" * 50)
    print("Uploading to PyPI...")
    print("You will be prompted for credentials:")
    print("  Username: __token__")
    print("  Password: [Your PyPI API token]")
    print("=" * 50)

    if not run_command("python -m twine upload dist/*", "Uploading to PyPI"):
        sys.exit(1)

    # Success message
    print("\n" + "=" * 50)
    print("  Release completed successfully!")
    print("=" * 50)
    print("\nYour package is now available on PyPI.")
    print("Check: https://pypi.org/project/typer-gui/")


if __name__ == "__main__":
    main()
