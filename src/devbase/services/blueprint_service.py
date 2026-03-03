"""
Blueprint Service
==================
Generates AI-powered project blueprints using Clean Architecture principles.

Dependencies are injected so the service is testable in isolation (DIP).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from devbase.ai.interface import LLMProvider

logger = logging.getLogger(__name__)


class BlueprintSecurityError(Exception):
    """Raised when a generated file path would escape the target directory."""
    pass


@dataclass
class BlueprintFile:
    """A single file in the generated blueprint."""

    path: str
    content: str


@dataclass
class Blueprint:
    """Generated project blueprint."""

    project_name: str
    files: list[BlueprintFile] = field(default_factory=list)


_SCAFFOLD_PROMPT = """\
Generate a project file structure for: "{description}".
Follow Clean Architecture principles (Domain, Use Cases, Interfaces, Infrastructure).
Return ONLY a valid JSON object with this exact schema:
{{
  "project_name": "suggested-kebab-name",
  "files": [
    {{"path": "relative/path/to/file.ext", "content": "Minimal content/stub code..."}}
  ]
}}
Do not include markdown blocks or extra text.
"""


class BlueprintService:
    """Generates project blueprints via LLM and writes them to disk.

    Args:
        root: Workspace root path.
        provider: LLM provider (resolved lazily if omitted).
    """

    def __init__(self, root: Path, provider: Optional[LLMProvider] = None) -> None:
        self.root = root
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        """Lazily resolve the LLM provider via the factory."""
        if self._provider is None:
            from devbase.ai.factory import AIProviderFactory
            self._provider = AIProviderFactory.get_provider(self.root)
        return self._provider

    def generate(self, description: str) -> Blueprint:
        """Generate a project blueprint from a natural-language description.

        Args:
            description: Human description of the project (e.g. "FastAPI with Redis").

        Returns:
            ``Blueprint`` with project name and file list.

        Raises:
            ProviderError: If the LLM call fails.
            ValueError: If the LLM response is not valid JSON.
        """
        prompt = _SCAFFOLD_PROMPT.format(description=description)
        raw_json = self.provider.complete(
            prompt, temperature=0.2, max_tokens=2048
        ).strip()

        # Strip potential markdown fencing from LLM response.
        if raw_json.startswith("```"):
            raw_json = raw_json.strip("`").replace("json", "").strip()

        try:
            plan = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        project_name = plan.get("project_name", "unnamed-project")
        files = [
            BlueprintFile(path=f["path"], content=f["content"])
            for f in plan.get("files", [])
        ]
        return Blueprint(project_name=project_name, files=files)

    def write_to_disk(self, blueprint: Blueprint, target_dir: Path) -> list[Path]:
        """Write blueprint files to disk with path-traversal protection.

        Args:
            blueprint: The generated blueprint.
            target_dir: Directory to write files into.

        Returns:
            List of successfully written file paths.

        Raises:
            BlueprintSecurityError: If any generated path tries to escape *target_dir*.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        resolved_target = target_dir.resolve()
        written: list[Path] = []

        for bf in blueprint.files:
            full_path = (target_dir / bf.path).resolve()
            try:
                full_path.relative_to(resolved_target)
            except ValueError:
                # Raise loudly so the caller and user are informed (Principle of Least Surprise).
                raise BlueprintSecurityError(
                    f"Generated path '{bf.path}' escapes the target directory. "
                    "Blueprint rejected for security reasons."
                )

            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(bf.content, encoding="utf-8")
                written.append(full_path)
            except OSError as exc:
                logger.warning("Failed to write blueprint file '%s': %s", bf.path, exc)

        return written

