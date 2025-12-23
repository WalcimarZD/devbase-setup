# 🏗️ Arquitetura do DevBase

> Documentação técnica detalhada sobre como o DevBase funciona internamente.

---

## 📋 Sumário

1. [Visão Geral](#1-visão-geral)
2. [Componentes Principais](#2-componentes-principais)
3. [Fluxo de Execução](#3-fluxo-de-execução)
4. [Sistema de Módulos](#4-sistema-de-módulos)
5. [Motor de Templates](#5-motor-de-templates)
6. [Engine de Migração](#6-engine-de-migração)
7. [CLI (Interface de Linha de Comando)](#7-cli-interface-de-linha-de-comando)
8. [Segurança](#8-segurança)
9. [Extensibilidade](#9-extensibilidade)
10. [Decisões de Design](#10-decisões-de-design)

---

## 1. Visão Geral

### 1.1 Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                    DevBase v5.0 (Monoglot)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ install.sh   │───▶│   main.py    │───▶│   Workspace  │       │
│  │ (Unix entry) │    │ (Typer app)  │    │  (Resultado) │       │
│  └──────────────┘    └──────┬───────┘    └──────────────┘       │
│         │                   │                                    │
│         │            ┌──────▼───────┐                            │
│         │            │ Python Core  │                            │
│         │            ├──────────────┤                            │
│         └───────────▶│ core setup   │◀── templates/core          │
│                      │ dev new      │◀── templates/pkm           │
│                      │ ops track    │◀── templates/code          │
│                      │ pkm graph    │◀── templates/operations    │
│                      └──────────────┘                            │
│                             │                                    │
│  ┌──────────────┐    ┌──────▼───────┐    ┌──────────────┐       │
│  │  Services    │◀───│   CLI app    │───▶│ devbase CLI  │       │
│  │(Utilitários) │    │ (Typer/Rich) │    │ (Global tool)│       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Princípios Arquiteturais

| Princípio | Descrição | Implementação |
|-----------|-----------|---------------|
| **Idempotência** | Executar múltiplas vezes produz mesmo resultado | Adapters verificam existência antes de criar |
| **Modularidade** | Funcionalidades separadas em módulos | Comandos Typer independentes |
| **Declarativo** | Templates definem o estado desejado | Arquivos `.template` via Jinja2 |
| **Segurança** | Proteção contra path traversal e vazamentos | Pathlib nativo, validação de BOM |
| **Portabilidade** | Funciona em Windows, Linux, macOS | Python 3.10+ (Monoglot) |

---

## 2. Componentes Principais

### 2.1 Mapa de Componentes

```
devbase-setup-v4/
│
├── devbase.py                 # 🐍 Entry point / CLI Shim
├── install.sh                 # 🐧 Wrapper shell para Unix
├── pyproject.toml             # 📦 Dependências e metadados (uv/hatch)
│
├── src/devbase/               # 📂 Source Code (Python)
│   ├── main.py                # 🎯 Entry point Typer
│   ├── commands/              # 📦 Comandos da CLI (core, dev, ops, etc)
│   ├── services/              # ⚙️ Lógica de negócio (setup, telemetry)
│   ├── adapters/              # 🔌 Interface p/ sistemas externos
│   └── utils/                 # 🛠️ Helpers (wizard, workspace)
│
├── templates/                 # 📝 Templates fonte
│   ├── core/                  # .gitignore, .editorconfig
│   ├── pkm/                   # ADRs, journals, TIL
│   ├── code/                  # Clean Architecture
│   ├── operations/            # Scripts de automação
│   └── ai/                    # Configuração IA
│
└── docs/                      # 📚 Documentação
    ├── USAGE-GUIDE.md
    └── ARCHITECTURE.md
```

### 2.2 Responsabilidades

| Componente | Responsabilidade | Dependências |
|------------|------------------|--------------|
| `main.py` | Orquestrar execução via Typer | `commands/`, `services/` |
| `filesystem_adapter.py` | Funções utilitárias de IO seguro | `pathlib` |
| `setup_core.py` | Criar estrutura Johnny.Decimal base | `filesystem_adapter` |
| `setup_pkm.py` | Criar estrutura de conhecimento | `filesystem_adapter` |
| `setup_code.py` | Criar estrutura de código e templates | `filesystem_adapter` |
| `setup_operations.py` | Instalar CLI e scripts de automação | `filesystem_adapter` |
| `setup_hooks.py` | Instalar e configurar git hooks | `filesystem_adapter` |
| `setup_ai.py` | Criar estrutura do módulo de IA | `filesystem_adapter` |

---

## 3. Fluxo de Execução

### 3.1 Fluxo do CLI

```
┌────────────────────────────────────────────────────────────────┐
│                     devbase.py (Shim)                          │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 1. CONFIGURAÇÃO INICIAL                                         │
│    • Detectar Workspace Root                                    │
│    • Inserir ./src no sys.path                                  │
│    • Carregar Typer app                                         │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. DESPACHO DE COMANDOS (Typer)                                 │
│    • core  → Configuração e Saúde                               │
│    • dev   → Criação e Auditoria                                │
│    • ops   → Telemetria e Backup                                │
│    • pkm   → Gestão de Conhecimento                             │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. EXECUÇÃO DE SERVIÇOS                                         │
│    • ProjectSetupService (Geração de arquivos)                  │
│    • TelemetryService (Logs de eventos)                         │
│    • WorkspaceService (Detecção e metadados)                    │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Diagrama de Sequência (Python v4)

```
Usuario           install.sh        devbase.py       Typer CLI        Services
   │                  │                  │                │                 │
   │ ─────execute───▶ │                  │                │                 │
   │                  │ ──check python─▶ │                │                 │
   │                  │ ◀──found─────    │                │                 │
   │                  │ ───execute────▶  │                │                 │
   │                  │                  │ ──dispatch───▶ │                 │
   │                  │                  │                │ ──run command──▶│
   │                  │                  │                │ ◀──success───── │
   │ ◀───complete────────────────────── │                │                 │
```

---

## 4. Sistema de Comandos (Typer)

### 4.1 Organização das Comandos

O DevBase v4.0 utiliza **Typer** para uma interface de linha de comando tipada e auto-documentada. Os comandos são organizados em arquivos sob `src/devbase/commands/`:

- `core.py`: Setup, Doctor, Hydrate (os blocos fundamentais)
- `development.py`: New (geração de projetos), Audit (naming standards)
- `operations.py`: Track, Stats (telemetria), Backup, Clean
- `navigation.py`: Goto (atalhos de pasta)
- `pkm.py`: Graph, Links, Index (gestão de notas)

### 4.2 Serviços de Suporte

A lógica de negócio é isolada em `src/devbase/services/`:

- `ProjectSetupService`: Orquestra a criação de novos projetos e aplicação de templates.
- `TelemetryService`: Gerencia o log atômico de eventos em JSONL.
- `WorkspaceService`: Provê metadados sobre o workspace Johnny.Decimal.

---

## 5. Motor de Templates (Jinja2 / Copier)

O DevBase evoluiu de substituição simples de strings para motores robustos:

- **Interno**: Scripts Python processam templates em `src/devbase/templates/` usando Jinja2.
- **Externo (Copier)**: Projetos complexos utilizam a biblioteca `copier` para scaffolding com suporte a atualizações futuras.

---

## 6. Segurança e Robustez

### 6.1 Proteções Pythonic

- **Pydantic**: Validação estática de configurações e metadados.
- **Pathlib**: Manipulação segura de caminhos, prevenindo path traversal nativamente.
- **Atomic Writes**: Uso de arquivos temporários e `replace` para garantir integridade de arquivos de estado.

### 6.2 Pre-commit Hooks

O sistema de hooks foi migrado para o framework `pre-commit`, gerenciado pelo arquivo `.pre-commit-config.yaml` na raiz do repositório, garantindo padronização via Ruff e Check-json.

---

## 7. Decisões de Design (ADRs)

| ADR | Decisão | Racional |
|-----|---------|----------|
| **ADR-001** | Python 3.13 + uv | Performance extrema e gestão de dependências isolada |
| **ADR-002** | Typer + Rich | UX superior no terminal com cores e tabelas |
| **ADR-003** | Johnny.Decimal | Organização de arquivos universal e escalável |
| **ADR-004** | Strangler Fig | Migração gradual de PS1 para Python garantindo paridade |

---

## 8. Extensibilidade

### 8.1 Adicionando Novo Comando

Como o DevBase utiliza o framework **Typer**, adicionar novas funcionalidades é direto:

1. Crie um novo módulo em `src/devbase/commands/`.
2. Defina uma instância de `typer.Typer()`.
3. Registre o novo comando no `app` principal em `src/devbase/main.py`.

### 8.2 Customizando Templates

Os templates Johnny.Decimal residem em `src/devbase/templates/`. Para customizar:

- Edite os arquivos `.template` ou diretórios base.
- Utilize o comando `devbase core hydrate --force` para propagar as mudanças para o workspace ativo.

---

### 9. Decisões Arquiteturais (ADRs)

Documentamos as decisões que moldaram a v5.0:

- **Monoglot Runtime**: Remoção definitiva do PowerShell em favor de Python 3.10+ como runtime único.
- **Gestão de Dependências**: Adoção total do `uv` para garantir builds reproduzíveis e instalação instantânea.
- **Interface Visual**: Uso do `Rich` para transformar o terminal em uma dashboard de produtividade informativa.

---

## 📚 Referências

- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Johnny.Decimal Methodology](https://johnnydecimal.com/)

---

<div align="center">

[⬆️ Voltar ao topo](#️-arquitetura-do-devbase)

</div>
