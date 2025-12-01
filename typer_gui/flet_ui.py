"""Flet-based GUI construction and event handling."""

import io
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Optional

import flet as ft

from .types import GuiApp, GuiCommand, GuiParam, ParamType, Markdown
from .ui_blocks import UiBlock, UiContext, set_context


class _RealTimeWriter(io.StringIO):
    """Custom writer that outputs to GUI in real-time for long-running commands."""

    def __init__(self, append_callback):
        super().__init__()
        self.append_callback = append_callback
        self.buffer = ""

    def write(self, text):
        if text:
            # Accumulate text in buffer
            self.buffer += text
            # If we have newlines, flush those lines
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                self.append_callback(line)
        return len(text)

    def flush(self):
        # Flush any remaining buffered text
        if self.buffer:
            self.append_callback(self.buffer)
            self.buffer = ""
        super().flush()


class TyperGUI:
    """Main GUI application class for Typer-GUI."""

    def __init__(self, gui_app: GuiApp):
        """Initialize the GUI with a GuiApp model."""
        self.gui_app = gui_app
        self.current_command: Optional[GuiCommand] = None
        self.form_controls: dict[str, ft.Control] = {}

        # UI components
        self.command_list: Optional[ft.ListView] = None
        self.form_container: Optional[ft.Column] = None
        self.output_view: Optional[ft.ListView] = None
        self.page: Optional[ft.Page] = None

    def build(self, page: ft.Page) -> None:
        """Build and display the GUI."""
        self.page = page
        page.title = self.gui_app.title or "Typer GUI"
        page.window_width = 1000
        page.window_height = 700
        page.padding = 0

        # Create the main layout
        header = self._create_header()
        content = self._create_content()

        page.add(
            ft.Column(
                controls=[header, content],
                expand=True,
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

        # Select the first command by default
        if self.gui_app.commands:
            self.select_command(self.gui_app.commands[0])

    def _create_header(self) -> ft.Container:
        """Create the header with title and description."""
        controls = []

        if self.gui_app.title:
            controls.append(
                ft.Text(
                    self.gui_app.title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                )
            )

        if self.gui_app.description:
            controls.append(
                ft.Text(
                    self.gui_app.description,
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
        """Create the main content area with command list and form."""
        # Left panel: Command list
        self.command_list = self._create_command_list()

        # Right panel: Form container
        self.form_container = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=12,
        )

        # Bottom panel: Output console
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
        """Create the list of commands."""
        if not self.gui_app.commands:
            return ft.ListView(
                controls=[ft.Text("No commands available", color=ft.Colors.GREY_600)],
            )

        command_buttons = []
        for cmd in self.gui_app.commands:
            # Create button based on gui_options.is_button
            if cmd.gui_options.is_button:
                # Elevated button for highlighted commands
                btn = ft.ElevatedButton(
                    text=cmd.name,
                    on_click=lambda e, command=cmd: self.select_command(command),
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                    ),
                )
            else:
                # Text button for regular commands
                btn = ft.TextButton(
                    text=cmd.name,
                    on_click=lambda e, command=cmd: self.select_command(command),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=5),
                    ),
                )
            command_buttons.append(btn)

        return ft.ListView(
            controls=command_buttons,
            spacing=5,
            expand=True,
        )

    def select_command(self, command: GuiCommand) -> None:
        """Update the form when a command is selected."""
        self.current_command = command
        self.form_controls.clear()

        # Clear output when switching commands
        if self.output_view:
            self.output_view.controls.clear()

        # Build form for the selected command
        form_controls = []

        # Command title and help
        form_controls.append(
            ft.Text(
                command.name.upper(),
                size=20,
                weight=ft.FontWeight.BOLD,
            )
        )

        if command.help_text:
            form_controls.append(
                ft.Text(
                    command.help_text,
                    size=14,
                    color=ft.Colors.GREY_700,
                )
            )

        form_controls.append(ft.Divider())

        # Create controls for each parameter
        for param in command.params:
            control = self._create_param_control(param)
            if control:
                form_controls.append(control)

        # Add Run button only if not auto-exec
        if not command.gui_options.is_auto_exec:
            run_button = ft.ElevatedButton(
                text="Run Command",
                icon=ft.Icons.PLAY_ARROW,
                on_click=lambda e: self.run_command(),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            )
            form_controls.append(
                ft.Container(content=run_button, margin=ft.margin.only(top=20))
            )

        # Update the form container
        self.form_container.controls = form_controls
        if self.page:
            self.page.update()

        # Auto-execute if configured
        if command.gui_options.is_auto_exec:
            self.run_command()

    def _create_param_control(self, param: GuiParam) -> Optional[ft.Control]:
        """Create a Flet control for a parameter."""
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
                    options=[
                        ft.dropdown.Option(choice) for choice in param.enum_choices
                    ],
                    value=str(param.default) if param.default is not None else None,
                    width=400,
                )

        elif param.param_type == ParamType.UNSUPPORTED:
            control = ft.TextField(
                label=label,
                hint_text=f"Unsupported type: {param.python_type}. Enter as string.",
                value=str(param.default) if param.default is not None else "",
                disabled=False,
                width=400,
            )

        if control:
            self.form_controls[param.name] = control
            return control

        return None

    def run_command(self) -> None:
        """Execute the selected command with form values."""
        if not self.current_command:
            self._append_output("ERROR: No command selected.")
            return

        try:
            # Parse form values
            kwargs = {}
            for param in self.current_command.params:
                control = self.form_controls.get(param.name)
                if not control:
                    continue

                value = self._extract_value_from_control(control, param)

                # Validate required parameters
                if param.required and value is None:
                    self._append_output(
                        f"ERROR: Required parameter '{param.name}' is missing."
                    )
                    return

                if value is not None:
                    kwargs[param.name] = value

            # Clear previous output
            if self.output_view:
                self.output_view.controls.clear()

            # Check if this is a long-running command
            is_long_running = self.current_command.gui_options.is_long

            if is_long_running:
                # Use real-time streaming for long-running commands
                stdout_writer = _RealTimeWriter(self._append_output)
                stderr_writer = _RealTimeWriter(
                    lambda text: self._append_output(f"[ERR] {text}")
                )

                try:
                    # Set up UI context for this command execution
                    context = UiContext(
                        mode="gui",
                        page=self.page,
                        output_view=self.output_view,
                        gui_app=self
                    )
                    set_context(context)

                    with redirect_stdout(stdout_writer), redirect_stderr(stderr_writer):
                        result = self.current_command.callback(**kwargs)

                    # Flush any remaining buffered output
                    stdout_writer.flush()
                    stderr_writer.flush()

                except Exception as e:
                    stdout_writer.flush()
                    stderr_writer.flush()
                    self._append_output("")
                    self._append_output(f"ERROR: {type(e).__name__}: {e}")
                    self._append_output("")
                    self._append_output("Traceback:")
                    self._append_output(traceback.format_exc())
                    return
                finally:
                    # Clear context after execution
                    set_context(None)

                # Handle result for long-running commands
                if result is not None:
                    if self.current_command.gui_options.is_markdown:
                        self._append_markdown(str(result))
                    elif isinstance(result, Markdown):
                        # Backward compatibility with Markdown class
                        self._append_markdown(result.content)
                    else:
                        self._append_output(f"Result: {result}")

            else:
                # Buffer output for regular commands
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()

                try:
                    # Set up UI context for this command execution
                    context = UiContext(
                        mode="gui",
                        page=self.page,
                        output_view=self.output_view,
                        gui_app=self
                    )
                    set_context(context)

                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        result = self.current_command.callback(**kwargs)

                    # Display captured output
                    stdout_text = stdout_capture.getvalue()
                    stderr_text = stderr_capture.getvalue()

                    if stdout_text:
                        self._append_output(stdout_text)

                    if stderr_text:
                        self._append_output("")
                        self._append_output("[STDERR]")
                        self._append_output(stderr_text)

                    if result is not None:
                        if self.current_command.gui_options.is_markdown:
                            self._append_markdown(str(result))
                        elif isinstance(result, Markdown):
                            # Backward compatibility with Markdown class
                            self._append_markdown(result.content)
                        else:
                            self._append_output(f"Result: {result}")

                except Exception as e:
                    stderr_text = stderr_capture.getvalue()
                    if stderr_text:
                        self._append_output("")
                        self._append_output("[STDERR]")
                        self._append_output(stderr_text)

                    self._append_output("")
                    self._append_output(f"ERROR: {type(e).__name__}: {e}")
                    self._append_output("")
                    self._append_output("Traceback:")
                    self._append_output(traceback.format_exc())
                finally:
                    # Clear context after execution
                    set_context(None)

        except Exception as e:
            self._append_output("")
            self._append_output(f"ERROR parsing parameters: {type(e).__name__}: {e}")
            self._append_output(traceback.format_exc())

    def _extract_value_from_control(self, control: ft.Control, param: GuiParam) -> Any:
        """Extract and parse the value from a Flet control."""
        if isinstance(control, ft.TextField):
            text_value = control.value or ""

            if not text_value:
                return param.default if param.default is not None else None

            # Parse based on type
            if param.param_type == ParamType.INTEGER:
                try:
                    return int(text_value)
                except ValueError:
                    raise ValueError(
                        f"Invalid integer value for '{param.name}': {text_value}"
                    )

            elif param.param_type == ParamType.FLOAT:
                try:
                    return float(text_value)
                except ValueError:
                    raise ValueError(
                        f"Invalid float value for '{param.name}': {text_value}"
                    )

            return text_value

        elif isinstance(control, ft.Checkbox):
            return control.value

        elif isinstance(control, ft.Dropdown):
            selected_value = control.value
            if selected_value is None:
                return param.default if param.default is not None else None

            # Convert back to enum if needed
            if param.python_type and param.param_type == ParamType.ENUM:
                try:
                    return param.python_type(selected_value)
                except Exception:
                    return selected_value

            return selected_value

        return None

    def _append_output(self, text: str) -> None:
        """Append text to the output console."""
        if self.output_view:
            # Split text by newlines and add each line as a Text widget
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

    def _append_markdown(self, content: str) -> None:
        """Append markdown formatted content to the output console."""
        if self.output_view:
            self.output_view.controls.append(
                ft.Markdown(
                    value=content,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    on_tap_link=lambda e: self.page.launch_url(e.data) if self.page else None,
                )
            )
            if self.page:
                self.page.update()

    def _append_ui_block(self, block: UiBlock) -> None:
        """Append a UI block to the output console."""
        if self.output_view:
            # Render the block using its Flet representation
            flet_component = block.render_flet()
            self.output_view.controls.append(flet_component)
            if self.page:
                self.page.update()


def create_flet_app(gui_app: GuiApp):
    """Create a Flet app function from a GuiApp model."""

    def main(page: ft.Page):
        app = TyperGUI(gui_app)
        app.build(page)

    return main
