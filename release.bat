@echo off
REM Release script for publishing to PyPI
REM Usage: release.bat

echo ====================================
echo   Typer-GUI Release Script
echo ====================================
echo.

REM Check if dist directory exists and clean it
if exist dist (
    echo Cleaning previous builds...
    rmdir /s /q dist
    echo Previous builds cleaned.
    echo.
)

REM Build the package
echo Building package...
python -m build
if errorlevel 1 (
    echo ERROR: Build failed!
    exit /b 1
)
echo Build successful!
echo.

REM Upload to PyPI
echo Uploading to PyPI...
echo You will be prompted for credentials:
echo   Username: __token__
echo   Password: [Your PyPI API token]
echo.
python -m twine upload dist/*
if errorlevel 1 (
    echo ERROR: Upload failed!
    exit /b 1
)

echo.
echo ====================================
echo   Release completed successfully!
echo ====================================
echo.
echo Your package is now available on PyPI.
echo Check: https://pypi.org/project/typer-gui/
