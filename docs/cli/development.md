# devbase development

🛠️ Ferramentas para desenvolvimento de software e gerenciamento de projetos.

## Subcomandos

### `new`

Cria um novo projeto a partir de templates (Clean Architecture, etc).

```bash
devbase dev new my-api
```

Ver [devbase dev new](new.md) para detalhes.

### `blueprint`

Gera estrutura de arquivos de projeto usando IA, baseado em uma descrição textual.

```bash
devbase dev blueprint "Uma API REST em FastAPI com usuários e produtos"
```

A IA irá sugerir uma estrutura de pastas e arquivos. Você deve confirmar antes da criação.

### `adr-gen`

Gera um rascunho de Architecture Decision Record (ADR) baseado em eventos recentes de telemetria (decisões arquiteturais detectadas).

```bash
devbase dev adr-gen
```

### `worktree`

Gerenciamento simplificado de Git Worktrees.

*   `worktree-add <nome>`: Cria uma nova worktree isolada para uma feature.
    ```bash
    devbase dev worktree-add feat/login
    ```
*   `worktree-list`: Lista as worktrees ativas.
*   `worktree-remove <nome>`: Remove uma worktree.

### `audit`

Audita o projeto atual em busca de violações de convenção (ex: nomes de arquivos).

```bash
devbase dev audit
```
