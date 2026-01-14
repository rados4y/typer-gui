"""GUI runner using Flet for desktop applications."""

import asyncio
import contextvars
import inspect
import io
import threading
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from typing import Any, Optional

import flet as ft

from .base import Runner
from .gui_context import GUIRunnerCtx
from ..specs import AppSpec, CommandSpec, ParamType
from ..ui_blocks import Text, set_current_runner


@dataclass
class ReactiveContext:
    """Context for reactive rendering into a container.

    When a reactive renderer executes, it operates within a ReactiveContext
    that captures all ui() calls into a dedicated container.
    """
    container: Any  # UiBlock Column container
    flet_control: ft.Column  # Flet control for the container
    component_id: int  # Unique ID for this reactive region


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


class _CommandView:
    """Container for per-command UI components."""
    def __init__(self):
        self.form_controls: dict[str, ft.Control] = {}
        self.form_container: Optional[ft.Column] = None
        self.output_view: Optional[ft.ListView] = None
        self.main_container: Optional[ft.Column] = None
        self.component_refs: dict[int, ft.Control] = {}
        self.text_buffer: list[str] = []  # Buffer for accumulating consecutive text
        self.current_text_control: Optional[ft.Text] = None  # For live text updates (long commands)
        self.run_button: Optional[ft.ElevatedButton] = None  # Reference to run button


class GUIRunner(Runner):
    """Runner for Flet-based GUI applications."""

    def __init__(self, app_spec: AppSpec, ui: Optional[Any] = None):
        super().__init__(app_spec)
        self.page: Optional[ft.Page] = None
        self.current_command: Optional[CommandSpec] = None
        self.channel = "gui"
        self.ui = ui

        # New architecture: GUIRunnerCtx instance (will be initialized when page is ready)
        self.ctx: Optional[GUIRunnerCtx] = None

        # Per-command views (lazy initialized)
        # Key: (tab_name, command_name) where tab_name is None for root commands
        self.command_views: dict[tuple[Optional[str], str], _CommandView] = {}

        # Container for all command views
        self.views_container: Optional[ft.Column] = None

        # UI components
        self.command_list: Optional[ft.ListView] = None

        # Tab management (for sub-applications)
        self.current_tab: Optional[str] = None  # None = root/main, otherwise sub-app name
        self.tab_buttons: dict[str, ft.TextButton] = {}  # Tab name -> button
        self.tab_content_controls: dict[str, ft.Container] = {}  # Tab name -> content control
        self.tab_contents: dict[Optional[str], tuple[ft.ListView, ft.Column]] = {}  # (command_list, views_container) per tab
        self._tab_content_container: Optional[ft.Container] = None  # Container holding current tab content

        # Component tracking for updates (global registry)
        self._control_registry: dict[Any, ft.Control] = {}

        # Context-aware command tracking for threads and async tasks
        # This ensures background threads/tasks output to their original command view
        self._thread_local = threading.local()  # For background threads
        self._async_context: contextvars.ContextVar[Optional[CommandSpec]] = \
            contextvars.ContextVar('command_context', default=None)  # For async tasks

        # Reactive state management
        # Maps component ID to Flet control for re-rendering
        self._reactive_components: dict[int, ft.Control] = {}

        # Reactive rendering context stack
        # Supports nested reactive contexts (though rare)
        self._reactive_contexts: list[ReactiveContext] = []

    def start(self) -> None:
        """Start the Flet GUI application."""
        # Flet app will be started via ft.app() externally
        pass

    def _get_current_view(self) -> Optional[_CommandView]:
        """Get the current command's view.

        Checks context-specific command (thread-local or async context) first,
        then falls back to global current_command. This ensures background
        threads and async tasks output to their original command view.

        Returns:
            CommandView if current command exists and has a view, None otherwise
        """
        # Priority 1: Check async context (for Mode 2: async commands)
        async_cmd = self._async_context.get()
        if async_cmd:
            key = (self.current_tab, async_cmd.name)
            if key in self.command_views:
                return self.command_views[key]

        # Priority 2: Check thread-local storage (for Mode 3: long-running threads)
        thread_cmd = getattr(self._thread_local, 'current_command', None)
        if thread_cmd:
            key = (self.current_tab, thread_cmd.name)
            if key in self.command_views:
                return self.command_views[key]

        # Priority 3: Fallback to global current_command (for Mode 1: default sync, UI interactions)
        if self.current_command:
            key = (self.current_tab, self.current_command.name)
            if key in self.command_views:
                return self.command_views[key]

        return None

    def add_to_output(self, control: ft.Control, component: Any = None) -> None:
        """Add Flet control to output view.

        Args:
            control: Flet control to add
            component: Optional UiBlock component reference for tracking
        """
        view = self._get_current_view()
        if view and view.output_view:
            # Flush text buffer before adding a non-text component
            self._flush_text_buffer(view)

            # Clear current text control (for long commands)
            # Next print will start a new text block
            view.current_text_control = None

            view.output_view.controls.append(control)
            if component:
                view.component_refs[id(component)] = control
                # If component is reactive, track it globally
                if hasattr(component, '_reactive_id'):
                    self._reactive_components[component._reactive_id] = control
            if self.page:
                # Thread-safe update for Flet 0.80+
                self._safe_page_update()

    def register_control(self, component: Any, control: ft.Control) -> None:
        """Register a control for later access.

        Args:
            component: UiBlock component
            control: Flet control
        """
        self._control_registry[component] = control

    def refresh(self) -> None:
        """Refresh the page."""
        if self.page:
            self.page.update()

    def _safe_page_update(self) -> None:
        """Thread-safe page update for Flet 0.80+.

        In Flet 0.80+, page.update() must be called from the main thread.
        This method uses page.run_task() to ensure thread-safe updates.
        """
        if not self.page:
            return

        # Use page.run_task for thread-safe async execution
        async def do_update():
            self.page.update()

        try:
            self.page.run_task(do_update)
        except Exception:
            # Fallback to direct update if run_task fails
            # (e.g., if already in main thread)
            self.page.update()

    @property
    def current_reactive_context(self) -> Optional[ReactiveContext]:
        """Get current reactive context, if any.

        Returns:
            Current ReactiveContext or None if not in reactive mode
        """
        return self._reactive_contexts[-1] if self._reactive_contexts else None

    def is_reactive_mode(self) -> bool:
        """Check if currently in reactive rendering mode.

        Returns:
            True if rendering into a reactive container
        """
        return len(self._reactive_contexts) > 0

    def execute_in_reactive_mode(self, container, renderer):
        """Execute renderer with all ui() calls going to container.

        Creates a reactive context and executes the renderer function.
        All ui() calls made during execution are captured into the container.

        Supports two patterns:
        1. Renderer calls ui() internally (ui pattern)
        2. Renderer returns a UiBlock (return pattern)

        Args:
            container: UiBlock Column to capture components
            renderer: Function to execute (reactive renderer)

        Returns:
            Tuple of (container, flet_control) - both the UiBlock and Flet control
        """
        # Create Flet control for container
        flet_control = ft.Column(controls=[], spacing=10)

        # Create reactive context
        context = ReactiveContext(
            container=container,
            flet_control=flet_control,
            component_id=id(container)
        )

        # Push context onto stack
        self._reactive_contexts.append(context)

        try:
            # Execute renderer - all ui() calls go to container
            result = renderer()

            # If renderer returns something, convert and add it to container
            if result is not None:
                from ..ui_blocks import to_component
                component = to_component(result)
                self.add_to_reactive_container(component)
        finally:
            # Pop context
            self._reactive_contexts.pop()

        return container, flet_control

    def add_to_reactive_container(self, component):
        """Add component to current reactive container.

        Called by ui() when in reactive mode. Adds the component
        to the container instead of the main output.

        Args:
            component: UiBlock component to add

        Raises:
            RuntimeError: If not in reactive mode
        """
        context = self.current_reactive_context
        if not context:
            raise RuntimeError("Not in reactive mode")

        # Build component using ctx (new architecture)
        if self.ctx:
            from ..ui_blocks import Text
            root = Text("")  # Dummy root
            control = self.ctx.build_child(root, component)
            if control:
                # Add to Flet control
                context.flet_control.controls.append(control)

                # Add to UiBlock container (for tracking)
                if isinstance(component, UiBlock):
                    context.container.children.append(component)

    def update_reactive_container(self, container, renderer):
        """Update reactive container by re-executing renderer.

        This clears the container and re-fills it with fresh components.
        Only the container is refreshed, not the whole page.

        Supports two patterns:
        1. Renderer calls ui() internally (ui pattern)
        2. Renderer returns a UiBlock (return pattern)

        Args:
            container: UiBlock Column container to update
            renderer: Function to re-execute
        """
        # Find the Flet control for this container
        flet_control = self._reactive_components.get(id(container))
        if not flet_control:
            return

        # Clear the container
        flet_control.controls.clear()
        container.children.clear()

        # Create new reactive context
        context = ReactiveContext(
            container=container,
            flet_control=flet_control,
            component_id=id(container)
        )

        # Push context
        self._reactive_contexts.append(context)

        try:
            # Re-execute renderer - fills container with new components
            result = renderer()

            # If renderer returns something, convert and add it to container
            if result is not None:
                from ..ui_blocks import to_component
                component = to_component(result)
                self.add_to_reactive_container(component)
        finally:
            # Pop context
            self._reactive_contexts.pop()

        # Refresh ONLY the container, not whole page
        if self.page:
            flet_control.update()

    def update_reactive_component(self, component_id: int, new_component) -> None:
        """Update a reactive component with its new render.

        Called by State when a value changes to re-render dependent components.

        Args:
            component_id: Unique ID of the component to update
            new_component: New component instance from re-executing renderer
        """
        view = self._get_current_view()
        if not view or not view.output_view:
            return

        # Find the old control in the output view
        old_control = self._reactive_components.get(component_id)
        if not old_control or not self.ctx:
            # No old control or no context
            return

        # Find the index of the old control in the output view
        try:
            index = view.output_view.controls.index(old_control)
        except ValueError:
            # Control not found in view
            return

        # Build new component using ctx (new architecture)
        from ..ui_blocks import Text
        root = Text("")  # Dummy root
        new_control = self.ctx.build_child(root, new_component)
        if not new_control:
            return

        # Replace the old control with the new one
        view.output_view.controls[index] = new_control

        # Update the reactive components mapping
        self._reactive_components[component_id] = new_control

        # Refresh the page
        if self.page:
            self.page.update()

    def build(self, page: ft.Page) -> None:
        """Build the Flet GUI.

        Args:
            page: Flet page instance
        """
        self.page = page

        # Initialize new architecture context
        self.ctx = GUIRunnerCtx(page)
        self.ctx.runner = self  # Store reference back to runner for callbacks
        GUIRunnerCtx._instance = self.ctx  # Set as global instance

        page.title = self.app_spec.title or "Typer GUI"
        page.window_width = 1000
        page.window_height = 700
        page.padding = 0
        page.bgcolor = "#FAFAFA"  # Light gray background

        # Create main layout
        content = self._create_content()

        # Only add separate header if we don't have sub-apps (they have integrated header)
        has_sub_apps = len(self.app_spec.sub_apps) > 0

        if has_sub_apps:
            page.add(content)
        else:
            header = self._create_header()
            page.add(
                ft.Column(
                    controls=[header, content],
                    expand=True,
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                )
            )

        # Call init callback if registered
        if self.ui and hasattr(self.ui, '_init_callback') and self.ui._init_callback:
            try:
                self.ui._init_callback()
            except Exception as e:
                print(f"Error in init callback: {e}")
                import traceback
                traceback.print_exc()

        # Select first command
        # Priority: main commands > sub-app commands
        first_command = None
        if self.app_spec.commands:
            # If we have main commands, select first main command
            first_command = self.app_spec.commands[0]
        elif self.app_spec.sub_apps and self.app_spec.sub_apps[0].commands:
            # Otherwise, select first command in first sub-app
            first_command = self.app_spec.sub_apps[0].commands[0]

        if first_command:
            # Schedule async task to select first command
            async def select_first():
                await self._select_command(first_command)

            page.run_task(select_first)

    def _create_header(self) -> ft.Container:
        """Create header with title and description."""
        controls = []

        if self.app_spec.title:
            controls.append(
                ft.Text(
                    self.app_spec.title,
                    size=28,
                    weight=ft.FontWeight.W_700,
                    color="#1F2937",
                )
            )

        if self.app_spec.description:
            controls.append(
                ft.Text(
                    self.app_spec.description,
                    size=15,
                    color="#6B7280",
                )
            )

        if not controls:
            return ft.Container()

        return ft.Container(
            content=ft.Column(controls=controls, spacing=6),
            padding=ft.Padding(left=28, right=28, top=12, bottom=12),
            bgcolor="#FFFFFF",
            border=ft.Border(bottom=ft.BorderSide(1, "#E5E7EB")),
        )

    def _create_content(self) -> ft.Control:
        """Create main content area.

        If app has sub-applications, creates tabbed layout.
        Otherwise, creates flat layout (backward compatible).
        """
        # Check if we have sub-applications
        has_sub_apps = len(self.app_spec.sub_apps) > 0

        if has_sub_apps:
            return self._create_tabbed_layout()
        else:
            return self._create_flat_layout()

    def _create_flat_layout(self) -> ft.Row:
        """Create flat layout (no tabs) - backward compatible."""
        # Command list for root commands
        self.current_tab = None
        self.command_list = self._create_command_list_for_commands(self.app_spec.commands)

        # Container that will hold all command views (lazy initialized)
        self.views_container = ft.Column(
            controls=[],
            expand=True,
            spacing=0,
        )

        # Store for current tab
        self.tab_contents[None] = (self.command_list, self.views_container)

        # Layout
        left_panel = ft.Container(
            content=self.command_list,
            width=220,
            bgcolor="#F9FAFB",
            padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            border=ft.Border(right=ft.BorderSide(1, "#E5E7EB")),
        )

        right_panel = ft.Container(
            content=self.views_container,
            expand=True,
            padding=0,
            bgcolor="#FFFFFF",
        )

        return ft.Row(
            controls=[left_panel, right_panel],
            expand=True,
            spacing=0,
        )

    def _create_tabbed_layout(self) -> ft.Column:
        """Create tabbed layout for sub-applications.

        If app has both main commands and sub-apps, creates a main tab first.
        """

        # Check if we have main/root commands
        has_main_commands = len(self.app_spec.commands) > 0

        # Determine initial tab
        if has_main_commands:
            # Start with main tab if we have main commands
            self.current_tab = self.app_spec.main_label
        elif self.app_spec.sub_apps:
            # Otherwise start with first sub-app
            self.current_tab = self.app_spec.sub_apps[0].name
        else:
            self.current_tab = None

        # Create tab buttons and content
        tab_buttons = []

        # Add main commands tab first if we have main commands
        if has_main_commands:
            async def handle_main_tab_click(e):
                await self._switch_to_tab(self.app_spec.main_label)

            is_active = (self.app_spec.main_label == self.current_tab)

            main_btn = ft.Container(
                content=ft.Text(
                    self.app_spec.main_label,
                    size=14,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                    color="#2563EB" if is_active else "#6B7280",
                ),
                padding=ft.Padding(left=20, right=20, top=12, bottom=12),
                border=ft.Border(
                    bottom=ft.BorderSide(3, "#2563EB" if is_active else "transparent")
                ),
                on_click=handle_main_tab_click,
                ink=True,
                ink_color="#EFF6FF",
            )
            tab_buttons.append(main_btn)
            self.tab_buttons[self.app_spec.main_label] = main_btn

            # Create content for main tab
            main_content = self._create_tab_content(self.app_spec.main_label, self.app_spec.commands)
            self.tab_content_controls[self.app_spec.main_label] = main_content

        # Add sub-app tabs
        for sub_app in self.app_spec.sub_apps:
            async def handle_tab_click(e, tab_name=sub_app.name):
                await self._switch_to_tab(tab_name)

            is_active = (sub_app.name == self.current_tab)

            btn = ft.Container(
                content=ft.Text(
                    sub_app.name,
                    size=14,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                    color="#2563EB" if is_active else "#6B7280",
                ),
                padding=ft.Padding(left=20, right=20, top=12, bottom=12),
                border=ft.Border(
                    bottom=ft.BorderSide(3, "#2563EB" if is_active else "transparent")
                ),
                on_click=handle_tab_click,
                ink=True,
                ink_color="#EFF6FF",
            )
            tab_buttons.append(btn)
            self.tab_buttons[sub_app.name] = btn

            # Create content for this tab
            tab_content = self._create_tab_content(sub_app.name, sub_app.commands)
            self.tab_content_controls[sub_app.name] = tab_content

        # Create combined header with title/description on left and tabs in same row on right
        title_desc_column = ft.Column(
            controls=[
                ft.Text(
                    self.app_spec.title,
                    size=24,
                    weight=ft.FontWeight.W_700,
                    color="#1F2937",
                ),
                ft.Text(
                    self.app_spec.description,
                    size=13,
                    color="#6B7280",
                ),
            ] if self.app_spec.description else [
                ft.Text(
                    self.app_spec.title,
                    size=24,
                    weight=ft.FontWeight.W_700,
                    color="#1F2937",
                ),
            ],
            spacing=4,
        )

        tabs_row = ft.Row(
            controls=tab_buttons,
            spacing=4,
        )

        # Combined header bar with title/description and tabs in same row
        combined_header = ft.Container(
            content=ft.Row(
                controls=[title_desc_column, tabs_row],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.END,
                spacing=40,
            ),
            bgcolor="#FFFFFF",
            padding=ft.Padding(left=28, right=28, top=16, bottom=0),
            border=ft.Border(bottom=ft.BorderSide(1, "#E5E7EB")),
        )

        # Content container showing current tab
        tab_content_container = ft.Container(
            content=self.tab_content_controls.get(self.current_tab),
            expand=True
        )

        # Store reference to container for switching
        self._tab_content_container = tab_content_container

        return ft.Column(
            controls=[combined_header, tab_content_container],
            expand=True,
            spacing=0,
        )

    def _create_tab_content(self, tab_name: str, commands: tuple) -> ft.Container:
        """Create content for a single tab (command list + views area)."""
        # Create command list for this tab
        command_list = self._create_command_list_for_commands(commands)

        # Create views container for this tab
        views_container = ft.Column(
            controls=[],
            expand=True,
            spacing=0,
        )

        # Store for this tab
        self.tab_contents[tab_name] = (command_list, views_container)

        # Layout: left panel (commands) + right panel (views)
        left_panel = ft.Container(
            content=command_list,
            width=220,
            bgcolor="#F9FAFB",
            padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            border=ft.Border(right=ft.BorderSide(1, "#E5E7EB")),
        )

        right_panel = ft.Container(
            content=views_container,
            expand=True,
            padding=0,
            bgcolor="#FFFFFF",
        )

        return ft.Container(
            content=ft.Row(
                controls=[left_panel, right_panel],
                expand=True,
                spacing=0,
            ),
            expand=True,
        )

    async def _switch_to_tab(self, tab_name: str):
        """Switch to a different tab."""
        if tab_name == self.current_tab:
            return  # Already on this tab

        # Update current tab
        old_tab = self.current_tab
        self.current_tab = tab_name

        # Update tab button styles
        for name, btn_container in self.tab_buttons.items():
            is_active = (name == tab_name)
            # Update the Text inside the Container
            text_control = btn_container.content
            text_control.weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400
            text_control.color = "#2563EB" if is_active else "#6B7280"
            # Update the Container border
            btn_container.border = ft.Border(
                bottom=ft.BorderSide(3, "#2563EB" if is_active else "transparent")
            )

        # Switch content
        if self._tab_content_container and tab_name in self.tab_content_controls:
            self._tab_content_container.content = self.tab_content_controls[tab_name]

        # Update page
        if self.page:
            self.page.update()

        # Find commands for this tab and select first one
        if tab_name == self.app_spec.main_label:
            # Switching to main tab - select first main command
            if self.app_spec.commands:
                await self._select_command(self.app_spec.commands[0])
        else:
            # Switching to sub-app tab - find sub-app and select first command
            sub_app = next((sa for sa in self.app_spec.sub_apps if sa.name == tab_name), None)
            if sub_app and sub_app.commands:
                await self._select_command(sub_app.commands[0])

    def _create_command_list_for_commands(self, commands: tuple) -> ft.ListView:
        """Create command list view for specific commands."""
        if not commands:
            return ft.ListView(
                controls=[ft.Text("No commands", color=ft.Colors.GREY_600)]
            )

        buttons = []
        for cmd in commands:
            # Use an async lambda for on_click handlers
            async def handle_click(e, command=cmd):
                await self._select_command(command)

            if cmd.ui_spec.button:
                btn = ft.ElevatedButton(
                    cmd.name,
                    on_click=handle_click,
                    bgcolor="#2563EB",
                    color="#FFFFFF",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                        shadow_color="#2563EB40",
                        elevation={"": 1, "hovered": 2},
                    ),
                )
            else:
                btn = ft.TextButton(
                    cmd.name,
                    on_click=handle_click,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.Padding(left=16, right=16, top=10, bottom=10),
                        color={"": "#374151", "hovered": "#2563EB"},
                        bgcolor={"": "transparent", "hovered": "#F3F4F6"},
                        overlay_color={"hovered": "#F3F4F610"},
                    ),
                )
            buttons.append(btn)

        return ft.ListView(controls=buttons, spacing=8, expand=True)


    async def _select_command(self, command: CommandSpec) -> None:
        """Select and display a command.

        Args:
            command: Command to select
        """
        self.current_command = command

        # Invoke on_select callback if provided
        if command.ui_spec.on_select:
            try:
                command.ui_spec.on_select()
            except Exception as e:
                print(f"Warning: on_select callback failed: {e}")

        # Handle modal commands differently
        if command.ui_spec.modal:
            await self._show_modal_command(command)
            return

        # Use tab-aware key
        key = (self.current_tab, command.name)

        # Lazy initialize command view if it doesn't exist
        if key not in self.command_views:
            await self._create_command_view(command)

        # Get views container for current tab
        if self.current_tab in self.tab_contents:
            _, views_container = self.tab_contents[self.current_tab]
        else:
            # Fallback to main views_container
            views_container = self.views_container

        # Hide all command views in current tab
        for (tab, cmd_name), view in self.command_views.items():
            if tab == self.current_tab and view.main_container:
                view.main_container.visible = False

        # Show selected command view
        selected_view = self.command_views[key]
        if selected_view.main_container:
            selected_view.main_container.visible = True

        # Clear output for non-long-running tasks on selection
        # Long-running tasks keep their output for review
        if not command.ui_spec.threaded and selected_view.output_view:
            if selected_view.output_view.controls:
                selected_view.output_view.controls.clear()

        if self.page:
            self.page.update()

        # Auto-execute only if this is the first time selecting this command
        # (Check if output is empty to avoid re-running on switch back)
        if command.ui_spec.auto and selected_view.output_view:
            if not selected_view.output_view.controls:
                await self._run_command()

    async def _show_modal_command(self, command: CommandSpec) -> None:
        """Show command in a modal dialog.

        Args:
            command: Command to show in modal
        """
        if not self.page:
            return

        # Build parameter form
        form_controls = []
        form_control_refs = {}

        # Title and description (controlled by header flag)
        if command.ui_spec.header:
            form_controls.append(
                ft.Text(
                    command.name.upper(),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                )
            )

            # Description
            if command.help_text:
                form_controls.append(
                    ft.Text(command.help_text, size=14, color=ft.Colors.GREY_700)
                )

            form_controls.append(ft.Divider())

        # Parameter inputs
        for param in command.params:
            control = self._create_param_control(param)
            form_control_refs[param.name] = control
            form_controls.append(control)

        # Output area (initially empty)
        output_view = ft.ListView(
            controls=[],
            auto_scroll=command.ui_spec.auto_scroll,
            expand=True,
        )

        # Close button (always enabled - allow closing without execution)
        close_button = ft.TextButton(
            "Close",
            disabled=False,
        )

        # Submit button
        async def on_submit(e):
            # Parse parameters
            kwargs = {}
            for param in command.params:
                control = form_control_refs.get(param.name)
                if not control:
                    continue

                value = self._extract_value(control, param)

                if param.required and value is None:
                    output_view.controls.append(
                        ft.Text(
                            f"ERROR: Required parameter '{param.name}' is missing.",
                            color=ft.Colors.RED,
                        )
                    )
                    self.page.update()
                    return

                if value is not None:
                    kwargs[param.name] = value

            # Clear previous output
            output_view.controls.clear()

            # Execute command
            try:
                # Create temporary command view for modal output
                saved_view = self.command_views.get(command.name)

                # Create a minimal view that redirects output to modal
                modal_view = _CommandView()
                modal_view.output_view = output_view
                self.command_views[command.name] = modal_view

                result, error, output = await self.execute_command(command.name, kwargs)

                # Restore previous view (or remove if there wasn't one)
                if saved_view:
                    self.command_views[command.name] = saved_view
                else:
                    del self.command_views[command.name]

                if error:
                    output_view.controls.append(
                        ft.Text(f"ERROR: {error}", color=ft.Colors.RED)
                    )
            except Exception as e:
                output_view.controls.append(
                    ft.Text(f"ERROR: {e}", color=ft.Colors.RED)
                )
            finally:
                # Update display
                self.page.update()

        # Submit button (hide if auto-executing)
        submit_button = ft.ElevatedButton(
            command.ui_spec.submit_name,
            on_click=on_submit,
            visible=not command.ui_spec.auto,
        )

        # Build content controls
        content_controls = []

        # Add form controls (if any)
        if form_controls:
            content_controls.extend(form_controls)
            content_controls.append(ft.Divider())

        # Add output section
        content_controls.append(ft.Text("Output:", weight=ft.FontWeight.BOLD))
        content_controls.append(
            ft.Container(
                content=output_view,
                border=ft.Border.all(1, ft.Colors.GREY_400),
                border_radius=5,
                padding=10,
                expand=True,
            )
        )

        # Create dialog with increased height (80% of typical screen)
        dialog = ft.AlertDialog(
            title=ft.Text(f"{command.name}") if command.ui_spec.header else None,
            content=ft.Column(
                controls=content_controls,
                scroll=ft.ScrollMode.AUTO,
                width=700,
                height=700,
                expand=True,
            ),
            actions=[
                submit_button,
                close_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Close button handler
        def on_close(e):
            dialog.open = False
            self.page.update()

        close_button.on_click = on_close

        # Show dialog
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

        # Auto-execute if auto flag is set
        if command.ui_spec.auto:
            await on_submit(None)

    async def _create_command_view(self, command: CommandSpec) -> None:
        """Create UI view for a command (lazy initialization).

        Args:
            command: Command to create view for
        """
        view = _CommandView()

        # Build form
        form_controls = []

        # Title (only if header=True)
        if command.ui_spec.header:
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
            control = self._create_param_control(param, view)
            if control:
                param_controls.append(control)

        form_controls.append(
            ft.Container(content=ft.Column(controls=param_controls, spacing=10))
        )

        # Buttons row
        if not command.ui_spec.auto:
            async def handle_run(e):
                await self._run_command()

            run_button = ft.ElevatedButton(
                command.ui_spec.submit_name,
                icon=ft.Icons.PLAY_ARROW,
                on_click=handle_run,
                bgcolor="#2563EB",
                color="#FFFFFF",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.Padding(left=20, right=20, top=12, bottom=12),
                    shadow_color="#2563EB40",
                    elevation={"": 2, "hovered": 3},
                ),
            )

            # Store button reference for enabling/disabling during execution
            view.run_button = run_button

            buttons = [run_button]

            # Add Clear button for threaded tasks
            if command.ui_spec.threaded:
                async def handle_clear(e):
                    # Clear output only (no reexecution)
                    if view.output_view:
                        view.output_view.controls.clear()
                        # Clear current text control for long commands
                        view.current_text_control = None
                        if self.page:
                            self.page.update()

                clear_button = ft.OutlinedButton(
                    "Clear",
                    icon=ft.Icons.CLEAR_ALL,
                    on_click=handle_clear,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.Padding(left=20, right=20, top=12, bottom=12),
                        color={"": "#6B7280"},
                        side={"": ft.BorderSide(1, "#D1D5DB")},
                    ),
                )
                buttons.append(clear_button)

            form_controls.append(
                ft.Container(
                    content=ft.Row(buttons, spacing=10),
                    margin=ft.Margin(left=0, right=0, top=20, bottom=0)
                )
            )

        # Create form container
        view.form_container = ft.Column(
            controls=form_controls,
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
        )

        # Create output view
        # Set auto_scroll based on command's ui_spec
        view.output_view = ft.ListView(
            controls=[],
            auto_scroll=command.ui_spec.auto_scroll,
            expand=True,
            spacing=0,
        )

        # Determine padding - no padding for view commands without header or params
        has_header = command.ui_spec.header
        has_params = len(command.params) > 0
        has_buttons = not command.ui_spec.auto

        # Only add padding if there's actual form content (header, params, or buttons)
        form_padding = 20 if (has_header or has_params or has_buttons) else 0

        # Create main container for this command view
        view.main_container = ft.Column(
            controls=[
                ft.Container(
                    content=view.form_container,
                    padding=form_padding,
                ),
                ft.Container(
                    content=view.output_view,
                    padding=ft.Padding(left=20, right=20, bottom=20, top=0),
                    expand=True,
                ),
            ],
            expand=True,
            visible=False,  # Hidden by default
        )

        # Get views container for current tab
        if self.current_tab in self.tab_contents:
            _, views_container = self.tab_contents[self.current_tab]
        else:
            # Fallback to main views_container
            views_container = self.views_container

        # Add to views container
        if views_container:
            views_container.controls.append(view.main_container)

        # Store view with tab-aware key
        key = (self.current_tab, command.name)
        self.command_views[key] = view

    def _create_param_control(self, param, view: Optional[_CommandView] = None) -> Optional[ft.Control]:
        """Create Flet control for parameter.

        Args:
            param: ParamSpec instance
            view: CommandView to store the control in (optional, for modals)

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
                width=450,
                border_color="#D1D5DB",
                focused_border_color="#2563EB",
                bgcolor="#FFFFFF",
                text_size=14,
            )
        elif param.param_type == ParamType.INTEGER:
            control = ft.TextField(
                label=label,
                hint_text=hint_text,
                value=str(param.default) if param.default is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=450,
                border_color="#D1D5DB",
                focused_border_color="#2563EB",
                bgcolor="#FFFFFF",
                text_size=14,
            )
        elif param.param_type == ParamType.FLOAT:
            control = ft.TextField(
                label=label,
                hint_text=hint_text,
                value=str(param.default) if param.default is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=450,
                border_color="#D1D5DB",
                focused_border_color="#2563EB",
                bgcolor="#FFFFFF",
                text_size=14,
            )
        elif param.param_type == ParamType.BOOLEAN:
            control = ft.Checkbox(
                label=label,
                value=bool(param.default) if param.default is not None else False,
            )
        elif param.param_type == ParamType.ENUM:
            if param.enum_choices:
                # Get default value - for enums, use .value attribute
                default_value = None
                if param.default is not None:
                    default_value = param.default.value if hasattr(param.default, 'value') else str(param.default)

                control = ft.Dropdown(
                    label=label,
                    hint_text=hint_text,
                    options=[ft.dropdown.Option(c) for c in param.enum_choices],
                    value=default_value,
                    width=450,
                    border_color="#D1D5DB",
                    focused_border_color="#2563EB",
                    bgcolor="#FFFFFF",
                    text_size=14,
                )
        elif param.param_type == ParamType.ENUM_LIST:
            # Multiple checkboxes for list[Enum]
            if param.enum_choices:
                # Determine default selected values
                default_values = set()
                if param.default is not None and isinstance(param.default, list):
                    default_values = {
                        item.value if hasattr(item, 'value') else str(item)
                        for item in param.default
                    }

                # Create a checkbox for each enum value
                checkboxes = []
                for choice in param.enum_choices:
                    cb = ft.Checkbox(
                        label=str(choice),
                        value=(choice in default_values),
                        data=choice,  # Store the enum value
                    )
                    checkboxes.append(cb)

                # Wrap in Column with label and horizontal row of checkboxes
                control = ft.Column(
                    controls=[
                        ft.Text(label, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=checkboxes,
                            spacing=10,
                            wrap=True,  # Wrap to next line if too many
                        ),
                    ],
                    spacing=5,
                )

        elif param.param_type == ParamType.LIST:
            # Multiline text field for list input (one item per line)
            default_text = ""
            if param.default is not None and isinstance(param.default, list):
                default_text = "\n".join(str(item) for item in param.default)

            control = ft.TextField(
                label=label,
                hint_text=hint_text or "Enter one value per line",
                value=default_text,
                multiline=True,
                min_lines=3,
                max_lines=10,
                width=450,
                border_color="#D1D5DB",
                focused_border_color="#2563EB",
                bgcolor="#FFFFFF",
                text_size=14,
            )

        if control and view:
            view.form_controls[param.name] = control

        return control

    async def _run_command(self) -> None:
        """Execute current command."""
        if not self.current_command:
            # Display error immediately for early returns
            view = self._get_current_view()
            if view and view.output_view:
                self._append_to_live_text("ERROR: No command selected.")
            return

        view = self._get_current_view()
        if not view:
            # Can't display - no view available
            return

        # Disable run button during execution
        if view.run_button:
            view.run_button.disabled = True
            if self.page:
                self.page.update()

        # Check if command is threaded (will run in background)
        is_threaded = self.current_command and self.current_command.ui_spec.threaded

        try:
            # Parse parameters
            kwargs = {}
            for param in self.current_command.params:
                control = view.form_controls.get(param.name)
                if not control:
                    continue

                value = self._extract_value(control, param)

                if param.required and value is None:
                    # Display validation error immediately
                    self._append_to_live_text(
                        f"ERROR: Required parameter '{param.name}' is missing."
                    )
                    return

                if value is not None:
                    kwargs[param.name] = value

            # Clear output for this command
            if view.output_view:
                view.output_view.controls.clear()
                if self.page:
                    self.page.update()

            # Execute command
            result, error, output = await self.execute_command(self.current_command.name, kwargs)
            if error:
                # Display error immediately (though execute_command should have already shown it)
                self._append_to_live_text(f"ERROR: {error}")

        except Exception as e:
            # Display exception immediately
            self._append_to_live_text(f"ERROR: {e}")
            self._append_to_live_text(traceback.format_exc())

        finally:
            # Re-enable run button after execution
            # BUT: Don't re-enable for threaded commands - they handle it themselves when done
            if not is_threaded and view.run_button:
                view.run_button.disabled = False
                if self.page:
                    self.page.update()

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
            elif param.param_type == ParamType.LIST:
                # Split by newlines, filter out empty lines
                items = [line.strip() for line in text.split('\n') if line.strip()]
                # Convert items to the target type if specified
                if param.python_type:
                    if param.python_type is int:
                        return [int(item) for item in items]
                    elif param.python_type is float:
                        return [float(item) for item in items]
                return items
            return text

        elif isinstance(control, ft.Checkbox):
            return control.value

        elif isinstance(control, ft.Dropdown):
            value = control.value
            if value is None:
                return param.default if param.default is not None else None

            if param.python_type and param.param_type == ParamType.ENUM:
                try:
                    # Convert string value to enum member
                    # Use _value2member_map_ for efficient lookup
                    if hasattr(param.python_type, '_value2member_map_'):
                        return param.python_type._value2member_map_.get(value, value)
                    # Fallback: iterate through members
                    for member in param.python_type:
                        if member.value == value:
                            return member
                    return value
                except Exception:
                    return value

            return value

        elif isinstance(control, ft.Column):
            # Handle ENUM_LIST (Column with label + Row of checkboxes)
            if param.param_type == ParamType.ENUM_LIST:
                selected_values = []
                # Get the Row containing checkboxes (should be at index 1)
                if len(control.controls) > 1 and isinstance(control.controls[1], ft.Row):
                    checkbox_row = control.controls[1]
                    # Iterate through checkboxes in the row
                    for ctrl in checkbox_row.controls:
                        if isinstance(ctrl, ft.Checkbox) and ctrl.value:
                            # Get the enum value from data attribute
                            selected_values.append(ctrl.data)

                # Convert string values back to enum members if python_type is available
                if param.python_type and selected_values:
                    try:
                        enum_members = []
                        for val in selected_values:
                            # Use _value2member_map_ for efficient lookup
                            if hasattr(param.python_type, '_value2member_map_'):
                                member = param.python_type._value2member_map_.get(val)
                                if member:
                                    enum_members.append(member)
                            else:
                                # Fallback: iterate through members
                                for member in param.python_type:
                                    if member.value == val:
                                        enum_members.append(member)
                                        break
                        return enum_members
                    except Exception:
                        return selected_values

                return selected_values

        return None

    async def execute_command(
        self, command_name: str, params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception], str]:
        """Execute command with stdout/stderr capture.

        Three execution modes:
        1. Default (sync, no is_long): Buffered output, executes in main thread
        2. Async: Immediate updates, executes as async task
        3. is_long flag: Immediate updates, executes in background thread

        Args:
            command_name: Command name
            params: Parameters

        Returns:
            Tuple of (result, exception, output_text)
        """
        # Find command in correct tab/sub-app
        command_spec: Optional[CommandSpec] = None

        # Determine which commands to search based on current tab
        if self.current_tab is None:
            # Search in root commands
            commands_to_search = self.app_spec.commands
        else:
            # Search in sub-app commands
            sub_app = next(
                (sa for sa in self.app_spec.sub_apps if sa.name == self.current_tab),
                None
            )
            commands_to_search = sub_app.commands if sub_app else ()

        # Find the command by name
        for cmd in commands_to_search:
            if cmd.name == command_name:
                command_spec = cmd
                break

        if not command_spec:
            return None, ValueError(f"Command not found: {command_name}"), ""

        # Determine execution mode
        # Check if the callback has an original async function stored
        original_async = getattr(command_spec.callback, '_original_async_func', None)
        is_async = inspect.iscoroutinefunction(command_spec.callback) or original_async is not None
        is_threaded = command_spec.ui_spec.threaded

        if is_threaded:
            # Mode 3: Execute in background thread with immediate updates
            return self._execute_in_thread(command_spec, params)
        elif is_async:
            # Mode 2: Execute as async with immediate updates
            return await self._execute_async(command_spec, params)
        else:
            # Mode 1: Default sync execution with buffered output
            return self._execute_sync(command_spec, params)

    def _execute_sync(
        self, command_spec: CommandSpec, params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception], str]:
        """Mode 1: Execute synchronously with buffered output."""
        # Save current runner for nested execution support
        from ..ui_blocks import get_current_runner
        saved_runner = get_current_runner()

        # Set this runner as current so ui() works
        set_current_runner(self)

        # Set current command in Ui
        if self.ui:
            self.ui.current_command = command_spec

        # Set context as current instance
        from ..context import UIRunnerCtx
        UIRunnerCtx._current_instance = self.ctx

        # Create root component for build_child() hierarchy
        from ..ui_blocks import Column
        root = Column([])

        result = None
        exception = None
        output_lines = []  # Capture text output

        # Create real-time writer for print() statements
        # This displays print() output immediately while also capturing it
        def display_print_line(line: str):
            """Display and capture a line from print()."""
            from ..output import ui
            from ..ui_blocks import Print

            output_lines.append(line)
            # Use Print() UI block to handle text accumulation
            # print() is now equivalent to ui(tu.Print(...))
            ui(Print(line))

        stdout_writer = _RealTimeWriter(display_print_line)
        stderr_capture = io.StringIO()

        try:
            # Execute command with UI stack context
            with self.ctx.new_ui_stack() as ui_stack:
                # Conditionally redirect stdout based on print2ui flag
                if self.ui and self.ui.print2ui:
                    # Capture print() statements
                    with redirect_stdout(stdout_writer), redirect_stderr(stderr_capture):
                        result = command_spec.callback(**params)

                        # Flush any remaining buffered output
                        stdout_writer.flush()
                else:
                    # Don't capture print() - let it go to stdout directly
                    with redirect_stderr(stderr_capture):
                        result = command_spec.callback(**params)

                # If command returns a value, add it to stack
                if result is not None:
                    ui_stack.append(result)

            # Process UI stack - build and add each item to output
            for item in ui_stack:
                # Build control from item
                control = self.ctx.build_child(root, item)
                self.add_to_output(control)

                # Capture text representation for output (from original item)
                text_repr = self._component_to_text(item)
                if text_repr:
                    output_lines.append(text_repr)

            stderr_text = stderr_capture.getvalue()

            if stderr_text:
                stderr_msg = f"[STDERR]\n{stderr_text}"
                output_lines.append(stderr_msg)
                self._append_text(stderr_msg)

        except Exception as e:
            exception = e
            error_text = f"ERROR: {e}"
            output_lines.append(error_text)
            self._append_text(error_text)
            self._append_text(traceback.format_exc())

        # Restore previous runner
        set_current_runner(saved_runner)

        # Flush any remaining text in buffer
        view = self._get_current_view()
        self._flush_text_buffer(view)

        # Join all output lines
        output_text = '\n'.join(output_lines)

        return result, exception, output_text

    async def _execute_async(
        self, command_spec: CommandSpec, params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception], str]:
        """Mode 2: Execute async function with immediate updates."""
        result = None
        exception = None
        output_lines = []

        # Save current runner
        from ..ui_blocks import get_current_runner
        saved_runner = get_current_runner()
        set_current_runner(self)

        if self.ui:
            self.ui.current_command = command_spec

        # Set async context for this command
        # This ensures output goes to THIS command's view even if user switches commands
        token = self._async_context.set(command_spec)

        # Set context as current instance
        from ..context import UIRunnerCtx
        UIRunnerCtx._current_instance = self.ctx

        # Create root component for build_child() hierarchy
        from ..ui_blocks import Column
        root = Column([])

        try:
            # Execute async command with UI stack context
            with self.ctx.new_ui_stack() as ui_stack:
                # Register observer for real-time updates during async execution
                def on_append(item):
                    """Build and display item immediately."""
                    control = self.ctx.build_child(root, item)
                    self.add_to_output(control)
                    if self.page:
                        self.page.update()

                    # Also capture for text output
                    text_repr = self._component_to_text(item)
                    if text_repr:
                        output_lines.append(text_repr)

                ui_stack.register_observer(on_append)

                # Get the actual async function (may be wrapped)
                async_func = getattr(command_spec.callback, '_original_async_func', None)
                if async_func is None:
                    async_func = command_spec.callback

                # Execute async command and await it
                result = await async_func(**params)

                # If command returns a value, add it to stack
                # (This will trigger on_append immediately)
                if result is not None:
                    ui_stack.append(result)

        except Exception as e:
            exception = e
            error_text = f"ERROR: {e}"
            output_lines.append(error_text)
            # Display error immediately in async mode for consistency
            self._append_to_live_text(error_text)
            self._append_to_live_text(traceback.format_exc())

        finally:
            # Reset async context
            self._async_context.reset(token)

        # Restore runner
        set_current_runner(saved_runner)

        # Flush any remaining text in buffer
        view = self._get_current_view()
        self._flush_text_buffer(view)

        return result, exception, '\n'.join(output_lines)

    def _execute_in_thread(
        self, command_spec: CommandSpec, params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception], str]:
        """Mode 3: Execute in background thread with immediate updates."""
        result = None
        exception = None
        output_lines = []

        # Save current runner
        from ..ui_blocks import get_current_runner
        saved_runner = get_current_runner()

        def thread_target():
            nonlocal result, exception

            # Set runner in thread
            set_current_runner(self)

            # Set thread-local command context
            # This ensures output goes to THIS command's view even if user switches commands
            self._thread_local.current_command = command_spec

            if self.ui:
                self.ui.current_command = command_spec

            # Set context as current instance
            from ..context import UIRunnerCtx
            UIRunnerCtx._current_instance = self.ctx

            # Create root component for build_child() hierarchy
            from ..ui_blocks import Column
            root = Column([])

            # Real-time streaming with thread-safe page updates
            def append_with_update(text):
                output_lines.append(text)
                # Use live text updates for immediate display
                self._append_to_live_text(text)

            stdout_writer = _RealTimeWriter(append_with_update)
            stderr_writer = _RealTimeWriter(
                lambda t: self._append_to_live_text(f"[ERR] {t}")
            )

            try:
                # Execute command with UI stack context
                with self.ctx.new_ui_stack() as ui_stack:
                    # Register observer for real-time updates during thread execution
                    def on_append(item):
                        """Build and display item immediately (thread-safe)."""
                        control = self.ctx.build_child(root, item)
                        self.add_to_output(control)
                        # Note: add_to_output already calls _safe_page_update()

                        # Also capture for text output
                        text_repr = self._component_to_text(item)
                        if text_repr:
                            output_lines.append(text_repr)

                    ui_stack.register_observer(on_append)

                    # Conditionally redirect stdout based on print2ui flag
                    if self.ui and self.ui.print2ui:
                        # Capture print() statements
                        with redirect_stdout(stdout_writer), redirect_stderr(stderr_writer):
                            result = command_spec.callback(**params)

                        stdout_writer.flush()
                        stderr_writer.flush()
                    else:
                        # Don't capture print() - let it go to stdout directly
                        with redirect_stderr(stderr_writer):
                            result = command_spec.callback(**params)

                        stderr_writer.flush()

                    # If command returns a value, add it to stack
                    # (This will trigger on_append immediately)
                    if result is not None:
                        ui_stack.append(result)

            except Exception as e:
                exception = e
                stdout_writer.flush()
                stderr_writer.flush()
                error_text = f"ERROR: {e}"
                output_lines.append(error_text)
                # Use live text for immediate error display in threaded mode
                self._append_to_live_text(error_text)
                self._append_to_live_text(traceback.format_exc())

            finally:
                # Restore runner
                set_current_runner(saved_runner)

                # Clear live text control (command finished)
                view = self._get_current_view()
                if view:
                    view.current_text_control = None
                    self._flush_text_buffer(view)

                    # Re-enable run button now that thread is done
                    if view.run_button:
                        view.run_button.disabled = False
                        if self.page:
                            self._safe_page_update()

        # Start thread
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()

        # Note: We return immediately, thread continues in background
        # This allows UI to remain responsive

        return result, exception, '\n'.join(output_lines)

    def _execute_tab_content(self, content_callable, target_container: ft.Column) -> None:
        """Execute a callable for tab content and capture ui() calls into target container.

        Args:
            content_callable: Function that uses ui() to build content
            target_container: Flet Column to receive the output
        """
        # Get current view
        current_view = self._get_current_view()
        if not current_view:
            return

        # Save current output view and runner context
        saved_output_view = current_view.output_view
        from ..ui_blocks import get_current_runner
        saved_runner = get_current_runner()

        # Temporarily redirect output to the target container
        current_view.output_view = target_container

        # Ensure runner context is set for ui() calls
        set_current_runner(self)

        try:
            # Execute the callable - all ui() calls will go to target_container
            content_callable()

            # Update the UI
            if self.page:
                self.page.update()

        except Exception as e:
            # Show error in the tab
            import traceback
            error_text = ft.Text(
                f"Error rendering tab content: {str(e)}\n{traceback.format_exc()}",
                color=ft.Colors.RED,
            )
            target_container.controls.append(error_text)
            if self.page:
                self.page.update()

        finally:
            # Restore original output view and runner context
            current_view.output_view = saved_output_view
            set_current_runner(saved_runner)

    def _component_to_text(self, component) -> str:
        """Convert UI component to text representation.

        Delegates to the component's to_text() method, which reuses
        the component's show_cli() logic. This eliminates code duplication
        and maintains separation of concerns.

        Args:
            component: UiBlock component

        Returns:
            Text representation of the component
        """
        from ..ui_blocks import UiBlock

        if isinstance(component, UiBlock):
            return component.to_text()
        else:
            # For non-UiBlock objects (strings, etc.)
            return str(component)

    def _flush_text_buffer(self, view: Optional[_CommandView] = None) -> None:
        """Flush accumulated text buffer to a single ft.Text control.

        Args:
            view: CommandView to flush buffer for (uses current view if None)
        """
        if view is None:
            view = self._get_current_view()

        if not view or not view.output_view or not view.text_buffer:
            return

        # Join all accumulated text with newlines
        combined_text = '\n'.join(view.text_buffer)

        # Create single ft.Text control
        view.output_view.controls.append(
            ft.Text(
                combined_text,
                selectable=True,
                font_family="Courier New",
                size=12,
            )
        )

        # Clear buffer
        view.text_buffer.clear()

        if self.page:
            # Thread-safe update for Flet 0.80+
            self._safe_page_update()

    def _append_to_live_text(self, text: str) -> None:
        """Append text with immediate display for long-running commands.

        Creates a single ft.Text control on first call, then appends to it
        on subsequent calls. This provides real-time updates while keeping
        consecutive text selectable as one block.

        Args:
            text: Text to append
        """
        view = self._get_current_view()
        if not view or not view.output_view:
            return

        if not view.current_text_control:
            # First text - create new ft.Text control
            view.current_text_control = ft.Text(
                text,
                selectable=True,
                font_family="Courier New",
                size=12,
            )
            view.output_view.controls.append(view.current_text_control)
        else:
            # Subsequent text - append with newline
            view.current_text_control.value += f"\n{text}"

        if self.page:
            # Thread-safe update
            self._safe_page_update()

    def _append_text(self, text: str) -> None:
        """Append plain text to buffer for later flushing."""
        view = self._get_current_view()
        if view and view.output_view:
            # Split text into lines and add to buffer
            lines = text.rstrip('\n').split('\n') if text else []
            view.text_buffer.extend(lines)


def create_flet_app(app_spec: AppSpec, ui: Optional[Any] = None):
    """Create Flet app function from AppSpec.

    Args:
        app_spec: Application specification
        ui: Optional Ui instance

    Returns:
        Flet main function
    """
    runner = GUIRunner(app_spec, ui)

    # Set the runner in the UI instance
    if ui:
        ui.runner = runner

    def main(page: ft.Page):
        runner.build(page)

    return main
