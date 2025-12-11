# devbase new

Cria um novo projeto a partir do template Clean Architecture.

## Uso

```bash
devbase new <project-name> [options]
```

## Argumentos

| Argumento | Descrição |
|-----------|-----------|
| `project-name` | Nome do novo projeto (kebab-case recomendado) |

## Opções

| Opção | Descrição |
|-------|-----------|
| `--root <path>` | Caminho para o workspace |
| `--dry-run` | Mostra o que seria criado |
| `--no-color` | Desabilita saída colorida |

## Exemplos

```bash
# Criar projeto
devbase new minha-api

# Ver o que seria criado
devbase new meu-projeto --dry-run
```

## Template Usado

O projeto é criado a partir de `20-29_CODE/__template-clean-arch/` com a estrutura:

```
minha-api/
├── src/
│   ├── Domain/
│   ├── Application/
│   ├── Infrastructure/
│   └── WebApi/
├── tests/
│   ├── Unit/
│   └── Integration/
├── README.md
└── .gitignore
```

## Destino

Os projetos são criados em:

```
20-29_CODE/21_monorepo_apps/<project-name>/
```

## Ver também

- [setup](setup.md) - Garantir que o template existe
- [hydrate](hydrate.md) - Atualizar templates
