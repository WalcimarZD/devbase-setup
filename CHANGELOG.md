# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased] - In Progress

### Changed
- Modified src/devbase/main.py
- Modified src/devbase/commands/audit.py

## [5.1.0-alpha.3] - 2025-12-28

### 📚 Documentação

- **Auditoria de Consistência**: Sincronização massiva entre código e documentação.
- **CLI Docs**: Adicionados manuais para `ai index`, `ai routine`, `dev blueprint`, `core debug` e `hydrate-icons`.
- **Technical Design**: Atualizado para refletir o uso de `DuckDB Native FTS`, `FastEmbed` e tabelas de vetores (`hot/cold_embeddings`).

## [5.1.0-alpha.1] - 2025-12-28

### ✨ Adicionado

- **Módulo de IA (`devbase ai`)**:
  - `ai config`: Configuração segura de API Key (Groq).
  - `ai organize`: Sugestão inteligente de organização de arquivos baseada em conteúdo.
  - `ai insights`: Análise arquitetural do workspace com recomendações de melhoria.
  - `ai chat`: Chat interativo com o workspace usando RAG (Retrieval-Augmented Generation).
  - `ai index`: Indexação semântica local para busca vetorial.
  - `ai classify/summarize`: Utilitários de processamento de texto via LLM.
  - Arquitetura Hexagonal (Ports & Adapters) para fácil extensão de providers.

- **Routine Agent (`devbase ai routine`)**:
  - `ai routine briefing`: Briefing matinal com tarefas pendentes e métricas.
  - `ai routine triage`: Classificação e organização automática da Inbox.
  - Integração com Telemetria (DuckDB) para análise de logs diários.

### 🛡️ Segurança

- **Prevenção de Injeção**: Whitelist de tabelas FTS e limpeza de inputs em queries Dinâmicas (DuckDB).
- **Sanitização de Contexto**: Filtros básicos antes de enviar dados do workspace para APIs de LLM.


### 🐛 Corrigido

- **Dependência de Produção**: Resolvido erro `ModuleNotFoundError: No module named 'pytest'` ao executar o comando `debug` em ambiente de produção (instalação via `uv tool`). O `pytest` agora é carregado apenas quando necessário (lazy loading).

## [3.2.0] - 2025-12-11

### ✨ Adicionado

- **CLI Python Unificado**: Migração completa de PowerShell para Python com 11 comandos
  - `setup` - Inicializa/atualiza estrutura DevBase
  - `doctor` - Verifica integridade do workspace
  - `audit` - Audita nomenclatura (kebab-case)
  - `new` - Cria novo projeto a partir do template
  - `hydrate` - Atualiza templates
  - `backup` - Executa backup 3-2-1
  - `clean` - Limpa arquivos temporários
  - `track` - Registra atividade (telemetria)
  - `stats` - Mostra estatísticas de uso
  - `weekly` - Gera relatório semanal
  - `dashboard` - Abre dashboard de telemetria

- **Dashboard de Telemetria**: Interface web com Chart.js
  - KPI cards (total, média, tipo mais frequente)
  - Gráfico de atividades por dia
  - Distribuição por tipo de atividade
  - Lista de atividades recentes

- **VS Code Extension**: Integração com o editor
  - 5 comandos (doctor, new, track, dashboard, hydrate)
  - Sidebar com estrutura Johnny.Decimal
  - Visualização de atividades recentes
  - Snippets (ADR, TIL, Journal, Weeknotes)

- **Shell Autocompletion**: Scripts para bash/zsh e PowerShell
  - `completions/devbase.bash`
  - `completions/_devbase.ps1`
  - Integração com argcomplete

- **Progress Bars**: Feedback visual com tqdm
  - Modo hydrate com barra de progresso
  - Fallback gracioso quando tqdm não instalado

- **MkDocs Documentation**: 14 páginas de documentação
  - Getting Started (Installation, Quick Start, Structure)
  - CLI Reference (todos os 11 comandos)
  - Contributing guide

### 🔧 Alterado

- **Dry-Run Mode**: Flag `--dry-run` em todos os comandos
  - FileSystem com suporte nativo a dry-run
  - Logs detalhados de operações simuladas

- **Cobertura de Testes**: Aumentada para 87%+
  - Suite completa em `test_devbase_cli.py`
  - Configuração de coverage no `pyproject.toml`

### 📦 Dependências

- Adicionado: `flask>=3.0` (dashboard)
- Adicionado: `tqdm>=4.66` (progress bars)
- Adicionado: `argcomplete>=3.0` (autocompletion)
- Adicionado: `mkdocs-material>=9.5` (documentação)

---

## [3.1.0] - 2025-11-XX

### Adicionado
- Módulo de IA local (30_ai)
- Templates PKM melhorados
- Suporte multi-plataforma (Python + PowerShell)

---

## [3.0.0] - 2025-XX-XX

### Adicionado
- Estrutura Johnny.Decimal v3
- CLI PowerShell (devbase.ps1)
- Sistema de governança
- Air-Gap security