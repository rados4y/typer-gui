#!/usr/bin/env python
"""Cross-platform release script for publishing to PyPI."""

import subprocess
import sys
import shutil
import re
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            text=True,
            capture_output=True
        )
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR: {description} failed!")
        print(f"  Exit code: {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False, ""


def get_current_version():
    """Read current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")

    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)

    print("✗ ERROR: Could not find version in pyproject.toml")
    sys.exit(1)


def bump_minor_version(version):
    """Bump the minor version number."""
    parts = version.split(".")
    if len(parts) != 3:
        print(f"✗ ERROR: Invalid version format: {version}")
        sys.exit(1)

    major, minor, patch = parts
    new_minor = int(minor) + 1
    return f"{major}.{new_minor}.0"


def update_version_in_file(file_path, old_version, new_version):
    """Update version in a file."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    # Replace version string
    updated = content.replace(f'"{old_version}"', f'"{new_version}"')

    path.write_text(updated, encoding="utf-8")
    print(f"  Updated {file_path}")


def main():
    """Main release workflow."""
    print("=" * 60)
    print("  Typer-GUI Automated Release Script")
    print("=" * 60)

    # Step 1: Get current version
    print("\n[1/8] Reading current version...")
    current_version = get_current_version()
    print(f"  Current version: {current_version}")

    # Step 2: Bump version
    print("\n[2/8] Bumping minor version...")
    new_version = bump_minor_version(current_version)
    print(f"  New version: {new_version}")

    # Confirm with user
    print("\n" + "=" * 60)
    response = input(f"Proceed with release v{new_version}? [y/N]: ").strip().lower()
    if response != "y":
        print("Release cancelled.")
        sys.exit(0)
    print("=" * 60)

    # Step 3: Update version in files
    print("\n[3/8] Updating version in files...")
    update_version_in_file("pyproject.toml", current_version, new_version)
    update_version_in_file("typer_gui/__init__.py", current_version, new_version)
    print("✓ Version updated in all files")

    # Step 4: Commit version bump
    print("\n[4/8] Committing version bump...")
    commit_msg = f"Bump version to {new_version}"
    success, _ = run_command(
        f'git add pyproject.toml typer_gui/__init__.py && git commit -m "{commit_msg}"',
        "Committing version bump"
    )
    if not success:
        print("✗ ERROR: Failed to commit version bump")
        sys.exit(1)

    # Step 5: Create git tag
    print("\n[5/8] Creating git tag...")
    tag_name = f"v{new_version}"
    success, _ = run_command(
        f'git tag -a {tag_name} -m "Release {tag_name}"',
        f"Creating tag {tag_name}"
    )
    if not success:
        print("✗ ERROR: Failed to create git tag")
        sys.exit(1)

    # Step 6: Push to remote
    print("\n[6/8] Pushing to remote repository...")
    success, _ = run_command(
        f"git push && git push origin {tag_name}",
        "Pushing commit and tag to remote"
    )
    if not success:
        print("✗ ERROR: Failed to push to remote")
        sys.exit(1)

    # Step 7: Clean and build package
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("\n[7/8] Cleaning previous builds...")
        shutil.rmtree(dist_dir)
        print("✓ Previous builds cleaned")

    success, _ = run_command("python -m build", "Building package")
    if not success:
        sys.exit(1)

    # Step 8: Upload to PyPI
    print("\n[8/8] Uploading to PyPI...")
    print("=" * 60)
    print("You will be prompted for credentials:")
    print("  Username: __token__")
    print("  Password: [Your PyPI API token]")
    print("=" * 60)

    success, _ = run_command("python -m twine upload dist/*", "Uploading to PyPI")
    if not success:
        sys.exit(1)

    # Success message
    print("\n" + "=" * 60)
    print(f"  Release v{new_version} completed successfully!")
    print("=" * 60)
    print(f"\n✓ Version bumped: {current_version} → {new_version}")
    print(f"✓ Git tag created: {tag_name}")
    print(f"✓ Pushed to GitHub")
    print(f"✓ Published to PyPI")
    print(f"\nCheck: https://pypi.org/project/typer-gui/")
    print(f"GitHub Release: https://github.com/rados4y/typer-gui/releases/tag/{tag_name}")


if __name__ == "__main__":
    main()
