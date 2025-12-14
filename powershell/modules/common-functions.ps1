<#
.SYNOPSIS
    Funções utilitárias compartilhadas para o DevBase Setup.

.DESCRIPTION
    Este módulo contém funções fundamentais usadas por todos os outros módulos do DevBase.

    CATEGORIAS DE FUNÇÕES:
    ─────────────────────
    1. OUTPUT FUNCTIONS      → Funções para exibir mensagens formatadas no console
    2. SECURITY FUNCTIONS    → Validações de segurança (path traversal, BOM, permissões)
    3. FILESYSTEM FUNCTIONS  → Operações atômicas de arquivo/diretório

    CONCEITOS IMPORTANTES:
    ──────────────────────
    • IDEMPOTÊNCIA: Todas as funções podem ser chamadas múltiplas vezes sem efeitos
      colaterais indesejados. Ex: New-DirSafe só cria o diretório se não existir.

    • OPERAÇÕES ATÔMICAS: Escritas de arquivo usam técnica de temp file + rename,
      garantindo que falhas não deixem arquivos corrompidos.

    • SEGURANÇA POR DESIGN: Validações de path traversal e permissões estão
      integradas nas funções de filesystem.

.NOTES
    Versão: 3.1.2
    Autor: DevBase Team

    COMO USAR ESTE MÓDULO:
    ─────────────────────
    # No início do seu script, faça dot-sourcing:
    . (Join-Path $PSScriptRoot "common-functions.ps1")

    # Isso importa todas as funções para o escopo atual

.EXAMPLE
    # Exibir mensagens formatadas
    Write-Header "Título da Seção"
    Write-Step "Operação concluída" "OK"
    Write-Step "Algo precisa atenção" "WARN"

.EXAMPLE
    # Criar estrutura de diretórios
    New-DirSafe -Path "C:\MeuProjeto\src\domain"

.EXAMPLE
    # Escrever arquivo de forma segura e atômica
    New-FileSafe -Path "C:\MeuProjeto\README.md" -Content "# Meu Projeto"
#>

# ============================================
# OUTPUT FUNCTIONS
# ============================================
# Funções para exibir mensagens formatadas no console.
# Usam cores definidas no escopo do script ($script:ColorXXX)
# que devem ser definidas no script chamador.
# ============================================

function Write-Header {
    <#
.SYNOPSIS
    Exibe um cabeçalho formatado para seções do script.

.DESCRIPTION
    Cria uma separação visual clara entre seções diferentes da execução.
    Usa a cor definida em $script:ColorHeader (geralmente Magenta).

.PARAMETER Title
    O título a ser exibido no cabeçalho.

.EXAMPLE
    Write-Header "1. Core - Structure and Governance"
    # Output:
    # ========================================
    #  1. Core - Structure and Governance
    # ========================================
#>
    param([string]$Title)
    Write-Host "`n========================================" -ForegroundColor $script:ColorHeader
    Write-Host " $Title" -ForegroundColor $script:ColorHeader
    Write-Host "========================================" -ForegroundColor $script:ColorHeader
}

function Write-Step {
    <#
.SYNOPSIS
    Exibe uma mensagem de status com prefixo e cor apropriados.

.DESCRIPTION
    Função principal para feedback visual durante a execução do script.
    Cada status tem um prefixo e cor específicos para fácil identificação:

    STATUS    PREFIXO    COR       USO
    ──────    ───────    ───       ───
    OK        [+]        Verde     Operação bem-sucedida
    WARN      [!]        Amarelo   Aviso, atenção necessária
    ERROR     [X]        Vermelho  Erro, operação falhou
    INFO      [i]        Ciano     Informação geral

.PARAMETER Message
    A mensagem a ser exibida.

.PARAMETER Status
    O tipo de status: "OK", "WARN", "ERROR", ou "INFO" (padrão).

.EXAMPLE
    Write-Step "Arquivo criado com sucesso" "OK"
    # Output: [+] Arquivo criado com sucesso (verde)

.EXAMPLE
    Write-Step "Configuração não encontrada, usando padrão" "WARN"
    # Output: [!] Configuração não encontrada, usando padrão (amarelo)
#>
    param([string]$Message, [string]$Status = "INFO")

    # Mapeia o status para a cor correspondente
    $color = switch ($Status) {
        "OK" { $script:ColorSuccess }
        "WARN" { $script:ColorWarning }
        "ERROR" { $script:ColorError }
        default { $script:ColorInfo }
    }

    # Mapeia o status para o prefixo visual
    $prefix = switch ($Status) {
        "OK" { " [+]" }
        "WARN" { " [!]" }
        "ERROR" { " [X]" }
        default { " [i]" }
    }

    Write-Host "$prefix $Message" -ForegroundColor $color
}

# ============================================
# SECURITY FUNCTIONS (BASELINES)
# ============================================
# Funções de segurança implementam "Security Baselines" -
# validações fundamentais que previnem vulnerabilidades comuns.
#
# VULNERABILIDADES PREVENIDAS:
# • Path Traversal: Acesso a arquivos fora do diretório permitido
# • BOM Issues: Problemas com UTF-8 BOM em scripts/configs
# • Permission Leaks: Arquivos sensíveis com permissões abertas
# ============================================

function Assert-SafePath {
    <#
.SYNOPSIS
    Previne ataques de Path Traversal validando que o caminho está dentro do root permitido.

.DESCRIPTION
    Path Traversal é uma vulnerabilidade onde um atacante usa sequências como "../"
    para acessar arquivos fora do diretório pretendido.

    EXEMPLO DE ATAQUE:
    ─────────────────
    Input malicioso: "../../../etc/passwd"
    Se não validado, poderia acessar arquivos do sistema!

    COMO FUNCIONA:
    ──────────────
    1. Resolve o caminho absoluto do target (elimina ../ e .\)
    2. Resolve o caminho absoluto do root permitido
    3. Verifica se target começa com root
    4. Se não, lança exceção

.PARAMETER TargetPath
    O caminho que queremos acessar/criar.

.PARAMETER AllowedRoot
    O diretório raiz que define o limite de acesso.

.EXAMPLE
    # Uso seguro
    Assert-SafePath -TargetPath "C:\DevBase\docs\readme.md" -AllowedRoot "C:\DevBase"
    # Passa sem erro

.EXAMPLE
    # Tentativa de path traversal (lança exceção)
    Assert-SafePath -TargetPath "C:\DevBase\..\Windows\system.ini" -AllowedRoot "C:\DevBase"
    # ERRO: SECURITY VIOLATION: Path Traversal detected!

.NOTES
    Esta função é crítica para segurança e deve ser chamada antes de qualquer
    operação de escrita em caminhos derivados de input externo.
#>
    param(
        [Parameter(Mandatory)][string]$TargetPath,
        [Parameter(Mandatory)][string]$AllowedRoot
    )
    try {
        # GetUnresolvedProviderPathFromPSPath resolve caminhos relativos
        # e sequências como ".." sem precisar que o caminho exista
        $absTarget = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($TargetPath)
        $absRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($AllowedRoot)

        # Verifica se o caminho alvo está contido no root permitido
        # InvariantCultureIgnoreCase: ignora maiúsculas/minúsculas (importante no Windows)
        if (-not $absTarget.StartsWith($absRoot, [StringComparison]::InvariantCultureIgnoreCase)) {
            throw "SECURITY VIOLATION: Path Traversal detected! '$absTarget' is outside '$absRoot'."
        }
    }
    catch {
        Write-Step "Path safety check failed: $_" "ERROR"
        throw  # Re-lança a exceção para o chamador tratar
    }
}

function Assert-NoBOM {
    <#
.SYNOPSIS
    Remove o UTF-8 BOM (Byte Order Mark) de arquivos se presente.

.DESCRIPTION
    O BOM (Byte Order Mark) é uma sequência de bytes no início de um arquivo
    que indica a codificação. Em UTF-8, o BOM é: EF BB BF (239 187 191 decimal).

    PROBLEMA COM BOM:
    ─────────────────
    • Scripts shell/bash podem falhar (#!/bin/bash não é reconhecido)
    • Arquivos JSON podem ser inválidos
    • Alguns parsers XML falham
    • Git pode mostrar diferenças falsas

    QUANDO ISSO ACONTECE:
    ─────────────────────
    • Notepad do Windows adiciona BOM por padrão
    • Alguns editores antigos
    • Conversão de codificação mal feita

.PARAMETER Path
    O caminho do arquivo a verificar/sanitizar.

.EXAMPLE
    Assert-NoBOM -Path "C:\DevBase\script.ps1"
    # Se o arquivo tiver BOM, será removido silenciosamente

.NOTES
    Esta função modifica o arquivo se BOM for detectado.
    É chamada automaticamente por Write-FileAtomic.
#>
    param([Parameter(Mandatory)][string]$Path)

    # Só verifica arquivos que existem
    if (-not (Test-Path $Path -PathType Leaf)) { return }

    try {
        # Lê os primeiros 3 bytes do arquivo (tamanho do BOM UTF-8)
        # Helper to support both Windows PowerShell (5.1) and PowerShell Core (6+)
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $bytes = Get-Content -Path $Path -AsByteStream -TotalCount 3 -ErrorAction SilentlyContinue
        }
        else {
            $bytes = Get-Content -Path $Path -Encoding Byte -TotalCount 3 -ErrorAction SilentlyContinue
        }

        # Verifica se os bytes são o BOM UTF-8: EF BB BF
        if ($null -ne $bytes -and $bytes.Count -eq 3 -and
            $bytes[0] -eq 239 -and # EF em decimal
            $bytes[1] -eq 187 -and # BB em decimal
            $bytes[2] -eq 191) {
            # BF em decimal

            Write-Step "Removing UTF-8 BOM from: $(Split-Path $Path -Leaf)" "WARN"

            # Lê o conteúdo completo
            $content = Get-Content -Path $Path -Raw

            # Cria encoding UTF-8 sem BOM (o $false no construtor significa "sem BOM")
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)

            # Reescreve o arquivo sem BOM
            [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
        }
    }
    catch {
        Write-Step "Failed to sanitize BOM: $_" "WARN"
    }
}

function Assert-Permissions {
    <#
.SYNOPSIS
    Verifica permissões de arquivos sensíveis (principalmente em Linux).

.DESCRIPTION
    Em sistemas Unix (Linux/macOS), permissões de arquivo são críticas para segurança.
    Arquivos com credenciais ou dados privados não devem ser legíveis por outros usuários.

    PERMISSÕES UNIX (rwxrwxrwx):
    ──────────────────────────
    Posição 1-3: Owner  (dono do arquivo)
    Posição 4-6: Group  (grupo do arquivo)
    Posição 7-9: Others (todos os outros)

    Para arquivos sensíveis, idealmente:
    • Owner: rwx (leitura, escrita, execução se necessário)
    • Group: --- (nenhuma permissão)
    • Others: --- (nenhuma permissão)
    • Ou seja: chmod 700 arquivo

.PARAMETER Path
    O caminho do arquivo a verificar.

.PARAMETER IsSensitive
    Switch que indica se o arquivo contém dados sensíveis.

.EXAMPLE
    Assert-Permissions -Path "/home/user/.ssh/id_rsa" -IsSensitive
    # Avisa se o arquivo tiver permissões muito abertas

.NOTES
    Esta verificação é mais relevante em Linux/macOS.
    No Windows, o modelo de permissões é diferente (ACLs).
#>
    param(
        [Parameter(Mandatory)][string]$Path,
        [switch]$IsSensitive
    )

    if (-not (Test-Path $Path)) { return }

    # Só faz verificação detalhada em Linux/macOS
    if ($IsLinux) {
        $mode = (Get-Item $Path).Mode

        # Verifica se "others" tem permissão de leitura/escrita/execução (rwx)
        # O padrão ".......rwx" verifica as últimas 3 posições
        if ($IsSensitive -and $mode -match ".......rwx") {
            Write-Step "SECURITY WARNING: '$Path' seems world-writable. Consider 'chmod 700'." "WARN"
        }
    }
}

# ============================================
# FILESYSTEM FUNCTIONS (ATOMIC)
# ============================================
# Funções de filesystem implementam operações ATÔMICAS.
#
# O QUE É ATOMICIDADE?
# ────────────────────
# Uma operação atômica é indivisível - ou completa totalmente,
# ou não acontece. Não há estado intermediário.
#
# POR QUE ISSO IMPORTA?
# ─────────────────────
# Imagine escrever um arquivo grande e a energia cair no meio:
# • SEM atomicidade: arquivo corrompido (escrita parcial)
# • COM atomicidade: arquivo original intacto (nova versão descartada)
#
# TÉCNICA USADA: Write-to-temp + Rename
# ─────────────────────────────────────
# 1. Escreve conteúdo em arquivo temporário
# 2. Renomeia temp para destino final (operação atômica no filesystem)
# 3. Se algo falhar, temp é deletado e original permanece
# ============================================

function New-DirSafe {
    <#
.SYNOPSIS
    Cria um diretório de forma idempotente (só cria se não existir).

.DESCRIPTION
    Função wrapper para criação de diretórios que:
    • Verifica se o diretório já existe antes de criar
    • Usa -Force para criar diretórios pais automaticamente
    • Registra a ação no console
    • Retorna $true se criou, $false se já existia

    IDEMPOTÊNCIA:
    ─────────────
    Pode ser chamada múltiplas vezes sem efeito colateral.
    Na primeira vez: cria o diretório
    Nas próximas: apenas retorna $false (já existe)

.PARAMETER Path
    O caminho do diretório a criar.

.RETURNS
    [bool] $true se o diretório foi criado, $false se já existia.

.EXAMPLE
    New-DirSafe -Path "C:\DevBase\src\domain"
    # Cria toda a estrutura de pastas se necessário
    # Output: [+] Created directory: C:\DevBase\src\domain

.EXAMPLE
    # Chamadas repetidas são seguras
    New-DirSafe -Path "C:\DevBase\src"  # Cria, retorna $true
    New-DirSafe -Path "C:\DevBase\src"  # Não faz nada, retorna $false
#>
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        # -Force cria diretórios pais automaticamente (como mkdir -p)
        # Out-Null suprime a saída do objeto DirectoryInfo
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Step "Created directory: $Path" "OK"
        return $true
    }
    return $false  # Já existe, não fez nada
}

function Write-FileAtomic {
    <#
.SYNOPSIS
    Escreve conteúdo em arquivo de forma ATÔMICA (segura contra corrupção).

.DESCRIPTION
    Implementa o padrão "write-to-temp-then-rename" para garantir que
    a escrita seja atômica. Isso previne corrupção de arquivo em caso
    de falha durante a escrita.

    FLUXO DE EXECUÇÃO:
    ──────────────────
    1. Cria diretório pai se não existir
    2. Gera nome único para arquivo temporário (.filename.GUID.tmp)
    3. Escreve conteúdo no arquivo temporário
    4. Remove BOM UTF-8 se presente (Assert-NoBOM)
    5. Move (rename) o temp para o destino final
    6. Se arquivo estiver em private_vault, verifica permissões

    POR QUE RENAME É ATÔMICO?
    ─────────────────────────
    Em sistemas de arquivos modernos, rename/move dentro do mesmo
    filesystem é uma operação atômica do kernel. O arquivo "aparece"
    no novo nome instantaneamente, sem estado intermediário.

.PARAMETER Path
    O caminho do arquivo destino.

.PARAMETER Content
    O conteúdo a escrever no arquivo.

.PARAMETER Encoding
    A codificação do arquivo (padrão: UTF8).

.RETURNS
    [bool] $true se bem-sucedido.

.EXAMPLE
    Write-FileAtomic -Path "C:\DevBase\config.json" -Content '{"version": "1.0"}'

.EXAMPLE
    $readme = @"
    # Meu Projeto
    Descrição do projeto
    "@
    Write-FileAtomic -Path ".\README.md" -Content $readme

.NOTES
    Em caso de falha, o arquivo temporário é deletado automaticamente.
    O arquivo original (se existir) permanece intacto.
#>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content,
        [string]$Encoding = "UTF8"
    )

    # Garante que o diretório pai existe
    $parentDir = Split-Path $Path -Parent
    if (-not (Test-Path $parentDir)) { New-DirSafe $parentDir }

    # Gera nome único para o arquivo temporário
    # Formato: .filename.GUID.tmp
    # O ponto no início esconde o arquivo em sistemas Unix
    $fileName = Split-Path $Path -Leaf
    $tempPath = Join-Path $parentDir ".$fileName.$([Guid]::NewGuid()).tmp"

    try {
        # Tratamento especial para JSON: não adiciona newline final
        # Outros arquivos recebem newline final (boa prática POSIX)
        if ($Path -like "*.json") {
            Set-Content -Path $tempPath -Value $Content -Encoding $Encoding -Force
        }
        else {
            # Garante que o arquivo termina com newline
            $ContentWithNewline = if ($Content.EndsWith("`n")) { $Content } else { "$Content`n" }
            Set-Content -Path $tempPath -Value $ContentWithNewline -Encoding $Encoding -Force
        }

        # Remove BOM UTF-8 se presente (problema comum em Windows)
        Assert-NoBOM -Path $tempPath

        # OPERAÇÃO ATÔMICA: Move substitui o arquivo destino instantaneamente
        Move-Item -LiteralPath $tempPath -Destination $Path -Force

        # Pós-escrita: verifica permissões se for arquivo sensível
        if ($Path -match "12_private_vault") {
            Assert-Permissions -Path $Path -IsSensitive
        }

        return $true
    }
    catch {
        Write-Step "Failed to write atomic: $_" "ERROR"

        # Limpeza: remove arquivo temporário em caso de erro
        if (Test-Path $tempPath) {
            Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
        }
        throw $_  # Re-lança exceção para o chamador
    }
}

function New-FileSafe {
    <#
.SYNOPSIS
    Cria um arquivo de forma idempotente e segura.

.DESCRIPTION
    Função de alto nível para criação de arquivos que combina:
    • Verificação de existência (idempotência)
    • Escrita atômica (via Write-FileAtomic)
    • Suporte a atualização condicional

    MODOS DE OPERAÇÃO:
    ──────────────────
    1. CRIAR: Se arquivo não existe, cria
    2. IGNORAR: Se arquivo existe e sem -Force/-UpdateIfExists, ignora
    3. ATUALIZAR: Se arquivo existe e com -Force ou -UpdateIfExists, sobrescreve

.PARAMETER Path
    O caminho do arquivo a criar.

.PARAMETER Content
    O conteúdo do arquivo.

.PARAMETER UpdateIfExists
    Se especificado, atualiza o arquivo mesmo se já existir.

.PARAMETER Force
    Alias para UpdateIfExists - força sobrescrita.

.RETURNS
    [bool] $true se o arquivo foi criado/atualizado, $false se ignorado.

.EXAMPLE
    # Criar arquivo (só se não existir)
    New-FileSafe -Path ".\README.md" -Content "# Projeto"

.EXAMPLE
    # Forçar atualização
    New-FileSafe -Path ".\README.md" -Content "# Projeto v2" -Force

.EXAMPLE
    # Múltiplas chamadas são seguras
    New-FileSafe -Path ".\config.json" -Content "{}"  # Cria
    New-FileSafe -Path ".\config.json" -Content "{}"  # Ignora (já existe)
    New-FileSafe -Path ".\config.json" -Content "{}" -UpdateIfExists  # Atualiza
#>
    param(
        [string]$Path,
        [string]$Content,
        [switch]$UpdateIfExists,
        [switch]$Force
    )

    $exists = Test-Path $Path
    $shouldUpdate = $exists -and ($Force.IsPresent -or $UpdateIfExists.IsPresent)

    # Só cria/atualiza se: não existe OU deve atualizar
    if (-not $exists -or $shouldUpdate) {
        Write-FileAtomic -Path $Path -Content $Content
        $action = if (-not $exists) { "Created" } else { "Updated" }
        Write-Step "$action`: $Path" "OK"
        return $true
    }
    return $false  # Arquivo existe e não deve atualizar
}

function Copy-ItemAtomic {
    <#
.SYNOPSIS
    Copia um arquivo de forma atômica usando temp file + rename.

.DESCRIPTION
    Similar a Write-FileAtomic, mas para cópia de arquivos existentes.
    Garante que a cópia seja completa antes de substituir o destino.

    FLUXO:
    ──────
    1. Cria diretório destino se necessário
    2. Copia para arquivo temporário
    3. Move temp para destino final

.PARAMETER Source
    Caminho do arquivo fonte.

.PARAMETER Destination
    Caminho do arquivo destino.

.EXAMPLE
    Copy-ItemAtomic -Source ".\template.md" -Destination ".\docs\README.md"
#>
    param(
        [string]$Source,
        [string]$Destination
    )

    # Garante que diretório destino existe
    $parent = Split-Path $Destination -Parent
    if (-not (Test-Path $parent)) { New-DirSafe $parent }

    # Cria nome único para temp
    $tmp = Join-Path $parent ".$(Split-Path $Destination -Leaf).tmp"

    try {
        # Copia para temp
        Copy-Item $Source $tmp -Force

        # Move (atômico) para destino final
        Move-Item $tmp $Destination -Force
    }
    catch {
        # Limpeza em caso de erro
        Remove-Item $tmp -ErrorAction SilentlyContinue
        throw
    }
}
