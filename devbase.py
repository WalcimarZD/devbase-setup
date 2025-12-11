#!/usr/bin/env python3
"""
DevBase CLI v3.2 (Python Implementation)
================================================================
PROPÓSITO:
    CLI unificado do DevBase com suporte a todos os comandos.
    Substitui tanto devbase.py (setup) quanto devbase.ps1 (CLI).

COMANDOS:
    setup     - Inicializa/atualiza estrutura DevBase
    doctor    - Verifica integridade do workspace
    audit     - Audita nomenclatura (kebab-case)
    new       - Cria novo projeto a partir do template
    hydrate   - Atualiza templates
    backup    - Executa backup 3-2-1
    clean     - Limpa arquivos temporários
    track     - Registra atividade (telemetria)
    stats     - Mostra estatísticas de uso
    weekly    - Gera relatório semanal

USO:
    $ python devbase.py setup --root ~/Dev_Workspace
    $ python devbase.py doctor
    $ python devbase.py new meu-projeto

Autor: DevBase Team
Versão: 3.2.0
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================
# CONFIGURAÇÃO DE PATH
# ============================================
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR / "modules" / "python"))

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
    print(f"Script dir: {SCRIPT_DIR}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

# Optional: argcomplete for shell autocompletion
try:
    import argcomplete
    HAS_ARGCOMPLETE = True
except ImportError:
    HAS_ARGCOMPLETE = False

# Optional: tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback: simple iterator wrapper
    def tqdm(iterable, *args, **kwargs):
        desc = kwargs.get('desc', '')
        if desc:
            print(f"  {desc}...")
        return iterable




SCRIPT_VERSION = "3.2.0"
POLICY_VERSION = "3.2"


def detect_devbase_root() -> Path:
    """
    Detecta o diretório root do DevBase.
    Procura pelo arquivo .devbase_state.json subindo na hierarquia.
    """
    current = Path.cwd()
    
    # Procurar .devbase_state.json subindo na árvore
    for parent in [current] + list(current.parents):
        state_file = parent / ".devbase_state.json"
        if state_file.exists():
            return parent
    
    # Fallback para o padrão
    default = Path.home() / "Dev_Workspace"
    if default.exists():
        return default
    
    return current


def get_common_parser():
    """Cria argumentos comuns para todos os comandos."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root path for DevBase workspace (auto-detected if not specified)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    return parser


def cmd_setup(args, ui: UI, root: Path):
    """Comando: setup - Inicializa/atualiza estrutura DevBase."""
    ui.print_banner(SCRIPT_VERSION)
    
    fs = FileSystem(str(root), dry_run=getattr(args, 'dry_run', False))
    state_mgr = StateManager(root)

    print(f"Root: {root}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'FORCE' if args.force else 'Normal'}")
    if args.dry_run:
        print("Mode: DRY-RUN (no changes will be made)")

    # Validações iniciais
    ui.print_header("Initial Validations")
    
    current_state = state_mgr.get_state()
    if current_state["version"] != "0.0.0":
        ui.print_step(f"Existing DevBase: v{current_state['version']}", "INFO")
        ui.print_step(f"Last updated: {current_state['lastUpdate']}", "INFO")

    # Execução dos módulos
    modules = [
        ("Core", run_setup_core),
        ("PKM", run_setup_pkm),
        ("Code", run_setup_code),
        ("AI", run_setup_ai),
        ("Operations", run_setup_operations),
    ]
    
    for name, run_func in modules:
        try:
            run_func(fs, ui, policy_version=POLICY_VERSION)
        except Exception as e:
            ui.print_step(f"Setup-{name} failed: {e}", "ERROR")
            sys.exit(1)

    # Atualização de estado
    if not args.dry_run:
        ui.print_header("Migration Engine")
        
        new_state = current_state.copy()
        new_state["version"] = SCRIPT_VERSION
        new_state["policyVersion"] = POLICY_VERSION
        new_state["lastUpdate"] = datetime.now().isoformat()
        if not new_state.get("installedAt"):
            new_state["installedAt"] = new_state["lastUpdate"]
        
        migration_id = f"v{SCRIPT_VERSION}-{datetime.now().strftime('%Y%m%d')}"
        if migration_id not in new_state["migrations"]:
            new_state["migrations"].append(migration_id)
            
        state_mgr.save_state(new_state)
        ui.print_step("State saved to .devbase_state.json", "OK")

    # Resumo final
    ui.print_header("Setup Complete")
    ui.print_step(f"DevBase v{SCRIPT_VERSION} installed successfully!", "OK")
    
    print("\nNext steps:")
    print("  1. Review the created structure")
    print("  2. Run 'devbase doctor' to verify")


def cmd_doctor(args, ui: UI, root: Path):
    """Comando: doctor - Verifica integridade do workspace."""
    ui.print_header("DevBase Doctor")
    print(f"Checking DevBase integrity at: {root}\n")

    issues = 0

    # 1. Verificar estrutura de áreas
    print("Checking area structure...")
    required_areas = [
        '00-09_SYSTEM',
        '10-19_KNOWLEDGE',
        '20-29_CODE',
        '30-39_OPERATIONS',
        '40-49_MEDIA_ASSETS',
        '90-99_ARCHIVE_COLD'
    ]

    for area in required_areas:
        path = root / area
        if path.exists():
            ui.print_step(area, "OK")
        else:
            ui.print_step(f"{area} - NOT FOUND", "ERROR")
            issues += 1

    # 2. Verificar arquivos de governança
    print("\nChecking governance files...")
    required_files = [
        '.editorconfig',
        '.gitignore',
        '00.00_index.md',
        '.devbase_state.json'
    ]

    for file in required_files:
        path = root / file
        if path.exists():
            ui.print_step(file, "OK")
        else:
            ui.print_step(f"{file} - NOT FOUND", "WARN")
            issues += 1

    # 3. Verificar Air-Gap do Private Vault
    print("\nChecking Air-Gap protection...")
    private_vault = root / "10-19_KNOWLEDGE" / "12_private_vault"
    gitignore = root / ".gitignore"

    if private_vault.exists():
        if gitignore.exists():
            content = gitignore.read_text()
            if "12_private_vault" in content:
                ui.print_step("Private Vault is protected in .gitignore", "OK")
            else:
                ui.print_step("Private Vault is NOT in .gitignore!", "ERROR")
                issues += 1
        else:
            ui.print_step(".gitignore not found", "WARN")
    else:
        ui.print_step("Private Vault does not exist (optional)", "INFO")

    # 4. Verificar state file
    print("\nChecking state file...")
    state_path = root / ".devbase_state.json"
    if state_path.exists():
        try:
            state_mgr = StateManager(root)
            state = state_mgr.get_state()
            ui.print_step(f"Version: {state['version']}", "OK")
            ui.print_step(f"Installed: {state.get('installedAt', 'Unknown')}", "INFO")
        except Exception:
            ui.print_step("State file corrupted", "ERROR")
            issues += 1
    else:
        ui.print_step("State file not found (.devbase_state.json)", "WARN")

    # Resultado final
    print("\n" + "=" * 50)
    if issues == 0:
        ui.print_step("DevBase is HEALTHY", "OK")
    else:
        ui.print_step(f"Found {issues} issue(s)", "WARN")
        print("Run 'devbase doctor' again after fixing.")


def cmd_audit(args, ui: UI, root: Path):
    """Comando: audit - Audita nomenclatura kebab-case."""
    ui.print_header("DevBase Audit")
    print(f"Auditing naming conventions at: {root}\n")

    import re
    import fnmatch

    # Padrões permitidos para nomes
    allowed_patterns = [
        r'^\d{2}(-\d{2})?_',           # Johnny.Decimal (00-09_SYSTEM)
        r'^[a-z0-9]+([-.][a-z0-9]+)*$', # kebab-case
        r'^\d+(\.\d+)*$',             # Versions (4.0.3)
        r'^\.',                        # Dotfiles
        r'^__',                         # Dunder (__pycache__)
    ]

    # Padrões padrão a ignorar (built-in)
    default_ignore = [
        'node_modules', '.git', '__pycache__', 'bin', 'obj', '.vs',
        '.vscode', 'packages', 'vendor', 'dist', 'build', 'target',
        '.idea', '.gradle', 'out', 'coverage', '.nyc_output',
    ]

    # Carregar .devbaseignore se existir
    ignore_patterns = list(default_ignore)
    ignore_file = root / ".devbaseignore"
    
    if ignore_file.exists():
        print(f"Loading ignore patterns from: {ignore_file}")
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_patterns.append(line)
            print(f"  Loaded {len(ignore_patterns) - len(default_ignore)} custom patterns\n")
        except Exception as e:
            ui.print_step(f"Error reading .devbaseignore: {e}", "WARN")

    def should_ignore(item_path: Path) -> bool:
        """Verifica se o path deve ser ignorado."""
        try:
            rel_path = str(item_path.relative_to(root)).replace("\\", "/")
        except ValueError:
            rel_path = str(item_path)
        name = item_path.name
        
        for pattern in ignore_patterns:
            # Glob patterns (*, **)
            if '*' in pattern:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(name, pattern):
                    return True
            else:
                # Match exato no nome ou em qualquer componente do path
                if pattern == name or pattern in rel_path.split("/"):
                    return True
        return False

    violations = []

    for item in root.rglob('*'):
        if not item.is_dir():
            continue
        
        name = item.name
        
        if should_ignore(item):
            continue

        is_allowed = any(re.match(pattern, name) for pattern in allowed_patterns)
        
        if not is_allowed:
            suggestion = re.sub(r'([a-z])([A-Z])', r'\1-\2', name).lower()
            suggestion = re.sub(r'[_ ]', '-', suggestion)
            violations.append({
                'path': item,
                'name': name,
                'suggestion': suggestion
            })

    if not violations:
        ui.print_step("No violations found", "OK")
    else:
        print(f"Found {len(violations)} violation(s):\n")
        
        for v in violations[:20]:
            print(f"  Current:   {v['name']}")
            print(f"  Suggested: {v['suggestion']}")
            print(f"  Path:      {v['path']}")
            print()

        if len(violations) > 20:
            print(f"  ... and {len(violations) - 20} more violations\n")

        if not ignore_file.exists():
            print("TIP: Create .devbaseignore to exclude directories:")
            print("     echo 'MyLegacyProject' >> .devbaseignore\n")

        if args.fix and not args.dry_run:
            print("Applying fixes...")
            for v in violations:
                try:
                    new_path = v['path'].parent / v['suggestion']
                    v['path'].rename(new_path)
                    ui.print_step(f"Renamed: {v['name']} -> {v['suggestion']}", "OK")
                except Exception as e:
                    ui.print_step(f"Failed to rename {v['name']}: {e}", "ERROR")


def cmd_new(args, ui: UI, root: Path):
    """Comando: new - Cria novo projeto a partir do template."""
    ui.print_header("DevBase New Project")

    name = args.name
    if not name:
        print("Error: Project name is required. Use: devbase new <project-name>")
        sys.exit(1)

    template_name = "__template-clean-arch"
    code_area = root / "20-29_CODE"
    source_path = code_area / template_name
    dest_path = code_area / "21_monorepo_apps" / name

    if not source_path.exists():
        ui.print_step(f"Template '{template_name}' not found", "ERROR")
        print(f"  Expected at: {source_path}")
        return

    if dest_path.exists():
        ui.print_step(f"Project '{name}' already exists", "ERROR")
        return

    if args.dry_run:
        ui.print_step(f"Would create project at: {dest_path}", "INFO")
        return

    print(f"Creating project '{name}' from template...")

    import shutil
    try:
        shutil.copytree(source_path, dest_path)
        ui.print_step(f"Project '{name}' created successfully!", "OK")
        print(f"  Path: {dest_path}")
    except Exception as e:
        ui.print_step(f"Failed to create project: {e}", "ERROR")


def cmd_hydrate(args, ui: UI, root: Path):
    """Comando: hydrate - Atualiza templates."""
    ui.print_header("DevBase Hydrate")
    print("Syncing workspace with latest templates...")

    if args.force:
        print("Force mode: All template files will be overwritten.")

    if args.dry_run:
        ui.print_step("DRY-RUN: Would sync all templates", "INFO")
        return

    fs = FileSystem(str(root), dry_run=args.dry_run)
    
    modules_to_run = [
        ("Core", run_setup_core),
        ("PKM", run_setup_pkm),
        ("Code", run_setup_code),
        ("Operations", run_setup_operations),
    ]

    # Use progress bar if available
    modules_iter = tqdm(modules_to_run, desc="Hydrating modules", disable=not HAS_TQDM)
    
    for name, run_func in modules_iter:
        if HAS_TQDM:
            modules_iter.set_postfix(module=name)
        else:
            ui.print_step(f"Hydrating {name}...", "INFO")
        try:
            run_func(fs, ui, policy_version=POLICY_VERSION)
        except Exception as e:
            ui.print_step(f"Error hydrating {name}: {e}", "ERROR")

    ui.print_step("Hydration complete!", "OK")



def cmd_backup(args, ui: UI, root: Path):
    """Comando: backup - Executa backup 3-2-1."""
    ui.print_header("DevBase Backup 3-2-1")

    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"devbase_backup_{timestamp}"
    backup_dir = root / "30-39_OPERATIONS" / "31_backups" / "local"
    backup_path = backup_dir / backup_name

    print(f"Creating backup at: {backup_path}\n")

    if args.dry_run:
        ui.print_step(f"Would create backup: {backup_path}", "INFO")
        return

    # Pastas a excluir
    exclude = {'node_modules', '.git', '31_backups', '__pycache__', '.vs', 'bin', 'obj'}

    def ignore_patterns(dir, files):
        return [f for f in files if f in exclude]

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, backup_path, ignore=ignore_patterns)
        
        # Calcular tamanho
        size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
        size_mb = size / (1024 * 1024)

        ui.print_step("Local backup created successfully", "OK")
        print(f"  Location: {backup_path}")
        print(f"  Size: {size_mb:.2f} MB")

    except Exception as e:
        ui.print_step(f"Backup failed: {e}", "ERROR")
        return

    print("\n3-2-1 Strategy:")
    print(f"  [1] Local: {backup_path}")
    print("  [2] Second disk: Copy to external drive")
    print("  [3] Off-site: Sync to cloud (except private_vault)")


def cmd_clean(args, ui: UI, root: Path):
    """Comando: clean - Limpa arquivos temporários."""
    ui.print_header("DevBase Clean")
    print("Cleaning temporary files...\n")

    patterns = ['*.log', '*.tmp', '*~', 'Thumbs.db', '.DS_Store']
    cleaned = 0

    for pattern in patterns:
        for file in root.rglob(pattern):
            if file.is_file():
                if args.dry_run:
                    print(f"  Would remove: {file}")
                else:
                    try:
                        file.unlink()
                        cleaned += 1
                    except Exception:
                        pass

    if args.dry_run:
        ui.print_step("DRY-RUN: Files listed above would be removed", "INFO")
    else:
        ui.print_step(f"Removed {cleaned} temporary file(s)", "OK")


def cmd_track(args, ui: UI, root: Path):
    """Comando: track - Registra atividade."""
    ui.print_header("DevBase Track")

    message = args.message
    if not message:
        print("Error: Message is required. Use: devbase track \"Your message\"")
        sys.exit(1)

    event_type = args.type or "work"
    
    # Salvar em .telemetry/events.jsonl
    telemetry_dir = root / ".telemetry"
    telemetry_dir.mkdir(exist_ok=True)
    events_file = telemetry_dir / "events.jsonl"

    import json
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "message": message
    }

    if args.dry_run:
        ui.print_step(f"Would track: [{event_type}] {message}", "INFO")
        return

    with open(events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    ui.print_step(f"Tracked: [{event_type}] {message}", "OK")


def cmd_stats(args, ui: UI, root: Path):
    """Comando: stats - Mostra estatísticas de uso."""
    ui.print_header("DevBase Stats")

    import json
    from collections import Counter

    events_file = root / ".telemetry" / "events.jsonl"

    if not events_file.exists():
        ui.print_step("No telemetry data found", "INFO")
        return

    events = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not events:
        ui.print_step("No events recorded", "INFO")
        return

    # Estatísticas
    type_counts = Counter(e.get("type", "unknown") for e in events)
    
    print(f"\nTotal events: {len(events)}")
    print("\nBy type:")
    for event_type, count in type_counts.most_common():
        print(f"  {event_type}: {count}")

    # Últimas 5 atividades
    print("\nRecent activity:")
    for event in events[-5:]:
        ts = event.get("timestamp", "")[:10]
        msg = event.get("message", "")[:50]
        print(f"  [{ts}] {msg}")


def cmd_weekly(args, ui: UI, root: Path):
    """Comando: weekly - Gera relatório semanal."""
    ui.print_header("DevBase Weekly Report")

    import json
    from datetime import datetime, timedelta

    events_file = root / ".telemetry" / "events.jsonl"

    if not events_file.exists():
        ui.print_step("No telemetry data found", "INFO")
        return

    # Filtrar última semana
    week_ago = datetime.now() - timedelta(days=7)
    events = []

    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    event = json.loads(line)
                    ts = datetime.fromisoformat(event.get("timestamp", ""))
                    if ts >= week_ago:
                        events.append(event)
                except (json.JSONDecodeError, ValueError):
                    pass

    # Gerar relatório
    report = f"""# Weekly Report

**Period**: {week_ago.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}
**Total activities**: {len(events)}

## Activities

"""
    for event in events:
        ts = event.get("timestamp", "")[:10]
        msg = event.get("message", "")
        report += f"- [{ts}] {msg}\n"

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        ui.print_step(f"Report saved to: {output_path}", "OK")
    else:
        print(report)


def cmd_dashboard(args, ui: UI, root: Path):
    """Comando: dashboard - Abre dashboard de telemetria."""
    ui.print_header("DevBase Dashboard")
    
    # Check if Flask is installed
    try:
        from dashboard.server import run_server, app
    except ImportError:
        ui.print_step("Flask is required for the dashboard", "ERROR")
        print("Install with: pip install flask")
        return
    
    # Set root in environment for the server
    import os
    os.environ["DEVBASE_ROOT"] = str(root)
    
    port = getattr(args, 'port', 5000)
    
    # Open browser
    import webbrowser
    import threading
    
    def open_browser():
        import time
        time.sleep(1)  # Wait for server to start
        webbrowser.open(f"http://127.0.0.1:{port}")
    
    if not args.no_browser:
        threading.Thread(target=open_browser, daemon=True).start()
    
    # Start server
    run_server(port=port, debug=False)


def cmd_ai(args, ui: UI, root: Path):
    """Comando: ai - Assistente de IA local."""
    from ai_assistant import OllamaClient, SYSTEM_PROMPTS, get_workspace_context
    
    subcommand = getattr(args, 'ai_command', 'chat')
    model = getattr(args, 'model', 'phi')
    
    # Check Ollama availability
    client = OllamaClient(model=model)
    
    if not client.is_available():
        ui.print_header("DevBase AI")
        ui.print_step("Ollama is not running", "ERROR")
        print("\nTo use AI features, install and start Ollama:")
        print("  1. Download: https://ollama.com/download")
        print("  2. Install and start Ollama")
        print("  3. Run: ollama pull phi")
        print("  4. Try again: devbase ai chat")
        return
    
    # Build context
    workspace_context = get_workspace_context(root)
    
    if subcommand == "chat":
        ui.print_header("DevBase AI Chat")
        print(f"Model: {model} | Type 'exit' to quit\n")
        
        system = SYSTEM_PROMPTS["default"] + "\n\n" + workspace_context
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ('exit', 'quit', 'q'):
                    print("Bye!")
                    break
                if not user_input:
                    continue
                
                print("AI: ", end="", flush=True)
                response = client.generate(user_input, system=system)
                print(response)
                print()
            except KeyboardInterrupt:
                print("\nBye!")
                break
            except Exception as e:
                ui.print_step(f"Error: {e}", "ERROR")
    
    elif subcommand == "summarize":
        ui.print_header("DevBase AI Summarize")
        
        file_path = getattr(args, 'file', None)
        if not file_path:
            ui.print_step("Please provide a file to summarize", "ERROR")
            return
        
        file_path = Path(file_path)
        if not file_path.exists():
            ui.print_step(f"File not found: {file_path}", "ERROR")
            return
        
        content = file_path.read_text(encoding="utf-8")[:4000]  # Limit context
        prompt = f"Summarize the following document:\n\n{content}"
        
        print(f"Summarizing: {file_path.name}\n")
        response = client.generate(prompt, system=SYSTEM_PROMPTS["summarize"])
        print(response)
    
    elif subcommand == "explain":
        ui.print_header("DevBase AI Explain")
        
        topic = getattr(args, 'topic', None)
        if not topic:
            ui.print_step("Please provide a topic to explain", "ERROR")
            return
        
        prompt = f"Explain this concept clearly: {topic}"
        response = client.generate(prompt, system=SYSTEM_PROMPTS["explain"])
        print(response)
    
    elif subcommand == "adr":
        ui.print_header("DevBase AI - Generate ADR")
        
        decision = getattr(args, 'decision', None)
        if not decision:
            ui.print_step("Please provide a decision to document", "ERROR")
            return
        
        prompt = f"Generate an ADR for this decision: {decision}"
        response = client.generate(prompt, system=SYSTEM_PROMPTS["adr"])
        print(response)
        
        # Optionally save
        if getattr(args, 'save', False):
            adr_dir = root / "10-19_KNOWLEDGE" / "18_adr-decisions"
            adr_dir.mkdir(parents=True, exist_ok=True)
            
            # Find next ADR number
            existing = list(adr_dir.glob("adr-*.md"))
            next_num = len(existing) + 1
            adr_file = adr_dir / f"adr-{next_num:03d}.md"
            
            adr_file.write_text(response, encoding="utf-8")
            ui.print_step(f"Saved to: {adr_file}", "OK")
    
    elif subcommand == "til":
        ui.print_header("DevBase AI - Generate TIL")
        
        learning = getattr(args, 'learning', None)
        if not learning:
            ui.print_step("Please provide what you learned", "ERROR")
            return
        
        prompt = f"Generate a TIL entry for: {learning}"
        response = client.generate(prompt, system=SYSTEM_PROMPTS["til"])
        print(response)
    
    elif subcommand == "quiz":
        ui.print_header("DevBase AI - Generate Quiz")
        
        file_path = getattr(args, 'file', None)
        if not file_path:
            ui.print_step("Please provide a file with --file", "ERROR")
            return
        
        file_path = Path(file_path)
        if not file_path.exists():
            ui.print_step(f"File not found: {file_path}", "ERROR")
            return
        
        content = file_path.read_text(encoding="utf-8")[:4000]
        prompt = f"Based on this content, generate a quiz:\n\n{content}"
        
        print(f"Generating quiz from: {file_path.name}\n")
        response = client.generate(prompt, system=SYSTEM_PROMPTS["quiz"])
        print(response)
    
    elif subcommand == "flashcards":
        ui.print_header("DevBase AI - Generate Flashcards")
        
        file_path = getattr(args, 'file', None)
        if not file_path:
            ui.print_step("Please provide a file with --file", "ERROR")
            return
        
        file_path = Path(file_path)
        if not file_path.exists():
            ui.print_step(f"File not found: {file_path}", "ERROR")
            return
        
        content = file_path.read_text(encoding="utf-8")[:4000]
        prompt = f"Generate flashcards from this content:\n\n{content}"
        
        print(f"Generating flashcards from: {file_path.name}\n")
        response = client.generate(prompt, system=SYSTEM_PROMPTS["flashcards"])
        print(response)
    
    elif subcommand == "readme":
        from ai_assistant import get_project_context
        ui.print_header("DevBase AI - Generate README")
        
        project_dir = getattr(args, 'project', None)
        if project_dir:
            project_path = Path(project_dir)
        else:
            project_path = Path.cwd()
        
        if not project_path.exists():
            ui.print_step(f"Directory not found: {project_path}", "ERROR")
            return
        
        project_context = get_project_context(project_path)
        prompt = f"Generate a README.md for this project:\n\n{project_context}"
        
        print(f"Generating README for: {project_path.name}\n")
        response = client.generate(prompt, system=SYSTEM_PROMPTS["readme"])
        print(response)
        
        if getattr(args, 'save', False):
            readme_file = project_path / "README.md"
            readme_file.write_text(response, encoding="utf-8")
            ui.print_step(f"Saved to: {readme_file}", "OK")

def main():
    """Entry point principal."""
    common = get_common_parser()
    
    parser = argparse.ArgumentParser(
        prog="devbase",
        description="DevBase CLI - Personal Engineering Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  devbase setup              Initialize/update DevBase structure
  devbase doctor             Check workspace health
  devbase new my-project     Create new project from template
  devbase track "Task done"  Record activity

VERSION: """ + SCRIPT_VERSION
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # === SETUP ===
    sp_setup = subparsers.add_parser("setup", parents=[common],
        help="Initialize or update DevBase structure")
    sp_setup.add_argument("--force", action="store_true",
        help="Force overwrite of existing templates")

    # === DOCTOR ===
    subparsers.add_parser("doctor", parents=[common],
        help="Check workspace integrity")

    # === AUDIT ===
    sp_audit = subparsers.add_parser("audit", parents=[common],
        help="Audit naming conventions (kebab-case)")
    sp_audit.add_argument("--fix", action="store_true",
        help="Automatically fix violations")

    # === NEW ===
    sp_new = subparsers.add_parser("new", parents=[common],
        help="Create new project from template")
    sp_new.add_argument("name", nargs="?",
        help="Name for the new project")

    # === HYDRATE ===
    sp_hydrate = subparsers.add_parser("hydrate", parents=[common],
        help="Sync workspace with latest templates")
    sp_hydrate.add_argument("--force", action="store_true",
        help="Force overwrite of all templates")

    # === BACKUP ===
    subparsers.add_parser("backup", parents=[common],
        help="Execute 3-2-1 backup strategy")

    # === CLEAN ===
    subparsers.add_parser("clean", parents=[common],
        help="Clean temporary files")

    # === TRACK ===
    sp_track = subparsers.add_parser("track", parents=[common],
        help="Record an activity (telemetry)")
    sp_track.add_argument("message", nargs="?",
        help="Activity message to record")
    sp_track.add_argument("--type", default="work",
        help="Event type (default: work)")

    # === STATS ===
    subparsers.add_parser("stats", parents=[common],
        help="Show usage statistics")

    # === WEEKLY ===
    sp_weekly = subparsers.add_parser("weekly", parents=[common],
        help="Generate weekly report")
    sp_weekly.add_argument("--output", "-o",
        help="Output file path for the report")

    # === DASHBOARD ===
    sp_dashboard = subparsers.add_parser("dashboard", parents=[common],
        help="Open telemetry dashboard in browser")
    sp_dashboard.add_argument("--port", "-p", type=int, default=5000,
        help="Port for dashboard server (default: 5000)")
    sp_dashboard.add_argument("--no-browser", action="store_true",
        help="Don't open browser automatically")

    # === AI ===
    sp_ai = subparsers.add_parser("ai", parents=[common],
        help="Local AI assistant (requires Ollama)")
    sp_ai.add_argument("ai_command", nargs="?", default="chat",
        choices=["chat", "summarize", "explain", "adr", "til", "quiz", "flashcards", "readme"],
        help="AI subcommand (default: chat)")
    sp_ai.add_argument("--model", "-m", default="phi",
        help="Model to use (default: phi)")
    sp_ai.add_argument("--file", "-f",
        help="File to process (for summarize/quiz/flashcards)")
    sp_ai.add_argument("--topic", "-t",
        help="Topic to explain (for explain)")
    sp_ai.add_argument("--decision", "-d",
        help="Decision to document (for adr)")
    sp_ai.add_argument("--learning", "-l",
        help="What you learned (for til)")
    sp_ai.add_argument("--project", "-p",
        help="Project directory (for readme)")
    sp_ai.add_argument("--save", "-s", action="store_true",
        help="Save generated output to file")


    # Enable shell autocompletion if argcomplete is installed
    if HAS_ARGCOMPLETE:
        argcomplete.autocomplete(parser)



    # Parse args
    args = parser.parse_args()

    # Se nenhum comando foi especificado, mostrar ajuda
    if not args.command:
        parser.print_help()
        sys.exit(0)


    # Inicializar UI
    ui = UI(no_color=args.no_color)

    # Detectar ou usar root especificado
    if args.root:
        root = Path(args.root).expanduser().resolve()
    else:
        root = detect_devbase_root()

    # Dispatcher de comandos
    commands = {
        "setup": cmd_setup,
        "doctor": cmd_doctor,
        "audit": cmd_audit,
        "new": cmd_new,
        "hydrate": cmd_hydrate,
        "backup": cmd_backup,
        "clean": cmd_clean,
        "track": cmd_track,
        "stats": cmd_stats,
        "weekly": cmd_weekly,
        "dashboard": cmd_dashboard,
        "ai": cmd_ai,
    }



    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args, ui, root)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
