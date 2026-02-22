"""
DevBase Setup Hooks Module
================================================================
PROPÓSITO:
    Configura Git Hooks baseados em shell/PowerShell para validação
    automática de commits, código e pushes.

    Equivalente Python do módulo setup-hooks.ps1.

O QUE SÃO GIT HOOKS?
────────────────────
    Git Hooks são scripts que o Git executa automaticamente em determinados
    eventos. Eles permitem automação e validação sem intervenção manual.

HOOKS CONFIGURADOS:
───────────────────
    • pre-commit     → Executado ANTES de cada commit
                       - Verifica formatação (prettier, eslint)
                       - Detecta secrets/credenciais no código
                       - Verifica arquivos grandes

    • commit-msg     → Valida a MENSAGEM do commit
                       - Garante formato Conventional Commits
                       - Ex: "feat(auth): add OAuth2 login"

    • pre-push       → Executado ANTES de cada push
                       - Executa testes
                       - Verifica push para branches protegidas
                       - Alerta sobre force push

    • post-commit    → Executado APÓS cada commit
                       - Sincroniza submodules
                       - Atualiza índices

CONVENTIONAL COMMITS:
────────────────────
    O hook commit-msg valida o formato:

      <type>(<scope>): <description>

    Tipos permitidos:
    • feat     → Nova funcionalidade
    • fix      → Correção de bug
    • docs     → Documentação
    • style    → Formatação
    • refactor → Refatoração
    • perf     → Performance
    • test     → Testes
    • build    → Build/deps
    • ci       → CI/CD
    • chore    → Manutenção

REQUISITOS:
    • Git 2.9+ (para core.hooksPath)
    • PowerShell 5.1+ ou Python 3.8+

Autor: DevBase Team
Versão: 3.2.0
"""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from filesystem import FileSystem
    from ui import UI


def run_setup_hooks(root_path: Path, fs: "FileSystem", ui: "UI") -> None:
    """
    Configura Git Hooks e o core.hooksPath do repositório.

    Esta função:
    1. Copia templates de hooks para o workspace (06_git_hooks/)
    2. Configura git core.hooksPath para usar o diretório centralizado

    Args:
        root_path: Caminho raiz do workspace DevBase.
        fs: Instância do FileSystem para operações de arquivo.
        ui: Instância do UI para output formatado.

    Example:
        >>> run_setup_hooks(Path("~/Dev_Workspace"), fs, ui)
    """
    ui.print_header("6. Git Hooks")

    # Define caminhos
    # Define caminhos
    script_dir = Path(__file__).parent.resolve()
    # Updated to point to shared templates directory (../../shared/templates)
    templates_root = script_dir.parent.parent / "shared" / "templates"
    hooks_templates_dir = templates_root / "hooks"

    # Diretório de destino: 00-09_SYSTEM/06_git_hooks/
    system_area = root_path / "00-09_SYSTEM"
    hooks_dest_dir = system_area / "06_git_hooks"

    # ================================================
    # FASE 1: COPIAR TEMPLATES DE HOOKS
    # ================================================
    if not hooks_templates_dir.exists():
        ui.print_step(
            f"Templates directory not found: {hooks_templates_dir}", "WARN"
        )
        return

    # Garante que o diretório de destino existe
    fs.ensure_dir(str(hooks_dest_dir))

    # Busca todos os templates de hooks
    template_files = list(hooks_templates_dir.glob("*.template"))

    if not template_files:
        ui.print_step("No hook templates found", "WARN")
        return

    hooks_copied = 0
    for template_file in template_files:
        # Lê conteúdo do template
        content = template_file.read_text(encoding="utf-8")

        # Remove extensão .template para obter nome do arquivo final
        dest_filename = template_file.name.replace(".template", "")

        # Caminho de destino
        dest_path = hooks_dest_dir / dest_filename

        # Cria o arquivo (não sobrescreve existente para preservar customizações)
        if not dest_path.exists():
            fs.write_atomic(str(dest_path), content)
            hooks_copied += 1
        else:
            ui.print_step(f"Hook already exists (kept): {dest_filename}", "INFO")

    if hooks_copied > 0:
        ui.print_step(f"Copied {hooks_copied} hook templates", "OK")

    # ================================================
    # FASE 2: CONFIGURAR GIT HOOKS PATH
    # ================================================
    # O Git 2.9+ suporta core.hooksPath, que permite centralizar hooks
    # em um diretório diferente de .git/hooks/

    # Caminho relativo (funciona em qualquer clone do repo)
    git_hooks_path = "00-09_SYSTEM/06_git_hooks"

    # Verifica se o workspace é um repositório Git
    git_dir = root_path / ".git"
    if git_dir.exists():
        try:
            # Configura o Git para usar nosso diretório de hooks
            result = subprocess.run(
                ["git", "-C", str(root_path), "config", "core.hooksPath", git_hooks_path],
                capture_output=True,
                text=True,
                check=True
            )
            ui.print_step(
                f"Git core.hooksPath configured to '{git_hooks_path}'", "OK"
            )
        except subprocess.CalledProcessError as e:
            ui.print_step(
                f"Failed to configure git core.hooksPath: {e.stderr}", "WARN"
            )
        except FileNotFoundError:
            ui.print_step(
                "Failed to configure git core.hooksPath. Make sure 'git' is in your PATH.",
                "WARN"
            )
    else:
        ui.print_step(
            "Not a git repository. Hooks are ready for when it becomes one.",
            "INFO"
        )


def verify_hooks_installation(root_path: Path, ui: "UI") -> bool:
    """
    Verifica se os git hooks estão corretamente instalados.

    Args:
        root_path: Caminho raiz do workspace DevBase.
        ui: Instância do UI para output formatado.

    Returns:
        bool: True se hooks estão configurados corretamente.
    """
    hooks_dir = root_path / "00-09_SYSTEM" / "06_git_hooks"
    git_dir = root_path / ".git"

    # Verifica se diretório de hooks existe
    if not hooks_dir.exists():
        ui.print_step("Git hooks directory not found", "WARN")
        return False

    # Verifica hooks essenciais
    essential_hooks = ["pre-commit.ps1", "commit-msg.ps1"]
    missing_hooks = [h for h in essential_hooks if not (hooks_dir / h).exists()]

    if missing_hooks:
        ui.print_step(f"Missing hooks: {', '.join(missing_hooks)}", "WARN")
        return False

    # Verifica configuração do Git
    if git_dir.exists():
        try:
            result = subprocess.run(
                ["git", "-C", str(root_path), "config", "--get", "core.hooksPath"],
                capture_output=True,
                text=True,
                check=True
            )
            configured_path = result.stdout.strip()
            expected_path = "00-09_SYSTEM/06_git_hooks"

            if configured_path == expected_path:
                ui.print_step("Git hooks configured correctly", "OK")
                return True
            else:
                ui.print_step(
                    f"Git hooks path mismatch: expected '{expected_path}', got '{configured_path}'",
                    "WARN"
                )
                return False
        except subprocess.CalledProcessError:
            ui.print_step("Git core.hooksPath not configured", "WARN")
            return False

    return True
