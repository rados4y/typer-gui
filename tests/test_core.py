"""Unit tests for core reflection logic."""

from enum import Enum

import typer

from typer2ui.spec_builder import build_app_spec
from typer2ui.specs import ParamType


class TestColor(str, Enum):
    """Test enum for color choices."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def test_build_gui_model_with_simple_command():
    """Test building GUI model from a simple Typer app."""
    app = typer.Typer()

    @app.command()
    def greet(name: str):
        """Greet someone."""
        print(f"Hello {name}")

    gui_model = build_app_spec(app)

    assert len(gui_model.commands) == 1
    cmd = gui_model.commands[0]
    assert cmd.name == "greet"
    assert cmd.help_text == "Greet someone."
    assert len(cmd.params) == 1
    assert cmd.params[0].name == "name"
    assert cmd.params[0].param_type == ParamType.STRING


def test_build_gui_model_with_multiple_param_types():
    """Test building GUI model with various parameter types."""
    app = typer.Typer()

    @app.command()
    def test_command(
        text: str,
        number: int,
        decimal: float,
        flag: bool = False,
    ):
        """Test command with multiple types."""
        pass

    gui_model = build_app_spec(app)

    assert len(gui_model.commands) == 1
    cmd = gui_model.commands[0]
    assert len(cmd.params) == 4

    # Check parameter types
    param_dict = {p.name: p for p in cmd.params}

    assert param_dict["text"].param_type == ParamType.STRING
    assert param_dict["number"].param_type == ParamType.INTEGER
    assert param_dict["decimal"].param_type == ParamType.FLOAT
    assert param_dict["flag"].param_type == ParamType.BOOLEAN
    assert param_dict["flag"].default is False


def test_build_gui_model_with_enum():
    """Test building GUI model with enum parameter."""
    app = typer.Typer()

    @app.command()
    def paint(color: TestColor):
        """Paint with a color."""
        pass

    gui_model = build_app_spec(app)

    assert len(gui_model.commands) == 1
    cmd = gui_model.commands[0]
    assert len(cmd.params) == 1

    param = cmd.params[0]
    assert param.name == "color"
    assert param.param_type == ParamType.ENUM
    assert param.enum_choices == ("red", "green", "blue")


def test_build_gui_model_with_defaults():
    """Test that default values are captured correctly."""
    app = typer.Typer()

    @app.command()
    def test_defaults(
        name: str = "World",
        count: int = 5,
        enabled: bool = True,
    ):
        """Test command with defaults."""
        pass

    gui_model = build_app_spec(app)

    cmd = gui_model.commands[0]
    param_dict = {p.name: p for p in cmd.params}

    assert param_dict["name"].default == "World"
    assert param_dict["count"].default == 5
    assert param_dict["enabled"].default is True


def test_build_gui_model_with_multiple_commands():
    """Test building GUI model with multiple commands."""
    app = typer.Typer()

    @app.command()
    def greet(name: str):
        """Greet someone."""
        pass

    @app.command()
    def farewell(name: str):
        """Say goodbye."""
        pass

    gui_model = build_app_spec(app)

    assert len(gui_model.commands) == 2
    assert gui_model.commands[0].name == "greet"
    assert gui_model.commands[1].name == "farewell"


def test_build_gui_model_with_title_and_description():
    """Test that title and description are set correctly."""
    app = typer.Typer()

    @app.command()
    def test():
        """Test command."""
        pass

    gui_model = build_app_spec(
        app,
        title="My App",
        description="This is my app",
    )

    assert gui_model.title == "My App"
    assert gui_model.description == "This is my app"


def test_build_gui_model_with_no_commands():
    """Test building GUI model from an app with no commands."""
    app = typer.Typer()
    gui_model = build_app_spec(app)

    assert len(gui_model.commands) == 0


def test_build_gui_model_required_vs_optional():
    """Test that required vs optional parameters are identified correctly."""
    app = typer.Typer()

    @app.command()
    def test_command(
        required_param: str,
        optional_param: str = "default",
    ):
        """Test required vs optional."""
        pass

    gui_model = build_app_spec(app)
    cmd = gui_model.commands[0]
    param_dict = {p.name: p for p in cmd.params}

    assert param_dict["required_param"].required is True
    assert param_dict["optional_param"].required is False
