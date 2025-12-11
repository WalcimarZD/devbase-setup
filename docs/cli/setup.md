# devbase setup

Inicializa ou atualiza a estrutura DevBase.

## Uso

```bash
devbase setup [options]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--root <path>` | Caminho para o workspace (default: `~/Dev_Workspace`) |
| `--force` | Força sobrescrita de templates existentes |
| `--dry-run` | Mostra o que seria feito sem executar |
| `--no-color` | Desabilita saída colorida |

## Exemplos

```bash
# Setup básico
devbase setup

# Setup em diretório personalizado
devbase setup --root ~/MeuWorkspace

# Forçar atualização de todos os templates
devbase setup --force

# Ver o que seria criado sem executar
devbase setup --dry-run
```

## O que é criado

O comando `setup` cria:

1. **Estrutura Johnny.Decimal** - Todas as áreas (00-09, 10-19, etc.)
2. **Arquivos de governança** - `.gitignore`, `.editorconfig`
3. **Templates** - ADR, TIL, Journal
4. **CLI** - Scripts em `35_devbase_cli/`
5. **State file** - `.devbase_state.json`

## Idempotência

O comando é **idempotente** - pode ser executado múltiplas vezes sem problemas:

- Diretórios existentes não são recriados
- Arquivos existentes não são sobrescritos (exceto com `--force`)
- Estado é atualizado incrementalmente

## Ver também

- [doctor](doctor.md) - Verificar integridade após setup
- [hydrate](hydrate.md) - Atualizar apenas templates
