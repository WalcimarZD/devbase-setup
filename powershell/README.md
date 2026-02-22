# DevBase PowerShell Version

The original PowerShell implementation of DevBase Personal Engineering Operating System.

## Overview

This is the legacy PowerShell implementation of DevBase, primarily designed for Windows environments. For cross-platform usage, consider using the Python version.

## Requirements

- PowerShell 5.1+ (Windows) or PowerShell Core 7+ (cross-platform)
- Git 2.9+ (for hooks support)

## Installation

```powershell
# Clone the repository
git clone https://github.com/youruser/devbase-setup.git
cd devbase-setup/powershell

# Run bootstrap
.\bootstrap.ps1 -RootPath "$HOME\Dev_Workspace"
```

## Commands

The PowerShell version uses the `bootstrap.ps1` script as the main entry point.

### Parameters

| Parameter | Description |
|-----------|-------------|
| `-RootPath` | Custom workspace path (default: `$HOME\Dev_Workspace`) |
| `-Force` | Overwrite existing files |
| `-SkipStorageValidation` | Skip SSD/NVMe check |

## Modules

- `common-functions.ps1` - Shared utility functions
- `cli-functions.ps1` - CLI command implementations
- `setup-core.ps1` - Core structure creation
- `setup-code.ps1` - Code areas setup
- `setup-pkm.ps1` - PKM areas setup
- `setup-ai.ps1` - AI module setup
- `setup-operations.ps1` - Operations areas setup
- `setup-hooks.ps1` - Git hooks configuration
- `setup-templates.ps1` - Templates publishing
- `detect-language.ps1` - Project stack detection

## Shell Completion

```powershell
# Add to your $PROFILE
. (Join-Path $PSScriptRoot "completions\_devbase.ps1")
```

## Note

This version is maintained for backward compatibility with existing Windows workflows. New features are developed primarily in the Python version.

## License

MIT License - See LICENSE file for details.
