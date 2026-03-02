# Plano de Ação: Remediação (v5.1.0)

## Fase 1: Higiene e Poluição do Repositório (Cleanup Track)
- [x] 1.1: Remover arquivos de teste trackeados em `10-19_KNOWLEDGE/` e `00-09_SYSTEM/` (preservando templates reais).
- [x] 1.2: Corrigir `.gitignore` para mapear corretamente nomes como `12_private-vault/` em vez de usar underscore.
- [x] 1.3: Atualizar configuração (se necessário) para rodar a suíte de testes em um ambiente virtual/temporário que não polua o repositório principal.

## Fase 2: Segurança e Privacidade (Security Track)
- [x] 2.1: Integrar `sanitize_context` da pasta `services/security/sanitizer.py` dentro de `devbase/ai/service.py` (antes de enviar requests para a LLM).
- [x] 2.2: Refatorar a extensão do VS Code (`vscode-devbase/src/commands/index.ts`) para remover o uso inseguro de `shell: true` e melhorar o tratamento de argumentos.

## Fase 3: Robustez da Arquitetura (Core Track)
- [x] 3.1: Remover blocos `except Exception: pass` no `src/devbase/main.py` e adicionar `logging` adequado.
- [x] 3.2: Ajustar tratamento de erro na inicialização do `duckdb_adapter.py` e `telemetry.py`.
- [x] 3.3: Consolidar a leitura de configurações: fazer com que a `AIProviderFactory` utilize o `get_config_path` de `paths.py` e que a factory passe o caminho raiz de forma consistente.

## Fase 4: Lógica e Otimizações (Logic Track)
- [x] 4.1: Corrigir o mapa semântico no `src/devbase/utils/context.py` trocando `12_private_vault` por `12_private-vault`.
- [x] 4.2: Consertar o controle de versões de banco de dados (`init_schema`) no adaptador do DuckDB.
- [x] 4.3: Refatorar `copy_atomic` em `src/devbase/utils/filesystem.py` para usar um arquivo temporário em vez de apenas `shutil.copy2`.
- [x] 4.4: Corrigir `scan_directory` para que seja possível ler metadados do `.devbase` caso requisitado.
