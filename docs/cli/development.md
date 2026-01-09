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


## Auto-Detected Commands

### `import_project`
📥 Import an existing project (brownfield).

Clones a Git repository or copies a local project into the DevBase workspace.
Imported projects are marked as 'external' and exempt from governance rules.

Examples:
    devbase dev import https://github.com/user/repo.git
    devbase dev import https://github.com/user/dotnet-app.git --restore
    devbase dev import D:\Projects\legacy-app --name legacy
**Arguments/Flags:** ctx, source, name, restore

### `open_project`
💻 Open a project in VS Code.

Opens the project's .code-workspace file or folder in VS Code.
If no name is provided, an interactive list is shown.

Examples:
    devbase dev open MedSempreMVC_GIT
    devbase dev open
**Arguments/Flags:** ctx, project_name

### `restore_packages`
📦 Restore NuGet packages for a .NET project.

Downloads nuget.exe automatically if needed and runs restore.

Examples:
    devbase dev restore MedSempreMVC_GIT
    devbase dev restore MyProject --solution MyProject.Web.sln
**Arguments/Flags:** ctx, project_name, solution

### `info_project`
ℹ️ Show project details.

Displays template used, creation date, and metadata.
**Arguments/Flags:** ctx, project_name

### `list_projects`
📂 List all projects.

scans 20-29_CODE/21_monorepo_apps and displays a table of projects.
**Arguments/Flags:** ctx

### `archive`
📦 Archive a project.

Moves the project from 21_monorepo_apps to 90-99_ARCHIVE_COLD/92_archived_projects/{year}.
**Arguments/Flags:** ctx, name, confirm

### `update`
🔄 Update a project from its template.

Supports:
- Copier (preferred): Runs 'copier update'
- Legacy: Checks if hydration is possible (warns mainly)
**Arguments/Flags:** ctx, name

### `adr_gen`
👻 Ghostwrite an ADR from recent activity.

Analyses recent 'track' events or uses provided context to generate
an Architecture Decision Record (MADR format).
**Arguments/Flags:** ctx, context

### `worktree_add`
🌳 Create a new worktree for a project.

Creates a worktree in 22_worktrees/<project>-<branch> (default).

Examples:
    devbase dev worktree-add MedSempreMVC_GIT feature/nova-rotina
    devbase dev worktree-add MyProject feature/xyz --create
    devbase dev worktree-add MyProject feature/xyz --name "my-feature-xyz"
**Arguments/Flags:** ctx, project_name, branch, create, name

### `worktree_list`
🌳 List worktrees for a project or all projects.

Examples:
    devbase dev worktree-list
    devbase dev worktree-list MedSempreMVC_GIT
**Arguments/Flags:** ctx, project_name

### `worktree_remove`
🌳 Remove a worktree.

Examples:
    devbase dev worktree-remove MedSempreMVC_GIT--feature-xyz
    devbase dev worktree-remove MyProject--hotfix --force
**Arguments/Flags:** ctx, worktree_name, force
