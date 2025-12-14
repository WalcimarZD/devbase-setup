<#
.SYNOPSIS
    DevBase v3.0 - Core Module (Módulo Principal)

.DESCRIPTION
    Este é o módulo fundamental do DevBase. Ele é responsável por:

    1. CRIAR A ESTRUTURA JOHNNY.DECIMAL
       ─────────────────────────────────
       A estrutura Johnny.Decimal usa números para organizar pastas:
       • 00-09_SYSTEM      → Configurações do sistema
       • 10-19_KNOWLEDGE   → Documentação e conhecimento
       • 20-29_CODE        → Código fonte
       • 30-39_OPERATIONS  → Automação e operações
       • 40-49_MEDIA       → Mídia e assets
       • 90-99_ARCHIVE     → Arquivo frio (dados antigos)

    2. PUBLICAR ARQUIVOS DE GOVERNANÇA
       ────────────────────────────────
       Arquivos que definem padrões para todo o workspace:
       • .gitignore     → Arquivos a ignorar no Git
       • .editorconfig  → Configurações de editor (indentação, encoding)
       • README.md      → Documentação principal
       • 00.00_index.md → Índice geral do DevBase

    COMO OS TEMPLATES FUNCIONAM:
    ────────────────────────────
    1. Templates ficam em: modules/templates/core/
    2. São arquivos com extensão .template
    3. Contêm placeholders como {{POLICY_VERSION}} e {{DATE}}
    4. Este módulo lê cada template, substitui os placeholders,
       e salva no workspace destino sem a extensão .template

.NOTES
    Versão: 3.0

    DEPENDÊNCIAS:
    • common-functions.ps1 deve estar carregado antes

    VARIÁVEIS ESPERADAS:
    • $script:PolicyVersion - Versão da política (ex: "3.1")

.EXAMPLE
    # Uso típico (chamado pelo bootstrap.ps1)
    Setup-Core -RootPath "C:\Dev_Workspace"
#>

function Setup-Core {
    <#
.SYNOPSIS
    Configura a estrutura de diretórios base e arquivos de governança.

.DESCRIPTION
    Esta função é o coração do DevBase. Ela:

    1. Cria todas as pastas da área 00-09_SYSTEM
    2. Cria pastas de mídia (40-49) e arquivo frio (90-99)
    3. Processa templates de governança (.gitignore, .editorconfig, etc.)

    ORDEM DE EXECUÇÃO IMPORTA:
    ──────────────────────────
    Este módulo deve ser executado PRIMEIRO, pois outros módulos
    dependem da estrutura que ele cria.

.PARAMETER RootPath
    O caminho raiz onde o workspace DevBase será criado.
    Exemplo: "C:\Users\Joao\Dev_Workspace"

.EXAMPLE
    Setup-Core -RootPath "$HOME\Dev_Workspace"

.EXAMPLE
    # Com caminho personalizado
    Setup-Core -RootPath "D:\Projetos\DevBase"
#>
    param([string]$RootPath)

    # Define o caminho onde os templates deste módulo estão localizados
    # Updated to point to shared templates directory (../../shared/templates/core)
    $scriptRootParent = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $templateSourceRoot = Join-Path $scriptRootParent "shared/templates/core"

    # ================================================
    # FASE 1: CRIAÇÃO DA ESTRUTURA DE DIRETÓRIOS
    # ================================================
    # Usamos New-DirSafe que é idempotente (pode ser chamado várias vezes)

    # Raiz do workspace
    New-DirSafe -Path $RootPath

    # 00-09_SYSTEM: Área de configuração e sistema
    # 02_scripts-boot: Scripts que rodam no boot/inicialização
    New-DirSafe -Path (Join-Path $RootPath "00-09_SYSTEM/02_scripts-boot")

    # 40-49_MEDIA_ASSETS: Organização de mídia por tipo
    # 41_raw_images: Imagens originais (RAW, PSD, etc.)
    # 42_videos_render: Vídeos e projetos de edição
    # 43_exports: Exportações finais (PNG, MP4 otimizado, etc.)
    New-DirSafe -Path (Join-Path $RootPath "40-49_MEDIA_ASSETS/41_raw_images")
    New-DirSafe -Path (Join-Path $RootPath "40-49_MEDIA_ASSETS/42_videos_render")
    New-DirSafe -Path (Join-Path $RootPath "40-49_MEDIA_ASSETS/43_exports")

    # 90-99_ARCHIVE_COLD: Arquivo frio (dados que raramente são acessados)
    # 91_archived_projects: Projetos finalizados/abandonados
    # 92_archived_data: Dados históricos, exports antigos
    New-DirSafe -Path (Join-Path $RootPath "90-99_ARCHIVE_COLD/91_archived_projects")
    New-DirSafe -Path (Join-Path $RootPath "90-99_ARCHIVE_COLD/92_archived_data")

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES (LÓGICA DECLARATIVA)
    # ================================================
    # Esta é a parte mais importante: transformar templates em arquivos reais

    # Busca todos os arquivos .template recursivamente no diretório de templates
    $templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse

    foreach ($templateFile in $templateFiles) {
        # ---- PASSO 1: Ler o conteúdo do template ----
        $content = Get-Content -Path $templateFile.FullName -Raw

        # ---- PASSO 2: Substituir placeholders dinâmicos ----
        # Os placeholders são cercados por {{ }} e serão substituídos
        # por valores calculados em tempo de execução

        # {{POLICY_VERSION}} → versão da política (ex: "3.1")
        $content = $content.Replace('{{POLICY_VERSION}}', $script:PolicyVersion)

        # {{DATE}} → data atual no formato ISO (ex: "2024-12-07")
        $content = $content.Replace('{{DATE}}', (Get-Date -Format 'yyyy-MM-dd'))

        # ---- PASSO 3: Calcular caminho de destino ----
        # Precisamos transformar:
        #   modules/templates/core/README.md.template
        # Em:
        #   Dev_Workspace/README.md

        # Obtém o caminho relativo removendo o prefixo do diretório fonte
        # Exemplo: "00-09_SYSTEM/00_inbox/README.md.template"
        $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)

        # Remove a extensão .template do nome do arquivo
        # Exemplo: "README.md.template" → "README.md"
        $destinationFileName = $templateFile.Name.Replace(".template", "")

        # Monta o caminho de destino completo
        # Split-Path -Parent obtém o diretório pai do caminho relativo
        $destinationDir = Join-Path $RootPath (Split-Path $relativeSourcePath -Parent)
        $destinationPath = Join-Path $destinationDir $destinationFileName

        # ---- PASSO 4: Garantir que o diretório destino existe ----
        if (-not (Test-Path $destinationDir)) {
            New-DirSafe -Path $destinationDir
        }

        # ---- PASSO 5: Criar o arquivo (idempotente) ----
        # -UpdateIfExists faz com que o arquivo seja atualizado se já existir
        # Isso é útil para atualizar templates quando o DevBase é atualizado
        New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
    }
}
