# devbase audit

Audita nomenclatura de diretórios, verificando conformidade com kebab-case.

## Uso

```bash
devbase audit [options]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--fix` | Renomeia automaticamente violações |
| `--root <path>` | Caminho para o workspace |
| `--dry-run` | Mostra correções sem aplicar |
| `--no-color` | Desabilita saída colorida |

## Padrões Permitidos

O audit aceita os seguintes padrões de nomenclatura:

| Padrão | Exemplo | Descrição |
|--------|---------|-----------|
| Johnny.Decimal | `00-09_system` | Áreas numéricas |
| kebab-case | `my-project` | Palavras minúsculas separadas por hífen |
| Versões | `4.0.3` | Números de versão |
| Dotfiles | `.gitignore` | Arquivos ocultos |
| Dunder | `__pycache__` | Diretórios especiais |

## Exemplos

```bash
# Verificar violações
devbase audit

# Corrigir automaticamente
devbase audit --fix

# Ver o que seria corrigido
devbase audit --fix --dry-run
```

## Exemplo de Saída

```
========================================
 DevBase Audit
========================================
Auditing naming conventions at: D:\Dev_Workspace

Found 2 violation(s):

  Current:   MyBadFolder
  Suggested: my-bad-folder
  Path:      D:\Dev_Workspace\MyBadFolder

  Current:   AnotherOne
  Suggested: another-one
  Path:      D:\Dev_Workspace\AnotherOne
```

## Ignorar Diretórios

Crie um arquivo `.devbaseignore` na raiz do workspace para excluir diretórios:

```
# Comentários começam com #

# Projetos legados (.NET com PascalCase)
**/MedSempreMVC*
**/Controllers
**/Models
**/Views

# Worktrees
23_worktrees

# Padrões glob
**/src
**/tests
```

**Padrões suportados:**

| Padrão | Exemplo | Match |
|--------|---------|-------|
| Nome exato | `MyProject` | Qualquer pasta com esse nome |
| Glob simples | `*.Tests` | Pastas terminando em `.Tests` |
| Glob recursivo | `**/bin` | `bin` em qualquer nível |
| Caminho | `20-29_CODE/legacy` | Caminho específico |

**Built-in ignores** (não precisa adicionar):
- `node_modules`, `.git`, `__pycache__`
- `bin`, `obj`, `packages`, `vendor`
- `.vs`, `.vscode`, `.idea`, `.gradle`
- `dist`, `build`, `target`, `out`

## Ver também

- [doctor](doctor.md) - Verificação completa do workspace
