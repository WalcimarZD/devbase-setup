# devbase debug

🐛 Ferramentas de depuração interna do DevBase.

**Nota:** Este comando é destinado a desenvolvedores do DevBase ou para diagnósticos avançados.

## Uso

```bash
devbase core debug [options]
```

## Funcionalidades

O comando `debug` executa um diagnóstico abrangente em 3 etapas:

1.  **Sanity Checks**: Verifica se todos os grupos de comandos (`core`, `dev`, `pkm`, etc.) carregam corretamente e exibem o help.
2.  **Smoke Tests (Sandbox)**: Executa fluxos críticos em um diretório temporário isolado:
    - `core setup`: Verifica a criação da estrutura de pastas e arquivos de governança.
    - `dev new`: Verifica a geração de projetos a partir de templates.
    - `ops backup`: Verifica a criação de backups.
3.  **Unit Tests**: Executa a suíte completa de testes (`pytest`) para validar a lógica interna.

Ao final, gera um relatório visual no terminal e um arquivo detalhado `debug_report.md`.

## Exemplo de Saída

```text
DEBUG REPORT
============
Timestamp: 2025-12-28T10:00:00

ENVIRONMENT
-----------
Python: 3.12.0
System: Linux-x86_64
Root: /home/user/Dev_Workspace

TESTS
-----
[PASS] Filesystem Write
[PASS] DuckDB Connection
[PASS] Template Rendering
```
