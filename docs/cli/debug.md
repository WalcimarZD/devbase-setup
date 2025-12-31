# devbase debug

🐛 Ferramentas de depuração interna do DevBase.

**Nota:** Este comando é destinado a desenvolvedores do DevBase ou para diagnósticos avançados.

## Uso

```bash
devbase core debug [options]
```

## Funcionalidades

O comando `debug`:
1.  Verifica o ambiente de execução (Python, OS, Variáveis).
2.  Executa um "Smoke Test" criando um projeto temporário em sandbox.
3.  Verifica a integridade dos módulos internos.
4.  Testa a conexão com o banco de dados (DuckDB).
5.  Gera um relatório Markdown com os resultados.

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
