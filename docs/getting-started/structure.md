# 📂 Estrutura do Workspace

O DevBase usa a metodologia **Johnny.Decimal** para organização. Cada área tem um propósito específico.

## Visão Geral

```
Dev_Workspace/
│
├── 📁 00-09_SYSTEM/              # ⚙️ Configurações do sistema
├── 📁 10-19_KNOWLEDGE/           # 📚 Conhecimento e documentação
├── 📁 20-29_CODE/                # 💻 Código fonte
├── 📁 30-39_OPERATIONS/          # 🔧 Operações e automação
├── 📁 40-49_MEDIA_ASSETS/        # 🎨 Mídia e assets
└── 📁 90-99_ARCHIVE_COLD/        # ❄️ Arquivo frio
```

## Detalhamento por Área

### 00-09_SYSTEM

Configurações do sistema e governança.

```
00-09_SYSTEM/
├── 00_inbox/           # Entrada temporária de arquivos
├── 01_dotfiles/        # Seus arquivos de configuração
│   └── links/          # Dotfiles a sincronizar com $HOME
├── 05_templates/       # Templates técnicos
└── 06_git_hooks/       # Git hooks do workspace
```

### 10-19_KNOWLEDGE

Conhecimento pessoal e documentação.

```
10-19_KNOWLEDGE/
├── 11_public_garden/   # Notas públicas, blog, TIL
│   ├── posts/          # Posts de blog
│   ├── notes/          # Notas avulsas
│   └── til/            # Today I Learned
├── 12_private_vault/   # 🔒 VAULT PRIVADO (Air-Gap)
│   ├── journal/        # Diário pessoal
│   ├── finances/       # Dados financeiros
│   └── credentials/    # Credenciais
├── 15_references/      # Referências e padrões
└── 18_adr-decisions/   # Architectural Decision Records
```

!!! warning "Air-Gap"
    A pasta `12_private_vault` **NUNCA** deve ser sincronizada com serviços de nuvem.

### 20-29_CODE

Código fonte e projetos.

```
20-29_CODE/
├── 21_monorepo_apps/       # Aplicações principais
├── 22_monorepo_packages/   # Bibliotecas compartilhadas
├── 23_worktrees/           # Git worktrees
└── __template-clean-arch/  # Template de projeto
```

### 30-39_OPERATIONS

Operações, automação e ferramentas.

```
30-39_OPERATIONS/
├── 30_ai/              # 🤖 Módulo de IA local
│   ├── 31_ai_local/    # Runtime e logs
│   ├── 32_ai_models/   # Modelos
│   └── 33_ai_config/   # Configurações
├── 31_backups/         # Backups (local + cloud)
├── 32_automation/      # Scripts de automação
├── 33_monitoring/      # Telemetria pessoal
└── 35_devbase_cli/     # CLI do DevBase
```

### 40-49_MEDIA_ASSETS

Mídia e recursos visuais.

```
40-49_MEDIA_ASSETS/
├── 41_raw_images/      # Imagens brutas
├── 42_videos_render/   # Vídeos e renderizações
└── 43_exports/         # Exportações finais
```

### 90-99_ARCHIVE_COLD

Arquivo frio para projetos antigos.

```
90-99_ARCHIVE_COLD/
├── 91_archived_projects/   # Projetos arquivados
└── 92_archived_data/       # Dados arquivados
```

## Arquivos de Governança

| Arquivo | Propósito |
|---------|-----------|
| `.gitignore` | Ignora arquivos do Git |
| `.editorconfig` | Configurações do editor |
| `.devbase_state.json` | Estado da instalação |
| `00.00_index.md` | Índice do workspace |

## Próximos Passos

- [CLI Reference](../cli/overview.md) - Comandos disponíveis
- [Architecture](../architecture.md) - Arquitetura interna
