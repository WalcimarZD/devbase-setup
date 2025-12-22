# 📝 note

> **Captura Rápida** — Anote ideias e TILs em segundos, sem sair do flow.

## Uso

```bash
devbase quick note "<conteúdo>" [opções]
```

## Por Que Usar?

O template completo de TIL tem 27 linhas. Às vezes você só precisa anotar algo **agora**. Este comando cria uma nota mínima (7 linhas) para captura instantânea.

## Exemplos

```bash
# Captura básica
devbase quick note "Python f-strings suportam = para debug: f'{var=}'"

# Abrir no VS Code após criar
devbase quick note "Descobri que uv é 100x mais rápido" --edit

# Nota rápida (salva como TIL por padrão)
devbase quick note "Docker compose watch é game changer" --til
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--edit`, `-e` | Abre no VS Code após criar |
| `--til`, `-t` | Salva como TIL (padrão: true) |

## Onde as Notas São Salvas?

As notas são salvas em:

```
~/Dev_Workspace/10-19_KNOWLEDGE/11_public_garden/til/
└── YYYY-MM-DD-seu-titulo.md
```

## Template Gerado

```markdown
---
date: 2025-12-22
tags: [til]
---

# Seu Conteúdo Aqui

Capturado via `devbase quick note`
```

## Veja Também

- [PKM Graph](pkm-graph.md) — Visualize conexões entre notas
- [Fluxo de Conhecimento](../concepts/pkm-philosophy.md)
