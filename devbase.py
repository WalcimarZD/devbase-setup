#!/usr/bin/env python3
"""
DevBase CLI v3.1 (Python Parallel Implementation)
================================================================

PROPÓSITO:
    Implementação Python do DevBase para sistemas não-Windows (Linux/macOS).
    Fornece funcionalidade básica equivalente ao bootstrap.ps1, mas em Python
    para ambientes onde PowerShell não está disponível.

QUANDO USAR:
    - Em sistemas Linux/macOS sem PowerShell instalado
    - Em ambientes containerizados (Docker)
    - Como fallback quando pwsh não está disponível
    - Para automação em pipelines CI/CD baseados em Python

LIMITAÇÕES vs POWERSHELL:
    - Não inclui todos os templates (apenas estrutura base)
    - Não configura git hooks automaticamente
    - Não tem validação de storage tier
    - Funcionalidade reduzida do CLI (doctor, help, etc.)

ARQUITETURA:
    Este script usa o módulo filesystem.py (modules/python/) que implementa
    operações atômicas de arquivo similares às do PowerShell (Write-FileAtomic).

USO:
    $ python3 devbase.py                    # Usar diretório padrão
    $ python3 devbase.py --root ~/MyWorkspace   # Diretório personalizado
    $ python3 devbase.py --force            # Forçar sobrescrita

NOTA:
    Para funcionalidade completa (templates, hooks, AI module), execute
    bootstrap.ps1 com PowerShell Core: pwsh bootstrap.ps1

Autor: DevBase Team
Versão: 3.1.0
"""
import argparse
import os
import sys
from datetime import datetime

# ============================================
# CONFIGURAÇÃO DE PATH
# ============================================
# Adiciona o diretório modules/python ao PYTHONPATH para que
# possamos importar o módulo filesystem.py sem precisar instalá-lo.
#
# Esta técnica é comum em scripts standalone que precisam de
# módulos auxiliares sem criar um pacote Python formal.
# ============================================
sys.path.append(os.path.join(os.path.dirname(__file__), "modules", "python"))
from filesystem import FileSystem  # noqa: E402


def main():
    """
    Função principal do DevBase Python CLI.

    Fluxo de execução:
    1. Parse dos argumentos de linha de comando
    2. Exibição do banner/informações
    3. Criação da estrutura de diretórios (Johnny.Decimal)
    4. Geração dos arquivos de governança básicos
    5. Resumo e próximos passos

    Returns:
        None (exit code 0 se sucesso)
    """
    # ============================================
    # PARSING DE ARGUMENTOS
    # ============================================
    # argparse é a biblioteca padrão Python para CLI.
    # Equivalente aos param() do PowerShell.
    # ============================================
    parser = argparse.ArgumentParser(
        description="DevBase Setup (Python) - Personal Engineering Operating System",
        epilog="Para funcionalidade completa, use bootstrap.ps1 com PowerShell Core.",
    )
    parser.add_argument(
        "--root",
        default=os.path.expanduser("~/Dev_Workspace"),
        help="Caminho raiz para o workspace DevBase (padrão: ~/Dev_Workspace)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Forçar sobrescrita de arquivos existentes"
    )
    args = parser.parse_args()

    # ============================================
    # BANNER E INFORMAÇÕES
    # ============================================
    print("\nDevBase v3.1 (Python Mode)")
    print(f"Root: {args.root}")
    print("-" * 40)

    # Inicializa o helper de filesystem com o diretório raiz
    # FileSystem encapsula operações atômicas e seguras de arquivo
    fs = FileSystem(args.root)

    # ============================================
    # DEFINIÇÃO DA ESTRUTURA (Johnny.Decimal)
    # ============================================
    # Esta lista define a estrutura de diretórios a ser criada.
    # Segue o padrão Johnny.Decimal com categorias numéricas:
    #
    # 00-09: SYSTEM     - Infraestrutura e configuração
    # 10-19: KNOWLEDGE  - Gestão de conhecimento (PKM)
    # 20-29: CODE       - Projetos de desenvolvimento
    # 30-39: OPERATIONS - Automação e DevOps
    # 40-49: MEDIA      - Assets multimídia
    # 90-99: ARCHIVE    - Arquivos históricos
    #
    # NOTA: Esta é uma versão simplificada. O bootstrap.ps1 cria
    # estrutura mais completa com todos os subdiretórios.
    # ============================================
    structure = [
        # SYSTEM (00-09): Infraestrutura
        "00-09_SYSTEM/00_inbox",  # Caixa de entrada GTD
        "00-09_SYSTEM/01_dotfiles/links",  # Configurações (symlinks)
        "00-09_SYSTEM/05_templates",  # Templates reutilizáveis
        "00-09_SYSTEM/06_git_hooks",  # Git hooks compartilhados
        # KNOWLEDGE (10-19): Gestão de conhecimento
        "10-19_KNOWLEDGE/11_public_garden",  # Jardim digital público
        "10-19_KNOWLEDGE/12_private_vault/credentials",  # Vault privado (Air-Gap!)
        "10-19_KNOWLEDGE/18_adr-decisions",  # Architecture Decision Records
        # CODE (20-29): Desenvolvimento
        "20-29_CODE/21_monorepo_apps",  # Projetos monorepo
        # OPERATIONS (30-39): DevOps e automação
        "30-39_OPERATIONS/30_ai",  # Módulo AI (simplificado)
        "30-39_OPERATIONS/31_backups",  # Scripts de backup
        # MEDIA (40-49): Assets multimídia
        "40-49_MEDIA_ASSETS",
        # ARCHIVE (90-99): Arquivos históricos
        "90-99_ARCHIVE_COLD",
    ]

    # ============================================
    # CRIAÇÃO DA ESTRUTURA DE DIRETÓRIOS
    # ============================================
    print("\n1. Building Directory Structure...")
    for folder in structure:
        # ensure_dir cria o diretório se não existir (idempotente)
        fs.ensure_dir(folder)

    # ============================================
    # ARQUIVOS DE GOVERNANÇA
    # ============================================
    # Cria arquivos essenciais para o funcionamento do workspace:
    # - README.md: Documentação principal
    # - .gitignore: Proteção do vault privado
    #
    # write_atomic usa o padrão write-to-temp-then-rename para
    # garantir que o arquivo nunca fique em estado inconsistente.
    # ============================================
    print("\n2. Generating Governance Files...")

    # README básico com timestamp de geração
    readme_content = f"""# DevBase Workspace

Generated by Python CLI on {datetime.now().isoformat()}

## Quick Start

Este workspace foi criado pelo DevBase Python CLI.
Para funcionalidade completa, execute o bootstrap.ps1 com PowerShell Core:

```bash
pwsh bootstrap.ps1
```

## Structure

- `00-09_SYSTEM/` - Infrastructure and configuration
- `10-19_KNOWLEDGE/` - Personal knowledge management
- `20-29_CODE/` - Development projects
- `30-39_OPERATIONS/` - Automation and DevOps
- `40-49_MEDIA_ASSETS/` - Media files
- `90-99_ARCHIVE_COLD/` - Historical archives
"""
    fs.write_atomic("README.md", readme_content)

    # .gitignore com proteção Air-Gap para vault privado
    # CRÍTICO: Nunca commitar credenciais ou dados privados!
    gitignore_content = """# DevBase .gitignore
# ===================
# Este arquivo protege dados sensíveis de serem commitados.

# AIR-GAP PROTECTION: Vault privado NUNCA deve ir para Git/Cloud
12_private_vault/

# Estado interno do DevBase
.devbase_state.json

# Arquivos de sistema
**/.DS_Store
**/Thumbs.db

# Credenciais (redundância de segurança)
**/credentials/
**/*.key
**/*.pem
**/*.env
"""
    fs.write_atomic(".gitignore", gitignore_content)

    # ============================================
    # RESUMO FINAL
    # ============================================
    print("-" * 40)
    print("✓ Python Bootstrap Complete.")
    print("\nNext Steps:")
    print("  1. Review the created structure")
    print("  2. For full features (templates, hooks, AI), run:")
    print("     pwsh bootstrap.ps1")
    print("\nNote: Python mode provides basic structure only.")


# ============================================
# ENTRY POINT
# ============================================
# O padrão if __name__ == "__main__" garante que main()
# só é executada quando o script é rodado diretamente,
# não quando é importado como módulo.
# ============================================
if __name__ == "__main__":
    main()
