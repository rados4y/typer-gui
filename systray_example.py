"""
Simple example showing how to use Flet with System Tray.
When minimized, the app goes to the system tray.
Right-click the tray icon to restore or exit the app.

Requirements:
    pip install flet pystray pillow
"""

import flet as ft
import pystray
from PIL import Image, ImageDraw


def create_tray_icon():
    """Create a simple icon image for the system tray."""
    # Create a simple 64x64 icon with a colored circle
    width = 64
    height = 64
    color1 = "blue"
    color2 = "white"

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.ellipse([width // 4, height // 4, width * 3 // 4, height * 3 // 4], fill=color2)

    return image


# Global reference to the page
page_ref: ft.Page = None
tray_image = create_tray_icon()


def show_window(icon, item):
    """Restore the window from system tray."""
    icon.visible = False
    page_ref.window.skip_task_bar = False
    page_ref.window.visible = True
    page_ref.update()
    print("Window restored")


def quit_app(icon, item):
    """Exit the application completely."""
    icon.stop()
    page_ref.window.destroy()
    print("Application closed")


# Create system tray icon
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


def on_window_event(e: ft.WindowEvent):
    """Handle window events like minimize, restore, close."""
    if e.data == "minimize":
        # Hide window and show in tray
        tray_icon.visible = True
        page_ref.window.skip_task_bar = True
        page_ref.window.visible = False
        page_ref.update()
        print("Minimized to tray")

    elif e.data == "restore":
        # Restore window from tray
        tray_icon.visible = False
        page_ref.window.skip_task_bar = False
        page_ref.update()
        print("Window restored")

    elif e.data == "close":
        # Handle window close
        tray_icon.stop()
        page_ref.window.destroy()
        print("Window closed")


def minimize_window():
    """Minimize the window programmatically."""
    page_ref.window.minimized = True
    page_ref.update()


def main(page: ft.Page):
    """Main Flet application."""
    global page_ref
    page_ref = page

    # Configure window
    page.title = "Flet System Tray Example"
    page.window.prevent_close = True
    page.window.on_event = on_window_event
    page.window.width = 500
    page.window.height = 400

    # Add UI elements
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("System Tray Example", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Instructions:", size=18, weight=ft.FontWeight.W_500),
                ft.Text("• Minimize this window to send it to the system tray"),
                ft.Text("• Look for the icon in your system tray (notification area)"),
                ft.Text("• Right-click the tray icon to restore or exit"),
                ft.Text("• Double-click the tray icon to restore the window"),
                ft.Divider(),
                ft.Button(
                    "Minimize to Tray",
                    icon=ft.Icons.MINIMIZE,
                    on_click=lambda _: minimize_window()
                ),
            ], spacing=10),
            padding=20
        )
    )


if __name__ == "__main__":
    # Start system tray in background
    tray_icon.run_detached()

    # Start Flet app
    ft.run(main)
