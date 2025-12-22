# 🚀 quickstart

> **Golden Path** — Projeto pronto para produção em menos de 60 segundos.

## Uso

```bash
devbase quick quickstart <nome> [--template <template>]
```

## O Que Faz?

Este é o comando "tudo em um" para criar projetos. Ele executa automaticamente:

1. ✅ Gera projeto a partir do template
2. ✅ Inicializa repositório Git
3. ✅ Instala dependências (via uv)
4. ✅ Abre no VS Code

## Exemplos

```bash
# Criar projeto com template padrão (clean-arch)
devbase quick quickstart minha-api

# Especificar template
devbase quick quickstart meu-cli --template cli

# Criar biblioteca compartilhada
devbase quick quickstart utils-lib --template package
```

## Templates Disponíveis

| Template | Descrição |
|----------|-----------|
| `clean-arch` | API Python com Clean Architecture (padrão) |
| `cli` | CLI com Typer + Rich |
| `package` | Biblioteca Python para pypi |
| `fastapi` | API REST com FastAPI |
| `minimal` | Estrutura mínima |

## Fluxo Visual

```mermaid
flowchart LR
    A[devbase quick quickstart] --> B[Gera Template]
    B --> C[git init]
    C --> D[uv sync]
    D --> E[code .]
    E --> F[🎉 Pronto!]
```

## Diferença para `devbase dev new`

| Aspecto | `dev new` | `quick quickstart` |
|---------|-----------|-------------------|
| Git init | ❌ Manual | ✅ Automático |
| Instalar deps | ❌ Manual | ✅ Automático |
| Abrir VS Code | ❌ Manual | ✅ Automático |
| Interativo | ✅ Sim | ❌ Não |

Use `dev new` quando quiser personalizar. Use `quickstart` quando quiser velocidade.

## Veja Também

- [dev new](new.md) — Criação interativa de projetos
- [Primeiro Projeto](../tutorials/first-project.md) — Tutorial completo
