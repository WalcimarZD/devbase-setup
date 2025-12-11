# DevBase VS Code Extension

A VS Code extension for integrating with DevBase - Personal Engineering Operating System.

## Features

- **🔍 Doctor Command**: Check workspace health directly from VS Code
- **📁 New Project**: Create new projects from templates via command palette
- **📝 Track Activity**: Record your work activities with quick picks
- **📊 Dashboard**: Open the telemetry dashboard in your browser
- **🌳 Structure View**: Navigate your Johnny.Decimal structure in the sidebar
- **📋 Recent Activity**: See your recent tracked activities
- **✂️ Snippets**: ADR, TIL, Journal, and Weeknotes templates

## Requirements

- Python 3.8+
- DevBase CLI (`devbase.py`)

## Installation

### From VSIX (Local)

1. Build the extension:
   ```bash
   npm install
   npm run compile
   npx vsce package
   ```

2. Install in VS Code:
   - Open Command Palette (Ctrl+Shift+P)
   - Run "Extensions: Install from VSIX..."
   - Select the generated `.vsix` file

### Configuration

In VS Code settings:

- `devbase.pythonPath`: Path to Python executable (default: `python`)
- `devbase.cliPath`: Path to `devbase.py` (auto-detected if empty)

## Usage

### Commands

All commands are available via Command Palette (Ctrl+Shift+P):

| Command | Description |
|---------|-------------|
| `DevBase: Doctor` | Check workspace health |
| `DevBase: New Project` | Create project from template |
| `DevBase: Track Activity` | Record work activity |
| `DevBase: Open Dashboard` | Open telemetry dashboard |
| `DevBase: Hydrate Templates` | Sync templates |

### Snippets

In Markdown files, type:

| Prefix | Template |
|--------|----------|
| `adr` | Architectural Decision Record |
| `til` | Today I Learned |
| `journal` | Daily journal entry |
| `weeknotes` | Weekly notes |
| `readme-project` | Project README |

## Development

```bash
# Install dependencies
npm install

# Compile
npm run compile

# Watch for changes
npm run watch

# Package
npx vsce package
```

## License

MIT
