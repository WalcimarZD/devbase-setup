# devbase clean

Limpa arquivos temporários e backups antigos.

## Uso

```bash
devbase clean [options]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--root <path>` | Caminho para o workspace |
| `--dry-run` | Mostra arquivos sem remover |
| `--no-color` | Desabilita saída colorida |

## Exemplos

```bash
# Limpar temporários
devbase clean

# Ver o que seria removido
devbase clean --dry-run
```

## Arquivos Removidos

| Padrão | Descrição |
|--------|-----------|
| `*.log` | Arquivos de log |
| `*.tmp` | Arquivos temporários |
| `*~` | Backups de editores |
| `Thumbs.db` | Cache de miniaturas do Windows |
| `.DS_Store` | Metadados do macOS |

## Backups Antigos

Além de temporários, o comando remove backups antigos em `31_backups/local/`, mantendo apenas os **últimos 5**.

## Saída

```
========================================
 DevBase Clean
========================================
Cleaning temporary files...

 [+] Removed 12 temporary file(s)

Removing old backups...
 [+] Removed: devbase_backup_20251201_100000
 [+] Removed: devbase_backup_20251202_100000
```

## Ver também

- [backup](backup.md) - Criar novos backups
