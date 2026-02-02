import ast
import pytest
from devbase.commands.audit import CLIParser

CODE_SAMPLE = """
import typer
app = typer.Typer()

@app.command("my-command")
def my_command(
    flag: bool = typer.Option(False, "--my-flag"),
    other_flag: str = typer.Option("default", "-o", "--other")
):
    pass

@app.command("another")
def another_command():
    pass
"""

def test_cli_parser_extracts_commands_and_flags():
    parser = CLIParser()
    parser.visit(ast.parse(CODE_SAMPLE))

    assert "my-command" in parser.commands
    assert "another" in parser.commands

    assert "--my-flag" in parser.flags
    assert "-o" in parser.flags
    assert "--other" in parser.flags
