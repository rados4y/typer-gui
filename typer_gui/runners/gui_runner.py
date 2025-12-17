"""GUI runner using Flet for desktop applications."""

import asyncio
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional

import flet as ft

from .base import Runner
from ..specs import AppSpec, CommandSpec, ParamType
from ..events import (
    Event,
    CommandSelected,
    CommandStarted,
    CommandFinished,
    TextEmitted,
    BlockEmitted,
    ContainerStarted,
    ContainerEnded,
    ErrorRaised,
)


class _RealTimeWriter(io.StringIO):
    """Custom writer for real-time output streaming."""

    def __init__(self, append_callback):
        super().__init__()
        self.append_callback = append_callback
        self.buffer = ""

    def write(self, text):
        if text:
            self.buffer += text
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                self.append_callback(line)
        return len(text)

    def flush(self):
        if self.buffer:
            self.append_callback(self.buffer)
            self.buffer = ""
        super().flush()


class GUIRunner(Runner):
    """Runner for Flet-based GUI applications."""

    def __init__(self, app_spec: AppSpec):
        super().__init__(app_spec)
        self.page: Optional[ft.Page] = None
        self.current_command: Optional[CommandSpec] = None
        self.form_controls: dict[str, ft.Control] = {}

        # UI components
        self.command_list: Optional[ft.ListView] = None
        self.form_container: Optional[ft.Column] = None
        self.output_view: Optional[ft.ListView] = None

        # Container stack for nested UI blocks
        self.container_stack: list[ft.Control] = []

    async def start(self) -> None:
        """Start the Flet GUI application."""
        # Flet app will be started via ft.app() externally
        # This method sets up the initial state
        pass

    def build(self, page: ft.Page) -> None:
        """Build the Flet GUI.

        Args:
            page: Flet page instance
        """
        self.page = page
        page.title = self.app_spec.title or "Typer GUI"
        page.window_width = 1000
        page.window_height = 700
        page.padding = 0

        # Create main layout
        header = self._create_header()
        content = self._create_content()

        page.add(
            ft.Column(
                controls=[header, content],
                expand=True,
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )

        # Select first command
        if self.app_spec.commands:
            self._select_command(self.app_spec.commands[0])

    def _create_header(self) -> ft.Container:
        """Create header with title and description."""
        controls = []

        if self.app_spec.title:
            controls.append(
                ft.Text(
                    self.app_spec.title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                )
            )

        if self.app_spec.description:
            controls.append(
                ft.Text(
                    self.app_spec.description,
                    size=14,
                    color=ft.Colors.GREY_700,
                )
            )

        if not controls:
            return ft.Container()

        return ft.Container(
            content=ft.Column(controls=controls, spacing=5),
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_50,
        )

    def _create_content(self) -> ft.Row:
        """Create main content area."""
        # Command list
        self.command_list = self._create_command_list()

        # Form container
        self.form_container = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=12,
        )

        # Output view
        self.output_view = ft.ListView(
            controls=[],
            auto_scroll=True,
            expand=True,
            spacing=0,
        )

        # Layout
        left_panel = ft.Container(
            content=self.command_list,
            width=185,
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=10,
        )

        right_panel = ft.Column(
            controls=[
                ft.Container(
                    content=self.form_container,
                    padding=20,
                ),
                ft.Container(
                    content=self.output_view,
                    padding=ft.padding.only(left=20, right=20, bottom=20),
                    expand=True,
                ),
            ],
            expand=True,
        )

        return ft.Row(
            controls=[left_panel, right_panel],
            expand=True,
            spacing=0,
        )

    def _create_command_list(self) -> ft.ListView:
        """Create command list view."""
        if not self.app_spec.commands:
            return ft.ListView(
                controls=[ft.Text("No commands", color=ft.Colors.GREY_600)]
            )

        buttons = []
        for cmd in self.app_spec.commands:
            if cmd.ui_spec.is_button:
                btn = ft.ElevatedButton(
                    text=cmd.name,
                    on_click=lambda e, command=cmd: self._select_command(command),
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                    ),
                )
            else:
                btn = ft.TextButton(
                    text=cmd.name,
                    on_click=lambda e, command=cmd: self._select_command(command),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                    ),
                )
            buttons.append(btn)

        return ft.ListView(controls=buttons, spacing=5, expand=True)

    def _select_command(self, command: CommandSpec) -> None:
        """Select and display a command.

        Args:
            command: Command to select
        """
        self.current_command = command
        self.form_controls.clear()

        # Clear output
        if self.output_view:
            self.output_view.controls.clear()

        # Build form
        form_controls = []

        # Title
        title_controls = []
        title_controls.append(
            ft.Text(
                command.name.upper(),
                size=20,
                weight=ft.FontWeight.BOLD,
            )
        )

        if command.help_text:
            title_controls.append(
                ft.Text(
                    command.help_text,
                    size=14,
                    color=ft.Colors.GREY_700,
                )
            )

        form_controls.append(
            ft.Container(content=ft.Column(controls=title_controls, spacing=5))
        )
        form_controls.append(ft.Divider())

        # Parameters
        param_controls = []
        for param in command.params:
            control = self._create_param_control(param)
            if control:
                param_controls.append(control)

        form_controls.append(
            ft.Container(content=ft.Column(controls=param_controls, spacing=10))
        )

        # Run button (if not auto-exec)
        if not command.ui_spec.is_auto_exec:
            run_button = ft.ElevatedButton(
                text="Run Command",
                icon=ft.Icons.PLAY_ARROW,
                on_click=lambda e: asyncio.create_task(self._run_command()),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            )
            form_controls.append(
                ft.Container(content=run_button, margin=ft.margin.only(top=20))
            )

        # Update form
        self.form_container.controls = form_controls
        if self.page:
            self.page.update()

        # Auto-execute
        if command.ui_spec.is_auto_exec:
            asyncio.create_task(self._run_command())

        # Emit selection event
        if self.ui_app:
            asyncio.create_task(
                self.ui_app.emit_event(CommandSelected(command_name=command.name))
            )

    def _create_param_control(self, param) -> Optional[ft.Control]:
        """Create Flet control for parameter.

        Args:
            param: ParamSpec instance

        Returns:
            Flet control or None
        """
        label = param.name
        if param.required:
            label += " *"

        hint_text = param.help_text or ""

        control: Optional[ft.Control] = None

        if param.param_type == ParamType.STRING:
            control = ft.TextField(
                label=label,
                hint_text=hint_text,
                value=str(param.default) if param.default is not None else "",
                width=400,
            )
        elif param.param_type == ParamType.INTEGER:
            control = ft.TextField(
                label=label,
                hint_text=hint_text,
                value=str(param.default) if param.default is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=400,
            )
        elif param.param_type == ParamType.FLOAT:
            control = ft.TextField(
                label=label,
                hint_text=hint_text,
                value=str(param.default) if param.default is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=400,
            )
        elif param.param_type == ParamType.BOOLEAN:
            control = ft.Checkbox(
                label=label,
                value=bool(param.default) if param.default is not None else False,
            )
        elif param.param_type == ParamType.ENUM:
            if param.enum_choices:
                control = ft.Dropdown(
                    label=label,
                    hint_text=hint_text,
                    options=[ft.dropdown.Option(c) for c in param.enum_choices],
                    value=str(param.default) if param.default is not None else None,
                    width=400,
                )

        if control:
            self.form_controls[param.name] = control

        return control

    async def _run_command(self) -> None:
        """Execute current command."""
        if not self.current_command:
            self._append_output("ERROR: No command selected.")
            return

        try:
            # Parse parameters
            kwargs = {}
            for param in self.current_command.params:
                control = self.form_controls.get(param.name)
                if not control:
                    continue

                value = self._extract_value(control, param)

                if param.required and value is None:
                    self._append_output(
                        f"ERROR: Required parameter '{param.name}' is missing."
                    )
                    return

                if value is not None:
                    kwargs[param.name] = value

            # Clear output
            if self.output_view:
                self.output_view.controls.clear()
                if self.page:
                    self.page.update()

            # Execute via UIApp if available
            if self.ui_app:
                await self.ui_app.run_command(**kwargs)
            else:
                # Fallback: execute directly
                result, error = await self.execute_command(
                    self.current_command.name, kwargs
                )
                if error:
                    self._append_output(f"ERROR: {error}")

        except Exception as e:
            self._append_output(f"ERROR: {e}")
            self._append_output(traceback.format_exc())

    def _extract_value(self, control: ft.Control, param) -> Any:
        """Extract value from Flet control."""
        if isinstance(control, ft.TextField):
            text = control.value or ""
            if not text:
                return param.default if param.default is not None else None

            if param.param_type == ParamType.INTEGER:
                return int(text)
            elif param.param_type == ParamType.FLOAT:
                return float(text)
            return text

        elif isinstance(control, ft.Checkbox):
            return control.value

        elif isinstance(control, ft.Dropdown):
            value = control.value
            if value is None:
                return param.default if param.default is not None else None

            if param.python_type and param.param_type == ParamType.ENUM:
                try:
                    return param.python_type(value)
                except Exception:
                    return value

            return value

        return None

    async def handle_event(self, event: Event) -> None:
        """Handle events from UIApp.

        Args:
            event: Event to handle
        """
        if isinstance(event, TextEmitted):
            self._append_output(event.text)
        elif isinstance(event, BlockEmitted):
            self._append_ui_block(event.block)
        elif isinstance(event, ContainerStarted):
            # Create container and push to stack
            if event.container_type == "row":
                container = ft.Row(controls=[])
            elif event.container_type == "column":
                container = ft.Column(controls=[])
            else:
                container = ft.Container()
            self.container_stack.append(container)
        elif isinstance(event, ContainerEnded):
            # Pop container and add to output
            if self.container_stack:
                container = self.container_stack.pop()
                self._append_control(container)
        elif isinstance(event, ErrorRaised):
            self._append_output(f"ERROR: {event.exception}")
            self._append_output(event.traceback)

    async def execute_command(
        self, command_name: str, params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception]]:
        """Execute command with stdout/stderr capture.

        Args:
            command_name: Command name
            params: Parameters

        Returns:
            Tuple of (result, exception)
        """
        # Find command
        command_spec: Optional[CommandSpec] = None
        for cmd in self.app_spec.commands:
            if cmd.name == command_name:
                command_spec = cmd
                break

        if not command_spec:
            return None, ValueError(f"Command not found: {command_name}")

        result = None
        exception = None

        # Check if long-running
        is_long = command_spec.ui_spec.is_long

        if is_long:
            # Real-time streaming
            stdout_writer = _RealTimeWriter(self._append_output)
            stderr_writer = _RealTimeWriter(
                lambda t: self._append_output(f"[ERR] {t}")
            )

            try:
                with redirect_stdout(stdout_writer), redirect_stderr(stderr_writer):
                    result = command_spec.callback(**params)
                    if asyncio.iscoroutine(result):
                        result = await result

                stdout_writer.flush()
                stderr_writer.flush()

            except Exception as e:
                exception = e
                stdout_writer.flush()
                stderr_writer.flush()
                self._append_output(f"ERROR: {e}")
                self._append_output(traceback.format_exc())

        else:
            # Buffered output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    result = command_spec.callback(**params)
                    if asyncio.iscoroutine(result):
                        result = await result

                stdout_text = stdout_capture.getvalue()
                stderr_text = stderr_capture.getvalue()

                if stdout_text:
                    self._append_output(stdout_text)
                if stderr_text:
                    self._append_output(f"[STDERR]\n{stderr_text}")

            except Exception as e:
                exception = e
                self._append_output(f"ERROR: {e}")
                self._append_output(traceback.format_exc())

        return result, exception

    def _append_output(self, text: str) -> None:
        """Append text to output view."""
        if self.output_view:
            lines = text.rstrip('\n').split('\n') if text else []
            for line in lines:
                self.output_view.controls.append(
                    ft.Text(
                        line,
                        selectable=True,
                        font_family="Courier New",
                        size=12,
                    )
                )
            if self.page:
                self.page.update()

    def _append_control(self, control: ft.Control) -> None:
        """Append Flet control to output."""
        if self.output_view:
            self.output_view.controls.append(control)
            if self.page:
                self.page.update()

    def _append_ui_block(self, block: Any) -> None:
        """Append UI block to output."""
        # If we have an active container, add to it
        if self.container_stack:
            container = self.container_stack[-1]
            if hasattr(container, 'controls'):
                flet_component = block.render_flet()
                container.controls.append(flet_component)
        else:
            # Add directly to output
            if self.output_view:
                flet_component = block.render_flet()
                self.output_view.controls.append(flet_component)
                if self.page:
                    self.page.update()


def create_flet_app(app_spec: AppSpec):
    """Create Flet app function from AppSpec.

    Args:
        app_spec: Application specification

    Returns:
        Flet main function
    """
    runner = GUIRunner(app_spec)

    def main(page: ft.Page):
        runner.build(page)

    return main
