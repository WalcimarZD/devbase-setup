<#
.SYNOPSIS
    DevBase v3.2 - AI Module (Módulo de Inteligência Artificial)
    
.DESCRIPTION
    Este módulo configura a infraestrutura para trabalhar com IA local,
    incluindo modelos de linguagem (LLMs), assistentes de código e contextos.
    
    ESTRUTURA CRIADA (30-39_OPERATIONS/30_ai):
    ──────────────────────────────────────────
    31_ai_local/              → Runtime de IA local
      ├── context/            → Contextos de projeto para assistentes
      └── logs/               → Logs de inferência e telemetria
    
    32_ai_models/             → Gerenciamento de modelos
      ├── models/             → Arquivos de modelo (.gguf, .bin)
      ├── metadata/           → Metadados dos modelos (configs, READMEs)
      └── benchmarks/         → Resultados de testes de performance
    
    33_ai_config/             → Configuração e políticas
      └── security/           → Políticas de privacidade e segurança
    
    scripts/                  → Scripts de automação para IA
    
    CASOS DE USO:
    ─────────────
    1. CONTEXTOS PARA ASSISTENTES DE CÓDIGO
       Coloque arquivos .md em context/ com informações do projeto:
       - Stack tecnológico
       - Convenções de código
       - Regras de negócio
       O assistente pode usar isso como contexto adicional.
    
    2. MODELOS LOCAIS (Ollama, LM Studio)
       Organize modelos baixados em 32_ai_models/models/
       Mantenha benchmarks em benchmarks/ para comparação
    
    3. POLÍTICAS DE SEGURANÇA
       Defina em 33_ai_config/security/policy.md:
       - Dados que nunca devem ser enviados para IA
       - Modelos aprovados para uso
       - Regras de auditoria
    
    PRIVACIDADE:
    ────────────
    NUNCA envie para IA (externa ou local não segura):
    • Conteúdo de 12_private_vault
    • Tokens, API keys, secrets
    • Dados de clientes/usuários
    • Informações confidenciais de negócio
    
    MODELOS LOCAIS vs CLOUD:
    ────────────────────────
    LOCAL (Ollama, LM Studio):
    + Privacidade total
    + Sem custos de API
    + Funciona offline
    - Requer hardware (GPU)
    - Performance limitada
    
    CLOUD (GPT-4, Claude):
    + Alta performance
    + Sempre atualizado
    - Dados enviados para terceiros
    - Custos por uso
    - Requer internet
    
.NOTES
    Versão: 3.2
    Novidades v3.2: Adição de benchmarks/ e security/
    
.EXAMPLE
    Setup-AI -RootPath "C:\Dev_Workspace"
#>

function Setup-AI {
    <#
.SYNOPSIS
    Cria a estrutura de diretórios para o módulo de IA (v3.2).
    
.DESCRIPTION
    Configura pastas para modelos locais, contextos, logs e políticas
    de segurança relacionadas a uso de IA.
    
.PARAMETER RootPath
    O caminho raiz do workspace DevBase.
    
.EXAMPLE
    Setup-AI -RootPath "$HOME\Dev_Workspace"
#>
    param([string]$RootPath)
    
    # Define caminhos principais
    $Area30 = Join-Path $RootPath "30-39_OPERATIONS"
    $AiRoot = Join-Path $Area30 "30_ai"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates/ai"

    # ================================================
    # FASE 1: ESTRUTURA DE DIRETÓRIOS
    # ================================================
    
    # Raízes
    New-DirSafe -Path $Area30
    New-DirSafe -Path $AiRoot
    
    # ---- 31_ai_local: Runtime e Contexto ----
    # context/: Arquivos de contexto para assistentes de código
    # Exemplo: project-context.md com stack, convenções, etc.
    New-DirSafe -Path (Join-Path $AiRoot "31_ai_local/context")
    
    # logs/: Logs de uso de IA para telemetria pessoal
    # Útil para rastrear quanto você usa IA e para quê
    New-DirSafe -Path (Join-Path $AiRoot "31_ai_local/logs")

    # ---- 32_ai_models: Modelos e Performance ----
    # models/: Arquivos de modelo (.gguf, .bin, etc.)
    # Modelos do Ollama, LM Studio, llama.cpp
    New-DirSafe -Path (Join-Path $AiRoot "32_ai_models/models")
    
    # metadata/: Configurações e READMEs dos modelos
    # Parâmetros de inferência, origens, licenças
    New-DirSafe -Path (Join-Path $AiRoot "32_ai_models/metadata")
    
    # benchmarks/: Resultados de testes de performance (v3.2)
    # Compare diferentes modelos e configurações
    New-DirSafe -Path (Join-Path $AiRoot "32_ai_models/benchmarks")

    # ---- 33_ai_config: Configuração e Segurança ----
    # security/: Políticas de privacidade e segurança (v3.2)
    # Define o que nunca deve ser enviado para IA
    New-DirSafe -Path (Join-Path $AiRoot "33_ai_config/security")
    
    # scripts/: Scripts de automação para IA
    # Instalação de modelos, pipelines, etc.
    New-DirSafe -Path (Join-Path $AiRoot "scripts")

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    # Templates incluem: scripts de benchmark, políticas de segurança
    
    if (Test-Path $templateSourceRoot) {
        $templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse
        
        foreach ($templateFile in $templateFiles) {
            # Lê conteúdo do template
            $content = Get-Content -Path $templateFile.FullName -Raw
            
            # Calcula caminho relativo
            # templates/ai/32_ai_models/benchmark.ps1.template
            # → 30_ai/32_ai_models/benchmark.ps1
            $relativePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)
            $destinationFileName = $templateFile.Name.Replace(".template", "")
            
            # Mapeia templates/ai → 30_ai
            $destinationDir = Join-Path $AiRoot (Split-Path $relativePath -Parent)
            $destinationPath = Join-Path $destinationDir $destinationFileName

            # Cria diretório se necessário (pode haver subpastas profundas)
            if (-not (Test-Path $destinationDir)) {
                New-DirSafe -Path $destinationDir
            }
            
            # Cria arquivo (atualiza se existir para aplicar melhorias)
            New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
        }
    }

    Write-Step "Módulo de IA (v3.2) configurado com Perf & Security." "OK"
}