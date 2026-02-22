# DevBase bash completion
# Install: eval "$(register-python-argcomplete devbase)"
# Or add to ~/.bashrc: source /path/to/devbase.bash

_devbase_complete() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    commands="setup doctor audit new hydrate backup clean track stats weekly"
    
    # Global options
    opts="--root --no-color --dry-run --help"
    
    # Handle command-specific options
    case "${prev}" in
        setup|hydrate)
            COMPREPLY=($(compgen -W "--force --root --no-color --dry-run" -- ${cur}))
            return 0
            ;;
        audit)
            COMPREPLY=($(compgen -W "--fix --root --no-color --dry-run" -- ${cur}))
            return 0
            ;;
        new)
            COMPREPLY=($(compgen -W "--root --no-color --dry-run" -- ${cur}))
            return 0
            ;;
        track)
            COMPREPLY=($(compgen -W "--type --root --no-color" -- ${cur}))
            return 0
            ;;
        weekly)
            COMPREPLY=($(compgen -W "--output -o --root --no-color" -- ${cur}))
            return 0
            ;;
        --root)
            COMPREPLY=($(compgen -d -- ${cur}))
            return 0
            ;;
        --type)
            COMPREPLY=($(compgen -W "work meeting learning review bugfix feature" -- ${cur}))
            return 0
            ;;
        devbase)
            COMPREPLY=($(compgen -W "${commands} ${opts}" -- ${cur}))
            return 0
            ;;
    esac

    # Default: complete commands and options
    if [[ ${cur} == -* ]]; then
        COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
    else
        COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
    fi
}

complete -F _devbase_complete devbase
complete -F _devbase_complete devbase.py
