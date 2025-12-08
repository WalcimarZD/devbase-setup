# 🏗️ Arquitetura do DevBase

> Documentação técnica detalhada sobre como o DevBase funciona internamente.

---

## 📋 Sumário

1. [Visão Geral](#1-visão-geral)
2. [Componentes Principais](#2-componentes-principais)
3. [Fluxo de Execução](#3-fluxo-de-execução)
4. [Sistema de Módulos](#4-sistema-de-módulos)
5. [Motor de Templates](#5-motor-de-templates)
6. [Engine de Migração](#6-engine-de-migração)
7. [CLI (Interface de Linha de Comando)](#7-cli-interface-de-linha-de-comando)
8. [Segurança](#8-segurança)
9. [Extensibilidade](#9-extensibilidade)
10. [Decisões de Design](#10-decisões-de-design)

---

## 1. Visão Geral

### 1.1 Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                         DevBase v3.1                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ install.sh   │───▶│ bootstrap.ps1│───▶│   Workspace  │       │
│  │ (Unix entry) │    │ (Orchestrator│    │  (Resultado) │       │
│  └──────────────┘    └──────┬───────┘    └──────────────┘       │
│         │                   │                                    │
│         │            ┌──────▼───────┐                            │
│         │            │    Modules   │                            │
│         │            ├──────────────┤                            │
│         └───────────▶│ setup-core   │◀── templates/core          │
│                      │ setup-pkm    │◀── templates/pkm           │
│                      │ setup-code   │◀── templates/code          │
│                      │ setup-ops    │◀── templates/operations    │
│                      │ setup-hooks  │◀── templates/hooks         │
│                      │ setup-ai     │◀── templates/ai            │
│                      │ setup-tpl    │◀── templates/patterns      │
│                      └──────────────┘                            │
│                             │                                    │
│  ┌──────────────┐    ┌──────▼───────┐    ┌──────────────┐       │
│  │common-funcs  │◀───│   Assets     │───▶│ devbase.ps1  │       │
│  │(Utilitários) │    │ (CLI Tools)  │    │ (CLI final)  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Princípios Arquiteturais

| Princípio | Descrição | Implementação |
|-----------|-----------|---------------|
| **Idempotência** | Executar múltiplas vezes produz mesmo resultado | `New-FileSafe` verifica existência antes de criar |
| **Modularidade** | Funcionalidades separadas em módulos | Cada `setup-*.ps1` é independente |
| **Declarativo** | Templates definem o estado desejado | Arquivos `.template` são processados automaticamente |
| **Segurança** | Proteção contra path traversal e vazamentos | `Assert-SafePath`, validação de BOM |
| **Portabilidade** | Funciona em Windows, Linux, macOS | PowerShell Core + fallback Python |

---

## 2. Componentes Principais

### 2.1 Mapa de Componentes

```
devbase-setup-v3/
│
├── bootstrap.ps1              # 🎯 Orquestrador principal
├── devbase.py                 # 🐍 Fallback Python (Linux/macOS)
├── install.sh                 # 🐧 Entry point Unix
│
├── modules/                   # 📦 Módulos de setup
│   ├── common-functions.ps1   # Utilitários compartilhados
│   ├── cli-functions.ps1      # Funções da CLI (testáveis)
│   ├── detect-language.ps1    # Detecção de stack
│   ├── setup-core.ps1         # Estrutura base
│   ├── setup-pkm.ps1          # Knowledge Management
│   ├── setup-code.ps1         # Templates de código
│   ├── setup-operations.ps1   # Automação e CLI
│   ├── setup-templates.ps1    # Padrões técnicos
│   ├── setup-hooks.ps1        # Git hooks
│   └── setup-ai.ps1           # Módulo de IA
│   │
│   ├── assets/                # 🔧 Scripts finais
│   │   ├── devbase.ps1.asset  # CLI principal
│   │   ├── telemetry.ps1.asset
│   │   ├── observability.ps1.asset
│   │   └── fs_performance.ps1.asset
│   │
│   ├── python/                # 🐍 Módulos Python
│   │   └── filesystem.py      # Operações de arquivo
│   │
│   └── templates/             # 📝 Templates fonte
│       ├── core/              # .gitignore, .editorconfig
│       ├── pkm/               # ADRs, journals, TIL
│       ├── code/              # Clean Architecture
│       ├── operations/        # Scripts de automação
│       ├── hooks/             # Git hooks
│       ├── patterns/          # Padrões técnicos
│       ├── prompts/           # System prompts IA
│       ├── ci/                # CI/CD templates
│       └── ai/                # Configuração IA
│
└── docs/                      # 📚 Documentação
    ├── USAGE-GUIDE.md
    └── ARCHITECTURE.md
```

### 2.2 Responsabilidades

| Componente | Responsabilidade | Dependências |
|------------|------------------|--------------|
| `bootstrap.ps1` | Orquestrar execução, validações iniciais | `common-functions.ps1`, todos os `setup-*.ps1` |
| `common-functions.ps1` | Funções utilitárias (Write-Step, New-FileSafe, etc.) | Nenhuma |
| `setup-core.ps1` | Criar estrutura Johnny.Decimal base | `common-functions.ps1` |
| `setup-pkm.ps1` | Criar estrutura de conhecimento | `common-functions.ps1` |
| `setup-code.ps1` | Criar estrutura de código e templates | `common-functions.ps1` |
| `setup-operations.ps1` | Instalar CLI e scripts de automação | `common-functions.ps1`, `assets/` |
| `setup-hooks.ps1` | Instalar e configurar git hooks | `common-functions.ps1` |
| `setup-ai.ps1` | Criar estrutura do módulo de IA | `common-functions.ps1` |
| `devbase.ps1.asset` | CLI do usuário final | `common-functions.ps1` |

---

## 3. Fluxo de Execução

### 3.1 Fluxo do Bootstrap

```
┌────────────────────────────────────────────────────────────────┐
│                     bootstrap.ps1                               │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 1. CONFIGURAÇÃO INICIAL                                         │
│    • Definir $ErrorActionPreference                             │
│    • Carregar common-functions.ps1                              │
│    • Exibir banner                                              │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. VALIDAÇÕES                                                   │
│    • Test-StorageTier (SSD/NVMe)                                │
│    • Carregar estado existente (.devbase_state.json)            │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. CARREGAR MÓDULOS                                             │
│    • setup-core.ps1                                             │
│    • setup-pkm.ps1                                              │
│    • setup-code.ps1                                             │
│    • setup-operations.ps1                                       │
│    • setup-templates.ps1                                        │
│    • setup-hooks.ps1                                            │
│    • setup-ai.ps1                                               │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. EXECUTAR SETUP (em ordem)                                    │
│    • Setup-Core       → Estrutura base                          │
│    • Setup-PKM        → Knowledge Management                    │
│    • Setup-Code       → Templates de código                     │
│    • Setup-Operations → CLI e automação                         │
│    • Setup-Templates  → Padrões técnicos                        │
│    • Setup-Hooks      → Git hooks                               │
│    • Setup-AI         → Módulo de IA                            │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. SALVAR ESTADO                                                │
│    • Atualizar .devbase_state.json                              │
│    • Registrar versão e data                                    │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. VALIDAÇÃO FINAL                                              │
│    • Verificar existência de pastas esperadas                   │
│    • Exibir resumo                                              │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Diagrama de Sequência

```
Usuario           install.sh        bootstrap.ps1      Módulos          Templates
   │                  │                  │                │                 │
   │ ─────execute───▶ │                  │                │                 │
   │                  │ ──check pwsh──▶  │                │                 │
   │                  │ ◀──found─────    │                │                 │
   │                  │ ───execute────▶  │                │                 │
   │                  │                  │ ──load───────▶ │                 │
   │                  │                  │ ◀──functions── │                 │
   │                  │                  │                │                 │
   │                  │                  │ ──Setup-Core───────────────────▶ │
   │                  │                  │ ◀──templates processed──────────│
   │                  │                  │                │                 │
   │                  │                  │ ──Setup-PKM────────────────────▶ │
   │                  │                  │ ◀──templates processed──────────│
   │                  │                  │                │                 │
   │                  │                  │ ─── ... ───────────────────────▶ │
   │                  │                  │                │                 │
   │                  │                  │ ──save state─▶ │                 │
   │                  │                  │                │                 │
   │ ◀───complete────────────────────── │                │                 │
```

---

## 4. Sistema de Módulos

### 4.1 Anatomia de um Módulo

Cada módulo `setup-*.ps1` segue este padrão:

```powershell
<#
.SYNOPSIS
    DevBase v3.x - [Nome] Module
.DESCRIPTION
    [Descrição do que o módulo faz]
#>

function Setup-[Nome] {
    <#
    .SYNOPSIS
        [Descrição curta]
    .PARAMETER RootPath
        O caminho raiz do workspace DevBase.
    #>
    param([string]$RootPath)

    # 1. Definir caminhos
    $Area = Join-Path $RootPath "[XX-XX_AREA]"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates/[area]"

    # 2. Criar estrutura de diretórios
    New-DirSafe -Path $Area
    New-DirSafe -Path (Join-Path $Area "subfolder")

    # 3. Processar templates
    $templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse

    foreach ($templateFile in $templateFiles) {
        $content = Get-Content -Path $templateFile.FullName -Raw

        # Substituir placeholders
        $content = $content.Replace('{{PLACEHOLDER}}', $value)

        # Calcular caminho de destino
        $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)
        $destinationFileName = $templateFile.Name.Replace(".template", "")
        $destinationDir = Join-Path $Area (Split-Path $relativeSourcePath -Parent)
        $destinationPath = Join-Path $destinationDir $destinationFileName

        # Criar arquivo
        New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
    }
}
```

### 4.2 Funções Compartilhadas (common-functions.ps1)

```powershell
# ============================================
# FUNÇÕES DE OUTPUT
# ============================================

Write-Header "Título"           # Exibe cabeçalho formatado
Write-Step "Mensagem" "OK"      # Exibe status [+] verde
Write-Step "Mensagem" "WARN"    # Exibe status [!] amarelo
Write-Step "Mensagem" "ERROR"   # Exibe status [X] vermelho
Write-Step "Mensagem" "INFO"    # Exibe status [i] ciano

# ============================================
# FUNÇÕES DE SEGURANÇA
# ============================================

Assert-SafePath -TargetPath $path -AllowedRoot $root  # Previne path traversal
Assert-NoBOM -Path $file                               # Remove BOM UTF-8
Assert-Permissions -Path $path -IsSensitive           # Verifica permissões

# ============================================
# FUNÇÕES DE FILESYSTEM (ATÔMICAS)
# ============================================

New-DirSafe -Path $path         # Cria diretório se não existir
Write-FileAtomic -Path $path -Content $content  # Escrita atômica via temp file
New-FileSafe -Path $path -Content $content      # Cria arquivo se não existir
New-FileSafe -Path $path -Content $content -Force  # Sobrescreve se existir
Copy-ItemAtomic -Source $src -Destination $dest    # Cópia atômica
```

### 4.3 Carregamento de Módulos

```powershell
# Em bootstrap.ps1:

$modulesPath = Join-Path $PSScriptRoot "modules"

$modules = @(
    "setup-core.ps1",
    "setup-pkm.ps1",
    "setup-code.ps1",
    "setup-operations.ps1",
    "setup-templates.ps1",
    "setup-hooks.ps1",
    "setup-ai.ps1"
)

# Dot-sourcing carrega cada módulo no escopo atual
foreach ($module in $modules) {
    $modulePath = Join-Path $modulesPath $module
    if (Test-Path $modulePath) {
        . $modulePath  # Importa funções para o escopo atual
    }
    else {
        Write-Step "Module not found: $module" "ERROR"
        exit 1
    }
}
```

---

## 5. Motor de Templates

### 5.1 Como Templates Funcionam

```
┌──────────────────────────────────────────────────────────────────┐
│                    Template Processing                            │
└──────────────────────────────────────────────────────────────────┘

  modules/templates/core/              →    Dev_Workspace/
  ├── .gitignore.template              →    .gitignore
  ├── .editorconfig.template           →    .editorconfig
  └── 00-09_SYSTEM/                    →    00-09_SYSTEM/
      └── 00_inbox/                    →        00_inbox/
          └── README.md.template       →            README.md

  Template Content:
  ┌────────────────────────────────────┐
  │ # Inbox - DevBase v{{POLICY_VERSION}}   │
  │ Created: {{DATE}}                  │
  └────────────────────────────────────┘
                   │
                   ▼ (processamento)
  ┌────────────────────────────────────┐
  │ # Inbox - DevBase v3.1             │
  │ Created: 2024-12-07                │
  └────────────────────────────────────┘
```

### 5.2 Placeholders Disponíveis

| Placeholder | Valor | Exemplo |
|-------------|-------|---------|
| `{{POLICY_VERSION}}` | Versão da política | `3.1` |
| `{{DATE}}` | Data atual | `2024-12-07` |
| `{{YEAR}}` | Ano atual | `2024` |
| `{{WEEK_NUMBER}}` | Número da semana | `49` |
| `{{DATE_PLUS_6}}` | Data + 6 dias | `2024-12-13` |

### 5.3 Processamento de Templates

```powershell
# Exemplo de processamento em setup-pkm.ps1

$templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse

foreach ($templateFile in $templateFiles) {
    # 1. Ler conteúdo do template
    $content = Get-Content -Path $templateFile.FullName -Raw

    # 2. Substituir placeholders dinâmicos
    $content = $content.Replace('{{YEAR}}', (Get-Date -Format 'yyyy'))
    $content = $content.Replace('{{DATE}}', (Get-Date -Format 'yyyy-MM-dd'))
    $content = $content.Replace('{{WEEK_NUMBER}}', (Get-Date -UFormat '%V'))

    # 3. Calcular caminho de destino
    #    Template: modules/templates/pkm/11_public_garden/til/template-til.md.template
    #    Destino:  Dev_Workspace/10-19_KNOWLEDGE/11_public_garden/til/template-til.md

    $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)
    $destinationFileName = $templateFile.Name.Replace(".template", "")
    $destinationDir = Join-Path $Area10 (Split-Path $relativeSourcePath -Parent)
    $destinationPath = Join-Path $destinationDir $destinationFileName

    # 4. Criar arquivo (idempotente)
    New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
}
```

### 5.4 Convenção de Nomes de Templates

```
[nome-arquivo].[extensão].template

Exemplos:
  README.md.template      → README.md
  .gitignore.template     → .gitignore
  pre-commit.ps1.template → pre-commit.ps1
  ci-node.yml.template    → ci-node.yml
```

---

## 6. Engine de Migração

### 6.1 Arquivo de Estado

O arquivo `.devbase_state.json` rastreia o estado do workspace:

```json
{
  "version": "3.1.0",
  "policyVersion": "3.1",
  "installedAt": "2024-01-15T10:30:00.0000000Z",
  "lastUpdate": "2024-12-07T14:25:00.0000000Z",
  "migrations": [
    "v3.0.0-20240115",
    "v3.1.0-20241207"
  ],
  "modules": [
    "setup-core.ps1",
    "setup-pkm.ps1",
    "setup-code.ps1",
    "setup-operations.ps1",
    "setup-templates.ps1",
    "setup-hooks.ps1",
    "setup-ai.ps1"
  ]
}
```

### 6.2 Fluxo de Migração

```
┌────────────────────────────────────────────────────────────────┐
│                     Migration Engine                            │
└────────────────────────────────────────────────────────────────┘

  1. Ler estado atual:
     ┌─────────────────────────────┐
     │ .devbase_state.json         │
     │ version: "3.0.0"            │
     └─────────────────────────────┘
                    │
                    ▼
  2. Comparar com versão do script:
     ┌─────────────────────────────┐
     │ $ScriptVersion = "3.1.0"    │
     │ Precisa migrar? SIM         │
     └─────────────────────────────┘
                    │
                    ▼
  3. Executar setup (adiciona/atualiza):
     ┌─────────────────────────────┐
     │ Setup-Core                  │
     │ Setup-PKM                   │
     │ Setup-AI (novo em 3.1)      │
     └─────────────────────────────┘
                    │
                    ▼
  4. Salvar novo estado:
     ┌─────────────────────────────┐
     │ .devbase_state.json         │
     │ version: "3.1.0"            │
     │ migrations: [..., "v3.1.0"] │
     └─────────────────────────────┘
```

### 6.3 Funções de Estado

```powershell
# Em bootstrap.ps1:

function Get-DevBaseState {
    if (Test-Path $script:StateFile) {
        return Get-Content $script:StateFile -Raw | ConvertFrom-Json
    }
    # Retorna estado inicial se não existir
    return @{
        version     = "0.0.0"
        installedAt = $null
        lastUpdate  = $null
        migrations  = @()
    }
}

function Save-DevBaseState {
    param([hashtable]$State)
    $State | ConvertTo-Json -Depth 10 | Set-Content $script:StateFile -Encoding UTF8
}
```

---

## 7. CLI (Interface de Linha de Comando)

### 7.1 Arquitetura da CLI

```
┌────────────────────────────────────────────────────────────────┐
│                      devbase.ps1                                │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ PARAM BLOCK                                                     │
│ ─────────────────────────────────────────────────────────────  │
│ param(                                                          │
│     [ValidateSet('doctor','audit','backup',...)]               │
│     [string]$Command = 'help',                                 │
│     [string]$Name,                                             │
│     [switch]$Fix,                                              │
│     [switch]$Force,                                            │
│     ...                                                        │
│ )                                                              │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ INITIALIZATION                                                  │
│ ─────────────────────────────────────────────────────────────  │
│ • Detectar $DevBaseRoot                                         │
│ • Carregar common-functions.ps1                                 │
│ • Definir cores                                                 │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│ COMMAND DISPATCHER                                              │
│ ─────────────────────────────────────────────────────────────  │
│ switch ($Command) {                                             │
│     'doctor' { Invoke-Doctor }                                  │
│     'audit'  { Invoke-Audit }                                   │
│     'backup' { Invoke-Backup }                                  │
│     'new'    { Invoke-NewProject -ProjectName $Name }           │
│     ...                                                        │
│ }                                                              │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 Comandos Disponíveis

| Comando | Função | Descrição |
|---------|--------|-----------|
| `doctor` | `Invoke-Doctor` | Verifica integridade |
| `audit` | `Invoke-Audit` | Audita nomenclatura |
| `backup` | `Invoke-Backup` | Backup 3-2-1 |
| `clean` | `Invoke-Clean` | Limpa temporários |
| `new` | `Invoke-NewProject` | Cria projeto |
| `link-dotfiles` | `Invoke-LinkDotfiles` | Sincroniza dotfiles |
| `hydrate` | `Invoke-Hydrate` | Atualiza templates |
| `track` | `Invoke-Track` | Registra atividade |
| `stats` | `Invoke-Stats` | Mostra estatísticas |
| `weekly` | `Invoke-Weekly` | Gera weeknotes |
| `brag` | `Invoke-Brag` | Gera brag doc |
| `init-ci` | `Invoke-InitCI` | Configura CI/CD |

### 7.3 Exemplo de Implementação de Comando

```powershell
function Invoke-Doctor {
    Write-Header "DevBase Doctor"
    Write-Host "Verificando integridade do DevBase em: $DevBaseRoot`n" -ForegroundColor $script:ColorInfo

    $issues = 0

    # 1. Verificar estrutura de áreas
    Write-Host "Verificando estrutura de áreas..." -ForegroundColor $script:ColorInfo
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

    # 2. Verificar arquivos de governança
    # ...

    # 3. Resultado final
    if ($issues -eq 0) {
        Write-Host "DevBase está SAUDÁVEL" -ForegroundColor $script:ColorSuccess
    } else {
        Write-Host "Encontrados $issues problemas" -ForegroundColor $script:ColorWarning
    }
}
```

---

## 8. Segurança

### 8.1 Proteções Implementadas

```
┌────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
└────────────────────────────────────────────────────────────────┘

  Layer 1: Path Traversal Prevention
  ┌─────────────────────────────────────────────────────────────┐
  │ Assert-SafePath -TargetPath $path -AllowedRoot $root        │
  │                                                             │
  │ Previne: ../../../etc/passwd                                │
  │ Valida que $path está dentro de $root                       │
  └─────────────────────────────────────────────────────────────┘

  Layer 2: BOM Sanitization
  ┌─────────────────────────────────────────────────────────────┐
  │ Assert-NoBOM -Path $file                                    │
  │                                                             │
  │ Remove UTF-8 BOM (EF BB BF) que pode causar problemas       │
  │ em scripts e arquivos de configuração                       │
  └─────────────────────────────────────────────────────────────┘

  Layer 3: Permission Checks
  ┌─────────────────────────────────────────────────────────────┐
  │ Assert-Permissions -Path $path -IsSensitive                 │
  │                                                             │
  │ Verifica se arquivos sensíveis (vault) não estão           │
  │ com permissões world-readable                              │
  └─────────────────────────────────────────────────────────────┘

  Layer 4: Air-Gap Enforcement
  ┌─────────────────────────────────────────────────────────────┐
  │ .gitignore contém: 12_private_vault                        │
  │ devbase doctor verifica esta proteção                       │
  └─────────────────────────────────────────────────────────────┘

  Layer 5: Atomic Operations
  ┌─────────────────────────────────────────────────────────────┐
  │ Write-FileAtomic usa temp file + rename                    │
  │ Previne corrupção em caso de falha durante escrita          │
  └─────────────────────────────────────────────────────────────┘
```

### 8.2 Implementação de Assert-SafePath

```powershell
function Assert-SafePath {
    param(
        [Parameter(Mandatory)][string]$TargetPath,
        [Parameter(Mandatory)][string]$AllowedRoot
    )
    try {
        # Resolve caminhos para evitar ../
        $absTarget = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($TargetPath)
        $absRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($AllowedRoot)

        if (-not $absTarget.StartsWith($absRoot, [StringComparison]::InvariantCultureIgnoreCase)) {
            throw "SECURITY VIOLATION: Path Traversal detected! '$absTarget' is outside '$absRoot'."
        }
    } catch {
        Write-Step "Path safety check failed: $_" "ERROR"
        throw
    }
}
```

### 8.3 Escrita Atômica

```powershell
function Write-FileAtomic {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content,
        [string]$Encoding = "UTF8"
    )

    $parentDir = Split-Path $Path -Parent
    if (-not (Test-Path $parentDir)) { New-DirSafe $parentDir }

    # 1. Escrever em arquivo temporário
    $fileName = Split-Path $Path -Leaf
    $tempPath = Join-Path $parentDir ".$fileName.$([Guid]::NewGuid()).tmp"

    try {
        # 2. Escrever conteúdo
        Set-Content -Path $tempPath -Value $Content -Encoding $Encoding -Force

        # 3. Sanitizar BOM
        Assert-NoBOM -Path $tempPath

        # 4. Rename atômico (operação do filesystem)
        Move-Item -LiteralPath $tempPath -Destination $Path -Force

        return $true
    }
    catch {
        # Limpar temp file em caso de erro
        if (Test-Path $tempPath) {
            Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
        }
        throw $_
    }
}
```

---

## 9. Extensibilidade

### 9.1 Adicionando Novo Módulo

```powershell
# 1. Criar modules/setup-meumodulo.ps1

<#
.SYNOPSIS
    DevBase v3.x - MeuModulo Module
#>

function Setup-MeuModulo {
    param([string]$RootPath)

    $Area = Join-Path $RootPath "XX-XX_MINHA_AREA"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates/meumodulo"

    # Criar estrutura
    New-DirSafe -Path $Area

    # Processar templates
    # ...
}

# 2. Criar modules/templates/meumodulo/ com seus .template

# 3. Adicionar ao bootstrap.ps1:
$modules = @(
    "setup-core.ps1",
    # ...
    "setup-meumodulo.ps1"  # Novo
)

# 4. Chamar no fluxo de execução:
Write-Header "X. MeuModulo"
Setup-MeuModulo -RootPath $RootPath
```

### 9.2 Adicionando Comando à CLI

```powershell
# 1. Em devbase.ps1.asset, adicionar ao param():

[ValidateSet(
    'doctor', 'audit', 'backup', 'clean', 'new', 'link-dotfiles', 'hydrate', 'help',
    'track', 'stats', 'weekly', 'brag',
    'meu-comando'  # Novo
)]

# 2. Criar função:

function Invoke-MeuComando {
    Write-Header "Meu Comando"

    # Sua lógica aqui
    Write-Step "Fazendo algo..." "INFO"

    # ...

    Write-Step "Concluído" "OK"
}

# 3. Adicionar ao switch:

switch ($Command) {
    'doctor' { Invoke-Doctor }
    # ...
    'meu-comando' { Invoke-MeuComando }  # Novo
}
```

### 9.3 Adicionando Templates

```
# 1. Criar arquivo .template

modules/templates/minha-area/meu-arquivo.md.template

# 2. Usar placeholders

# Meu Arquivo - v{{POLICY_VERSION}}
Criado em: {{DATE}}

# 3. O módulo correspondente processará automaticamente
```

---

## 10. Decisões de Design

### 10.1 ADRs do Projeto

| ADR | Decisão | Justificativa |
|-----|---------|---------------|
| ADR-001 | PowerShell como linguagem principal | Nativo no Windows, portável via pwsh |
| ADR-002 | Johnny.Decimal para organização | Estrutura clara e escalável |
| ADR-003 | Templates declarativos | Facilita manutenção e customização |
| ADR-004 | Operações atômicas | Previne corrupção de dados |
| ADR-005 | Air-Gap para vault | Segurança por design |
| ADR-006 | Idempotência | Permite re-execução segura |
| ADR-007 | Fallback Python | Suporte a Linux/macOS sem pwsh |

### 10.2 Por que PowerShell?

**Prós:**
- Nativo no Windows (sem instalação)
- PowerShell Core funciona em Linux/macOS
- Sintaxe expressiva para manipulação de arquivos
- Cmdlets para Git, filesystem, etc.
- Objetos ao invés de strings (mais robusto)

**Contras:**
- Menos familiar para desenvolvedores Unix
- Performance em operações massivas
- Verbosidade em algumas operações

### 10.3 Por que Johnny.Decimal?

- **Previsibilidade**: Sempre sei onde está cada tipo de conteúdo
- **Escalabilidade**: Funciona de 10 arquivos a 100.000
- **Numeração**: Permite ordenação natural
- **Áreas**: Separação clara de responsabilidades

### 10.4 Trade-offs

| Aspecto | Escolha | Trade-off |
|---------|---------|-----------|
| Linguagem | PowerShell | Menos portável que Bash/Python puro |
| Templates | Declarativos | Menos flexível que código |
| Estado | JSON file | Não é database, mas suficiente |
| Segurança | Air-Gap | Usuário deve manter disciplina |
| CLI | Script único | Sem auto-complete avançado |

---

## 📚 Referências

- [PowerShell Documentation](https://docs.microsoft.com/powershell/)
- [Johnny.Decimal](https://johnnydecimal.com/)
- [Conventional Commits](https://conventionalcommits.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [ADR Templates](https://adr.github.io/)

---

<div align="center">

[⬆️ Voltar ao topo](#️-arquitetura-do-devbase)

</div>
