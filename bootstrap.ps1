<#
.SYNOPSIS
    DevBase Bootstrap Shim (Legacy Redirect)
.DESCRIPTION
    Redirects execution to powershell/bootstrap.ps1
#>

$Target = Join-Path $PSScriptRoot "powershell/bootstrap.ps1"

if (-not (Test-Path $Target)) {
    Write-Error "Could not find bootstrap script at $Target"
    exit 1
}

# Forward execution with all arguments
& $Target @args
