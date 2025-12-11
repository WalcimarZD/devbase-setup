# devbase hydrate

Sincroniza o workspace com os templates mais recentes.

## Uso

```bash
devbase hydrate [options]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--force` | Sobrescreve todos os templates existentes |
| `--root <path>` | Caminho para o workspace |
| `--dry-run` | Mostra o que seria atualizado |
| `--no-color` | Desabilita saída colorida |

## Exemplos

```bash
# Atualizar templates (preserva existentes)
devbase hydrate

# Forçar atualização de tudo
devbase hydrate --force

# Ver o que seria atualizado
devbase hydrate --dry-run
```

## Módulos Atualizados

O hydrate processa os seguintes módulos:

| Módulo | O que atualiza |
|--------|----------------|
| Core | `.gitignore`, `.editorconfig`, estrutura base |
| PKM | Templates de ADR, TIL, Journal |
| Code | Template Clean Architecture |
| Operations | CLI scripts |

## Progress Bar

Com `tqdm` instalado, uma barra de progresso é exibida:

```
Hydrating modules: 100%|████████████| 4/4 [00:02<00:00, 1.50 modules/s]
```

## Quando usar

- Após atualizar o repositório DevBase (`git pull`)
- Para aplicar novos templates
- Para restaurar arquivos de governança

## Ver também

- [setup](setup.md) - Setup completo
- [doctor](doctor.md) - Verificar resultado
