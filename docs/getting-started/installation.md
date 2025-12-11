# 📥 Instalação

## Pré-requisitos

| Requisito | Versão Mínima | Verificar |
|-----------|---------------|-----------|
| **Python** | 3.8+ | `python --version` |
| **Git** | 2.25+ | `git --version` |

## Instalação

### Opção 1: Clone e Execute (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/WalcimarZD/devbase-setup.git
cd devbase-setup

# 2. (Opcional) Instale dependências para recursos extras
pip install -r requirements.txt

# 3. Execute o setup
python devbase.py setup

# 4. Verifique a instalação
python devbase.py doctor
```

### Opção 2: Workspace Personalizado

```bash
# Especifique um caminho personalizado
python devbase.py setup --root ~/MeuWorkspace
```

### Opção 3: PowerShell (Windows Legacy)

```powershell
# Execute o bootstrap antigo
.\bootstrap.ps1
```

## Verificação

Após a instalação, execute o diagnóstico:

```bash
python devbase.py doctor
```

Se tudo estiver correto, você verá:

```
========================================
 DevBase Doctor
========================================
Checking area structure...
 [+] 00-09_SYSTEM
 [+] 10-19_KNOWLEDGE
 [+] 20-29_CODE
 [+] 30-39_OPERATIONS
 [+] 40-49_MEDIA_ASSETS
 [+] 90-99_ARCHIVE_COLD
==================================================
 [+] DevBase is HEALTHY
```

## Shell Autocompletion

### Bash/Zsh

```bash
# Adicione ao ~/.bashrc ou ~/.zshrc
eval "$(register-python-argcomplete devbase)"

# Ou use o script fornecido
source completions/devbase.bash
```

### PowerShell

```powershell
# Adicione ao $PROFILE
Import-Module ./completions/_devbase.ps1
```

## Próximos Passos

- [Quick Start](quick-start.md) - Seus primeiros comandos
- [Structure](structure.md) - Entenda a estrutura Johnny.Decimal
- [CLI Reference](../cli/overview.md) - Todos os comandos
