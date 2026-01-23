import ast
import pytest
from typing import Dict, List, Set

from devbase.commands.audit import extract_commands_from_source

def test_extract_decorated_command():
    code = """
import typer

app = typer.Typer()

@app.command()
def my_cmd(
    name: str,
    force: bool = typer.Option(False, "--force", "-f"),
    dry_run: bool = typer.Option(False, "--dry-run")
):
    pass
    """
    commands = extract_commands_from_source(code)
    assert "my_cmd" in commands
    flags = commands["my_cmd"]
    assert "--force" in flags
    assert "--dry-run" in flags
    assert "-f" in flags

def test_extract_annotated_command():
    code = """
from typing import Annotated
import typer

@app.command()
def annotated_cmd(
    force: Annotated[bool, typer.Option("--force")] = False,
    verbose: Annotated[bool, typer.Option("--verbose")] = False
):
    pass
    """
    commands = extract_commands_from_source(code)
    assert "annotated_cmd" in commands
    flags = commands["annotated_cmd"]
    assert "--force" in flags
    assert "--verbose" in flags

def test_extract_named_decorated_command():
    code = """
@app.command("custom-name")
def implementation(
    verbose: bool = typer.Option(False, "--verbose")
):
    pass
    """
    commands = extract_commands_from_source(code)
    assert "custom-name" in commands
    assert "implementation" not in commands # Should prefer the name
    assert "--verbose" in commands["custom-name"]

def test_extract_mounted_command():
    # Test for app.command(name="debug")(debug_cmd) pattern
    code = """
app.command(name="debug")(debug_cmd)
    """
    commands = extract_commands_from_source(code)
    assert "debug" in commands

def test_ignore_helper_functions():
    code = """
def helper(x: int):
    pass
    """
    commands = extract_commands_from_source(code)
    assert not commands

def test_extract_argument_should_be_ignored_if_only_flags_wanted():
    code = """
@app.command()
def process(
    path: Path = typer.Argument(..., help="The path"),
    recursive: bool = typer.Option(False, "--recursive")
):
    pass
    """
    commands = extract_commands_from_source(code)
    assert "process" in commands
    assert "--recursive" in commands["process"]
