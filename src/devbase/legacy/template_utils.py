"""
DevBase Template Utils
================================================================
PROPÓSITO:
    Funções utilitárias para processamento de templates.
    Extraído para evitar duplicação entre setup_core e setup_code.

USO:
    from devbase._deprecated.template_utils import process_templates
    
    process_templates(fs, ui, templates_root, dest_root, policy_version)
"""

from pathlib import Path
from datetime import datetime
from .filesystem import FileSystem
from .ui import UI


def process_templates(
    fs: FileSystem, 
    ui: UI, 
    templates_root: Path, 
    base_dest_path: str = "", 
    policy_version: str = "3.1",
    extra_replacements: dict = None
) -> None:
    """
    Busca e processa arquivos .template em um diretório.

    Args:
        fs: FileSystem.
        ui: UI.
        templates_root: Path absoluto para a pasta de templates (origem).
        base_dest_path: Caminho base de destino (relativo ao root do FS).
        policy_version: Versão da política para substituição.
        extra_replacements: Dicionário de placeholders adicionais (ex: {"{{YEAR}}": "2024"}).
    """
    if extra_replacements is None:
        extra_replacements = {}

    if not templates_root.exists():
        ui.print_step(f"Templates dir not found: {templates_root}", "WARN")
        return

    # Busca todos .template recursivamente
    template_files = list(templates_root.rglob("*.template"))
    
    if not template_files:
         ui.print_step(f"No templates found in: {templates_root}", "WARN")

    for template_file in template_files:
        try:
            # 1. Ler conteúdo
            content = template_file.read_text(encoding="utf-8")

            # 2. Replace placeholders (Default + Extra)
            # Default
            content = content.replace("{{POLICY_VERSION}}", policy_version)
            content = content.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
            
            # Extra
            for placeholder, value in extra_replacements.items():
                content = content.replace(placeholder, str(value))

            # 3. Calcular destino
            # Remove prefixo do root de templates
            rel_path_from_template_root = template_file.relative_to(templates_root)
            
            # Handle {{PLACEHOLDERS}} in filenames (common in PKM)
            # Apply replacements to the relative path string BEFORE resolving destination
            rel_path_str = str(rel_path_from_template_root)
            for placeholder, value in extra_replacements.items():
                rel_path_str = rel_path_str.replace(placeholder, str(value))
                
            # Remove extensão .template
            final_filename = rel_path_str.replace(".template", "")
            
            # Combina com o base_dest_path se fornecido
            if base_dest_path:
                # Usa Path para juntar corretamente (handling de barras)
                # Mas write_atomic espera string ou Path, fs converte.
                final_dest_path = str(Path(base_dest_path) / final_filename)
            else:
                final_dest_path = final_filename
            
            # 4. Escrever (idempotente)
            fs.write_atomic(final_dest_path, content)
            
        except Exception as e:
            ui.print_step(f"Failed to process template {template_file.name}: {e}", "ERROR")
