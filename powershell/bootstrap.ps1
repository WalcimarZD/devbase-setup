<#
.SYNOPSIS
    DevBase v3.1 - Bootstrap (Orquestrador Principal)

.DESCRIPTION
    Este é o script principal do DevBase - o "maestro" que coordena toda a
    configuração do seu Personal Engineering Operating System.

    ╔═══════════════════════════════════════════════════════════════════╗
    ║  O QUE ESTE SCRIPT FAZ:                                          ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║  1. Valida o ambiente (storage, estado anterior)                 ║
    ║  2. Carrega todos os módulos de setup                            ║
    ║  3. Executa cada módulo em ordem                                 ║
    ║  4. Salva o estado para futuras migrações                        ║
    ║  5. Valida a estrutura final                                     ║
    ╚═══════════════════════════════════════════════════════════════════╝

    CONCEITO: IDEMPOTÊNCIA
    ──────────────────────
    Este script é IDEMPOTENTE - você pode executá-lo quantas vezes quiser
    sem efeitos colaterais indesejados:
    • Diretórios existentes não são recriados
    • Arquivos existentes não são sobrescritos (exceto com -Force)
    • Estado é rastreado para evitar retrabalho

    CONCEITO: DECLARATIVO vs IMPERATIVO
    ────────────────────────────────────
    O DevBase usa uma abordagem declarativa: você define o ESTADO DESEJADO
    através de templates, e o sistema cuida de chegar lá.

    Imperativo: "Crie pasta X, depois Y, depois arquivo Z"
    Declarativo: "O sistema deve ter esta estrutura" → sistema calcula o que fazer

    ORDEM DE EXECUÇÃO DOS MÓDULOS:
    ──────────────────────────────
    1. setup-core.ps1       → Estrutura base Johnny.Decimal
    2. setup-pkm.ps1        → Knowledge Management (PKM)
    3. setup-code.ps1       → Templates de código
    4. setup-operations.ps1 → CLI e automação
    5. setup-templates.ps1  → Padrões técnicos
    6. setup-hooks.ps1      → Git hooks
    7. setup-ai.ps1         → Módulo de IA local

    A ordem importa! Módulos posteriores podem depender de estruturas
    criadas por módulos anteriores.

.PARAMETER RootPath
    O caminho raiz para o workspace DevBase (onde a estrutura será criada).
    Se não especificado, usa "$HOME\Dev_Workspace".

    DICA: Use um SSD/NVMe para melhor performance!

.PARAMETER SkipStorageValidation
    Pula a verificação de tipo de storage (SSD/NVMe).
    Útil para VMs ou ambientes de teste onde o tipo de storage não pode
    ser determinado automaticamente.

.PARAMETER Force
    Força a atualização de TODOS os arquivos de template, sobrescrevendo
    arquivos existentes no destino.

    ⚠️  CUIDADO: Isso sobrescreve customizações que você tenha feito nos
    arquivos gerados pelo DevBase.

    Quando usar -Force:
    • Ao atualizar o DevBase para uma nova versão
    • Para restaurar templates ao estado original
    • Em ambiente de desenvolvimento do DevBase

.PARAMETER SkipHooks
    Impede a instalação de git hooks e a configuração de `core.hooksPath`.

    Quando usar -SkipHooks:
    • Quando você tem hooks próprios que não quer substituir
    • Em ambientes CI/CD onde hooks não são necessários
    • Se não usa Git no workspace

.EXAMPLE
    # Execução básica - usa localização padrão ($HOME\Dev_Workspace)
    .\bootstrap.ps1

.EXAMPLE
    # Execução em diretório personalizado
    .\bootstrap.ps1 -RootPath "D:\DevBase"

.EXAMPLE
    # Atualização forçada de todos os templates
    .\bootstrap.ps1 -Force

.EXAMPLE
    # Setup completo com todas as opções
    .\bootstrap.ps1 -RootPath "D:\DevBase" -Force -SkipStorageValidation

.NOTES
    Versão: 3.1.0
    Requer: PowerShell 5.1+ ou PowerShell Core 7+

    ARQUIVOS IMPORTANTES:
    • .devbase_state.json  → Estado da instalação (versão, migrações)
    • 00.00_index.md       → Índice principal do workspace
    • .gitignore           → Proteção do vault privado

    TROUBLESHOOTING:
    • Se der erro de permissão: Execute como Administrador
    • Se módulo não for encontrado: Verifique se a pasta modules/ está completa
    • Se storage validation falhar: Use -SkipStorageValidation
#>

param (
    [string]$RootPath = "$HOME\Dev_Workspace",
    [switch]$SkipStorageValidation,
    [switch]$Force,
    [switch]$SkipHooks
)

# ============================================
# CONFIGURAÇÃO GLOBAL
# ============================================
# Estas configurações afetam todo o comportamento do script.
#
# $ErrorActionPreference = "Stop"
#   → Faz o script parar imediatamente se qualquer erro ocorrer
#   → Importante para evitar execução parcial com estado inconsistente
#
# Versões são usadas para:
# • $ScriptVersion: Rastrear qual versão do DevBase está instalada
# • $PolicyVersion: Versão das políticas/templates (pode mudar independentemente)
# ============================================
$ErrorActionPreference = "Stop"
$ScriptVersion = "3.1.0"
$PolicyVersion = "3.1"

# ============================================
# CONFIGURAÇÃO DE CORES DO CONSOLE
# ============================================
# Cores são definidas no escopo $script: para serem acessíveis
# por todas as funções, incluindo as importadas de common-functions.ps1
#
# Usar variáveis de cor ao invés de valores hardcoded permite:
# • Consistência visual em todo o script
# • Fácil customização do esquema de cores
# • Adaptação para diferentes terminais
# ============================================
$script:ColorSuccess = "Green"    # Operações bem-sucedidas [+]
$script:ColorWarning = "Yellow"   # Avisos que precisam atenção [!]
$script:ColorError = "Red"        # Erros que impedem execução [X]
$script:ColorInfo = "Cyan"        # Informações gerais [i]
$script:ColorHeader = "Magenta"   # Cabeçalhos de seção

# ============================================
# ARQUIVO DE ESTADO (Migration Engine)
# ============================================
# O arquivo de estado rastreia informações sobre a instalação:
# • Versão instalada
# • Data de instalação/atualização
# • Histórico de migrações
#
# Isso permite que futuras versões do DevBase saibam o que já foi
# instalado e apliquem apenas as mudanças necessárias (migrações).
# ============================================
$script:StateFile = Join-Path $RootPath ".devbase_state.json"

# ============================================
# IMPORTAÇÃO DE FUNÇÕES UTILITÁRIAS
# ============================================
# O operador "." (dot-sourcing) importa funções do arquivo para
# o escopo atual, tornando-as disponíveis como se estivessem aqui.
#
# common-functions.ps1 contém:
# • Write-Header, Write-Step (output formatado)
# • New-DirSafe, New-FileSafe (operações de filesystem)
# • Assert-SafePath, Assert-NoBOM (segurança)
# ============================================
. (Join-Path $PSScriptRoot "modules/common-functions.ps1")

# ============================================
# FUNÇÕES ESPECÍFICAS DO BOOTSTRAP
# ============================================
# Estas funções são usadas apenas pelo bootstrap.ps1 e não são
# compartilhadas com outros módulos (diferente de common-functions.ps1).
# ============================================

<#
.SYNOPSIS
    Recupera o estado atual da instalação DevBase.

.DESCRIPTION
    Lê o arquivo .devbase_state.json para determinar:
    - Qual versão está instalada
    - Quando foi instalada/atualizada
    - Quais migrações já foram aplicadas

    Se o arquivo não existir, retorna um estado "vazio" (versão 0.0.0)
    indicando uma instalação nova.

.OUTPUTS
    [PSCustomObject] ou [hashtable] com o estado atual

.NOTES
    Este padrão é comum em ferramentas de migração (como Flyway, Alembic):
    manter um registro de "o que já foi feito" para saber "o que falta fazer".
#>
function Get-DevBaseState {
    if (Test-Path $script:StateFile) {
        return Get-Content $script:StateFile -Raw | ConvertFrom-Json
    }
    # Estado inicial para instalação nova
    return @{
        version     = "0.0.0"      # Indica que nenhuma versão está instalada
        installedAt = $null         # Data da primeira instalação
        lastUpdate  = $null         # Data da última atualização
        migrations  = @()           # Lista de migrações aplicadas
    }
}

<#
.SYNOPSIS
    Salva o estado atual da instalação DevBase.

.DESCRIPTION
    Persiste o estado em .devbase_state.json para permitir:
    - Detecção de atualizações futuras
    - Rollback se necessário
    - Auditoria de quando mudanças foram feitas

.PARAMETER State
    Hashtable com o estado a ser salvo

.NOTES
    UTF8 é usado para garantir compatibilidade cross-platform
    e suporte a caracteres especiais.
#>
function Save-DevBaseState {
    param([hashtable]$State)
    # ConvertTo-Json com Depth 10 garante que objetos aninhados sejam serializados
    $State | ConvertTo-Json -Depth 10 | Set-Content $script:StateFile -Encoding UTF8
}

<#
.SYNOPSIS
    Verifica se o storage é adequado para o DevBase (SSD/NVMe).

.DESCRIPTION
    O DevBase usa conceitos de "Storage Tiers":
    - Tier 0 (Hot): SSD/NVMe - Para workspace ativo (dados quentes)
    - Tier 1 (Warm): HDD - Para backups recentes
    - Tier 2 (Cold): Cloud/External - Para arquivos históricos

    Esta função verifica se o diretório está em storage Tier 0,
    que é recomendado para melhor performance de I/O.

.PARAMETER Path
    Caminho do diretório a ser verificado

.OUTPUTS
    [bool] - $true se o storage é adequado (ou se a verificação foi pulada)

.NOTES
    Esta verificação é Windows-específica e usa WMI/CIM para
    consultar informações do disco físico.

    Em Linux/macOS, a verificação é pulada automaticamente.
#>
function Test-StorageTier {
    param([string]$Path)

    # Permite pular a verificação via parâmetro
    if ($SkipStorageValidation) {
        Write-Step "Storage validation skipped" "WARN"
        return $true
    }

    # Verificação só funciona no Windows (usa WMI)
    # $IsWindows é automático no PowerShell Core
    if (-not $IsWindows) {
        Write-Step "Storage type check skipped (not Windows)" "INFO"
        return $true
    }

    # Extrai a letra do drive (ex: "D" de "D:\DevBase")
    $driveLetter = (Split-Path $Path -Qualifier).TrimEnd(':')

    try {
        # Pipeline WMI para descobrir o tipo de mídia do disco físico
        # Get-PhysicalDisk → Get-Partition → Get-Disk → verificar MediaType
        $disk = Get-PhysicalDisk | Where-Object {
            $partitions = Get-Partition | Where-Object { $_.DriveLetter -eq $driveLetter }
            $diskNumber = ($partitions | Get-Disk).Number
            $_.DeviceId -eq $diskNumber
        } | Select-Object -First 1

        if ($disk) {
            $mediaType = $disk.MediaType
            # SSD, NVMe ou Unspecified (VMs/WSL) são aceitáveis
            if ($mediaType -in @("SSD", "NVMe", "Unspecified")) {
                Write-Step "Storage Tier 0 confirmed: $mediaType" "OK"
                return $true
            }
            else {
                # HDD funciona mas não é ideal para workspace ativo
                Write-Step "Storage is HDD - SSD/NVMe recommended for Tier 0" "WARN"
                return $true
            }
        }
    }
    catch {
        # Se não conseguir verificar, apenas avisa e continua
        Write-Step "Could not verify storage type" "WARN"
    }
    return $true
}

# ============================================
# BANNER ASCII ART
# ============================================
# O banner é exibido no início da execução para:
# • Identificação visual clara do DevBase
# • Mostrar a versão atual
# • Dar um "look profissional" ao script
#
# A here-string @"..."@ permite texto multi-linha
# preservando formatação e caracteres especiais.
# ============================================

Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ██████╗ ███████╗██╗   ██╗██████╗  █████╗ ███████╗███████╗
║     ██╔══██╗██╔════╝██║   ██║██╔══██╗██╔══██╗██╔════╝██╔════╝
║     ██║  ██║█████╗  ██║   ██║██████╔╝███████║███████╗█████╗
║     ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██╗██╔══██║╚════██║██╔══╝
║     ██████╔╝███████╗ ╚████╔╝ ██████╔╝██║  ██║███████║███████╗
║     ╚═════╝ ╚══════╝  ╚═══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
║                                                           ║
║              Personal Engineering Operating System        ║
║                      Version $ScriptVersion                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor $script:ColorInfo

# Informações de contexto da execução
Write-Host "Root: $RootPath" -ForegroundColor White
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "Mode: $(if ($Force) { 'FORCE (overwrite all)' } else { 'Normal' })" -ForegroundColor White

# ============================================
# VALIDAÇÕES INICIAIS
# ============================================
# Antes de iniciar o setup, validamos:
# 1. Tipo de storage (SSD recomendado)
# 2. Estado de instalação anterior (para atualizações)
#
# Isso garante que o usuário está ciente de qualquer
# problema potencial antes de prosseguir.
# ============================================

Write-Header "Initial Validations"

# Validar Storage - avisa se não for SSD/NVMe
Test-StorageTier -Path $RootPath | Out-Null

# Verificar se já existe uma instalação anterior
# Isso é útil para informar o usuário sobre atualização vs. instalação nova
$currentState = Get-DevBaseState
if ($currentState.version -ne "0.0.0") {
    Write-Step "Existing DevBase: v$($currentState.version)" "INFO"
    Write-Step "Last updated: $($currentState.lastUpdate)" "INFO"
}

# ============================================
# CARREGAMENTO DE MÓDULOS
# ============================================
# O DevBase é modular: cada Setup-* está em seu próprio arquivo.
#
# Benefícios da arquitetura modular:
# • Separação de responsabilidades (Single Responsibility)
# • Facilita manutenção e testes
# • Permite desabilitar módulos específicos
# • Código mais organizado e navegável
#
# A ORDEM dos módulos importa! Dependências devem vir primeiro.
# Ex: setup-core.ps1 cria a estrutura base necessária para os outros.
# ============================================

$modulesPath = Join-Path $PSScriptRoot "modules"

# Lista ordenada de módulos a serem carregados
# IMPORTANTE: Manter ordem correta de dependências!
$modules = @(
    "setup-core.ps1",        # Base: estrutura Johnny.Decimal + governança
    "setup-pkm.ps1",         # PKM: jardim digital + vault privado
    "setup-code.ps1",        # Code: Clean Architecture + template projeto
    "setup-operations.ps1",  # Operations: scripts de automação
    "setup-templates.ps1",   # Templates: padrões técnicos (CI, git, SQL)
    "setup-hooks.ps1",       # Hooks: git hooks para validação
    "setup-ai.ps1"           # AI: módulo de IA local/privacidade
)

# Carrega cada módulo via dot-sourcing
# Se qualquer módulo estiver faltando, o script falha imediatamente
foreach ($module in $modules) {
    $modulePath = Join-Path $modulesPath $module
    if (Test-Path $modulePath) {
        . $modulePath  # Dot-sourcing importa funções para escopo atual
    }
    else {
        Write-Step "Module not found: $module" "ERROR"
        exit 1
    }
}

# ============================================
# EXECUÇÃO DO SETUP (Pipeline Principal)
# ============================================
# Cada módulo é executado em sequência, criando sua parte
# da estrutura. A ordem reflete a lógica de construção:
#
# 1. CORE       → Estrutura base (precisa existir primeiro)
# 2. PKM        → Gestão de conhecimento (depende de 10-19_KNOWLEDGE)
# 3. CODE       → Área de código (depende de 20-29_CODE)
# 4. OPERATIONS → Automação (depende de 30-39_OPERATIONS)
# 5. TEMPLATES  → Padrões técnicos (depende de 05_templates)
# 6. HOOKS      → Git hooks (depende de 06_git_hooks)
# 7. AI         → Módulo IA (depende de 32_ai_models, 33_ai_config)
#
# IDEMPOTÊNCIA: Cada Setup-* verifica se os arquivos já existem
# e só cria/atualiza quando necessário (ou quando -Force é usado).
# ============================================

# 1. Core - Estrutura base Johnny.Decimal e arquivos de governança
Write-Header "1. Core - Structure and Governance"
Setup-Core -RootPath $RootPath

# 2. PKM - Sistema de gestão de conhecimento pessoal
#    Cria jardim digital, vault privado, referências
Write-Header "2. PKM - Knowledge Management"
Setup-PKM -RootPath $RootPath

# 3. Code - Área de desenvolvimento de software
#    Inclui template Clean Architecture + DDD
Write-Header "3. Code - Clean Architecture"
Setup-Code -RootPath $RootPath

# 4. Operations - Scripts de automação e utilitários
#    Git cleanup, Docker cleanup, update-all
Write-Header "4. Operations - Automation"
Setup-Operations -RootPath $RootPath

# 5. Templates - Padrões técnicos reutilizáveis
#    CI/CD, Git patterns, SQL patterns
Write-Header "5. Templates - Technical Standards"
Setup-Templates -RootPath $RootPath

# 6. Git Hooks - Validação automática de commits
#    Conventional Commits, pre-push checks
if (-not $SkipHooks) {
    Write-Header "6. Git Hooks"
    Setup-Hooks -RootPath $RootPath
}
else {
    Write-Step "Git Hooks skipped (-SkipHooks)" "WARN"
}

# 7. AI - Infraestrutura para IA local com privacidade
#    Modelos locais, configuração, pipelines
Write-Header "7. AI - Local Intelligence"
Setup-AI -RootPath $RootPath

# ============================================
# MIGRATION ENGINE - PERSISTÊNCIA DE ESTADO
# ============================================
# O Migration Engine é responsável por:
# • Rastrear qual versão está instalada
# • Manter histórico de atualizações
# • Permitir que futuras versões saibam o que já foi feito
#
# CONCEITO: Similar a Flyway, Alembic, EF Migrations
# Cada "migration" é registrada para evitar re-execução.
#
# O arquivo .devbase_state.json contém:
# {
#   "version": "3.1.0",           // Versão atual instalada
#   "policyVersion": "3.1",       // Versão das políticas
#   "installedAt": "2024-...",    // Data da primeira instalação
#   "lastUpdate": "2024-...",     // Data da última atualização
#   "migrations": [...],          // Lista de migrações aplicadas
#   "modules": [...]              // Módulos instalados
# }
# ============================================

Write-Header "Migration Engine"

# Monta o novo estado preservando data de instalação original
$newState = @{
    version       = $ScriptVersion
    policyVersion = $PolicyVersion
    # Preserva installedAt se já existir (atualização), senão usa agora (instalação nova)
    installedAt   = if ($currentState.installedAt) { $currentState.installedAt } else { (Get-Date -Format "o") }
    lastUpdate    = (Get-Date -Format "o")  # ISO 8601 format
    # Adiciona esta execução ao histórico de migrações
    migrations    = @($currentState.migrations) + @("v$ScriptVersion-$(Get-Date -Format 'yyyyMMdd')")
    modules       = $modules
}

Save-DevBaseState -State $newState
Write-Step "State saved to .devbase_state.json" "OK"

# ============================================
# VALIDAÇÃO FINAL (devbase doctor lite)
# ============================================
# Esta é uma versão simplificada do comando "devbase doctor".
# Verifica se todas as pastas esperadas foram criadas corretamente.
#
# A lista $expectedFolders representa a estrutura mínima
# que deve existir após um setup bem-sucedido. Se alguma
# pasta estiver faltando, algo deu errado.
#
# DICA: Execute "devbase doctor" para validação mais completa.
# ============================================

Write-Header "Final Validation"

# Lista de pastas essenciais que devem existir
# Usa / como separador para compatibilidade cross-platform
# Join-Path converterá para \ no Windows automaticamente
$expectedFolders = @(
    # SYSTEM (00-09): Infraestrutura e configuração
    "00-09_SYSTEM/00_inbox",           # Caixa de entrada (GTD)
    "00-09_SYSTEM/01_dotfiles",        # Configurações pessoais
    "00-09_SYSTEM/05_templates",       # Templates reutilizáveis
    "00-09_SYSTEM/06_git_hooks",       # Git hooks compartilhados
    "00-09_SYSTEM/07_documentation",   # Documentação do DevBase

    # KNOWLEDGE (10-19): Gestão de conhecimento
    "10-19_KNOWLEDGE/11_public_garden",        # Jardim digital público
    "10-19_KNOWLEDGE/12_private_vault",        # Vault privado (Air-Gap)
    "10-19_KNOWLEDGE/15_references/patterns",  # Padrões técnicos
    "10-19_KNOWLEDGE/18_adr-decisions",        # Architecture Decision Records

    # CODE (20-29): Desenvolvimento de software
    "20-29_CODE/21_monorepo_apps",             # Projetos monorepo
    "20-29_CODE/__template-clean-arch",        # Template Clean Architecture

    # OPERATIONS (30-39): Automação e infraestrutura
    "30-39_OPERATIONS/31_backups",             # Scripts de backup
    "30-39_OPERATIONS/35_devbase_cli",         # CLI do DevBase

    # MEDIA (40-49): Assets multimídia
    "40-49_MEDIA_ASSETS",

    # ARCHIVE (90-99): Arquivos históricos
    "90-99_ARCHIVE_COLD"
)

# Verifica cada pasta e reporta status
$allValid = $true
foreach ($folder in $expectedFolders) {
    $fullPath = Join-Path $RootPath $folder
    if (Test-Path $fullPath) {
        Write-Host " [OK] $folder" -ForegroundColor $script:ColorSuccess
    }
    else {
        Write-Host " [X] MISSING: $folder" -ForegroundColor $script:ColorError
        $allValid = $false  # Corrigido: era "false" (string), agora é $false (boolean)
    }
}

# ============================================
# RESUMO FINAL E PRÓXIMOS PASSOS
# ============================================
# O resumo final fornece ao usuário:
# • Confirmação de sucesso/avisos
# • Informações sobre o que foi instalado
# • Orientação sobre o que fazer a seguir
#
# Esta seção é importante para a experiência do usuário,
# ajudando a entender o que aconteceu e como prosseguir.
# ============================================

Write-Header "Setup Complete"

# Mensagem de status baseada na validação
if ($allValid) {
    Write-Host "DevBase v$ScriptVersion installed successfully!" -ForegroundColor $script:ColorSuccess
}
else {
    Write-Host "Setup completed with warnings" -ForegroundColor $script:ColorWarning
}

# Resumo com próximos passos recomendados
Write-Host @"

📍 Location: $RootPath
📋 Policy: v$PolicyVersion
🔧 Script: v$ScriptVersion

Next steps:
 1. Execute: devbase doctor (validate structure)
 2. Configure dotfiles in 01_dotfiles/
 3. Create your first ADR in 18_adr-decisions/
 4. Configure .cursorrules in 35_ai-context/

"@ -ForegroundColor White

# Aviso importante sobre segurança do vault privado
# O Air-Gap é uma proteção crucial que o usuário deve entender
Write-Host "[!] The 12_private_vault folder is protected by Air-Gap" -ForegroundColor $script:ColorWarning

# ============================================
# FIM DO BOOTSTRAP
# ============================================
# O script termina aqui. O workspace está pronto para uso.
#
# Para mais informações:
# • README.md - Visão geral do projeto
# • docs/USAGE-GUIDE.md - Guia completo de utilização
# • docs/ARCHITECTURE.md - Arquitetura interna
# • devbase help - Comandos disponíveis
# ============================================
