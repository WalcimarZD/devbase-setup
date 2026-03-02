# Especificação: Remediação e Melhorias (v5.1.0)

## 1. Visão Geral
Esta trilha consolida as correções apontadas na análise de qualidade de código do DevBase. O objetivo é restaurar a integridade da arquitetura, a segurança, e limpar os artefatos de testes que poluem o repositório principal.

## 2. Objetivos
- **Higiene**: Eliminar arquivos "mock" gerados nos diretórios Johnny.Decimal e isolar a execução de testes.
- **Segurança**: Ativar o `Context Sanitizer` nos provedores de LLM e remover riscos de Command Injection na extensão VS Code.
- **Robustez**: Eliminar o engolimento de erros (`except Exception: pass`) na injeção de dependências e banco de dados, além de unificar a configuração.
- **Lógica e Correção**: Corrigir bugs de detecção de diretório e otimizar operações atômicas de arquivo.
