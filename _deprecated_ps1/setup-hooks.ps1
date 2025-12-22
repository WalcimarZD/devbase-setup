<#
.SYNOPSIS
    DevBase v3.0 - Git Hooks Module (Módulo de Hooks do Git)

.DESCRIPTION
    Este módulo configura Git Hooks baseados em PowerShell para validação
    automática de commits, código e pushes.

    O QUE SÃO GIT HOOKS?
    ────────────────────
    Git Hooks são scripts que o Git executa automaticamente em determinados
    eventos. Eles permitem automação e validação sem intervenção manual.

    HOOKS CONFIGURADOS:
    ───────────────────
    • pre-commit     → Executado ANTES de cada commit
                       - Verifica formatação (prettier, eslint)
                       - Detecta secrets/credenciais no código
                       - Verifica arquivos grandes

    • commit-msg     → Valida a MENSAGEM do commit
                       - Garante formato Conventional Commits
                       - Ex: "feat(auth): add OAuth2 login"

    • pre-push       → Executado ANTES de cada push
                       - Executa testes
                       - Verifica push para branches protegidas
                       - Alerta sobre force push

    CONVENTIONAL COMMITS
    ────────────────────
    O hook commit-msg valida o formato:

      <type>(<scope>): <description>

    Tipos permitidos:
    • feat     → Nova funcionalidade
    • fix      → Correção de bug
    • docs     → Documentação
    • style    → Formatação
    • refactor → Refatoração
    • perf     → Performance
    • test     → Testes
    • build    → Build/deps
    • ci       → CI/CD
    • chore    → Manutenção

    COMO FUNCIONA A CONFIGURAÇÃO:
    ─────────────────────────────
    1. Hooks são copiados para 06_git_hooks/
    2. Git é configurado para usar esse diretório (core.hooksPath)
    3. Hooks são escritos em PowerShell para portabilidade

    NOTA SOBRE PORTABILIDADE:
    ─────────────────────────
    Hooks em PowerShell requerem PowerShell instalado na máquina.
    Em Linux/macOS, instale PowerShell Core (pwsh).

.NOTES
    Versão: 3.0

    REQUISITOS:
    • Git 2.9+ (para core.hooksPath)
    • PowerShell 5.1+ ou PowerShell Core

.EXAMPLE
    Setup-Hooks -RootPath "C:\Dev_Workspace"
#>

function Setup-Hooks {
    <#
.SYNOPSIS
    Configura Git Hooks e o core.hooksPath do repositório.

.DESCRIPTION
    Copia templates de hooks para o workspace e configura o Git
    para usar o diretório de hooks do DevBase.

.PARAMETER RootPath
    O caminho raiz do workspace DevBase.

.EXAMPLE
    Setup-Hooks -RootPath "$HOME\Dev_Workspace"
#>
    param(
        [string]$RootPath
    )

    # Define caminhos
    $templateSubDir = "hooks"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates"
    $templatesDir = Join-Path $templateSourceRoot $templateSubDir

    # ================================================
    # FASE 1: COPIAR TEMPLATES DE HOOKS
    # ================================================

    # Busca todos os templates de hooks
    $templateFiles = Get-ChildItem -Path $templatesDir -Filter "*.template" -Recurse

    foreach ($templateFile in $templateFiles) {
        # Lê conteúdo do template
        $content = Get-Content -Path $templateFile.FullName -Raw

        # Calcula caminho relativo a partir do diretório de hooks
        $relativePath = $templateFile.FullName.Substring($templatesDir.Length + 1)

        # Remove extensão .template
        $destinationFileName = $relativePath.Replace(".template", "")

        # Monta caminho de destino: 00-09_SYSTEM/06_git_hooks/
        $destinationPath = Join-Path -Path (Join-Path -Path $RootPath -ChildPath "00-09_SYSTEM") -ChildPath "06_git_hooks" | Join-Path -ChildPath $destinationFileName

        # Cria o arquivo (não sobrescreve por padrão - sem -UpdateIfExists)
        # Isso preserva customizações do usuário nos hooks
        New-FileSafe -Path $destinationPath -Content $content
    }

    # ================================================
    # FASE 2: CONFIGURAR GIT HOOKS PATH
    # ================================================
    # O Git 2.9+ suporta core.hooksPath, que permite centralizar hooks
    # em um diretório diferente de .git/hooks/

    # Caminho relativo (funciona em qualquer clone do repo)
    $gitHooksPath = "00-09_SYSTEM/06_git_hooks"

    # Verifica se o workspace é um repositório Git
    if (Test-Path (Join-Path $RootPath ".git")) {
        try {
            # Configura o Git para usar nosso diretório de hooks
            # -C $RootPath: executa no diretório especificado
            git -C $RootPath config core.hooksPath $gitHooksPath
            Write-Step "Git core.hooksPath configured to '$gitHooksPath'" "OK"
        }
        catch {
            # Pode falhar se Git não estiver no PATH
            Write-Step "Failed to configure git core.hooksPath. Make sure 'git' is in your PATH." "WARN"
        }
    }
    # Se não for um repo Git, os hooks ficam prontos para quando for
}
