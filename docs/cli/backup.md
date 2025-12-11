# devbase backup

Executa backup seguindo a estratégia 3-2-1.

## Uso

```bash
devbase backup [options]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--root <path>` | Caminho para o workspace |
| `--dry-run` | Mostra o que seria feito |
| `--no-color` | Desabilita saída colorida |

## Exemplos

```bash
# Executar backup
devbase backup

# Ver o que seria copiado
devbase backup --dry-run
```

## Estratégia 3-2-1

| Cópia | Descrição | Destino |
|-------|-----------|---------|
| 1 | Local | `30-39_OPERATIONS/31_backups/local/` |
| 2 | Segundo disco | Manual - copie para disco externo |
| 3 | Off-site | Manual - sincronize com nuvem |

## O que é excluído

Por padrão, os seguintes diretórios são excluídos do backup:

- `node_modules/`
- `.git/`
- `31_backups/` (evita recursão)
- `__pycache__/`
- `.vs/`
- `bin/` e `obj/`

## Retenção

O comando `devbase clean` remove backups antigos, mantendo os últimos 5.

## Saída

```
========================================
 DevBase Backup 3-2-1
========================================
Creating backup at: D:\Dev_Workspace\30-39_OPERATIONS\31_backups\local\devbase_backup_20251211_163000

 [+] Local backup created successfully
  Location: D:\...\devbase_backup_20251211_163000
  Size: 245.32 MB

3-2-1 Strategy:
  [1] Local: D:\...\devbase_backup_20251211_163000
  [2] Second disk: Copy to external drive
  [3] Off-site: Sync to cloud (except private_vault)
```

## Ver também

- [clean](clean.md) - Limpar backups antigos
