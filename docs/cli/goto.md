# 🧭 goto

> **Navegação Semântica** — Pule para qualquer área do seu workspace com um único comando.

## Uso

```bash
devbase nav goto <localização>
```

## Localizações Disponíveis

| Localização | Destino |
|-------------|---------|
| `code` | `20-29_CODE/21_monorepo_apps` |
| `packages` | `20-29_CODE/22_shared_packages` |
| `knowledge` | `10-19_KNOWLEDGE/11_public_garden` |
| `vault` | `10-19_KNOWLEDGE/12_private_vault` |
| `ai` | `30-39_OPERATIONS/30_ai` |
| `backups` | `30-39_OPERATIONS/31_backups` |
| `inbox` | `00-09_SYSTEM/00_inbox` |
| `templates` | `00-09_SYSTEM/01_templates` |
| `dotfiles` | `00-09_SYSTEM/02_dotfiles` |

## Exemplos

```bash
# Ir para pasta de código
devbase nav goto code

# Ir para o vault privado
devbase nav goto vault

# Ir para configuração de IA
devbase nav goto ai
```

## Integração com Shell

Para usar `goto` diretamente (sem `devbase nav`), adicione ao seu `~/.bashrc` ou `~/.zshrc`:

=== "Bash/Zsh"

    ```bash
    goto() {
        cd $(devbase nav goto "$1")
    }
    ```

=== "PowerShell"

    ```powershell
    function goto($location) {
        Set-Location (devbase nav goto $location)
    }
    ```

Depois, use simplesmente:

```bash
goto code      # 🚀 Mágico!
goto vault
```

## Veja Também

- [Cheatsheet](../cheatsheet.md) — Referência rápida
- [Estrutura Johnny.Decimal](../getting-started/structure.md)
