# ⚡ Quick Start

Este guia mostra os comandos mais comuns do DevBase para você começar rapidamente.

## Fluxo de Trabalho Típico

### 1. Verificar Saúde do Workspace

```bash
devbase doctor
```

Isso verifica se todas as áreas e arquivos de governança existem.

### 2. Criar um Novo Projeto

```bash
devbase new meu-projeto
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
devbase track "Implementei autenticação OAuth2"

# Com tipo personalizado
devbase track "Corrigi bug de login" --type bugfix
```

### 5. Ver Estatísticas

```bash
devbase stats
```

### 6. Gerar Relatório Semanal

```bash
devbase weekly

# Ou salvar em arquivo
devbase weekly --output ~/weeknotes.md
```

### 7. Fazer Backup

```bash
devbase backup
```

## Comandos Mais Usados

| Comando | Descrição |
|---------|-----------|
| `devbase doctor` | Verifica integridade do workspace |
| `devbase new <nome>` | Cria novo projeto |
| `devbase track "msg"` | Registra atividade |
| `devbase stats` | Mostra estatísticas |
| `devbase backup` | Executa backup 3-2-1 |
| `devbase clean` | Limpa temporários |

## Dicas Pro

### Dry-Run Mode

Veja o que seria feito sem executar:

```bash
devbase clean --dry-run
devbase setup --dry-run
```

### Force Mode

Force atualização de templates:

```bash
devbase hydrate --force
```

### Audit e Fix

Verifique e corrija nomenclatura automaticamente:

```bash
devbase audit        # Apenas verifica
devbase audit --fix  # Corrige automaticamente
```

## Próximos Passos

- [Structure](structure.md) - Entenda a organização Johnny.Decimal
- [CLI Reference](../cli/overview.md) - Documentação completa dos comandos
