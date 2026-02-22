"""
DevBase Setup Templates Module
================================================================
PROPÓSITO:
    Configura templates de padrões técnicos, prompts de IA e workflows
    para o workspace DevBase.

    Equivalente Python do módulo setup-templates.ps1.

DIRETÓRIOS CRIADOS:
    • 00-09_SYSTEM/05_templates/patterns/  → Padrões técnicos (ADR, RFC)
    • 00-09_SYSTEM/05_templates/prompts/   → Prompts para IA
    • 00-09_SYSTEM/05_templates/ci/        → Templates de CI/CD

TEMPLATES PUBLICADOS:
    Os templates são copiados de /modules/templates/ para o workspace,
    permitindo customização local pelo usuário.

Autor: DevBase Team
Versão: 3.2.0
"""

from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from filesystem import FileSystem
    from ui import UI


def run_setup_templates(root_path: Path, fs: "FileSystem", ui: "UI") -> None:
    """
    Configura o diretório de templates e padrões técnicos.

    Esta função:
    1. Cria estrutura de diretórios para templates
    2. Copia templates de patterns, prompts e CI

    Args:
        root_path: Caminho raiz do workspace DevBase.
        fs: Instância do FileSystem para operações de arquivo.
        ui: Instância do UI para output formatado.

    Example:
        >>> run_setup_templates(Path("~/Dev_Workspace"), fs, ui)
    """
    ui.print_header("5. Templates & Standards")

    # Define caminhos
    script_dir = Path(__file__).parent.resolve()
    # Updated to point to shared templates directory (../../shared/templates)
    templates_source_root = script_dir.parent.parent / "shared" / "templates"

    # Diretório de destino: 00-09_SYSTEM/05_templates/
    system_area = root_path / "00-09_SYSTEM"
    templates_dest_dir = system_area / "05_templates"

    # ================================================
    # FASE 1: CRIAR ESTRUTURA DE DIRETÓRIOS
    # ================================================
    subdirs = ["patterns", "prompts", "ci"]
    for subdir in subdirs:
        fs.ensure_dir(str(templates_dest_dir / subdir))

    # ================================================
    # FASE 2: PUBLICAR TEMPLATES
    # ================================================
    template_subdirs = ["patterns", "prompts", "core", "ci"]
    total_copied = 0

    for subdir in template_subdirs:
        subdir_source = templates_source_root / subdir
        if not subdir_source.exists():
            continue

        # Busca todos os templates (.template)
        template_files = list(subdir_source.glob("**/*.template"))

        for template_file in template_files:
            # Lê conteúdo do template
            content = template_file.read_text(encoding="utf-8")

            # Determina caminho de destino
            # Calcula path relativo a partir do templates_source_root
            relative_path = template_file.relative_to(templates_source_root)

            # Remove extensão .template
            dest_filename = template_file.name.replace(".template", "")

            # Monta caminho de destino
            dest_dir = templates_dest_dir / relative_path.parent
            dest_path = dest_dir / dest_filename

            # Garante diretório de destino existe
            fs.ensure_dir(str(dest_dir))

            # Escreve arquivo (sobrescreve se existir - UpdateIfExists)
            fs.write_atomic(str(dest_path), content)
            total_copied += 1

    if total_copied > 0:
        ui.print_step(f"Published {total_copied} templates", "OK")
    else:
        ui.print_step("No templates found to publish", "INFO")


def get_available_templates(root_path: Path) -> List[dict]:
    """
    Lista todos os templates disponíveis no workspace.

    Args:
        root_path: Caminho raiz do workspace DevBase.

    Returns:
        List[dict]: Lista de templates com nome, categoria e caminho.
    """
    templates_dir = root_path / "00-09_SYSTEM" / "05_templates"

    if not templates_dir.exists():
        return []

    templates = []
    for category_dir in templates_dir.iterdir():
        if category_dir.is_dir():
            for template_file in category_dir.glob("*"):
                if template_file.is_file():
                    templates.append({
                        "name": template_file.name,
                        "category": category_dir.name,
                        "path": str(template_file)
                    })

    return templates


def apply_template(
    template_name: str,
    dest_path: Path,
    fs: "FileSystem",
    ui: "UI",
    variables: dict = None
) -> bool:
    """
    Aplica um template criando um novo arquivo com variáveis substituídas.

    Args:
        template_name: Nome do template (ex: "adr.md")
        dest_path: Caminho de destino para o arquivo criado
        fs: Instância do FileSystem
        ui: Instância do UI
        variables: Dicionário de variáveis para substituição

    Returns:
        bool: True se template foi aplicado com sucesso.
    """
    templates_dir = fs.root / "00-09_SYSTEM" / "05_templates"

    # Busca o template em qualquer categoria
    template_file = None
    for category_dir in templates_dir.iterdir():
        if category_dir.is_dir():
            candidate = category_dir / template_name
            if candidate.exists():
                template_file = candidate
                break

    if not template_file:
        ui.print_step(f"Template not found: {template_name}", "ERROR")
        return False

    # Lê conteúdo do template
    content = template_file.read_text(encoding="utf-8")

    # Substitui variáveis se fornecidas
    if variables:
        for key, value in variables.items():
            placeholder = f"${{{key}}}"  # Formato: ${VARIABLE}
            content = content.replace(placeholder, str(value))

    # Escreve arquivo de destino
    fs.write_atomic(str(dest_path), content)
    ui.print_step(f"Created from template: {dest_path.name}", "OK")

    return True
