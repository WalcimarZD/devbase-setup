# DevBase Python Version

A Python implementation of the DevBase Personal Engineering Operating System.

## Overview

This is the modern Python implementation of DevBase, providing a cross-platform CLI for managing your development workspace using the Johnny.Decimal methodology.

## Requirements

- Python 3.8+
- Git 2.9+ (for hooks support)

## Installation

```bash
# Clone the repository
git clone https://github.com/youruser/devbase-setup.git
cd devbase-setup/python

# Install dependencies
pip install -r requirements.txt

# Run setup
python devbase.py setup --root ~/Dev_Workspace
```

## Commands

| Command | Description |
|---------|-------------|
| `setup` | Initialize/update DevBase workspace |
| `doctor` | Verify workspace integrity |
| `new` | Create new project from template |
| `hydrate` | Update all templates |
| `audit` | Audit naming conventions |
| `backup` | Execute 3-2-1 backup strategy |
| `clean` | Remove temporary files |
| `track` | Log activity for telemetry |
| `stats` | Show usage statistics |
| `weekly` | Generate weekly report |
| `dashboard` | Open telemetry dashboard |
| `ai` | Local AI assistant (requires Ollama) |

## Project Structure

```
python/
├── devbase.py              # Main CLI entry point
├── modules/
│   ├── filesystem.py       # Safe filesystem operations
│   ├── ui.py               # Console output formatting
│   ├── state.py            # State management
│   ├── setup_core.py       # Core structure setup
│   ├── setup_code.py       # Code areas setup
│   ├── setup_pkm.py        # PKM areas setup
│   ├── setup_ai.py         # AI module setup
│   ├── setup_operations.py # Operations areas setup
│   ├── setup_hooks.py      # Git hooks setup
│   ├── setup_templates.py  # Templates setup
│   ├── detect_language.py  # Project stack detection
│   └── ai_assistant.py     # Ollama integration
├── tests/                  # Unit tests
├── requirements.txt
└── pyproject.toml
```

## Development

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=modules/python

# Lint
python -m flake8 modules/ devbase.py
```

## License

MIT License - See LICENSE file for details.
