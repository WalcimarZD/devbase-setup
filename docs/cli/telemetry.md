# Comandos de Telemetria

Os comandos de telemetria permitem rastrear suas atividades e gerar relatórios.

## track

Registra uma atividade.

### Uso

```bash
devbase track "<message>" [options]
```

### Opções

| Opção | Descrição | Default |
|-------|-----------|---------|
| `--type <type>` | Tipo do evento | `work` |
| `--root <path>` | Caminho para o workspace | Auto |

### Tipos de Evento

| Tipo | Descrição |
|------|-----------|
| `work` | Trabalho geral |
| `meeting` | Reuniões |
| `learning` | Estudo e aprendizado |
| `review` | Code review |
| `bugfix` | Correção de bugs |
| `feature` | Nova funcionalidade |

### Exemplos

```bash
# Registrar trabalho
devbase track "Implementei autenticação OAuth2"

# Com tipo específico
devbase track "Corrigi bug de login" --type bugfix

# Reunião
devbase track "Daily standup" --type meeting
```

---

## stats

Mostra estatísticas de uso.

### Uso

```bash
devbase stats [options]
```

### Exemplo de Saída

```
========================================
 DevBase Stats
========================================

Total events: 45

By type:
  work: 32
  meeting: 8
  bugfix: 3
  learning: 2

Recent activity:
  [2025-12-11] Implementei feature X
  [2025-12-10] Code review do PR #123
  [2025-12-10] Daily standup
  [2025-12-09] Corrigi bug de login
  [2025-12-09] Estudei Kubernetes
```

---

## weekly

Gera relatório semanal em Markdown.

### Uso

```bash
devbase weekly [options]
```

### Opções

| Opção | Descrição |
|-------|-----------|
| `--output <path>` | Salvar em arquivo |
| `--root <path>` | Caminho para o workspace |

### Exemplos

```bash
# Exibir no terminal
devbase weekly

# Salvar em arquivo
devbase weekly --output ~/weeknotes/semana-50.md
```

### Formato de Saída

```markdown
# Weekly Report

**Period**: 2025-12-04 to 2025-12-11
**Total activities**: 23

## Activities

- [2025-12-11] Implementei autenticação OAuth2
- [2025-12-10] Code review do PR #123
- [2025-12-10] Daily standup
...
```

---

## Armazenamento

Os eventos são salvos em `.telemetry/events.jsonl` no formato JSON Lines:

```json
{"timestamp": "2025-12-11T10:30:00", "type": "work", "message": "Implementei feature X"}
{"timestamp": "2025-12-11T11:00:00", "type": "meeting", "message": "Daily standup"}
```

## Ver também

- [doctor](doctor.md) - Verificar workspace
