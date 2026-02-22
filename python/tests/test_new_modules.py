"""
Tests for DevBase setup_hooks module.
"""

import sys
from pathlib import Path

# Add modules/python to sys.path for imports
SCRIPT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR / "modules" / "python"))

import pytest
from unittest.mock import MagicMock, patch
import tempfile
import shutil


class TestSetupHooks:
    """Test suite for setup_hooks module."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI instance."""
        ui = MagicMock()
        ui.print_header = MagicMock()
        ui.print_step = MagicMock()
        return ui

    @pytest.fixture
    def mock_fs(self, temp_workspace):
        """Create a mock FileSystem instance."""
        from filesystem import FileSystem
        return FileSystem(str(temp_workspace))

    def test_run_setup_hooks_creates_hooks_directory(self, temp_workspace, mock_fs, mock_ui):
        """Test that setup_hooks creates the hooks directory."""
        from setup_hooks import run_setup_hooks

        # Run setup
        run_setup_hooks(temp_workspace, mock_fs, mock_ui)

        # Verify hooks directory was created
        hooks_dir = temp_workspace / "00-09_SYSTEM" / "06_git_hooks"
        assert hooks_dir.exists()

    def test_run_setup_hooks_prints_header(self, temp_workspace, mock_fs, mock_ui):
        """Test that setup_hooks prints the correct header."""
        from setup_hooks import run_setup_hooks

        run_setup_hooks(temp_workspace, mock_fs, mock_ui)

        mock_ui.print_header.assert_called_with("6. Git Hooks")

    @patch('subprocess.run')
    def test_run_setup_hooks_configures_git(self, mock_run, temp_workspace, mock_fs, mock_ui):
        """Test that setup_hooks configures git core.hooksPath."""
        from setup_hooks import run_setup_hooks

        # Create a fake .git directory
        git_dir = temp_workspace / ".git"
        git_dir.mkdir(parents=True)

        mock_run.return_value = MagicMock(returncode=0)

        run_setup_hooks(temp_workspace, mock_fs, mock_ui)

        # Verify git config was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "core.hooksPath" in call_args[0][0]

    def test_verify_hooks_installation_returns_false_when_no_hooks_dir(self, temp_workspace, mock_ui):
        """Test verification fails when hooks directory doesn't exist."""
        from setup_hooks import verify_hooks_installation

        result = verify_hooks_installation(temp_workspace, mock_ui)

        assert result is False


class TestSetupTemplates:
    """Test suite for setup_templates module."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI instance."""
        ui = MagicMock()
        ui.print_header = MagicMock()
        ui.print_step = MagicMock()
        return ui

    @pytest.fixture
    def mock_fs(self, temp_workspace):
        """Create a mock FileSystem instance."""
        from filesystem import FileSystem
        return FileSystem(str(temp_workspace))

    def test_run_setup_templates_creates_template_directories(self, temp_workspace, mock_fs, mock_ui):
        """Test that setup_templates creates the template directories."""
        from setup_templates import run_setup_templates

        run_setup_templates(temp_workspace, mock_fs, mock_ui)

        # Verify template directories were created
        templates_dir = temp_workspace / "00-09_SYSTEM" / "05_templates"
        assert templates_dir.exists()
        assert (templates_dir / "patterns").exists()
        assert (templates_dir / "prompts").exists()
        assert (templates_dir / "ci").exists()

    def test_run_setup_templates_prints_header(self, temp_workspace, mock_fs, mock_ui):
        """Test that setup_templates prints the correct header."""
        from setup_templates import run_setup_templates

        run_setup_templates(temp_workspace, mock_fs, mock_ui)

        mock_ui.print_header.assert_called_with("5. Templates & Standards")

    def test_get_available_templates_returns_empty_when_no_templates(self, temp_workspace):
        """Test get_available_templates returns empty list when no templates exist."""
        from setup_templates import get_available_templates

        result = get_available_templates(temp_workspace)

        assert result == []

    def test_get_available_templates_lists_templates(self, temp_workspace):
        """Test get_available_templates lists templates correctly."""
        from setup_templates import get_available_templates

        # Create a template
        templates_dir = temp_workspace / "00-09_SYSTEM" / "05_templates" / "patterns"
        templates_dir.mkdir(parents=True)
        (templates_dir / "adr.md").write_text("# ADR Template")

        result = get_available_templates(temp_workspace)

        assert len(result) == 1
        assert result[0]["name"] == "adr.md"
        assert result[0]["category"] == "patterns"


class TestDetectLanguage:
    """Test suite for detect_language module."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_detect_node_project(self, temp_project):
        """Test detection of Node.js projects."""
        from detect_language import get_project_stack

        # Create package.json
        (temp_project / "package.json").write_text('{"name": "test"}')

        stack = get_project_stack(temp_project)

        assert stack["type"] == "node"
        assert stack["name"] == "Node.js"
        assert stack["package_manager"] == "npm"

    def test_detect_typescript_project(self, temp_project):
        """Test detection of TypeScript projects."""
        from detect_language import get_project_stack

        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "tsconfig.json").write_text('{}')

        stack = get_project_stack(temp_project)

        assert stack["type"] == "node"
        assert stack["name"] == "TypeScript"

    def test_detect_python_project(self, temp_project):
        """Test detection of Python projects."""
        from detect_language import get_project_stack

        (temp_project / "requirements.txt").write_text("flask==2.0.0")

        stack = get_project_stack(temp_project)

        assert stack["type"] == "python"
        assert stack["name"] == "Python"
        assert stack["package_manager"] == "pip"

    def test_detect_dotnet_project(self, temp_project):
        """Test detection of .NET projects."""
        from detect_language import get_project_stack

        (temp_project / "MyApp.csproj").write_text("<Project></Project>")

        stack = get_project_stack(temp_project)

        assert stack["type"] == "dotnet"
        assert stack["name"] == "C#"
        assert stack["package_manager"] == "nuget"

    def test_detect_go_project(self, temp_project):
        """Test detection of Go projects."""
        from detect_language import get_project_stack

        (temp_project / "go.mod").write_text("module example.com/mymodule")

        stack = get_project_stack(temp_project)

        assert stack["type"] == "go"
        assert stack["name"] == "Go"
        assert stack["package_manager"] == "go mod"

    def test_detect_rust_project(self, temp_project):
        """Test detection of Rust projects."""
        from detect_language import get_project_stack

        (temp_project / "Cargo.toml").write_text('[package]\nname = "test"')

        stack = get_project_stack(temp_project)

        assert stack["type"] == "rust"
        assert stack["name"] == "Rust"
        assert stack["package_manager"] == "cargo"

    def test_detect_pnpm_package_manager(self, temp_project):
        """Test detection of pnpm package manager."""
        from detect_language import get_project_stack

        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "pnpm-lock.yaml").write_text("")

        stack = get_project_stack(temp_project)

        assert stack["package_manager"] == "pnpm"

    def test_detect_yarn_package_manager(self, temp_project):
        """Test detection of yarn package manager."""
        from detect_language import get_project_stack

        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "yarn.lock").write_text("")

        stack = get_project_stack(temp_project)

        assert stack["package_manager"] == "yarn"

    def test_detect_poetry_package_manager(self, temp_project):
        """Test detection of poetry package manager."""
        from detect_language import get_project_stack

        (temp_project / "pyproject.toml").write_text("")
        (temp_project / "poetry.lock").write_text("")

        stack = get_project_stack(temp_project)

        assert stack["package_manager"] == "poetry"

    def test_returns_generic_for_unknown_project(self, temp_project):
        """Test that unknown projects return generic stack."""
        from detect_language import get_project_stack

        stack = get_project_stack(temp_project)

        assert stack["type"] == "generic"
        assert stack["name"] == "Unknown"

    def test_returns_generic_for_nonexistent_path(self):
        """Test that nonexistent paths return generic stack."""
        from detect_language import get_project_stack

        stack = get_project_stack(Path("/nonexistent/path"))

        assert stack["type"] == "generic"

    def test_detect_frameworks_nextjs(self, temp_project):
        """Test detection of Next.js framework."""
        from detect_language import get_project_stack, detect_frameworks

        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "next.config.js").write_text("")

        stack = get_project_stack(temp_project)
        frameworks = detect_frameworks(temp_project, stack)

        assert "Next.js" in frameworks

    def test_detect_frameworks_django(self, temp_project):
        """Test detection of Django framework."""
        from detect_language import get_project_stack, detect_frameworks

        (temp_project / "requirements.txt").write_text("django")
        (temp_project / "manage.py").write_text("")

        stack = get_project_stack(temp_project)
        frameworks = detect_frameworks(temp_project, stack)

        assert "Django" in frameworks
