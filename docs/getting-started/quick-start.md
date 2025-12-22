# ⚡ Quick Start

Este guia mostra os comandos mais comuns do DevBase para você começar rapidamente.

## Fluxo de Trabalho Típico

### 1. Verificar Saúde do Workspace

```bash
devbase core doctor
```

Isso verifica se todas as áreas e arquivos de governança existem.

### 2. Criar um Novo Projeto

```bash
devbase dev new meu-projeto
```

Cria um novo projeto em `20-29_CODE/21_monorepo_apps/meu-projeto` usando o template Clean Architecture.

### 3. Trabalhar no Projeto

```bash
cd 20-29_CODE/21_monorepo_apps/meu-projeto
# ... edite os arquivos, faça commits ...
```

### 4. Registrar Atividades

```bash
# Ao terminar uma tarefa
devbase ops track "Implementei autenticação OAuth2"

# Com tipo personalizado
devbase ops track "Corrigi bug de login" --type bugfix
```

### 5. Ver Estatísticas

```bash
devbase ops stats
```

### 6. Gerar Relatório Semanal

```bash
devbase ops weekly

# Ou salvar em arquivo
devbase ops weekly --output ~/weeknotes.md
```

### 7. Fazer Backup

```bash
devbase ops backup
```

## Comandos Mais Usados

| Comando | Descrição |
|---------|-----------|
| `devbase core doctor` | Verifica integridade do workspace |
| `devbase dev new <nome>` | Cria novo projeto |
| `devbase ops track "msg"` | Registra atividade |
| `devbase ops stats` | Mostra estatísticas |
| `devbase ops backup` | Executa backup 3-2-1 |
| `devbase ops clean` | Limpa temporários |

## Dicas Pro

### Dry-Run Mode

Veja o que seria feito sem executar:

```bash
devbase ops clean --dry-run
devbase core setup --dry-run
```

### Force Mode

Force atualização de templates:

```bash
devbase core hydrate --force
```

### Audit e Fix

Verifique e corrija nomenclatura automaticamente:

```bash
devbase dev audit        # Apenas verifica
devbase dev audit --fix  # Corrige automaticamente
```

## Próximos Passos

- [Structure](structure.md) - Entenda a organização Johnny.Decimal
- [CLI Reference](../cli/overview.md) - Documentação completa dos comandos
