# Flet System Tray Example

A simple standalone example demonstrating how to use Flet with system tray functionality.

## Requirements

Install the required packages:

```bash
pip install flet pystray pillow
```

## Running the Example

Simply run:

```bash
python systray_example.py
```

## How It Works

1. **Window Opens**: The application starts with a normal Flet window
2. **Minimize to Tray**: When you minimize the window (or click the "Minimize to Tray" button), it disappears from the taskbar and appears in the system tray
3. **Restore Window**:
   - Double-click the tray icon, OR
   - Right-click and select "Show Window"
4. **Exit**: Right-click the tray icon and select "Exit"

## Key Features

- **No external icon file needed**: Creates a simple icon programmatically using PIL
- **System tray integration**: Uses `pystray` library
- **Window event handling**: Detects minimize, restore, and close events
- **Clean shutdown**: Properly stops tray icon when exiting

## Code Highlights

### Creating a Simple Icon

```python
def create_tray_icon():
    """Create a simple icon image for the system tray."""
    image = Image.new('RGB', (64, 64), "blue")
    dc = ImageDraw.Draw(image)
    dc.ellipse([16, 16, 48, 48], fill="white")
    return image
```

### System Tray Setup

```python
tray_icon = pystray.Icon(
    name="FletApp",
    icon=tray_image,
    title="Flet System Tray Example",
    menu=pystray.Menu(
        pystray.MenuItem("Show Window", show_window, default=True),
        pystray.MenuItem("Exit", quit_app)
    ),
    visible=False
)
```

### Window Event Handler

```python
def on_window_event(e: ft.WindowEvent):
    if e.data == "minimize":
        tray_icon.visible = True
        page_ref.window_skip_task_bar = True
        page_ref.window_visible = False
    # ... other events
```

## Platform Notes

- **Windows**: Fully tested and working
- **macOS**: Should work but may require different icon format
- **Linux**: Depends on desktop environment's system tray support

## Troubleshooting

**Tray icon not appearing?**
- Check your system tray settings
- On Windows 11, make sure system tray icons are visible in Settings

**Application won't close?**
- Use the "Exit" option from the tray icon menu
- The window close button is prevented to allow minimize-to-tray behavior
