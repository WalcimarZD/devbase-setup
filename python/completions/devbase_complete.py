#!/usr/bin/env python3
"""
DevBase CLI Shell Completions
================================================================
PROPÓSITO:
    Fornece autocompletion para o CLI DevBase em Bash, Zsh e Fish.
    Usa argcomplete para integração nativa com argparse.

INSTALAÇÃO:
    Bash:
        eval "$(register-python-argcomplete devbase)"

    Zsh:
        autoload -U bashcompinit
        bashcompinit
        eval "$(register-python-argcomplete devbase)"

    Fish:
        register-python-argcomplete --shell fish devbase | source

    Global (ativa para todos os scripts com argcomplete):
        activate-global-python-argcomplete

REQUISITOS:
    pip install argcomplete

Autor: DevBase Team
Versão: 3.2.0
"""

# Lista de comandos disponíveis no DevBase CLI
COMMANDS = [
    'setup',
    'doctor',
    'audit',
    'new',
    'hydrate',
    'backup',
    'clean',
    'track',
    'stats',
    'weekly',
    'dashboard',
    'ai',
]

# Opções globais (aplicam a todos os comandos)
GLOBAL_OPTIONS = [
    '--root',
    '--no-color',
    '--dry-run',
    '--help',
    '-h',
]

# Opções específicas por comando
COMMAND_OPTIONS = {
    'setup': ['--force'],
    'hydrate': ['--force'],
    'audit': ['--fix'],
    'track': ['--type', '--message', '-m'],
    'weekly': ['--output', '-o'],
    'dashboard': ['--port', '--no-browser'],
    'ai': ['--model', 'chat', 'summarize', 'explain', 'adr', 'til'],
    'new': [],  # Positional argument (project name)
}


def get_completions():
    """Retorna estrutura de completions para uso externo."""
    return {
        'commands': COMMANDS,
        'global_options': GLOBAL_OPTIONS,
        'command_options': COMMAND_OPTIONS,
    }


def setup_argcomplete(parser):
    """
    Configura argcomplete para o parser argparse.

    Args:
        parser: Instância do argparse.ArgumentParser

    Example:
        >>> import argparse
        >>> parser = argparse.ArgumentParser()
        >>> setup_argcomplete(parser)
    """
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        # argcomplete não instalado - completions não funcionam
        pass


def generate_bash_completion():
    """Gera script de completion para Bash."""
    script = '''
# DevBase Bash Completion
# Add to ~/.bashrc or /etc/bash_completion.d/devbase

_devbase_completions() {
    local cur prev commands opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    commands="setup doctor audit new hydrate backup clean track stats weekly dashboard ai"
    global_opts="--root --no-color --dry-run --help"
    
    # Command-specific options
    case "${prev}" in
        setup|hydrate)
            opts="--force ${global_opts}"
            ;;
        audit)
            opts="--fix ${global_opts}"
            ;;
        track)
            opts="--type --message -m ${global_opts}"
            ;;
        weekly)
            opts="--output -o ${global_opts}"
            ;;
        dashboard)
            opts="--port --no-browser ${global_opts}"
            ;;
        ai)
            opts="chat summarize explain adr til --model ${global_opts}"
            ;;
        *)
            opts="${global_opts}"
            ;;
    esac
    
    # Determine what to complete
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    elif [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
    fi
    
    return 0
}

complete -F _devbase_completions devbase
complete -F _devbase_completions devbase.py
complete -F _devbase_completions python\ devbase.py
'''
    return script.strip()


def generate_zsh_completion():
    """Gera script de completion para Zsh."""
    script = '''
#compdef devbase devbase.py

# DevBase Zsh Completion
# Add to ~/.zshrc or /usr/share/zsh/site-functions/_devbase

_devbase() {
    local -a commands
    local -a global_opts

    commands=(
        'setup:Initialize or update DevBase workspace'
        'doctor:Verify workspace integrity'
        'audit:Audit naming conventions (kebab-case)'
        'new:Create new project from template'
        'hydrate:Update all templates'
        'backup:Execute 3-2-1 backup strategy'
        'clean:Remove temporary files'
        'track:Log activity for telemetry'
        'stats:Show usage statistics'
        'weekly:Generate weekly report'
        'dashboard:Open telemetry dashboard'
        'ai:Local AI assistant'
    )

    global_opts=(
        '--root[Root path for workspace]:path:_files -/'
        '--no-color[Disable colored output]'
        '--dry-run[Show what would be done]'
        '--help[Show help]'
    )

    _arguments -C \\
        $global_opts \\
        '1:command:->command' \\
        '*::arg:->args'

    case "$state" in
        command)
            _describe -t commands 'devbase commands' commands
            ;;
        args)
            case $words[1] in
                setup|hydrate)
                    _arguments '--force[Force overwrite templates]'
                    ;;
                audit)
                    _arguments '--fix[Auto-fix naming violations]'
                    ;;
                track)
                    _arguments \\
                        '--type[Event type]:type:(work learn break)' \\
                        '--message[Activity message]:message:'
                    ;;
                weekly)
                    _arguments '--output[Output file]:file:_files'
                    ;;
                dashboard)
                    _arguments \\
                        '--port[Server port]:port:' \\
                        '--no-browser[Do not open browser]'
                    ;;
                ai)
                    _arguments \\
                        '1:subcommand:(chat summarize explain adr til)' \\
                        '--model[AI model]:model:'
                    ;;
                new)
                    _arguments '1:project name:'
                    ;;
            esac
            ;;
    esac
}

_devbase "$@"
'''
    return script.strip()


def generate_fish_completion():
    """Gera script de completion para Fish shell."""
    script = '''
# DevBase Fish Completion
# Add to ~/.config/fish/completions/devbase.fish

# Disable file completions for devbase
complete -c devbase -f
complete -c devbase.py -f

# Commands
complete -c devbase -n '__fish_use_subcommand' -a 'setup' -d 'Initialize or update DevBase workspace'
complete -c devbase -n '__fish_use_subcommand' -a 'doctor' -d 'Verify workspace integrity'
complete -c devbase -n '__fish_use_subcommand' -a 'audit' -d 'Audit naming conventions'
complete -c devbase -n '__fish_use_subcommand' -a 'new' -d 'Create new project from template'
complete -c devbase -n '__fish_use_subcommand' -a 'hydrate' -d 'Update all templates'
complete -c devbase -n '__fish_use_subcommand' -a 'backup' -d 'Execute 3-2-1 backup'
complete -c devbase -n '__fish_use_subcommand' -a 'clean' -d 'Remove temporary files'
complete -c devbase -n '__fish_use_subcommand' -a 'track' -d 'Log activity'
complete -c devbase -n '__fish_use_subcommand' -a 'stats' -d 'Show statistics'
complete -c devbase -n '__fish_use_subcommand' -a 'weekly' -d 'Generate weekly report'
complete -c devbase -n '__fish_use_subcommand' -a 'dashboard' -d 'Open dashboard'
complete -c devbase -n '__fish_use_subcommand' -a 'ai' -d 'AI assistant'

# Global options
complete -c devbase -l root -d 'Workspace root path' -r
complete -c devbase -l no-color -d 'Disable colors'
complete -c devbase -l dry-run -d 'Show what would be done'
complete -c devbase -l help -s h -d 'Show help'

# Command-specific options
complete -c devbase -n '__fish_seen_subcommand_from setup hydrate' -l force -d 'Force overwrite'
complete -c devbase -n '__fish_seen_subcommand_from audit' -l fix -d 'Auto-fix violations'
complete -c devbase -n '__fish_seen_subcommand_from track' -l type -d 'Event type' -r
complete -c devbase -n '__fish_seen_subcommand_from track' -l message -s m -d 'Message' -r
complete -c devbase -n '__fish_seen_subcommand_from weekly' -l output -s o -d 'Output file' -r
complete -c devbase -n '__fish_seen_subcommand_from dashboard' -l port -d 'Server port' -r
complete -c devbase -n '__fish_seen_subcommand_from dashboard' -l no-browser -d 'No browser'
complete -c devbase -n '__fish_seen_subcommand_from ai' -l model -d 'AI model' -r

# AI subcommands
complete -c devbase -n '__fish_seen_subcommand_from ai' -a 'chat summarize explain adr til'
'''
    return script.strip()


def generate_powershell_completion():
    """Gera script de completion para PowerShell."""
    script = '''
# DevBase PowerShell Completion
# Add to your $PROFILE

Register-ArgumentCompleter -Native -CommandName devbase, devbase.py, python -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $commands = @(
        'setup', 'doctor', 'audit', 'new', 'hydrate', 
        'backup', 'clean', 'track', 'stats', 'weekly',
        'dashboard', 'ai'
    )
    
    $globalOptions = @(
        '--root', '--no-color', '--dry-run', '--help', '-h'
    )
    
    $commandOptions = @{
        'setup'     = @('--force')
        'hydrate'   = @('--force')
        'audit'     = @('--fix')
        'track'     = @('--type', '--message', '-m')
        'weekly'    = @('--output', '-o')
        'dashboard' = @('--port', '--no-browser')
        'ai'        = @('--model', 'chat', 'summarize', 'explain', 'adr', 'til')
    }
    
    $elements = $commandAst.CommandElements
    $command = $null
    
    foreach ($elem in $elements) {
        if ($commands -contains $elem.ToString()) {
            $command = $elem.ToString()
            break
        }
    }
    
    if ($wordToComplete.StartsWith('-')) {
        $opts = $globalOptions
        if ($command -and $commandOptions.ContainsKey($command)) {
            $opts += $commandOptions[$command]
        }
        $opts | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
        }
    }
    elseif (-not $command) {
        $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'Command', $_)
        }
    }
}
'''
    return script.strip()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python devbase_complete.py [bash|zsh|fish|powershell]")
        print("\nGenerates shell completion scripts for DevBase CLI.")
        sys.exit(1)

    shell = sys.argv[1].lower()
    
    generators = {
        'bash': generate_bash_completion,
        'zsh': generate_zsh_completion,
        'fish': generate_fish_completion,
        'powershell': generate_powershell_completion,
        'pwsh': generate_powershell_completion,
    }

    if shell in generators:
        print(generators[shell]())
    else:
        print(f"Unknown shell: {shell}")
        print(f"Supported shells: {', '.join(generators.keys())}")
        sys.exit(1)
