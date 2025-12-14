<#
.SYNOPSIS
    DevBase v3.0 - PKM (Personal Knowledge Management) Module

.DESCRIPTION
    Este módulo configura toda a estrutura de gestão de conhecimento pessoal.

    O QUE É PKM?
    ────────────
    Personal Knowledge Management é uma metodologia para capturar, organizar
    e recuperar conhecimento de forma eficiente. O DevBase implementa PKM
    através de uma estrutura clara e templates pré-definidos.

    ESTRUTURA CRIADA (10-19_KNOWLEDGE):
    ────────────────────────────────────
    11_public_garden/     → Conteúdo para compartilhar publicamente
      ├── posts/          → Blog posts e artigos
      ├── notes/          → Notas avulsas e rascunhos
      └── til/            → "Today I Learned" - aprendizados diários

    12_private_vault/     → 🔒 DADOS SENSÍVEIS (Air-Gap)
      ├── journal/        → Diário pessoal
      ├── finances/       → Dados financeiros
      ├── credentials/    → Senhas e chaves (NUNCA sincronizar!)
      └── brag-docs/      → Conquistas para reviews de performance

    15_references/        → Material de referência
      ├── papers/         → Papers acadêmicos e técnicos
      ├── books/          → Notas de livros
      ├── patterns/       → Padrões técnicos (SQL, Git, etc.)
      └── checklists/     → Checklists reutilizáveis

    18_adr-decisions/     → Architectural Decision Records

    CONCEITO: AIR-GAP SECURITY
    ──────────────────────────
    A pasta 12_private_vault é protegida por "air-gap" - ela NUNCA deve
    ser sincronizada com nuvem ou incluída em repositórios Git.
    O .gitignore gerado pelo DevBase já inclui esta proteção.

    CONCEITO: DIGITAL GARDEN
    ────────────────────────
    11_public_garden implementa o conceito de "jardim digital" - um espaço
    onde ideias crescem e evoluem publicamente, diferente de um blog
    tradicional onde posts são "finalizados".

.NOTES
    Versão: 3.0

    SEGURANÇA:
    • 12_private_vault NUNCA deve ir para nuvem ou Git
    • Faça backup criptografado localmente

.EXAMPLE
    Setup-PKM -RootPath "C:\Dev_Workspace"
#>

function Setup-PKM {
    <#
.SYNOPSIS
    Configura a estrutura de Knowledge Management e templates de notas.

.DESCRIPTION
    Cria toda a hierarquia de pastas para PKM e popula com templates
    para diferentes tipos de documentos (TIL, ADR, Journal, etc.).

.PARAMETER RootPath
    O caminho raiz do workspace DevBase.

.EXAMPLE
    Setup-PKM -RootPath "$HOME\Dev_Workspace"
#>
    param([string]$RootPath)

    # Define os caminhos principais
    $Area10 = Join-Path $RootPath "10-19_KNOWLEDGE"
    $Area10 = Join-Path $RootPath "10-19_KNOWLEDGE"
    # Updated to point to shared templates directory (../../shared/templates/pkm)
    $scriptRootParent = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $templateSourceRoot = Join-Path $scriptRootParent "shared/templates/pkm"

    # ================================================
    # FASE 1: CRIAÇÃO DA ESTRUTURA DE DIRETÓRIOS
    # ================================================
    # Criamos imperativemente para maior clareza sobre a estrutura

    # Raiz da área de conhecimento
    New-DirSafe -Path $Area10

    # ---- PUBLIC GARDEN (11): Conteúdo compartilhável ----
    # Este é seu "jardim digital" - ideias em crescimento
    New-DirSafe -Path (Join-Path $Area10 "11_public_garden/posts")   # Blog posts
    New-DirSafe -Path (Join-Path $Area10 "11_public_garden/notes")   # Notas públicas
    New-DirSafe -Path (Join-Path $Area10 "11_public_garden/til")     # Today I Learned

    # ---- PRIVATE VAULT (12): Dados sensíveis - NUNCA SINCRONIZAR! ----
    # Esta área é protegida por "air-gap" - isolamento total da nuvem
    New-DirSafe -Path (Join-Path $Area10 "12_private_vault/journal")     # Diário pessoal
    New-DirSafe -Path (Join-Path $Area10 "12_private_vault/finances")    # Finanças
    New-DirSafe -Path (Join-Path $Area10 "12_private_vault/credentials") # Credenciais
    New-DirSafe -Path (Join-Path $Area10 "12_private_vault/brag-docs")   # Conquistas

    # ---- REFERENCES (15): Material de referência ----
    # Conhecimento externo organizado para consulta rápida
    New-DirSafe -Path (Join-Path $Area10 "15_references/papers")     # Papers acadêmicos
    New-DirSafe -Path (Join-Path $Area10 "15_references/books")      # Notas de livros
    New-DirSafe -Path (Join-Path $Area10 "15_references/patterns")   # Padrões técnicos
    New-DirSafe -Path (Join-Path $Area10 "15_references/checklists") # Checklists

    # ---- ADR (18): Architectural Decision Records ----
    # Documentação de decisões técnicas importantes
    # Formato MADR: https://adr.github.io/madr/
    New-DirSafe -Path (Join-Path $Area10 "18_adr-decisions")

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================
    # Templates incluem: TIL, ADR, Journal, Weeknotes, Brag Docs

    # Busca todos os .template recursivamente
    $templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse

    foreach ($templateFile in $templateFiles) {
        # ---- Ler conteúdo do template ----
        $content = Get-Content -Path $templateFile.FullName -Raw

        # ---- Substituir placeholders dinâmicos ----
        # PKM usa mais placeholders de data que outros módulos

        # {{YEAR}} → ano atual (ex: "2024")
        $content = $content.Replace('{{YEAR}}', (Get-Date -Format 'yyyy'))

        # {{DATE}} → data completa (ex: "2024-12-07")
        $content = $content.Replace('{{DATE}}', (Get-Date -Format 'yyyy-MM-dd'))

        # {{WEEK_NUMBER}} → número da semana ISO (ex: "49")
        $content = $content.Replace('{{WEEK_NUMBER}}', (Get-Date -UFormat '%V'))

        # {{DATE_PLUS_6}} → data daqui a 6 dias (útil para weeknotes)
        $content = $content.Replace('{{DATE_PLUS_6}}', (Get-Date (Get-Date).AddDays(6) -Format 'yyyy-MM-dd'))

        # ---- Calcular caminho de destino ----
        $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)

        # Alguns templates têm {{YEAR}} no nome do arquivo
        # Ex: brag-{{YEAR}}.md.template → brag-2024.md
        $destinationFileName = $templateFile.Name.Replace("{{YEAR}}", (Get-Date -Format 'yyyy')).Replace(".template", "")

        # O destino é relativo à Area10 (10-19_KNOWLEDGE)
        $destinationDir = Join-Path $Area10 (Split-Path $relativeSourcePath -Parent)
        $destinationPath = Join-Path $destinationDir $destinationFileName

        # ---- Criar diretório e arquivo ----
        if (-not (Test-Path $destinationDir)) {
            New-DirSafe -Path $destinationDir
        }

        New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
    }
}
