<#
.SYNOPSIS
    Detects the programming language and stack of a project.
.DESCRIPTION
    Analyzes file indicators (package.json, pyproject.toml, etc.) to determine the stack.
    Returns a hashtable with stack details.
#>

function Get-ProjectStack {
    param(
        [Parameter(Mandatory)][string]$Path
    )

    $stack = @{
        Type = "generic"
        Name = "Unknown"
        PackageManager = $null
        ciTemplate = "ci-generic.yml.template"
    }

    if (-not (Test-Path $Path)) { return $stack }

    # 1. Node.js / TypeScript
    if (Test-Path (Join-Path $Path "package.json")) {
        $stack.Type = "node"
        $stack.Name = "Node.js"

        if (Test-Path (Join-Path $Path "pnpm-lock.yaml")) { $stack.PackageManager = "pnpm" }
        elseif (Test-Path (Join-Path $Path "yarn.lock")) { $stack.PackageManager = "yarn" }
        else { $stack.PackageManager = "npm" }

        $stack.ciTemplate = "ci-node.yml.template"
        return $stack
    }

    # 2. Python
    if ((Test-Path (Join-Path $Path "requirements.txt")) -or (Test-Path (Join-Path $Path "pyproject.toml"))) {
        $stack.Type = "python"
        $stack.Name = "Python"
        $stack.PackageManager = "pip"
        $stack.ciTemplate = "ci-python.yml.template"
        return $stack
    }

    # 3. .NET
    $csproj = Get-ChildItem -Path $Path -Filter "*.csproj" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($csproj) {
        $stack.Type = "dotnet"
        $stack.Name = ".NET"
        $stack.PackageManager = "nuget"
        $stack.ciTemplate = "ci-dotnet.yml.template"
        return $stack
    }

    # 4. Go (Golang)
    if (Test-Path (Join-Path $Path "go.mod")) {
        $stack.Type = "go"
        $stack.Name = "Go"
        $stack.PackageManager = "go mod"
        $stack.ciTemplate = "ci-go.yml.template" # Future use
        return $stack
    }

    return $stack
}
