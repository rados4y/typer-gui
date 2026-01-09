"""Interactive components - Button, Link, TextInput, Alert, Confirm."""

from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from .base import UiBlock, get_current_runner, set_current_runner


@dataclass
class Button(UiBlock):
    """Interactive button that executes an action (GUI only)."""

    text: str
    on_click: Callable
    icon: Optional[str] = None

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def is_gui_only(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": "button",
            "text": self.text,
            "icon": self.icon,
            "action_id": id(self.on_click),  # Can't serialize callback
        }

    def build_cli(self, ctx) -> Any:
        """Build Button for CLI (returns empty string - GUI only).

        Args:
            ctx: CLI runner context

        Returns:
            Empty string (buttons don't render in CLI)
        """
        return ""

    def build_gui(self, ctx) -> Any:
        """Build Button for GUI (returns Flet ElevatedButton).

        Args:
            ctx: GUI runner context

        Returns:
            Flet ElevatedButton control
        """
        import flet as ft

        icon_obj = None
        if self.icon:
            icon_obj = getattr(ft.Icons, self.icon.upper(), None)

        def handle_click(e):
            # Set runner context for callback execution
            saved_runner = get_current_runner()
            # Try to get runner from ctx if available
            runner = getattr(ctx, "runner", None)
            if runner:
                set_current_runner(runner)
            try:
                # Create UI stack context for callback
                with ctx.new_ui_stack() as callback_stack:
                    self.on_click()
                    # Display any ui() output from callback
                    for item in callback_stack:
                        control = ctx.build_child(self, item)
                        runner.add_to_output(control)
            finally:
                set_current_runner(saved_runner)

        return ft.ElevatedButton(
            self.text,
            icon=icon_obj,
            on_click=handle_click,
        )


@dataclass
class Link(UiBlock):
    """Interactive link that executes an action (GUI only)."""

    text: str
    on_click: Callable

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def is_gui_only(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": "link",
            "text": self.text,
            "action_id": id(self.on_click),
        }

    def build_cli(self, ctx) -> Any:
        """Build Link for CLI (returns empty string - GUI only).

        Args:
            ctx: CLI runner context

        Returns:
            Empty string (links don't render in CLI)
        """
        return ""

    def build_gui(self, ctx) -> Any:
        """Build Link for GUI (returns Flet TextButton).

        Args:
            ctx: GUI runner context

        Returns:
            Flet TextButton control
        """
        import flet as ft

        def handle_click(e):
            # Set runner context for callback execution
            saved_runner = get_current_runner()
            runner = getattr(ctx, "runner", None)
            if runner:
                set_current_runner(runner)
            try:
                # Create UI stack context for callback
                with ctx.new_ui_stack() as callback_stack:
                    self.on_click()
                    # Display any ui() output from callback
                    for item in callback_stack:
                        control = ctx.build_child(self, item)
                        runner.add_to_output(control)
            finally:
                set_current_runner(saved_runner)

        return ft.TextButton(
            self.text,
            icon=ft.Icons.LINK,
            on_click=handle_click,
        )


@dataclass
class TextInput(UiBlock):
    """Text input field."""

    label: str
    value: str = ""
    on_change: Optional[Callable[[str], None]] = None

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {
            "type": "text_input",
            "label": self.label,
            "value": self.value,
        }

    def build_cli(self, ctx) -> Any:
        """Build TextInput for CLI (returns Rich Text - prompts for input).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable with input result
        """
        from rich.text import Text as RichText

        # Note: In CLI mode, this would typically use input() during show_cli
        # For build_cli, we just return the current state
        return RichText(f"{self.label}: {self.value}")

    def build_gui(self, ctx) -> Any:
        """Build TextInput for GUI (returns Flet TextField).

        Args:
            ctx: GUI runner context

        Returns:
            Flet TextField control
        """
        import flet as ft

        def handle_change(e):
            self.value = e.control.value
            if self.on_change:
                # Set runner context for callback execution
                saved_runner = get_current_runner()
                runner = getattr(ctx, "runner", None)
                if runner:
                    set_current_runner(runner)
                try:
                    # Create UI stack context for callback
                    with ctx.new_ui_stack() as callback_stack:
                        self.on_change(e.control.value)
                        # Display any ui() output from callback
                        for item in callback_stack:
                            control = ctx.build_child(self, item)
                            runner.add_to_output(control)
                finally:
                    set_current_runner(saved_runner)

        return ft.TextField(
            label=self.label,
            value=self.value,
            on_change=handle_change,
        )


@dataclass
class Alert(UiBlock):
    """Alert dialog with OK button to dismiss."""

    title: str
    content: Union[str, UiBlock]

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {
            "type": "alert",
            "title": self.title,
            "content": str(self.content),
        }

    def build_cli(self, ctx) -> Any:
        """Build Alert for CLI (prints content and waits for Enter).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable with alert content
        """
        from rich.text import Text as RichText
        from rich.panel import Panel

        # Convert content to string
        if isinstance(self.content, UiBlock):
            content_text = self.content.to_text()
        else:
            content_text = str(self.content)

        # Show alert in CLI by printing and waiting for confirmation
        print(f"\n{'='*60}")
        print(f"ALERT: {self.title}")
        print('='*60)
        print(content_text)
        print('='*60)
        input("Press Enter to continue...")
        print()

        return RichText("")  # Return empty - already printed

    def build_gui(self, ctx) -> Any:
        """Build Alert for GUI (shows AlertDialog with OK button).

        Args:
            ctx: GUI runner context

        Returns:
            Empty Container (dialog is shown via page overlay)
        """
        import flet as ft

        # Get page from ctx
        runner = getattr(ctx, "runner", None)
        if not runner or not hasattr(runner, "page") or not runner.page:
            return ft.Container()  # Can't show dialog without page

        page = runner.page

        # Build content control with UI stack context
        with ctx.new_ui_stack() as ui_stack:
            if isinstance(self.content, UiBlock):
                content_control = ctx.build_child(self, self.content)
            else:
                # Convert string to Md component
                from .md import Md
                content_control = ctx.build_child(self, Md(str(self.content)))

        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text(self.title),
            content=content_control,
            actions=[
                ft.TextButton("OK", on_click=lambda e: close_dialog(dialog, page))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def close_dialog(dlg, pg):
            """Close the dialog."""
            dlg.open = False
            pg.update()

        # Show dialog
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        # Return empty container (dialog is in overlay)
        return ft.Container()


@dataclass
class Confirm(UiBlock):
    """Confirmation dialog with Yes/No buttons."""

    title: str
    message: Union[str, UiBlock]
    on_yes: Optional[Callable] = None
    on_no: Optional[Callable] = None

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {
            "type": "confirm",
            "title": self.title,
            "message": str(self.message),
        }

    def build_cli(self, ctx) -> Any:
        """Build Confirm for CLI (prompts for y/n input).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable with confirmation result
        """
        from rich.text import Text as RichText

        # Convert message to string
        if isinstance(self.message, UiBlock):
            message_text = self.message.to_text()
        else:
            message_text = str(self.message)

        # Show confirmation prompt
        print(f"\n{'='*60}")
        print(f"CONFIRM: {self.title}")
        print('='*60)
        print(message_text)
        print('='*60)

        while True:
            response = input("Continue? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                if self.on_yes:
                    saved_runner = get_current_runner()
                    runner = getattr(ctx, "runner", None)
                    if runner:
                        set_current_runner(runner)
                    try:
                        self.on_yes()
                    finally:
                        set_current_runner(saved_runner)
                break
            elif response in ['n', 'no']:
                if self.on_no:
                    saved_runner = get_current_runner()
                    runner = getattr(ctx, "runner", None)
                    if runner:
                        set_current_runner(runner)
                    try:
                        self.on_no()
                    finally:
                        set_current_runner(saved_runner)
                break
            else:
                print("Please enter 'y' or 'n'")

        print()
        return RichText("")  # Return empty - already printed

    def build_gui(self, ctx) -> Any:
        """Build Confirm for GUI (shows AlertDialog with Yes/No buttons).

        Args:
            ctx: GUI runner context

        Returns:
            Empty Container (dialog is shown via page overlay)
        """
        import flet as ft

        # Get page from ctx
        runner = getattr(ctx, "runner", None)
        if not runner or not hasattr(runner, "page") or not runner.page:
            return ft.Container()  # Can't show dialog without page

        page = runner.page

        # Build message control with UI stack context
        with ctx.new_ui_stack() as ui_stack:
            if isinstance(self.message, UiBlock):
                message_control = ctx.build_child(self, self.message)
            else:
                # Convert string to Text component
                from .text import Text
                message_control = ctx.build_child(self, Text(str(self.message)))

        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text(self.title),
            content=message_control,
            actions=[
                ft.TextButton(
                    "Yes",
                    on_click=lambda e: handle_yes(dialog, page)
                ),
                ft.TextButton(
                    "No",
                    on_click=lambda e: handle_no(dialog, page)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def handle_yes(dlg, pg):
            """Handle Yes button click."""
            dlg.open = False
            pg.update()
            if self.on_yes:
                saved_runner = get_current_runner()
                if runner:
                    set_current_runner(runner)
                try:
                    # Create UI stack context for callback
                    with ctx.new_ui_stack() as callback_stack:
                        self.on_yes()
                        # Display any ui() output from callback
                        for item in callback_stack:
                            control = ctx.build_child(self, item)
                            runner.add_to_output(control)
                finally:
                    set_current_runner(saved_runner)

        def handle_no(dlg, pg):
            """Handle No button click."""
            dlg.open = False
            pg.update()
            if self.on_no:
                saved_runner = get_current_runner()
                if runner:
                    set_current_runner(runner)
                try:
                    # Create UI stack context for callback
                    with ctx.new_ui_stack() as callback_stack:
                        self.on_no()
                        # Display any ui() output from callback
                        for item in callback_stack:
                            control = ctx.build_child(self, item)
                            runner.add_to_output(control)
                finally:
                    set_current_runner(saved_runner)

        # Show dialog
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        # Return empty container (dialog is in overlay)
        return ft.Container()
