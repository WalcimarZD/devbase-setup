# DevBase v5.1 — Technical Design Document (TDD)

**Versão:** 1.3
**Data:** 2025-12-28
**Status:** Em Implementação

---

## 1. Stack Tecnológica

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| **Runtime** | Python 3.13 | Performance, tipagem moderna, ecosystem |
| **CLI Framework** | Typer | Type-safe, zero boilerplate, auto-docs |
| **Terminal UI** | Rich | Cores, tabelas, progress bars |
| **Package Manager** | uv | 10-100x mais rápido que pip |
| **Database** | DuckDB | OLAP embarcado, SQL nativo, zero-config |
| **Templating** | Jinja2 + Copier | Flexibilidade + scaffolding robusto |
| **AI (Remote)** | Groq | Inferência LLM ultra-rápida (Llama 3, Mixtral) |
| **AI (Local)** | FastEmbed | Geração de vetores local e offline |
| **Knowledge Graph** | NetworkX | Modelagem de grafos e dependências |
| **Search** | DuckDB FTS | Busca híbrida (Full-Text + Vector) |

---

## 2. Arquitetura: Command-Service-Adapter (CSA)

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (Typer)                       │
│                   src/devbase/commands/                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  core   │ │   dev   │ │   ops   │ │   pkm   │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼───────────┼───────────┼───────────┼─────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer (Pure Python)               │
│                    src/devbase/services/                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ProjectSetup │ │  Telemetry  │ │SearchEngine │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
└─────────┼───────────────┼───────────────┼───────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Adapter Layer (I/O)                      │
│           src/devbase/adapters/ + src/devbase/utils/         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Filesystem│ │  DuckDB  │ │VectorStore │ │   Groq   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Regras por Camada

| Camada | Pode | Não Pode |
|--------|------|----------|
| **CLI** | Parse args, validar input, chamar services, printar output | Lógica de negócio, I/O direto |
| **Service** | Orquestrar lógica, chamar adapters, retornar DTOs | Print, I/O direto, conhecer CLI |
| **Adapter** | I/O real, queries, chamadas externas | Lógica de negócio, conhecer services |

---

## 3. Modelo de Dados (DuckDB)

O DevBase utiliza tabelas padrão do DuckDB e a extensão `fts` para busca textual, além de tabelas específicas para vetores (embeddings).

```sql
-- Índice principal de notas
CREATE TABLE notes_index (
    file_path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    jd_category TEXT,
    tags TEXT,
    maturity TEXT CHECK(maturity IN ('draft', 'review', 'stable', 'deprecated')),
    mtime_epoch BIGINT NOT NULL
);

-- FTS Hot (Active Knowledge 10-19)
CREATE TABLE hot_fts (
    file_path TEXT PRIMARY KEY,
    title TEXT,
    content TEXT,
    tags TEXT,
    note_type TEXT,
    mtime_epoch BIGINT
);

-- FTS Cold (Archived 90-99)
CREATE TABLE cold_fts (
    file_path TEXT PRIMARY KEY,
    title TEXT,
    content TEXT,
    tags TEXT,
    note_type TEXT,
    mtime_epoch BIGINT
);

-- Índices FTS (Criados via PRAGMA)
-- PRAGMA create_fts_index('hot_fts', 'file_path', 'content', 'title', 'tags');
-- PRAGMA create_fts_index('cold_fts', 'file_path', 'content', 'title', 'tags');

-- Embeddings (Hot/Cold Separation)
-- Armazena vetores gerados pelo FastEmbed para busca semântica
CREATE TABLE hot_embeddings (
    file_path TEXT,
    chunk_id INTEGER,
    content_chunk TEXT,
    embedding DOUBLE[],
    mtime_epoch BIGINT,
    PRIMARY KEY (file_path, chunk_id)
);

CREATE TABLE cold_embeddings (
    file_path TEXT,
    chunk_id INTEGER,
    content_chunk TEXT,
    embedding DOUBLE[],
    mtime_epoch BIGINT,
    PRIMARY KEY (file_path, chunk_id)
);

-- Queue de tarefas async (IA)
CREATE TABLE ai_task_queue (
    id INTEGER PRIMARY KEY DEFAULT nextval('ai_task_queue_id_seq'),
    task_type TEXT CHECK(task_type IN ('classify', 'synthesize', 'summarize')),
    payload TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'done', 'failed')),
    created_at TIMESTAMP DEFAULT current_timestamp
);

-- Telemetria local
CREATE TABLE events (
    id INTEGER PRIMARY KEY DEFAULT nextval('events_id_seq'),
    timestamp TIMESTAMP DEFAULT current_timestamp,
    event_type TEXT NOT NULL,
    project TEXT,
    message TEXT,
    metadata TEXT
);

-- Versão do schema
CREATE TABLE schema_version (version TEXT PRIMARY KEY);
```

---

## 4. Requisitos Não-Funcionais (Specs)

| ID | Requisito | Spec | Enforcement |
|----|-----------|------|-------------|
| **RP01** | Cold Start | < 50ms | CI benchmark gate |
| **RP02** | Busca FTS | < 200ms | Hot/Cold separation |
| **RP03** | Tracking | < 50ms | Append-only, no sync |
| **RS01** | Zero network | Path crítico offline | Lint rule |
| **RS02** | Secrets | Nunca em logs | Sanitização 4 camadas |
| **RS03** | Quotas IA | Max 5 artifacts/dia | Config enforcement |

---

## 5. API/CLI Contract

### 5.1 Grupos de Comandos

```
devbase
├── core
│   ├── setup [--interactive]
│   ├── doctor [--fix]
│   ├── hydrate [--force]
│   ├── hydrate-icons
│   └── debug
├── dev
│   ├── new <name> [--template] [--no-setup]
│   ├── blueprint <name>
│   ├── adr-gen
│   ├── worktree-add <name>
│   └── audit [--fix]
├── ops
│   ├── track <message> [--type]
│   ├── stats
│   ├── weekly [--output]
│   └── backup
├── ai
│   ├── chat
│   ├── index
│   ├── classify
│   ├── summarize
│   └── routine (briefing, triage)
├── nav
│   └── goto <location>
├── pkm
│   ├── find <query>
│   ├── links <file>
│   ├── graph [--html]
│   └── new <name> --type <diataxis>
└── quick
    ├── note <message> [--edit]
    └── sync
```

### 5.2 Exit Codes

| Code | Significado |
|------|-------------|
| 0 | Sucesso |
| 1 | Erro genérico |
| 2 | Argumento inválido |
| 3 | Workspace não encontrado |
| 4 | Permissão negada |
| 5 | Quota excedida |

---

## 6. ADRs (Architectural Decision Records)

### ADR-001: Python 3.13 + uv como Runtime Único

**Status:** Aceito  
**Contexto:** v4 usava PowerShell + Python híbrido, causando complexidade de manutenção.  
**Decisão:** Consolidar em Python 3.13 com uv para gestão de dependências.  
**Consequências:** 
- (+) Codebase unificada
- (+) Performance 10x em instalação
- (-) Requer uv instalado

### ADR-002: DuckDB para Analytics e FTS

**Status:** Aceito  
**Contexto:** SQLite funciona mas carece de features OLAP e FTS moderno.  
**Decisão:** Usar DuckDB com FTS5 para busca e analytics.  
**Consequências:**
- (+) Queries analíticas 10-100x mais rápidas
- (+) FTS tokenização multilíngue
- (-) Binário maior (~15MB)

### ADR-003: Johnny.Decimal como Taxonomia

**Status:** Aceito  
**Contexto:** Desenvolvedores organizam arquivos de formas inconsistentes.  
**Decisão:** Impor estrutura Johnny.Decimal (00-99) como padrão.  
**Consequências:**
- (+) Navegação previsível
- (+) Automação simplificada
- (-) Curva de aprendizado inicial

### ADR-004: IA Assíncrona e Opcional

**Status:** Aceito  
**Contexto:** Chamadas LLM são lentas (300ms+) e requerem network.  
**Decisão:** Toda IA é processada em background thread, nunca no path crítico.  
**Consequências:**
- (+) Cold start preservado (<50ms)
- (+) Funciona 100% offline
- (-) Resultados IA não são imediatos

### ADR-005: Hot/Cold FTS Separation

**Status:** Aceito  
**Contexto:** Índice FTS monolítico de 100MB+ violava budget de 50ms.  
**Decisão:** Particionar em hot (7 dias) e cold (arquivo).  
**Consequências:**
- (+) Busca em hot é instantânea
- (+) Cold carrega sob demanda
- (-) Complexidade de sync

---

## 7. Segurança

### 7.1 Sanitização de Contexto (4 Camadas)

```python
def sanitize_context(raw: str, config: SecurityConfig) -> SanitizedContext:
    step1 = remove_secrets(raw, SECRETS_PATTERNS)     # Layer 1
    step2 = anonymize_paths(step1, salt=config.salt)  # Layer 2
    step3 = truncate_tokens(step2, max_tokens=2000)   # Layer 3
    signature = sha256(step3.encode()).hexdigest()    # Layer 4
    audit_log(signature, datetime.now())              # Audit (hash only)
    return SanitizedContext(content=step3, signature=signature)
```

### 7.2 Padrões de Secrets Bloqueados

```python
SECRETS_PATTERNS = [
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]",
    r"sk-[a-zA-Z0-9]{48}",   # OpenAI
    r"ghp_[a-zA-Z0-9]{36}",  # GitHub
    r"AKIA[0-9A-Z]{16}",     # AWS
]
```

### 7.3 Quotas de IA

```toml
[security.ai_generation]
max_daily_artifacts = 5
human_approval_required = true
blocked_paths = ["12_private_vault/", "*.env", "credentials/"]
```

---

## 8. Estrutura de Diretórios

```
src/devbase/
├── main.py              # Entry point Typer
├── commands/            # CLI layer
│   ├── core.py
│   ├── dev.py
│   ├── ops.py
│   ├── nav.py
│   └── pkm.py
├── services/            # Business logic
│   ├── project_setup.py
│   ├── telemetry.py
│   ├── search_engine.py
│   └── async_worker.py
├── adapters/            # External I/O
│   └── storage/
│       └── duckdb_adapter.py
├── utils/               # Shared utilities
│   ├── config.py
│   ├── filesystem.py
│   └── wizard.py
├── config/              # SSOT configs
│   └── taxonomy.py      # JD v5.0 definitions
└── templates/           # Jinja2 templates
```

---

## Referências

- [Typer Documentation](https://typer.tiangolo.com)
- [DuckDB Documentation](https://duckdb.org/docs)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
