# devbase ai

🧠 AI-powered features for classification, summarization, and chat.

## Overview

The `ai` command group provides access to AI capabilities powered by Groq's ultra-fast inference API. Features include:

- **Interactive chat** with LLMs
- **Text classification** into custom categories
- **Smart summarization** of long content
- **Background worker** for async task processing

## Prerequisites

Set your Groq API key:

```bash
export GROQ_API_KEY="your-api-key-here"
```

Get a free API key at [console.groq.com](https://console.groq.com)

## Commands

### `devbase ai chat`

💬 Send a prompt and get an AI response.

```bash
devbase ai chat "Explain SOLID principles briefly"
devbase ai chat "Suggest a project name" --temperature 1.0
```

**Options:**
- `--model, -m`: Model to use (default: llama-3.1-8b-instant)
- `--temperature, -t`: Creativity level 0.0-2.0 (default: 0.7)

### `devbase ai classify`

🏷️ Classify text into one of your categories.

```bash
devbase ai classify "Fix login button not working" -c "bug,feature,docs"
devbase ai classify "Add dark mode support"
```

**Options:**
- `--categories, -c`: Comma-separated list (default: feature,bug,docs,chore,refactor)

### `devbase ai summarize`

📝 Create a concise summary of text.

```bash
devbase ai summarize "Long article text here..." --max-length 50
```

**Options:**
- `--max-length, -l`: Maximum words (default: 50)

### `devbase ai status`

📊 Check AI worker status and queue statistics.

```bash
devbase ai status
```

Shows:
- Worker running state
- Pending/processing/done/failed task counts

### `devbase ai start`

🚀 Manually start the background AI worker.

```bash
devbase ai start
```

## Background Worker

The AI worker processes queued tasks asynchronously. Tasks are stored in DuckDB and processed by a daemon thread.

### Task Types

| Type | Description |
|------|-------------|
| `classify` | Categorize content |
| `summarize` | Generate summary |
| `synthesize` | Generate new content |

### Enqueue Tasks Programmatically

```python
from devbase.adapters.storage.duckdb_adapter import enqueue_ai_task

task_id = enqueue_ai_task(
    "classify",
    '{"content": "Fix bug", "categories": ["bug", "feature"]}'
)
```

## Configuration

Enable auto-start of AI worker in config:

```bash
devbase config set ai.enabled true
```

## Models

Default model: `llama-3.1-8b-instant` (optimized for speed)

Available Groq models:
- `llama-3.1-8b-instant` - Fast, good for most tasks
- `llama-3.1-70b-versatile` - More capable, slower
- `mixtral-8x7b-32768` - Large context window
