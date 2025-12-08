<#
.SYNOPSIS
    DevBase v3.0 - Templates Module
.DESCRIPTION
    Creates templates for technical standards, AI prompts, and workflows declaratively.
#>

function Setup-Templates {
<#
.SYNOPSIS
    Sets up the technical standards and templates directory.
.PARAMETER RootPath
    The root path of the DevBase workspace.
#>
    param([string]$RootPath)
    
    $SystemArea = Join-Path $RootPath "00-09_SYSTEM"
    $TemplatesDestDir = Join-Path $SystemArea "05_templates"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates"

    # Main folder structure
    New-DirSafe -Path $TemplatesDestDir
    New-DirSafe -Path (Join-Path $TemplatesDestDir "patterns")
    New-DirSafe -Path (Join-Path $TemplatesDestDir "prompts")
    New-DirSafe -Path (Join-Path $TemplatesDestDir "ci")

    # === TEMPLATE PUBLISHING LOGIC ===
    
   $templateSubDirs = @("patterns", "prompts", "core", "ci")
    
    foreach ($subDir in $templateSubDirs) {
        $subDirSource = Join-Path $templateSourceRoot $subDir
        if (-not (Test-Path $subDirSource)) { continue }
        
        $templateFiles = Get-ChildItem -Path $subDirSource -Filter "*.template" -Recurse
        
        foreach ($templateFile in $templateFiles) {
            $content = Get-Content -Path $templateFile.FullName -Raw
            
            # Determine destination path
            $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)
            $destinationFileName = $templateFile.Name.Replace(".template", "")
            $destinationDir = Join-Path $TemplatesDestDir (Split-Path $relativeSourcePath -Parent)
            $destinationPath = Join-Path $destinationDir $destinationFileName

            # Ensure destination directory exists
            if (-not (Test-Path $destinationDir)) {
                New-DirSafe -Path $destinationDir
            }
            
            New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
        }
    }
}
