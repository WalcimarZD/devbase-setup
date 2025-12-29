"""
Debug Command: Check system health and integrity
================================================
Runs sanity checks, smoke tests, and unit tests to diagnose system health.
"""
import io
import shutil
import sys
import tempfile
import importlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated
from typer.testing import CliRunner

console = Console()
runner = CliRunner()


class DebugReport:
    """Manages the generation of the debug report (Terminal and Markdown)."""

    def __init__(self, root: Path):
        self.root = root
        self.timestamp = datetime.now()
        self.sanity_checks: List[Dict[str, Any]] = []
        self.smoke_tests: List[Dict[str, Any]] = []
        self.unit_tests: Dict[str, Any] = {}
        self.logs: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Add a log entry."""
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}"
        self.logs.append(entry)
        if level == "ERROR":
            console.print(f"[red]{message}[/red]")
        elif level == "WARNING":
            console.print(f"[yellow]{message}[/yellow]")

    def add_sanity_result(self, command: str, status: str, error: Optional[str] = None):
        self.sanity_checks.append({
            "command": command,
            "status": status,
            "error": error
        })

    def add_smoke_result(self, test_name: str, status: str, checks: List[str], error: Optional[str] = None):
        self.smoke_tests.append({
            "name": test_name,
            "status": status,
            "checks": checks,
            "error": error
        })

    def set_unit_test_result(self, exit_code: int, output: str):
        self.unit_tests = {
            "exit_code": exit_code,
            "output": output,
            "status": "PASSED" if exit_code == 0 else "FAILED"
        }

    def print_terminal_summary(self):
        """Print visual summary to terminal."""
        console.print()
        console.print(Panel.fit(
            f"[bold]DevBase Debug Report[/bold]\n"
            f"Timestamp: {self.timestamp}",
            border_style="blue"
        ))

        # Sanity Checks
        table = Table(title="1. Command Sanity Checks (Load & Help)", show_lines=True)
        table.add_column("Command Group", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        for check in self.sanity_checks:
            status_style = "[green]OK[/green]" if check["status"] == "PASSED" else "[red]FAIL[/red]"
            details = check["error"] if check["error"] else "-"
            table.add_row(check["command"], status_style, details)

        console.print(table)
        console.print()

        # Smoke Tests
        table_smoke = Table(title="2. Functional Smoke Tests (Sandbox)", show_lines=True)
        table_smoke.add_column("Test Case", style="cyan")
        table_smoke.add_column("Status", justify="center")
        table_smoke.add_column("Physical Checks")

        for test in self.smoke_tests:
            status_style = "[green]PASSED[/green]" if test["status"] == "PASSED" else "[red]FAILED[/red]"
            checks_formatted = "\n".join([f"• {c}" for c in test["checks"]])
            if test["error"]:
                checks_formatted += f"\n[bold red]Error:[/bold red] {test['error']}"
            table_smoke.add_row(test["name"], status_style, checks_formatted)

        console.print(table_smoke)
        console.print()

        # Unit Tests
        ut_status = "[green]PASSED[/green]" if self.unit_tests.get("status") == "PASSED" else "[red]FAILED[/red]"
        console.print(Panel(
            f"Exit Code: {self.unit_tests.get('exit_code')}\n"
            f"Status: {ut_status}\n\n"
            "[dim](See detailed report for full output)[/dim]",
            title="3. Unit Tests (pytest)",
            border_style="green" if self.unit_tests.get("status") == "PASSED" else "red"
        ))

    def save_markdown_report(self):
        """Save detailed report to debug_report.md."""
        report_path = self.root / "debug_report.md"

        md = f"# DevBase Debug Report\n\n"
        md += f"**Date:** {self.timestamp}\n"
        md += f"**Workspace:** {self.root}\n\n"

        md += "## 1. Sanity Checks\n\n"
        md += "| Command Group | Status | Details |\n"
        md += "|---|---|---|\n"
        for check in self.sanity_checks:
            md += f"| `{check['command']}` | **{check['status']}** | {check['error'] or '-'} |\n"

        md += "\n## 2. Smoke Tests (Sandbox Execution)\n\n"
        for test in self.smoke_tests:
            status_icon = "✅" if test["status"] == "PASSED" else "❌"
            md += f"### {status_icon} {test['name']}\n\n"
            md += "**Physical Verification:**\n"
            for check in test["checks"]:
                md += f"- {check}\n"
            if test["error"]:
                md += f"\n**Error:**\n```\n{test['error']}\n```\n"

        md += "\n## 3. Unit Tests Output\n\n"
        md += f"**Status:** {self.unit_tests.get('status')} (Exit Code: {self.unit_tests.get('exit_code')})\n\n"

        # Sanitize output (remove color codes if possible, though strict stripping is complex without deps)
        # For now, wrap in code block
        output = self.unit_tests.get("output", "No output captured.")
        # Simple removal of ANSI codes (rudimentary)
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', output)

        md += "```text\n"
        md += clean_output
        md += "\n```\n"

        md += "\n## 4. Execution Log\n\n"
        md += "```log\n"
        for log in self.logs:
            md += f"{log}\n"
        md += "```\n"

        report_path.write_text(md, encoding="utf-8")
        console.print(f"\n[green]Detailed report saved to:[/green] [cyan]{report_path}[/cyan]")


def run_sanity_checks(report: DebugReport):
    """Verify that command groups load and display help."""
    # Import inside function to avoid circular dependency
    from devbase.main import app as main_app

    # List of expected command groups based on main.py
    groups = ["core", "dev", "nav", "ops", "quick", "pkm", "study", "analytics", "ai"]

    report.log("Starting Sanity Checks...")

    for group in groups:
        try:
            # We use CliRunner to invoke "devbase <group> --help"
            # We explicitly pass the root to avoid "no workspace detected" errors
            result = runner.invoke(main_app, ["--root", str(report.root), group, "--help"])

            if result.exit_code == 0:
                report.add_sanity_result(f"devbase {group}", "PASSED")
            else:
                report.add_sanity_result(f"devbase {group}", "FAILED", error=f"Exit code {result.exit_code}")
        except Exception as e:
             report.add_sanity_result(f"devbase {group}", "FAILED", error=str(e))


def run_smoke_tests(report: DebugReport):
    """Run functional tests in a sandbox environment."""
    # Import inside function to avoid circular dependency
    from devbase.main import app as main_app

    report.log("Starting Smoke Tests...")

    with tempfile.TemporaryDirectory() as temp_dir:
        sandbox_root = Path(temp_dir)
        report.log(f"Created sandbox at {sandbox_root}")

        # === Test 1: Core Setup ===
        try:
            report.log("Running 'core setup' in sandbox...")
            # Note: We need to pass --root to override the context detection
            result = runner.invoke(main_app, ["--root", str(sandbox_root), "core", "setup", "--no-interactive", "--force"])

            checks = []
            failed_checks = []

            # Physical verification
            expected_files = [
                "00-09_SYSTEM",
                "20-29_CODE",
                ".gitignore",
                ".editorconfig",
                ".devbase_state.json"
            ]

            for f in expected_files:
                path = sandbox_root / f
                if path.exists():
                    checks.append(f"Found: {f}")
                else:
                    failed_checks.append(f"Missing: {f}")

            if result.exit_code != 0:
                report.add_smoke_result("core setup", "FAILED", checks, error=f"Command failed (Exit: {result.exit_code})\nOutput: {result.stdout}")
            elif failed_checks:
                error_msg = "SILENT FAILURE: Command succeeded but files are missing.\n" + "\n".join(failed_checks)
                report.add_smoke_result("core setup", "FAILED", checks, error=error_msg)
            else:
                report.add_smoke_result("core setup", "PASSED", checks)

        except Exception as e:
            report.add_smoke_result("core setup", "CRITICAL", [], error=str(e))

        # === Test 2: Dev New ===
        try:
            report.log("Running 'dev new' in sandbox...")

            # Setup: Create a dummy template in the sandbox so 'dev new' can find it
            # The command looks in 20-29_CODE/__template-{name}
            template_name = "clean-arch"
            template_dir = sandbox_root / "20-29_CODE" / f"__template-{template_name}"
            template_dir.mkdir(parents=True, exist_ok=True)
            (template_dir / "README.md.template").write_text("# {{ project_name }}\n\nDescription: {{ description }}", encoding="utf-8")

            project_name = "test-smoke-project"
            # We disable setup to avoid lengthy network calls (pip install, etc) for a smoke test unless requested
            # The requirement said "simular fluxos críticos". Installing deps might be too slow for a debug command?
            # User said: "Verificar se a pasta do projeto surgiu ... e se contém arquivos de template."
            # So --no-setup is appropriate to test file generation speed.

            result = runner.invoke(main_app, [
                "--root", str(sandbox_root),
                "dev", "new", project_name,
                "--template", template_name,
                "--no-interactive",
                "--no-setup" # Skip git init/pip install for speed
            ])

            checks = []
            failed_checks = []

            project_path = sandbox_root / "20-29_CODE" / "21_monorepo_apps" / project_name

            if project_path.exists():
                checks.append(f"Project folder created: {project_name}")
                if (project_path / "README.md").exists():
                    checks.append("Template file found: README.md")
                else:
                    failed_checks.append("Missing template file: README.md")
            else:
                failed_checks.append(f"Missing project folder: {project_path}")

            if result.exit_code != 0:
                # Capture exception info if available
                error_details = f"Output: {result.stdout}"
                if result.exc_info:
                    error_details += f"\nException: {result.exc_info[1]}"

                report.add_smoke_result("dev new", "FAILED", checks, error=f"Command failed (Exit: {result.exit_code})\n{error_details}")
            elif failed_checks:
                error_msg = "SILENT FAILURE: Command succeeded but files are missing.\n" + "\n".join(failed_checks)
                report.add_smoke_result("dev new", "FAILED", checks, error=error_msg)
            else:
                report.add_smoke_result("dev new", "PASSED", checks)

        except Exception as e:
            report.add_smoke_result("dev new", "CRITICAL", [], error=str(e))

        # === Test 3: Ops Backup ===
        try:
            report.log("Running 'ops backup' in sandbox...")

            # Create a dummy file to backup
            (sandbox_root / "dummy_data.txt").write_text("important data")

            result = runner.invoke(main_app, [
                "--root", str(sandbox_root),
                "ops", "backup"
            ])

            checks = []
            failed_checks = []

            backup_dir = sandbox_root / "30-39_OPERATIONS" / "31_backups" / "local"

            # Find any backup folder created
            backups = list(backup_dir.glob("devbase_backup_*")) if backup_dir.exists() else []

            if backups:
                checks.append(f"Backup created: {backups[0].name}")
                if (backups[0] / "dummy_data.txt").exists():
                    checks.append("Content verified inside backup")
                else:
                    failed_checks.append("Backup content missing (dummy_data.txt)")
            else:
                failed_checks.append(f"No backup folder found in {backup_dir}")

            if result.exit_code != 0:
                report.add_smoke_result("ops backup", "FAILED", checks, error=f"Command failed (Exit: {result.exit_code})\nOutput: {result.stdout}")
            elif failed_checks:
                error_msg = "SILENT FAILURE: Command succeeded but backup artifact missing.\n" + "\n".join(failed_checks)
                report.add_smoke_result("ops backup", "FAILED", checks, error=error_msg)
            else:
                report.add_smoke_result("ops backup", "PASSED", checks)

        except Exception as e:
            report.add_smoke_result("ops backup", "CRITICAL", [], error=str(e))


def run_unit_tests(report: DebugReport):
    """Run pytest and capture output."""
    report.log("Running Unit Tests (pytest)...")

    try:
        import pytest
    except ImportError:
        report.log("pytest not found. Skipping unit tests.", level="WARNING")
        report.set_unit_test_result(-1, "pytest not installed. Install dev dependencies to run unit tests.")
        return

    # Capture stdout/stderr
    capture = io.StringIO()
    # We use a context manager to redirect stdout/stderr
    # Note: pytest.main() prints to file descriptor 1/2 directly often, so we use capsys inside pytest usually.
    # But here we are invoking pytest from outside.

    # To properly capture pytest output when running programmatically:
    # We can use the 'capsys' plugin if we were in a test, but we are the runner.
    # Simplest way is to run it as a subprocess or try to redirect sys.stdout

    from contextlib import redirect_stdout, redirect_stderr

    try:
        # We need to ensure we run tests on the actual source code
        # Assuming we are in the repo root or src is in path

        with redirect_stdout(capture), redirect_stderr(capture):
            # Run pytest with -v for verbosity and colored output disabled for easier log parsing (optional)
            # We invoke it on "tests/" directory
            exit_code = pytest.main(["tests", "-v", "--color=no"])

        report.set_unit_test_result(exit_code, capture.getvalue())

    except Exception as e:
        report.set_unit_test_result(-1, str(e))


def debug_cmd(
    ctx: typer.Context,
) -> None:
    """
    🐞 System Debug & Diagnostics.

    Executes a comprehensive health check including:
    1. Sanity Check: Verifies all command groups load correctly
    2. Smoke Tests: Runs critical flows (setup, new project, backup) in a sandbox
    3. Unit Tests: Runs the full pytest suite

    Generates a visual report and a detailed 'debug_report.md' file.
    """
    root: Path = ctx.obj["root"]
    report = DebugReport(root)

    console.print(Panel.fit("[bold yellow]Running System Diagnostics...[/bold yellow]\nThis may take a minute.", border_style="yellow"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # Step 1: Sanity Checks
        task1 = progress.add_task("Verifying command groups...", total=None)
        run_sanity_checks(report)
        progress.update(task1, completed=True, description="[green]✓[/green] Sanity Checks Complete")

        # Step 2: Smoke Tests
        task2 = progress.add_task("Running functional smoke tests (Sandbox)...", total=None)
        run_smoke_tests(report)
        progress.update(task2, completed=True, description="[green]✓[/green] Smoke Tests Complete")

        # Step 3: Unit Tests
        task3 = progress.add_task("Running unit tests...", total=None)
        run_unit_tests(report)
        progress.update(task3, completed=True, description="[green]✓[/green] Unit Tests Complete")

    # Final Report
    report.print_terminal_summary()
    report.save_markdown_report()
