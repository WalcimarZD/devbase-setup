<#
.SYNOPSIS
    DevBase v3.1 - Operations Module
.DESCRIPTION
    Creates the operations area, including the DevBase CLI, automation scripts, and Telemetry.
#>

function Setup-Operations {
<#
.SYNOPSIS
    Sets up the operations directory structure, CLI, and automation scripts.
.PARAMETER RootPath
    The root path of the DevBase workspace.
#>
    param([string]$RootPath)

    $Area30 = Join-Path $RootPath "30-39_OPERATIONS"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates/operations"

    # Main structure
    New-DirSafe -Path $Area30
    $backupsPath = Join-Path $Area30 "31_backups"
    New-DirSafe -Path $backupsPath
    New-DirSafe -Path (Join-Path $backupsPath "local")
    New-DirSafe -Path (Join-Path $backupsPath "cloud")
    $automationPath = Join-Path $Area30 "32_automation"
    New-DirSafe -Path $automationPath
    New-DirSafe -Path (Join-Path $Area30 "33_monitoring") # Monitoring/Telemetry (v3.1)
    $credentialsPath = Join-Path $Area30 "34_credentials"
    New-DirSafe -Path $credentialsPath
    $cliPath = Join-Path $Area30 "35_devbase_cli"
    New-DirSafe -Path $cliPath

    # === TEMPLATE PUBLISHING LOGIC ===
    # Copia templates genéricos de operações
    $templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse

    foreach ($templateFile in $templateFiles) {
        $content = Get-Content -Path $templateFile.FullName -Raw

        $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)
        $destinationFileName = $templateFile.Name.Replace(".template", "")

        $destinationDir = Join-Path $Area30 (Split-Path $relativeSourcePath -Parent)
        $destinationPath = Join-Path $destinationDir $destinationFileName

        if (-not (Test-Path $destinationDir)) {
            New-DirSafe -Path $destinationDir
        }

        New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
    }

    # === DEVBASE CLI MAIN SCRIPTS ===
    # Instala o devbase.ps1 e as novas ferramentas de telemetria da v3.1
    # Nota: Assume que os assets existem na pasta modules/assets/

    $cliTools = @(
        "devbase.ps1",
        "telemetry.ps1",      # Novo na v3.1
        "observability.ps1",  # Novo na v3.1
        "fs_performance.ps1"  # Novo na v3.1
    )

    foreach ($tool in $cliTools) {
        $assetPath = Join-Path $PSScriptRoot "assets/$tool.asset"
        if (Test-Path $assetPath) {
            $toolContent = Get-Content $assetPath -Raw
            New-FileSafe -Path (Join-Path $cliPath $tool) -Content $toolContent -UpdateIfExists
        } else {
            # Opcional: Avisar se um asset esperado não for encontrado
            # Write-Step "Asset não encontrado: $assetPath" "WARN"
        }
    }

	$libsToCopy = @(
			"common-functions.ps1",
			"cli-functions.ps1",
			"detect-language.ps1"
		)

		foreach ($lib in $libsToCopy) {
			# Procura na mesma pasta do script (modules)
			$srcPath = Join-Path $PSScriptRoot $lib
			$destPath = Join-Path $cliPath $lib

			if (Test-Path $srcPath) {
				Copy-Item -Path $srcPath -Destination $destPath -Force
				Write-Step "Biblioteca instalada: $lib" "OK"
			} else {
				Write-Step "ERRO CRÍTICO: Biblioteca '$lib' não encontrada na origem!" "ERROR"
			}
		}
	}
