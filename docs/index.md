# 🚀 DevBase

**Personal Engineering Operating System**

O DevBase é um sistema operacional de engenharia pessoal - uma estrutura padronizada para organizar, automatizar e gerenciar todo o seu ambiente de desenvolvimento.

## ✨ Características

<div class="grid cards" markdown>

- :material-folder-multiple: **Estrutura Johnny.Decimal**
  
    Organização hierárquica e intuitiva de arquivos

- :material-console: **CLI Integrada**
  
    Comandos `devbase` para todas as operações

- :material-book-open-variant: **PKM Integrado**
  
    Personal Knowledge Management com ADRs e TIL

- :material-shield-lock: **Segurança Air-Gap**
  
    Vault privado nunca sincroniza com nuvem

- :material-hook: **Git Hooks**
  
    Validação automática de commits e código

- :material-robot: **Módulo de IA**
  
    Estrutura para modelos locais e contextos

</div>

## 🏃 Quick Start

```bash
# Instale globalmente (recomendado)
uv tool install devbase

# Execute o setup interativo
devbase core setup

# Verifique a instalação
devbase core doctor
```

## 📚 Documentação

- [**Getting Started**](getting-started/installation.md) - Instalação e configuração inicial
- [**CLI Reference**](cli/overview.md) - Todos os comandos disponíveis
- [**Architecture**](architecture.md) - Como o DevBase funciona internamente

## 🎯 Por que DevBase?

| Problema | Solução DevBase |
|----------|-----------------|
| 🗂️ Arquivos espalhados sem organização | Estrutura Johnny.Decimal para tudo |
| 🔄 Configurações inconsistentes | Templates padronizados e dotfiles centralizados |
| 📝 Falta de documentação estruturada | Sistema PKM integrado |
| 🔒 Dados sensíveis sem proteção | Air-Gap Security para vault privado |
| ⏰ Tarefas manuais repetitivas | Automação via CLI e hooks |

## 📦 Versão Atual

**v4.0.0** (Modern Python CLI)

- ✅ Typer CLI com type-safety
- ✅ Rich terminal output
- ✅ Autocompletion para bash/zsh/PowerShell
- ✅ uv package management
- ✅ Dry-run mode
