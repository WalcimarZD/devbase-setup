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
# Clone o repositório
git clone https://github.com/WalcimarZD/devbase-setup.git
cd devbase-setup

# Execute o setup interativo
python devbase.py setup --interactive

# Verifique a instalação
python devbase.py doctor

# Veja seu progresso de onboarding
python devbase.py onboarding
```

## 📚 Documentação

### Tutoriais (Aprendizado prático)
- [**Primeiro Projeto em 5 min**](tutorials/first-project.md) - Hello World com DevBase

### How-To (Guias de tarefa)
- [**Configurar Git Hooks**](how-to/setup-git-hooks.md) - Validação de commits
- [**Backup do Workspace**](how-to/backup-workspace.md) - Estratégia 3-2-1

### Explicação (Conceitos)
- [**Johnny.Decimal**](explanation/johnny-decimal.md) - Sistema de organização
- [**Clean Architecture**](explanation/clean-architecture.md) - Template de projeto
- [**Air-Gap Security**](explanation/air-gap-security.md) - Proteção do vault

### Referência
- [**CLI Reference**](cli/overview.md) - Todos os comandos disponíveis
- [**Architecture**](ARCHITECTURE.md) - Como o DevBase funciona internamente

## 🎯 Por que DevBase?

| Problema | Solução DevBase |
|----------|-----------------| 
| 🗂️ Arquivos espalhados sem organização | Estrutura Johnny.Decimal para tudo |
| 🔄 Configurações inconsistentes | Templates padronizados e dotfiles centralizados |
| 📝 Falta de documentação estruturada | Sistema PKM integrado |
| 🔒 Dados sensíveis sem proteção | Air-Gap Security para vault privado |
| ⏰ Tarefas manuais repetitivas | Automação via CLI e hooks |

## 📦 Versão Atual

**v3.2.0** (Python Edition)

- ✅ CLI Python unificado
- ✅ Wizard interativo (`--interactive`)
- ✅ Onboarding checklist
- ✅ Autocompletion para bash/zsh/PowerShell
- ✅ Progress bars com tqdm
- ✅ Dry-run mode
- ✅ 87%+ test coverage
