# 🚀 DevBase - Personal Engineering Operating System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Codecov](https://img.shields.io/codecov/c/gh/WalcimarZD/devbase-setup.svg?logo=codecov)](https://codecov.io/gh/WalcimarZD/devbase-setup)

<div align="center">

```
╔═══════════════════════════════════════════════════════════╗
║     ██████╗ ███████╗██╗   ██╗██████╗  █████╗ ███████╗███████╗ ║
║     ██╔══██╗██╔════╝██║   ██║██╔══██╗██╔══██╗██╔════╝██╔════╝ ║
║     ██║  ██║█████╗  ██║   ██║██████╔╝███████║███████╗█████╗   ║
║     ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██╗██╔══██║╚════██║██╔══╝   ║
║     ██████╔╝███████╗ ╚████╔╝ ██████╔╝██║  ██║███████║███████╗ ║
║     ╚═════╝ ╚══════╝  ╚═══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝ ║
╚═══════════════════════════════════════════════════════════╝
```

**Versão 3.2.0** | [📖 Docs](https://walcimarzd.github.io/devbase-setup/) | [🤝 Contribuição](CONTRIBUTING.md)

</div>

---

## 📋 Índice

- [O que é o DevBase?](#-o-que-é-o-devbase)
- [Instalação](#-instalação)
- [Comandos](#-comandos)
- [Estrutura do Workspace](#-estrutura-do-workspace)
- [Versão PowerShell (Legacy)](#-versão-powershell-legacy)

---

## 🎯 O que é o DevBase?

O **DevBase** é um **Sistema Operacional de Engenharia Pessoal** — uma estrutura padronizada para organizar seu ambiente de desenvolvimento usando a metodologia **Johnny.Decimal**.

| Problema | Solução DevBase |
|----------|-----------------|
| 🗂️ Arquivos espalhados | Estrutura Johnny.Decimal organizada |
| 🔄 Configurações inconsistentes | Templates padronizados |
| 📝 Falta de documentação | Sistema PKM integrado |
| 🔒 Dados sensíveis expostos | Vault privado com Air-Gap |
| ⏰ Tarefas manuais repetitivas | CLI automatizada |
| 🤖 IA local desorganizada | Módulo dedicado (Ollama) |

### ✨ Características

- **📁 Johnny.Decimal** - Organização hierárquica de arquivos
- **🔧 CLI Python** - Cross-platform (Windows/Linux/macOS)
- **📚 PKM** - Personal Knowledge Management integrado
- **🛡️ Air-Gap** - Vault privado nunca sincroniza
- **🎣 Git Hooks** - Conventional Commits automático
- **🤖 AI Local** - Integração com Ollama
- **📊 Dashboard** - Visualização de telemetria
- **🧩 VS Code Extension** - Integração com editor

---

## 🚀 Instalação

### Requisitos

| Requisito | Versão | Verificar |
|-----------|--------|-----------|
| Python | 3.8+ | `python --version` |
| Git | 2.9+ | `git --version` |

### Quick Start

```bash
# 1. Clone o repositório
git clone https://github.com/WalcimarZD/devbase-setup.git
cd devbase-setup

# 2. Instale dependências (opcional, para dashboard e AI)
pip install -r requirements.txt

# 3. Execute o setup
python devbase.py setup

# 4. Verifique a instalação
python devbase.py doctor
```

### Instalação Customizada

```bash
# Especificar diretório
python devbase.py setup --root ~/MeuWorkspace

# Modo dry-run (apenas mostra o que faria)
python devbase.py setup --dry-run

# Forçar atualização de todos os templates
python devbase.py setup --force
```

### Shell Completions

```bash
# Bash (adicione ao ~/.bashrc)
eval "$(python completions/devbase_complete.py bash)"

# Zsh (adicione ao ~/.zshrc)
source <(python completions/devbase_complete.py zsh)

# Fish
python completions/devbase_complete.py fish > ~/.config/fish/completions/devbase.fish

# PowerShell (adicione ao $PROFILE)
python completions/devbase_complete.py powershell >> $PROFILE
```

---

## 🖥️ Comandos

### Gestão do Workspace

| Comando | Descrição |
|---------|-----------|
| `setup` | Inicializa/atualiza workspace |
| `doctor` | Verifica integridade |
| `audit` | Audita nomenclatura (kebab-case) |
| `hydrate` | Atualiza templates |
| `new <nome>` | Cria projeto do template |
| `clean` | Remove arquivos temporários |
| `backup` | Executa backup 3-2-1 |

### Telemetria

| Comando | Descrição |
|---------|-----------|
| `track -m "msg"` | Registra atividade |
| `stats` | Mostra estatísticas |
| `weekly` | Gera relatório semanal |
| `dashboard` | Abre dashboard web |

### AI Local (requer Ollama)

| Comando | Descrição |
|---------|-----------|
| `ai chat` | Chat interativo |
| `ai summarize <file>` | Resume documento |
| `ai explain <topic>` | Explica conceito |
| `ai adr <decision>` | Gera ADR |
| `ai til <topic>` | Gera TIL |

### Exemplos

```bash
# Fluxo típico de trabalho
python devbase.py doctor              # Verificar saúde
python devbase.py new meu-projeto     # Criar projeto
python devbase.py track -m "Feature X implementada"
python devbase.py weekly              # Relatório semanal
python devbase.py backup              # Backup
```

---

## 📂 Estrutura do Workspace

```
Dev_Workspace/
│
├── 📁 00-09_SYSTEM/              # ⚙️ Sistema
│   ├── 00_inbox/                 # Entrada temporária
│   ├── 01_dotfiles/              # Configurações
│   ├── 05_templates/             # Templates técnicos
│   └── 06_git_hooks/             # Git hooks
│
├── 📁 10-19_KNOWLEDGE/           # 📚 Conhecimento
│   ├── 11_public_garden/         # Notas públicas, TIL
│   ├── 12_private_vault/         # 🔒 VAULT PRIVADO
│   ├── 15_references/            # Referências técnicas
│   └── 18_adr-decisions/         # ADRs
│
├── 📁 20-29_CODE/                # 💻 Código
│   ├── 21_monorepo_apps/         # Aplicações
│   ├── 22_monorepo_packages/     # Bibliotecas
│   └── 23_worktrees/             # Git worktrees
│
├── 📁 30-39_OPERATIONS/          # 🔧 Operações
│   ├── 30_ai/                    # 🤖 IA local
│   ├── 31_backups/               # Backups
│   └── 32_automation/            # Scripts
│
├── 📁 40-49_MEDIA_ASSETS/        # 🎨 Mídia
│
└── 📁 90-99_ARCHIVE_COLD/        # ❄️ Arquivo
```

### 🔒 Segurança Air-Gap

| Pasta | Sync Cloud? | Git? |
|-------|:-----------:|:----:|
| `11_public_garden` | ✅ | ✅ |
| `12_private_vault` | ❌ | ❌ |
| `15_references` | ✅ | ✅ |

---

## 🔷 Versão PowerShell (Legacy)

> **Nota**: A versão PowerShell é mantida para compatibilidade. Novos recursos são desenvolvidos apenas na versão Python.

```powershell
# Instalação PowerShell
.\bootstrap.ps1

# Com parâmetros
.\bootstrap.ps1 -RootPath "D:\DevBase" -Force
```

Para documentação completa do PowerShell, veja [powershell/README.md](powershell/README.md).

---

## 📚 Módulos

| Módulo | Descrição |
|--------|-----------|
| `setup_core.py` | Estrutura base e governança |
| `setup_pkm.py` | Knowledge Management |
| `setup_code.py` | Templates de código |
| `setup_operations.py` | CLI e automação |
| `setup_ai.py` | Módulo de IA |
| `setup_hooks.py` | Git hooks |
| `setup_templates.py` | Templates técnicos |
| `detect_language.py` | Detecção de stack |

---

## ❓ FAQ

**P: Posso usar em múltiplas máquinas?**
R: Sim! Sincronize via Git (exceto `12_private_vault`).

**P: Como atualizar?**
R: `git pull && python devbase.py setup --force`

**P: Como backup do vault privado?**
R: Use backup local criptografado (7z, VeraCrypt).

---

## 🤝 Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Licença

MIT License - veja [LICENSE](LICENSE).

---

<div align="center">

**DevBase** - Seu sistema operacional de engenharia pessoal 🚀

</div>
