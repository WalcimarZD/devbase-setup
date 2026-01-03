# devbase pkm

🧠 Personal Knowledge Management (PKM) commands.

Manage your knowledge graph, search notes, and analyze connections using DuckDB and NetworkX.

## Usage

```bash
devbase pkm <command> [options]
```

## Commands

### `find`

Fast search across your knowledge base using DuckDB Full-Text Search.

```bash
devbase pkm find [QUERY] [OPTIONS]
```

**Arguments:**
- `QUERY`: Text to search for in title and content.

**Options:**
- `--tag, -t <tag>`: Filter by tag(s). Can be used multiple times.
- `--type <type>`: Filter by note type (e.g., `til`, `adr`).
- `--reindex`: Force a full rebuild of the search index before searching.
- `--global, -g`: Include archived content (`90-99_ARCHIVE_COLD`) in search.

**Examples:**
```bash
# Search for 'python' in active notes
devbase pkm find python

# Search for notes tagged 'git' and 'cli'
devbase pkm find --tag git --tag cli

# Search including archives
devbase pkm find legacy-code --global
```

### `graph`

Visualize and analyze the knowledge graph structure.

```bash
devbase pkm graph [OPTIONS]
```

**Options:**
- `--export, -e`: Export the graph to Graphviz DOT format (`knowledge_graph.dot`).
- `--html`: Generate an interactive HTML visualization (`knowledge_graph.html`).
- `--global`: Include archived content in the graph.

**Metrics Displayed:**
- Total files, nodes, and links.
- Connection density.
- Hub notes (most connected).
- Orphan notes (isolated).

### `links`

Show incoming and outgoing connections for a specific note.

```bash
devbase pkm links <NOTE_PATH>
```

**Arguments:**
- `NOTE_PATH`: Path to the note (relative to `10-19_KNOWLEDGE`).

**Example:**
```bash
devbase pkm links til/2025-12-22-typer-context.md
```

### `index`

Generate a Map of Content (MOC) / Index for a folder.

```bash
devbase pkm index <FOLDER>
```

Creates an `_index.md` file in the target folder with a chronological list of notes and a tag cloud.

**Arguments:**
- `FOLDER`: Subfolder within `10-19_KNOWLEDGE/11_public_garden`.

**Example:**
```bash
devbase pkm index til
```

### `new`

Create a new structured note and queue it for AI classification.

```bash
devbase pkm new <NAME> [OPTIONS]
```

**Arguments:**
- `NAME`: Name of the note (will be slugified).

**Options:**
- `--type, -t <type>`: Diataxis type (`tutorial`, `how-to`, `reference`, `explanation`, `daily`, `meeting`).

**Example:**
```bash
devbase pkm new my-new-concept --type explanation
```
