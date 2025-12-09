#!/usr/bin/env python3
"""
DevBase CLI v3.1 (Python Implementation)
================================================================
PROPÓSITO:
    Orquestrador principal do DevBase em Python.
    Gerencia a execução dos módulos de setup (Core, Code, PKM, etc.)
    e mantém o estado da instalação.

ARQUITETURA:
    - ui.py: Output formatado
    - filesystem.py: Operações de arquivo atômicas
    - state.py: Gerenciamento de estado (.devbase_state.json)
    - modules/python/setup_core.py: Setup base

USO:
    $ python3 devbase.py --root ~/Dev_Workspace

Autor: DevBase Team
Versão: 3.1.0
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================
# CONFIGURAÇÃO DE PATH
# ============================================
sys.path.append(os.path.join(os.path.dirname(__file__), "modules", "python"))

# Imports dos módulos locais
try:
    from filesystem import FileSystem
    from ui import UI
    from state import StateManager
    from setup_core import run_setup_core
    from setup_code import run_setup_code
    from setup_pkm import run_setup_pkm
    from setup_ai import run_setup_ai
    from setup_operations import run_setup_operations
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import DevBase modules: {e}")
    sys.exit(1)


SCRIPT_VERSION = "3.1.0"
POLICY_VERSION = "3.1"


def check_storage_tier(root_path: Path, ui: UI) -> bool:
    """
    Verifica se o storage é adequado (Tier 0).
    Simplificado para Python: Apenas avisa se não conseguir determinar.
    """
    # Em implementação real, usaríamos psutil ou platform-specifics
    # Por enquanto, apenas um placeholder que pode ser expandido
    return True


def main():
    # ============================================
    # 1. PARSING DE ARGUMENTOS
    # ============================================
    parser = argparse.ArgumentParser(
        description="DevBase Setup (Python) - Personal Engineering Operating System",
        epilog="For full functionality on Windows, consider using bootstrap.ps1.",
    )
    parser.add_argument(
        "--root",
        default=os.path.expanduser("~/Dev_Workspace"),
        help="Root path for DevBase workspace (default: ~/Dev_Workspace)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force overwrite of existing templates"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )
    args = parser.parse_args()

    # ============================================
    # 2. INICIALIZAÇÃO
    # ============================================
    ui = UI(no_color=args.no_color)
    fs = FileSystem(args.root)
    state_mgr = StateManager(Path(args.root))

    ui.print_banner(SCRIPT_VERSION)
    
    print(f"Root: {args.root}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'FORCE' if args.force else 'Normal'}")

    # ============================================
    # 3. VALIDAÇÕES INICIAIS
    # ============================================
    ui.print_header("Initial Validations")
    
    check_storage_tier(Path(args.root), ui)
    
    current_state = state_mgr.get_state()
    if current_state["version"] != "0.0.0":
        ui.print_step(f"Existing DevBase: v{current_state['version']}", "INFO")
        ui.print_step(f"Last updated: {current_state['lastUpdate']}", "INFO")

    # ============================================
    # 4. EXECUÇÃO DOS MÓDULOS
    # ============================================
    # A ordem de execução é crítica
    
    # --- 1. CORE ---
    try:
        run_setup_core(fs, ui, policy_version=POLICY_VERSION)
    except Exception as e:
        ui.print_step(f"Setup-Core failed: {e}", "ERROR")
        sys.exit(1)

    # --- 2. PKM ---
    try:
        run_setup_pkm(fs, ui, policy_version=POLICY_VERSION)
    except Exception as e:
        ui.print_step(f"Setup-PKM failed: {e}", "ERROR")
        sys.exit(1)

    # --- 3. CODE ---
    try:
        run_setup_code(fs, ui, policy_version=POLICY_VERSION)
    except Exception as e:
        ui.print_step(f"Setup-Code failed: {e}", "ERROR")
        sys.exit(1)

    # --- 4. AI ---
    try:
        run_setup_ai(fs, ui, policy_version=POLICY_VERSION)
    except Exception as e:
        ui.print_step(f"Setup-AI failed: {e}", "ERROR")
        sys.exit(1)

    # --- 5. OPERATIONS ---
    try:
        run_setup_operations(fs, ui, policy_version=POLICY_VERSION)
    except Exception as e:
        ui.print_step(f"Setup-Operations failed: {e}", "ERROR")
        sys.exit(1)

    # ============================================
    # 5. ATUALIZAÇÃO DE ESTADO
    # ============================================
    ui.print_header("Migration Engine")
    
    new_state = current_state.copy()
    new_state["version"] = SCRIPT_VERSION
    new_state["policyVersion"] = POLICY_VERSION
    new_state["lastUpdate"] = datetime.now().isoformat()
    if not new_state.get("installedAt"):
        new_state["installedAt"] = new_state["lastUpdate"]
    
    # Adiciona migração ao histórico
    migration_id = f"v{SCRIPT_VERSION}-{datetime.now().strftime('%Y%m%d')}"
    if migration_id not in new_state["migrations"]:
        new_state["migrations"].append(migration_id)
        
    state_mgr.save_state(new_state)
    ui.print_step("State saved to .devbase_state.json", "OK")

    # ============================================
    # 6. RESUMO FINAL
    # ============================================
    ui.print_header("Setup Complete")
    ui.print_step(f"DevBase v{SCRIPT_VERSION} installed successfully!", "OK")
    
    print("\nNext steps:")
    print("  1. Review the created structure")
    print("  2. Configure your dotfiles")
    print("\nNote: All modules (Core, PKM, Code, AI, Operations) are migrated to Python.")


if __name__ == "__main__":
    main()
