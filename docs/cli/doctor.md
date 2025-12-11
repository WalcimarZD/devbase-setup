# devbase doctor

Verifica a integridade do workspace DevBase.

## Uso

```bash
devbase doctor [options]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--root <path>` | Caminho para o workspace |
| `--no-color` | Desabilita saída colorida |

## O que é verificado

1. **Estrutura de áreas** - Todas as áreas Johnny.Decimal existem?
2. **Arquivos de governança** - `.gitignore`, `.editorconfig`, etc.
3. **Air-Gap** - Private vault está protegido no `.gitignore`?
4. **State file** - `.devbase_state.json` existe e é válido?

## Exemplo de Saída

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

Checking governance files...
 [+] .editorconfig
 [+] .gitignore
 [+] 00.00_index.md
 [+] .devbase_state.json

Checking Air-Gap protection...
 [+] Private Vault is protected in .gitignore

Checking state file...
 [+] Version: 3.2.0
 [i] Installed: 2025-12-11

==================================================
 [+] DevBase is HEALTHY
```

## Símbolos

| Símbolo | Significado |
|---------|-------------|
| `[+]` | OK - Verificação passou |
| `[!]` | Warning - Atenção necessária |
| `[X]` | Error - Problema encontrado |
| `[i]` | Info - Informação |

## Ver também

- [setup](setup.md) - Corrigir problemas encontrados
- [audit](audit.md) - Auditoria de nomenclatura
