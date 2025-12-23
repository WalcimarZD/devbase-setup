# 📥 Instalação

## Pré-requisitos

| Requisito | Versão Mínima | Verificar |
|-----------|---------------|-----------|
| **Python** | 3.8+ | `python --version` |
| **Git** | 2.25+ | `git --version` |

## Instalação

### Opção 1: Instalação Global (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/WalcimarZD/devbase-setup.git
cd devbase-setup

# 2. Instale o CLI globalmente usando uv (ou pip install .)
uv tool install --force .

# 3. Execute o setup interativo
devbase core setup

# 4. Verifique a saúde do workspace
devbase core doctor
```

### Opção 2: Desenvolvimento Local (uv)

```bash
# 1. Clone o repositório
git clone https://github.com/WalcimarZD/devbase-setup.git
cd devbase-setup

# 2. Sincronize dependências
uv sync

# 3. Execute via uv run
uv run devbase core setup
```

### Configuração do Workspace
 
Por padrão, o DevBase tentará detectar um workspace existente na pasta atual ou criará um novo. Para especificar um local diferente, use a flag global `--root`.
 
#### Padrão (Auto-detect)
```bash
# Usa o diretório atual como raiz
devbase core setup
```
 
#### Personalizado
```bash
# Especifica um caminho absoluto ou relativo
devbase --root "D:\MeusProjetos\Workspace" core setup
 
# Ou via variável de ambiente
export DEVBASE_ROOT="D:\MeusProjetos\Workspace"
devbase core setup
```


## Verificação

Após a instalação, execute o diagnóstico:

```bash
devbase core doctor
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


## Próximos Passos

- [Quick Start](quick-start.md) - Seus primeiros comandos
- [Structure](structure.md) - Entenda a estrutura Johnny.Decimal
- [CLI Reference](../cli/overview.md) - Todos os comandos
