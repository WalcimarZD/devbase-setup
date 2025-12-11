# DevBase PowerShell completion
# Install: Import-Module /path/to/_devbase.ps1
# Or add to $PROFILE

Register-ArgumentCompleter -Native -CommandName devbase, devbase.py -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $commands = @(
        'setup', 'doctor', 'audit', 'new', 'hydrate', 
        'backup', 'clean', 'track', 'stats', 'weekly'
    )
    
    $globalOptions = @(
        '--root', '--no-color', '--dry-run', '--help'
    )
    
    $commandOptions = @{
        'setup'   = @('--force')
        'hydrate' = @('--force')
        'audit'   = @('--fix')
        'track'   = @('--type')
        'weekly'  = @('--output', '-o')
    }
    
    $elements = $commandAst.CommandElements
    $command = $null
    
    # Find the subcommand
    foreach ($elem in $elements) {
        if ($commands -contains $elem.ToString()) {
            $command = $elem.ToString()
            break
        }
    }
    
    # Determine what to complete
    if ($wordToComplete.StartsWith('-')) {
        # Complete options
        $opts = $globalOptions
        if ($command -and $commandOptions.ContainsKey($command)) {
            $opts += $commandOptions[$command]
        }
        $opts | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
        }
    }
    elseif (-not $command) {
        # Complete commands
        $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'Command', $_)
        }
    }
}
