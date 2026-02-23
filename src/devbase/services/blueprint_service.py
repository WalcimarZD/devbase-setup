"""
Blueprint Service
==================
Generates AI-powered project blueprints using Clean Architecture principles.

Extracted from commands/development.py to respect the
Command-Service-Adapter separation (ARCHITECTURE.md).

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


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


class BlueprintService:
    """
    Generates project blueprints via LLM.

    Responsibilities:
    - Construct the LLM prompt for Clean Architecture scaffolding
    - Parse the JSON response
    - Write files to disk with path traversal safety

    Args:
        root: Workspace root path
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def generate(self, description: str) -> Blueprint:
        """
        Generate a project blueprint from a natural-language description.

        Args:
            description: Human description of the project (e.g., "API FastAPI com Redis")

        Returns:
            Blueprint with project name and file list

        Raises:
            ProviderError: If the LLM call fails
            ValueError: If the LLM response is not valid JSON
        """
        from devbase.adapters.ai.groq_adapter import GroqProvider

        provider = GroqProvider()

        prompt = f"""
Generate a project file structure for: "{description}".
Follow Clean Architecture principles (Domain, Use Cases, Interfaces, Infrastructure).
Return ONLY a valid JSON object with this exact schema:
{{
  "project_name": "suggested-kebab-name",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "Minimal content/stub code..."
    }}
  ]
}}
Do not include markdown blocks or extra text.
"""

        response = provider.generate(prompt, temperature=0.2, model="llama-3.3-70b-versatile")
        raw_json = response.content.strip()

        # Cleanup potential markdown fencing
        if raw_json.startswith("```"):
            raw_json = raw_json.strip("`").replace("json", "").strip()

        try:
            plan = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}") from e

        project_name = plan.get("project_name", "unnamed-project")
        files = [
            BlueprintFile(path=f["path"], content=f["content"])
            for f in plan.get("files", [])
        ]

        return Blueprint(project_name=project_name, files=files)

    def write_to_disk(self, blueprint: Blueprint, target_dir: Path) -> list[Path]:
        """
        Write blueprint files to disk with path traversal protection.

        Args:
            blueprint: The generated blueprint
            target_dir: Directory to write files into

        Returns:
            List of successfully written file paths
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []

        for bf in blueprint.files:
            try:
                full_path = (target_dir / bf.path).resolve()
                # Security: ensure path stays within target_dir
                full_path.relative_to(target_dir.resolve())

                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(bf.content, encoding="utf-8")
                written.append(full_path)
            except ValueError:
                logger.warning(f"Skipped unsafe path (traversal attempt): {bf.path}")
            except OSError as e:
                logger.warning(f"Failed to write {bf.path}: {e}")

        return written
