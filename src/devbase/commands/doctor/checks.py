from pathlib import Path
import re
from devbase.commands.doctor.base import BaseCheck, HealthIssue
from devbase.utils.filesystem import get_filesystem

class StructureCheck(BaseCheck):
    def run(self) -> list[HealthIssue]:
        issues = []
        required_areas = [
            '00-09_SYSTEM', '10-19_KNOWLEDGE', '20-29_CODE',
            '30-39_OPERATIONS', '40-49_MEDIA_ASSETS', '90-99_ARCHIVE_COLD'
        ]
        for area in required_areas:
            area_path = self.root / area
            if not area_path.exists():
                issues.append(HealthIssue(
                    description=f"Missing folder: {area}",
                    fix_action=lambda p=area_path: p.mkdir(parents=True, exist_ok=True),
                    fix_description=f"Create {area}"
                ))
        return issues

class GovernanceCheck(BaseCheck):
    def run(self) -> list[HealthIssue]:
        issues = []
        required_files = [
            ('.editorconfig', "root = true

[*]
indent_style = space
indent_size = 4
"),
            ('.gitignore', "# DevBase
.devbase_state.json
__pycache__/
")
        ]
        for filename, content in required_files:
            file_path = self.root / filename
            if not file_path.exists():
                issues.append(HealthIssue(
                    description=f"Missing: {filename}",
                    fix_action=lambda p=file_path, c=content: p.write_text(c),
                    fix_description=f"Create default {filename}"
                ))
        return issues

class SecurityCheck(BaseCheck):
    def run(self) -> list[HealthIssue]:
        issues = []
        private_vault = self.root / "10-19_KNOWLEDGE" / "12_private_vault"
        gitignore = self.root / ".gitignore"
        
        if private_vault.exists() and gitignore.exists():
            content = gitignore.read_text()
            if "12_private_vault" not in content:
                issues.append(HealthIssue(
                    description="Private Vault exposed to Git (missing from .gitignore)",
                    fix_action=lambda: gitignore.write_text(content + "
12_private_vault/
"),
                    fix_description="Add 12_private_vault to .gitignore"
                ))
        return issues
