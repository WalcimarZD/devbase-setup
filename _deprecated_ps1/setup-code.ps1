<#
.SYNOPSIS
    DevBase v3.0 - Code Module (Módulo de Código)

.DESCRIPTION
    Este módulo configura toda a estrutura para desenvolvimento de código,
    incluindo um template baseado em Clean Architecture + DDD.

    ESTRUTURA CRIADA (20-29_CODE):
    ───────────────────────────────
    21_monorepo_apps/           → Aplicações principais
    22_monorepo_packages/       → Bibliotecas compartilhadas
      ├── shared-types/         → Tipos TypeScript/interfaces
      └── shared-utils/         → Funções utilitárias
    23_worktrees/               → Git worktrees para branches paralelas
    __template-clean-arch/      → 📐 Template de projeto

    O QUE É CLEAN ARCHITECTURE?
    ───────────────────────────
    Clean Architecture é um padrão de arquitetura que organiza o código
    em camadas concêntricas, onde as camadas internas não conhecem as externas:

         ┌─────────────────────────────────────┐
         │          PRESENTATION               │  ← UI, API, CLI
         │   ┌─────────────────────────────┐   │
         │   │       APPLICATION           │   │  ← Use Cases, DTOs
         │   │   ┌─────────────────────┐   │   │
         │   │   │      DOMAIN         │   │   │  ← Entities, Rules
         │   │   └─────────────────────┘   │   │
         │   └─────────────────────────────┘   │
         └─────────────────────────────────────┘

    BENEFÍCIOS:
    • Independência de frameworks
    • Testabilidade (camadas isoladas)
    • Independência de UI
    • Independência de banco de dados

    O QUE É DDD (Domain-Driven Design)?
    ────────────────────────────────────
    DDD é uma abordagem que coloca o domínio do negócio no centro do design:
    • Entities: Objetos com identidade única
    • Value Objects: Objetos definidos por seus valores
    • Repositories: Abstrações para persistência
    • Services: Lógica que não pertence a entidades
    • Events: Coisas que acontecem no domínio

    GIT WORKTREES
    ─────────────
    A pasta 23_worktrees é para usar git worktrees, que permitem ter
    múltiplas branches checadas simultaneamente em diretórios separados:

    # Exemplo de uso
    git worktree add ../23_worktrees/feature-x feature/PROJ-123

.NOTES
    Versão: 3.0

.EXAMPLE
    Setup-Code -RootPath "C:\Dev_Workspace"
#>

function Setup-Code {
    <#
.SYNOPSIS
    Configura a estrutura de código e o template Clean Architecture.

.DESCRIPTION
    Cria a hierarquia de pastas para projetos de código e popula
    o template de projeto com a estrutura Clean Architecture + DDD.

.PARAMETER RootPath
    O caminho raiz do workspace DevBase.

.EXAMPLE
    Setup-Code -RootPath "$HOME\Dev_Workspace"
#>
    param([string]$RootPath)

    # Define os caminhos principais
    $Area20 = Join-Path $RootPath "20-29_CODE"
    $templateSourceRoot = Join-Path $PSScriptRoot "templates/code"

    # ================================================
    # FASE 1: ESTRUTURA PRINCIPAL
    # ================================================

    # Raiz da área de código
    New-DirSafe -Path $Area20

    # 21_monorepo_apps: Onde ficam as aplicações principais
    # Ex: api-usuarios, web-dashboard, mobile-app
    New-DirSafe -Path (Join-Path $Area20 "21_monorepo_apps")

    # 22_monorepo_packages: Bibliotecas compartilhadas entre apps
    # Útil para monorepos onde múltiplas apps compartilham código
    $monorepoPackagesPath = Join-Path $Area20 "22_monorepo_packages"
    New-DirSafe -Path $monorepoPackagesPath

    # Pacotes compartilhados pré-definidos:
    # shared-types: Tipos TypeScript, interfaces, enums compartilhados
    New-DirSafe -Path (Join-Path $monorepoPackagesPath "shared-types")
    # shared-utils: Funções utilitárias genéricas
    New-DirSafe -Path (Join-Path $monorepoPackagesPath "shared-utils")

    # 23_worktrees: Para git worktrees (branches paralelas)
    New-DirSafe -Path (Join-Path $Area20 "23_worktrees")

    # ================================================
    # FASE 2: PUBLICAÇÃO DE TEMPLATES
    # ================================================

    $templateFiles = Get-ChildItem -Path $templateSourceRoot -Filter "*.template" -Recurse

    foreach ($templateFile in $templateFiles) {
        $content = Get-Content -Path $templateFile.FullName -Raw

        # Calcular caminho de destino (relativo à Area20)
        $relativeSourcePath = $templateFile.FullName.Substring($templateSourceRoot.Length + 1)
        $destinationFileName = $templateFile.Name.Replace(".template", "")

        # Destino é relativo à Area20 (20-29_CODE)
        $destinationDir = Join-Path $Area20 (Split-Path $relativeSourcePath -Parent)
        $destinationPath = Join-Path $destinationDir $destinationFileName

        # Criar diretório e arquivo
        if (-not (Test-Path $destinationDir)) {
            New-DirSafe -Path $destinationDir
        }

        New-FileSafe -Path $destinationPath -Content $content -UpdateIfExists
    }

    # ================================================
    # FASE 3: ESTRUTURA CLEAN ARCHITECTURE + DDD
    # ================================================
    # Cria as pastas vazias do template que não têm arquivos .template
    # Isso garante que a estrutura completa esteja presente

    $TemplateRoot = Join-Path $Area20 "__template-clean-arch"

    # ---- DOMAIN LAYER (Camada de Domínio) ----
    # O coração do sistema - regras de negócio puras
    # Esta camada NÃO conhece nenhuma outra camada

    # Entities: Objetos com identidade única (User, Order, Product)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/domain/entities")

    # Value Objects: Objetos imutáveis definidos por valores (Email, CPF, Money)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/domain/value-objects")

    # Repositories: Interfaces (contratos) para persistência
    # Implementações ficam em infrastructure/
    New-DirSafe -Path (Join-Path $TemplateRoot "src/domain/repositories")

    # Services: Lógica de domínio que não pertence a nenhuma entidade
    New-DirSafe -Path (Join-Path $TemplateRoot "src/domain/services")

    # Events: Domain Events - coisas que acontecem no domínio (UserCreated, OrderPlaced)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/domain/events")

    # ---- APPLICATION LAYER (Camada de Aplicação) ----
    # Orquestra o domínio - casos de uso da aplicação

    # Use Cases: Cada arquivo = um caso de uso (CreateUser, ProcessPayment)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/application/use-cases")

    # DTOs: Data Transfer Objects - objetos para transporte de dados
    New-DirSafe -Path (Join-Path $TemplateRoot "src/application/dtos")

    # Mappers: Conversores entre Entity ↔ DTO
    New-DirSafe -Path (Join-Path $TemplateRoot "src/application/mappers")

    # Interfaces: Portas (ports) para serviços externos
    New-DirSafe -Path (Join-Path $TemplateRoot "src/application/interfaces")

    # ---- INFRASTRUCTURE LAYER (Camada de Infraestrutura) ----
    # Implementações concretas - detalhes técnicos

    # Persistence/Repositories: Implementações de repositórios (Postgres, MongoDB)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/infrastructure/persistence/repositories")

    # Persistence/Migrations: Migrações de banco de dados
    New-DirSafe -Path (Join-Path $TemplateRoot "src/infrastructure/persistence/migrations")

    # External: Integrações com APIs externas (Stripe, SendGrid)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/infrastructure/external")

    # Messaging: Filas e mensageria (RabbitMQ, SQS)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/infrastructure/messaging")

    # ---- PRESENTATION LAYER (Camada de Apresentação) ----
    # Interface com o mundo externo

    # API: REST/GraphQL controllers
    New-DirSafe -Path (Join-Path $TemplateRoot "src/presentation/api")

    # CLI: Comandos de linha de comando
    New-DirSafe -Path (Join-Path $TemplateRoot "src/presentation/cli")

    # Web: Frontend (se aplicável)
    New-DirSafe -Path (Join-Path $TemplateRoot "src/presentation/web")

    # ---- TESTS (Testes) ----
    # Separados por tipo para facilitar execução seletiva

    # Unit: Testes unitários (rápidos, sem I/O)
    New-DirSafe -Path (Join-Path $TemplateRoot "tests/unit")

    # Integration: Testes de integração (com banco, APIs)
    New-DirSafe -Path (Join-Path $TemplateRoot "tests/integration")

    # E2E: Testes end-to-end (sistema completo)
    New-DirSafe -Path (Join-Path $TemplateRoot "tests/e2e")
}
