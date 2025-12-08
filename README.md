# 🚀 DevBase - Personal Engineering Operating System

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

**Versão 3.1** | [🤝 Contribuição](CONTRIBUTING.md)

> **📖 Documentação:** Após instalar via `bootstrap.ps1`, consulte `00-09_SYSTEM/07_documentation/USAGE-GUIDE.md` e `ARCHITECTURE.md` no seu workspace

</div>

---

## 📋 Sumário

- [O que é o DevBase?](#-o-que-é-o-devbase)
- [Início Rápido](#-início-rápido)
- [Estrutura do Workspace](#-estrutura-do-workspace)
- [Comandos da CLI](#-comandos-da-cli)
- [Configuração Avançada](#-configuração-avançada)
- [Perguntas Frequentes](#-perguntas-frequentes)
- [Recursos Adicionais](#-recursos-adicionais)

---

## 🎯 O que é o DevBase?

O **DevBase** é um **Sistema Operacional de Engenharia Pessoal** — uma estrutura padronizada para organizar, automatizar e gerenciar todo o seu ambiente de desenvolvimento. Ele resolve problemas comuns de desenvolvedores:

| Problema | Solução DevBase |
|----------|-----------------|
| 🗂️ Arquivos espalhados sem organização | Estrutura Johnny.Decimal para tudo |
| 🔄 Configurações inconsistentes entre projetos | Templates padronizados e dotfiles centralizados |
| 📝 Falta de documentação estruturada | Sistema PKM (Personal Knowledge Management) integrado |
| 🔒 Dados sensíveis sem proteção | Air-Gap Security para vault privado |
| ⏰ Tarefas manuais repetitivas | Automação via CLI e hooks |
| 🤖 IA local desorganizada | Módulo dedicado para modelos e contextos |

### ✨ Características Principais

- **📁 Estrutura Johnny.Decimal**: Organização hierárquica e intuitiva de arquivos
- **🔧 CLI Integrada**: Comandos `devbase` para todas as operações
- **📚 PKM (Personal Knowledge Management)**: Sistema para documentação, ADRs, e notas
- **🛡️ Segurança Air-Gap**: Vault privado nunca sincroniza com nuvem
- **🎣 Git Hooks**: Validação automática de commits e código
- **🤖 Módulo de IA**: Estrutura para modelos locais e contextos
- **💾 Backup 3-2-1**: Estratégia de backup automatizada
- **🔀 Multi-plataforma**: Windows (PowerShell) + Linux/macOS (Python/Bash)

---

## 🚀 Início Rápido

### Pré-requisitos

| Requisito | Versão Mínima | Verificar |
|-----------|---------------|-----------|
| **PowerShell** (Windows) | 5.1+ ou Core 7+ | `$PSVersionTable.PSVersion` |
| **Python** (Linux/macOS) | 3.8+ | `python3 --version` |
| **Git** | 2.25+ | `git --version` |

### Instalação em 3 Passos

#### **Windows (PowerShell)**

```powershell
# 1. Clone o repositório
git clone https://github.com/seu-usuario/devbase-setup-v3.git
cd devbase-setup-v3

# 2. Execute o bootstrap (localização padrão: ~/Dev_Workspace)
.\bootstrap.ps1

# 3. (Opcional) Especifique um caminho personalizado
.\bootstrap.ps1 -RootPath "D:\MeuWorkspace"
```

#### **Linux/macOS**

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/devbase-setup-v3.git
cd devbase-setup-v3

# 2. Torne o instalador executável e execute
chmod +x install.sh
./install.sh
```

### Verificação da Instalação

```powershell
# Navegue até o workspace criado
cd ~/Dev_Workspace

# Execute o diagnóstico de saúde
.\30-39_OPERATIONS\35_devbase_cli\devbase.ps1 doctor
```

Se tudo estiver correto, você verá:
```
DevBase está SAUDÁVEL
```

---

## 📂 Estrutura do Workspace

O DevBase usa a metodologia **Johnny.Decimal** para organização. Cada área tem um propósito específico:

```
Dev_Workspace/
│
├── 📁 00-09_SYSTEM/              # ⚙️ Configurações do sistema
│   ├── 00_inbox/                 # Entrada temporária de arquivos
│   ├── 01_dotfiles/              # Seus arquivos de configuração
│   │   └── links/                # Dotfiles a sincronizar com $HOME
│   ├── 05_templates/             # Templates técnicos
│   └── 06_git_hooks/             # Git hooks do workspace
│
├── 📁 10-19_KNOWLEDGE/           # 📚 Conhecimento e documentação
│   ├── 11_public_garden/         # Notas públicas, blog, TIL
│   │   ├── posts/                # Posts de blog
│   │   ├── notes/                # Notas avulsas
│   │   └── til/                  # Today I Learned
│   ├── 12_private_vault/         # 🔒 VAULT PRIVADO (Air-Gap)
│   │   ├── journal/              # Diário pessoal
│   │   ├── finances/             # Dados financeiros
│   │   ├── credentials/          # Credenciais (não sincronizar!)
│   │   └── brag-docs/            # Conquistas profissionais
│   ├── 15_references/            # Referências e padrões
│   │   ├── patterns/             # Padrões técnicos (SQL, Git)
│   │   ├── checklists/           # Checklists reutilizáveis
│   │   └── papers/               # Papers e artigos
│   └── 18_adr-decisions/         # Architectural Decision Records
│
├── 📁 20-29_CODE/                # 💻 Código fonte
│   ├── 21_monorepo_apps/         # Aplicações principais
│   ├── 22_monorepo_packages/     # Bibliotecas compartilhadas
│   │   ├── shared-types/         # Tipos TypeScript compartilhados
│   │   └── shared-utils/         # Utilitários comuns
│   ├── 23_worktrees/             # Git worktrees
│   └── __template-clean-arch/    # 📐 Template Clean Architecture
│
├── 📁 30-39_OPERATIONS/          # 🔧 Operações e automação
│   ├── 30_ai/                    # 🤖 Módulo de IA local
│   │   ├── 31_ai_local/          # Runtime e logs
│   │   ├── 32_ai_models/         # Modelos e benchmarks
│   │   └── 33_ai_config/         # Configurações e segurança
│   ├── 31_backups/               # Backups (local + cloud)
│   ├── 32_automation/            # Scripts de automação
│   ├── 33_monitoring/            # Telemetria pessoal
│   ├── 34_credentials/           # Credenciais de ops (cuidado!)
│   └── 35_devbase_cli/           # 🖥️ CLI do DevBase
│
├── 📁 40-49_MEDIA_ASSETS/        # 🎨 Mídia e assets
│   ├── 41_raw_images/            # Imagens brutas
│   ├── 42_videos_render/         # Vídeos e renderizações
│   └── 43_exports/               # Exportações finais
│
└── 📁 90-99_ARCHIVE_COLD/        # ❄️ Arquivo frio
    ├── 91_archived_projects/     # Projetos arquivados
    └── 92_archived_data/         # Dados arquivados
```

### 🔒 Segurança Air-Gap

A pasta `12_private_vault` **NUNCA** deve ser sincronizada com serviços de nuvem:

| Pasta | Sync Cloud? | Git? | Descrição |
|-------|:-----------:|:----:|-----------|
| `11_public_garden` | ✅ | ✅ | Conteúdo público |
| `12_private_vault` | ❌ | ❌ | **NUNCA SINCRONIZAR** |
| `15_references` | ✅ | ✅ | Referências técnicas |
| `18_adr-decisions` | ✅ | ✅ | Decisões arquiteturais |

---

## 🖥️ Comandos da CLI

A CLI do DevBase (`devbase.ps1`) oferece comandos para gerenciar seu workspace:

### Comandos de Gestão

```powershell
# Verificar saúde do workspace
devbase doctor

# Auditar nomenclatura (kebab-case)
devbase audit

# Corrigir nomenclatura automaticamente
devbase audit -Fix

# Atualizar todos os templates
devbase hydrate

# Forçar atualização de templates
devbase hydrate -Force

# Criar novo projeto usando template Clean Architecture
devbase new -Name "meu-projeto"

# Sincronizar dotfiles para $HOME
devbase link-dotfiles

# Executar backup 3-2-1
devbase backup

# Limpar arquivos temporários
devbase clean
```

### Comandos de Telemetria (v3.2)

```powershell
# Registrar uma atividade
devbase track -Message "Implementei feature X"

# Ver estatísticas de uso
devbase stats

# Gerar relatório semanal
devbase weekly

# Gerar relatório semanal em arquivo
devbase weekly -Output ./weeknotes.md

# Gerar Brag Document (conquistas)
devbase brag -Output ./brag-2024.md
```

### Exemplos Práticos

```powershell
# === Fluxo de trabalho típico ===

# 1. Verificar se o workspace está saudável
devbase doctor

# 2. Criar um novo projeto
devbase new -Name "api-usuarios"

# 3. Trabalhar no projeto...
# 4. Ao final do dia, registrar o que foi feito
devbase track -Message "Finalizei autenticação OAuth2"

# 5. Ao final da semana, gerar relatório
devbase weekly -Output ~/weeknotes/semana-49.md

# 6. Fazer backup
devbase backup
```

---

## ⚙️ Configuração Avançada

### Parâmetros do Bootstrap

```powershell
.\bootstrap.ps1 [parâmetros]
```

| Parâmetro | Descrição | Valor Padrão |
|-----------|-----------|--------------|
| `-RootPath` | Diretório raiz do workspace | `$HOME\Dev_Workspace` |
| `-SkipStorageValidation` | Pula verificação de SSD/NVMe | `$false` |
| `-Force` | Sobrescreve todos os templates | `$false` |
| `-SkipHooks` | Não instala git hooks | `$false` |

### Exemplos de Instalação

```powershell
# Instalação básica (padrão)
.\bootstrap.ps1

# Instalação em disco específico
.\bootstrap.ps1 -RootPath "D:\DevBase"

# Instalação forçada (atualiza tudo)
.\bootstrap.ps1 -Force

# Instalação sem hooks (ex: em VM)
.\bootstrap.ps1 -SkipHooks

# Combinação de parâmetros
.\bootstrap.ps1 -RootPath "E:\Work" -Force -SkipStorageValidation
```

### Arquivo de Estado

O arquivo `.devbase_state.json` na raiz do workspace rastreia:
- Versão instalada
- Data de instalação
- Histórico de migrações
- Módulos instalados

```json
{
  "version": "3.1.0",
  "policyVersion": "3.1",
  "installedAt": "2024-01-15T10:30:00Z",
  "lastUpdate": "2024-12-07T14:25:00Z",
  "migrations": ["v3.0.0-20240115", "v3.1.0-20241207"],
  "modules": ["setup-core.ps1", "setup-pkm.ps1", "..."]
}
```

---

## ❓ Perguntas Frequentes

### **P: Posso usar o DevBase em mais de uma máquina?**

**R:** Sim! A estrutura é portável. Recomendamos:
1. Sincronize tudo **exceto** `12_private_vault` via Git ou cloud storage
2. Mantenha credenciais no vault local de cada máquina
3. Use `devbase hydrate` após clonar para atualizar templates

### **P: Como faço backup do vault privado?**

**R:** Use backup local criptografado:
```powershell
# Exemplo com 7-Zip
7z a -p -mhe=on vault-backup.7z ".\12_private_vault"
```

### **P: Como adicionar meus dotfiles?**

**R:**
1. Copie seus dotfiles para `00-09_SYSTEM/01_dotfiles/links/`
2. Execute `devbase link-dotfiles`
3. O DevBase criará symlinks em `$HOME`

### **P: O que acontece se eu rodar `bootstrap.ps1` novamente?**

**R:** O script é **idempotente**:
- Não sobrescreve arquivos existentes (exceto com `-Force`)
- Cria apenas o que está faltando
- Atualiza o arquivo de estado

### **P: Como atualizar para uma nova versão do DevBase?**

**R:**
```powershell
# 1. No diretório do repositório DevBase
git pull origin main

# 2. No seu workspace
.\bootstrap.ps1 -Force
```

### **P: Posso personalizar os templates?**

**R:** Sim! Os templates estão em `modules/templates/`. Modifique-os e rode:
```powershell
devbase hydrate -Force
```

---

## 📚 Recursos Adicionais

### Documentação Completa

**Após instalar o DevBase**, a documentação estará disponível em seu workspace:

```
Dev_Workspace/00-09_SYSTEM/07_documentation/
├── ARCHITECTURE.md        # 🏗️ Arquitetura interna do DevBase
└── USAGE-GUIDE.md         # 📖 Guia de uso completo
```

Referências técnicas também incluídas:

| Documento | Localização | Descrição |
|-----------|-------------|-----------|
| Clean Architecture Template | `modules/templates/code/__template-clean-arch/README.md.template` | Como usar o template de projeto |
| Padrões Git | `modules/templates/patterns/git-patterns.md.template` | Conventional Commits, branching, etc. |
| ADR Template | `modules/templates/pkm/18_adr-decisions/template-madr.md.template` | Como documentar decisões |

### Estrutura dos Módulos

| Módulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| Core | `setup-core.ps1` | Estrutura base e governança |
| PKM | `setup-pkm.ps1` | Knowledge Management |
| Code | `setup-code.ps1` | Templates de código |
| Operations | `setup-operations.ps1` | CLI e automação |
| Templates | `setup-templates.ps1` | Padrões técnicos |
| Hooks | `setup-hooks.ps1` | Git hooks |
| AI | `setup-ai.ps1` | Módulo de IA local |

---

## 🤝 Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines.

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**DevBase** - Seu sistema operacional de engenharia pessoal 🚀

[⬆️ Voltar ao topo](#-devbase---personal-engineering-operating-system)

</div>
