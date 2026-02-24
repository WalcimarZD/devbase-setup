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
        
        # 1. Check .editorconfig existence
        editorconfig = self.root / ".editorconfig"
        if not editorconfig.exists():
            issues.append(HealthIssue(
                description="Missing: .editorconfig",
                fix_action=lambda: editorconfig.write_text("root = true\n\n[*]\nindent_style = space\nindent_size = 4\n"),
                fix_description="Create default .editorconfig"
            ))

        # 2. Check .gitignore content (Smart Check)
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            issues.append(HealthIssue(
                description="Missing: .gitignore",
                fix_action=lambda: gitignore.write_text("# DevBase Global Workspace Ignore\n.devbase_state.json\n20-29_CODE/\n90-99_ARCHIVE_COLD/\n"),
                fix_description="Create default .gitignore"
            ))
        else:
            content = gitignore.read_text()
            required_patterns = ["20-29_CODE/", "90-99_ARCHIVE_COLD/", "30-39_OPERATIONS/31_backups/"]
            missing = [p for p in required_patterns if p not in content]
            
            if missing:
                def fix_gitignore():
                    with open(gitignore, "a") as f:
                        f.write("\n# Added by DevBase Doctor (Isolation Rules)\n")
                        for p in missing:
                            f.write(f"{p}\n")
                
                issues.append(HealthIssue(
                    description=f".gitignore is missing isolation rules: {', '.join(missing)}",
                    fix_action=fix_gitignore,
                    fix_description="Add missing isolation rules to .gitignore"
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
                    fix_action=lambda: gitignore.write_text(content + "\n12_private_vault/\n"),
                    fix_description="Add 12_private_vault to .gitignore"
                ))
        return issues

class EnvironmentCheck(BaseCheck):
    """Detects and fixes executable shadowing (ghosts in global Python path)."""
    def run(self) -> list[HealthIssue]:
        import shutil
        import sys
        import os
        issues = []
        
        # We only care about devbase and db executables
        targets = ["devbase", "db"]
        
        # Common global python script paths on Windows
        python_scripts = Path(sys.executable).parent / "Scripts"
        
        for target in targets:
            # Check if an executable exists in the global Python Scripts folder
            global_exe = python_scripts / f"{target}.exe"
            
            # Check if 'uv' tool path is currently shadowed
            current_path = shutil.which(target)
            
            # If current path points to global python, it's shadowing our uv tool
            if current_path and str(global_exe).lower() in current_path.lower():
                issues.append(HealthIssue(
                    description=f"Shadowing detected: '{target}' points to global Python scripts ({global_exe})",
                    fix_action=lambda p=global_exe: p.unlink() if p.exists() else None,
                    fix_description=f"Remove global ghost: {global_exe}"
                ))
        return issues

