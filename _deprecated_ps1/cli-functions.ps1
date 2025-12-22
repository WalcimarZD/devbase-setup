# Este arquivo contém as implementações de função para a DevBase CLI.
# Ele é separado do script principal para permitir testes de unidade mais fáceis.

# ============================================
# FUNÇÕES DE COMANDO
# ============================================

# === COMANDO: HYDRATE ===
function Invoke-Hydrate {
    param([string]$DevBaseRoot, [switch]$Force)
    Write-Header "DevBase Hydrate"
    Write-Host "Sincronizando workspace com os templates mais recentes..." -ForegroundColor $script:ColorInfo
    if ($Force) {
        Write-Host "Modo Forçado: Todos os arquivos de template serão sobreescritos, independentemente da data." -ForegroundColor $script:ColorWarning
    }

    $modulesDir = Join-Path $DevBaseRoot "modules"

    try {
        . (Join-Path $modulesDir "setup-core.ps1")
        Setup-Core -RootPath $DevBaseRoot -Force:$Force

        . (Join-Path $modulesDir "setup-pkm.ps1")
        Setup-PKM -RootPath $DevBaseRoot -Force:$Force

        . (Join-Path $modulesDir "setup-code.ps1")
        Setup-Code -RootPath $DevBaseRoot -Force:$Force

        . (Join-Path $modulesDir "setup-operations.ps1")
        Setup-Operations -RootPath $DevBaseRoot -Force:$Force

        . (Join-Path $modulesDir "setup-templates.ps1")
        Setup-Templates -RootPath $DevBaseRoot -Force:$Force

        . (Join-Path $modulesDir "setup-hooks.ps1")
        Setup-Hooks -RootPath $DevBaseRoot -Force:$Force

        Write-Host "`n✅ Hidratação concluída." -ForegroundColor $script:ColorSuccess
    } catch {
        Write-Step "Ocorreu um erro durante a hidratação: $_" "ERROR"
    }
}

# === COMANDO: LINK-DOTFILES ===
function Invoke-LinkDotfiles {
    param([string]$DevBaseRoot)
    Write-Header "DevBase Link Dotfiles"

    $sourceDir = Join-Path $DevBaseRoot "00-09_SYSTEM/01_dotfiles/links"
    $targetDir = $HOME

    if (-not (Test-Path $sourceDir)) {
        Write-Step "Diretório de origem para links não encontrado: $sourceDir" "WARN"
        return
    }

    $dotfiles = Get-ChildItem -Path $sourceDir -File
    if ($dotfiles.Count -eq 0) {
        Write-Step "Nenhum dotfile encontrado em $sourceDir para vincular." "INFO"
        return
    }

    Write-Host "Vinculando dotfiles de '$sourceDir' para '$targetDir'..." -ForegroundColor $script:ColorInfo

    foreach ($file in $dotfiles) {
        $sourceFile = $file.FullName
        $targetFile = Join-Path $targetDir $file.Name

        try {
            if (Test-Path $targetFile -PathType Container) {
                 Write-Step "Um diretório com o mesmo nome já existe em '$targetFile'. Pulando." "WARN"
                 continue
            }
            if (Test-Path $targetFile) {
                $backupPath = "$targetFile.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"
                Write-Step "Arquivo existente encontrado em '$targetFile'. Fazendo backup para '$backupPath'..." "WARN"
                Move-Item -Path $targetFile -Destination $backupPath -Force
            }

            New-Item -ItemType SymbolicLink -Path $targetFile -Value $sourceFile -Force
            Write-Step "Link criado: '$targetFile' -> '$sourceFile'" "OK"

        } catch {
            Write-Step "Falha ao criar link para '$($file.Name)': $_" "ERROR"
        }
    }
    Write-Host "`nVinculação de dotfiles concluída." -ForegroundColor $script:ColorSuccess
}

# === COMANDO: NEW ===
function Invoke-NewProject {
    param([string]$ProjectName, [string]$DevBaseRoot)
    Write-Header "DevBase New Project"

    if (-not $ProjectName) {
        $ProjectName = Read-Host "Digite o nome para o novo projeto (ex: my-cool-app)"
        if (-not $ProjectName) {
            Write-Step "Nome do projeto não pode ser vazio." "ERROR"
            return
        }
    }

    $templateName = "__template-clean-arch"
    $sourcePath = Join-Path $DevBaseRoot "20-29_CODE" $templateName
    $destinationPath = Join-Path $DevBaseRoot "20-29_CODE/21_monorepo_apps" $ProjectName

    if (-not (Test-Path $sourcePath)) {
        Write-Step "Diretório de template '$templateName' não encontrado." "ERROR"
        return
    }

    if (Test-Path $destinationPath) {
        Write-Step "O projeto '$ProjectName' já existe no destino." "ERROR"
        return
    }

    Write-Host "Criando projeto '$ProjectName' a partir do template '$templateName'..." -ForegroundColor $script:ColorInfo

    try {
        Copy-Item -Path $sourcePath -Destination $destinationPath -Recurse -Force
        Write-Step "Projeto '$ProjectName' criado com sucesso em:" "OK"
        Write-Host $destinationPath -ForegroundColor Gray
    } catch {
        Write-Step "Falha ao criar o projeto: $_" "ERROR"
    }
}

# === COMANDO: DOCTOR ===
function Invoke-Doctor {
    param([string]$DevBaseRoot)
    Write-Header "DevBase Doctor"
    Write-Host "Verificando integridade do DevBase em: $DevBaseRoot`n" -ForegroundColor $script:ColorInfo

    $issues = 0

    $requiredAreas = @(
        '00-09_SYSTEM',
        '10-19_KNOWLEDGE',
        '20-29_CODE',
        '30-39_OPERATIONS',
        '40-49_MEDIA_ASSETS',
        '90-99_ARCHIVE_COLD'
    )

    foreach ($area in $requiredAreas) {
        $path = Join-Path $DevBaseRoot $area
        if (Test-Path $path) {
            Write-Step "$area" "OK"
        } else {
            Write-Step "$area - NÃO ENCONTRADO" "ERROR"
            $issues++
        }
    }

    $requiredFiles = @(
        '.editorconfig',
        '.gitignore',
        '00.00_index.md',
        '.devbase_state.json'
    )

    foreach ($file in $requiredFiles) {
        $path = Join-Path $DevBaseRoot $file
        if (Test-Path $path) {
            Write-Step "$file" "OK"
        } else {
            Write-Step "$file - NÃO ENCONTRADO" "WARN"
            $issues++
        }
    }

    $privatePath = Join-Path $DevBaseRoot '10-19_KNOWLEDGE/12_private_vault'
    $gitignorePath = Join-Path $DevBaseRoot '.gitignore'

    if (Test-Path $privatePath) {
        if (Test-Path $gitignorePath) {
            $gitignoreContent = Get-Content $gitignorePath -Raw
            if ($gitignoreContent -match '12_private_vault') {
                Write-Step "Private Vault está protegido no .gitignore" "OK"
            } else {
                Write-Step "Private Vault NÃO está no .gitignore!" "ERROR"
                $issues++
            }
        } else {
            Write-Step ".gitignore não encontrado" "WARN"
        }
    } else {
        Write-Step "Private Vault não existe" "INFO"
    }

    if (Get-Command git -ErrorAction SilentlyContinue) {
        $isGitRepo = git -C $DevBaseRoot rev-parse --is-inside-work-tree 2>$null
        if ($isGitRepo) {
            $hooksPath = (git -C $DevBaseRoot config core.hooksPath 2>$null).Replace('\', '/')
            $expectedPath = "00-09_SYSTEM/06_git_hooks"
            if ($hooksPath -eq $expectedPath) {
                Write-Step "Git Hooks configurados corretamente." "OK"
            } else {
                Write-Step "Git Hooks não configurados." "WARN"
            }
        } else {
            Write-Step "Diretório não é um repositório Git." "INFO"
        }
    } else {
        Write-Step "Git não encontrado." "INFO"
    }
}

# === COMANDO: AUDIT ===
function Invoke-Audit {
    param([string]$DevBaseRoot, [switch]$Fix)
    Write-Header "DevBase Audit"
    Write-Host "Auditando nomenclatura em: $DevBaseRoot`n" -ForegroundColor $script:ColorInfo

    $violations = @()

    # Allowed patterns
    $allowedPatterns = @(
        '^\d{2}(-\d{2})?_',
        '^[a-z0-9]+(-[a-z0-9]+)*$',
        '^\.',
        '^__',
        '^node_modules$',
        '^\.git$'
    )

    Get-ChildItem -Path $DevBaseRoot -Recurse -Directory | ForEach-Object {
        $name = $_.Name
        $isAllowed = $false

        foreach ($pattern in $allowedPatterns) {
            if ($name -match $pattern) {
                $isAllowed = $true
                break
            }
        }

        if (-not $isAllowed) {
            $violations += [PSCustomObject]@{
                Path = $_.FullName
                Name = $name
                Suggestion = ($name -replace '([a-z])([A-Z])', '$1-$2').ToLower() -replace '[_ ]', '-'
            }
        }
    }

    if ($violations.Count -eq 0) {
        Write-Step "Nenhuma violação encontrada" "OK"
    } else {
        Write-Host "Encontradas $($violations.Count) violações:`n" -ForegroundColor $script:ColorWarning

        $violations | ForEach-Object {
            Write-Host "  Current:     " -NoNewline -ForegroundColor $script:ColorError
            Write-Host $_.Name -ForegroundColor $script:ColorError
            Write-Host "  Suggested:  " -NoNewline -ForegroundColor $script:ColorSuccess
            Write-Host $_.Suggestion -ForegroundColor $script:ColorSuccess
            Write-Host "  Path:      $($_.Path)" -ForegroundColor Gray
            Write-Host ""
        }

        if ($Fix) {
            Write-Host "Aplicando correções..." -ForegroundColor $script:ColorInfo
            $violations | ForEach-Object {
                $newPath = Join-Path (Split-Path $_.Path -Parent) $_.Suggestion
                try {
                    Rename-Item -Path $_.Path -NewName $_.Suggestion -ErrorAction Stop
                    Write-Step "Renomeado: $($_.Name) -> $($_.Suggestion)" "OK"
                } catch {
                    Write-Step "Falha ao renomear: $($_.Name)" "ERROR"
                }
            }
        }
    }
}

# === COMANDO: BACKUP ===
function Invoke-Backup {
    param([string]$DevBaseRoot)
    Write-Header "DevBase Backup 3-2-1"

    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupName = "devbase_backup_$timestamp"
    $backupPath = Join-Path $DevBaseRoot "30-39_OPERATIONS" "31_backups" "local" $backupName

    Write-Host "Criando backup em: $backupPath`n" -ForegroundColor $script:ColorInfo

    try {
        if ($IsWindows) {
            Write-Host "Usando 'robocopy' para backup otimizado no Windows..." -ForegroundColor $script:ColorInfo
            $exclude = @(
                'node_modules',
                '.git',
                '31_backups'
            )
            $excludeDirs = $exclude | ForEach-Object { "/XD", $_ }
            robocopy $DevBaseRoot $backupPath /MIR $excludeDirs /XF *.log /NFL /NDL /NJH /NJS
        }
        else { # Linux ou macOS
            if (-not (Get-Command rsync -ErrorAction SilentlyContinue)) {
                Write-Step "Comando 'rsync' não encontrado. Backup automático não suportado neste sistema." "ERROR"
                Write-Host "Por favor, instale 'rsync' ou use outra ferramenta de backup manual." -ForegroundColor $script:ColorInfo
                return
            }

            Write-Host "Usando 'rsync' para backup em ambiente non-Windows..." -ForegroundColor $script:ColorInfo
            $rsyncExcludes = @(
                '--exclude=node_modules/',
                '--exclude=.git/',
                '--exclude=31_backups/',
                '--exclude=*.log'
            )
            # The slash at the end of the source path is crucial for rsync
            $sourcePath = "$DevBaseRoot/"

            # -a: archive mode (recursive, preserves links, permissions, etc.)
            # --delete: deletes files in the destination that no longer exist in the source
            rsync -a --delete $rsyncExcludes $sourcePath $backupPath
        }

        Write-Step "Backup local criado com sucesso" "OK"
        Write-Host "  Localização: $backupPath" -ForegroundColor Gray

        # Calculate size (cross-platform method)
        $size = (Get-ChildItem -Path $backupPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-Host "  Tamanho: $sizeMB MB" -ForegroundColor Gray

    } catch {
        Write-Step "Falha no backup: $_" "ERROR"
    }

    Write-Host "`nEstratégia 3-2-1:" -ForegroundColor $script:ColorInfo
    Write-Host "  [1] Local: $backupPath" -ForegroundColor Gray
    Write-Host "  [2] Segundo disco: Copie para um disco externo." -ForegroundColor $script:ColorWarning
    Write-Host "  [3] Off-site: Sincronize com a nuvem (exceto private_vault)." -ForegroundColor $script:ColorWarning
}

# === COMANDO: CLEAN ===
function Invoke-Clean {
    param([string]$DevBaseRoot)
    Write-Header "DevBase Clean"

    Write-Host "Limpando arquivos temporários...`n" -ForegroundColor $script:ColorInfo

    $patterns = @(
        '*.log',
        '*.tmp',
        '*~',
        'Thumbs.db',
        '.DS_Store'
    )

    $cleaned = 0

    foreach ($pattern in $patterns) {
        $files = Get-ChildItem -Path $DevBaseRoot -Filter $pattern -Recurse -File -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Remove-Item $file.FullName -Force
            $cleaned++
        }
    }

    Write-Step "Removed $cleaned temporary files" "OK"

    # Clean old backups (keep last 5)
    $backupDir = Join-Path $DevBaseRoot "30-39_OPERATIONS" "31_backups" "local"
    if (Test-Path $backupDir) {
        $oldBackups = Get-ChildItem -Path $backupDir -Directory |
            Sort-Object CreationTime -Descending |
            Select-Object -Skip 5

        if ($oldBackups.Count -gt 0) {
            Write-Host "`nRemoving old backups..." -ForegroundColor $script:ColorInfo
            $oldBackups | ForEach-Object {
                Remove-Item $_.FullName -Recurse -Force
                Write-Step "Removed: $($_.Name)" $script:ColorSuccess
            }
        }
    }
}

# Carregar deteção de linguagem
. (Join-Path $PSScriptRoot "detect-language.ps1")

function Invoke-InitCI {
    param([string]$DevBaseRoot)

    Write-Header "DevBase CI Bootstrap"
    $targetPath = Get-Location

    Write-Host "Analyzing project at: $targetPath" -ForegroundColor Gray

    # 1. Detect Stack
    $stack = Get-ProjectStack -Path $targetPath

    if ($stack.Type -eq "generic") {
        Write-Step "Could not detect a specific stack (Node/Python/.NET)." "WARN"
        $proceed = Read-Host "Do you want to install a generic CI template? (y/n)"
        if ($proceed -ne 'y') { return }
    } else {
        Write-Step "Detected Stack: $($stack.Name) (Manager: $($stack.PackageManager))" "OK"
    }

    # 2. Determine Source Template
    $templateName = $stack.ciTemplate
    $sourceTemplate = Join-Path $DevBaseRoot "00-09_SYSTEM/05_templates/ci/$templateName"

    if (-not (Test-Path $sourceTemplate)) {
        # Fallback to module source if not hydrated yet
        $sourceTemplate = Join-Path $DevBaseRoot "modules/templates/ci/$templateName"
        if (-not (Test-Path $sourceTemplate)) {
            Write-Step "Template not found: $templateName" "ERROR"
            return
        }
    }

    # 3. Install to .github/workflows
    $githubDir = Join-Path $targetPath ".github/workflows"
    New-DirSafe $githubDir

    $destFile = Join-Path $githubDir "ci.yml"

    # Check overwrite
    if (Test-Path $destFile) {
        Write-Step "CI workflow already exists at .github/workflows/ci.yml" "WARN"
        $confirm = Read-Host "Overwrite? (y/n)"
        if ($confirm -ne 'y') { return }
    }

    $content = Get-Content $sourceTemplate -Raw
    New-FileSafe -Path $destFile -Content $content -Force

    Write-Host "`n[✔] CI/CD Pipeline configured for $($stack.Name)!" -ForegroundColor Green
    Write-Host "    Next step: git add .github/workflows/ci.yml && git commit -m 'ci: add workflow'" -ForegroundColor Gray
}
