# 📖 Guia de Uso Completo do DevBase

> Este guia abrangente ensina você a utilizar todas as funcionalidades do DevBase, do básico ao avançado.

---

## 📋 Sumário

1. [Introdução](#1-introdução)
2. [Primeiros Passos](#2-primeiros-passos)
3. [Entendendo a Estrutura Johnny.Decimal](#3-entendendo-a-estrutura-johnnydecimal)
4. [Usando a CLI do DevBase](#4-usando-a-cli-do-devbase)
5. [Gerenciamento de Conhecimento (PKM)](#5-gerenciamento-de-conhecimento-pkm)
6. [Trabalhando com Código](#6-trabalhando-com-código)
7. [Git Hooks e Automação](#7-git-hooks-e-automação)
8. [Segurança e Private Vault](#8-segurança-e-private-vault)
9. [Backup e Recuperação](#9-backup-e-recuperação)
10. [Telemetria Pessoal](#10-telemetria-pessoal)
11. [Módulo de IA Local](#11-módulo-de-ia-local)
12. [Personalização e Extensão](#12-personalização-e-extensão)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Introdução

### O que é o DevBase?

O **DevBase** é um **Sistema Operacional de Engenharia Pessoal** — não um sistema operacional literal, mas uma metodologia e conjunto de ferramentas para:

- 📁 **Organizar** todos os seus arquivos de desenvolvimento de forma consistente
- 📚 **Documentar** conhecimento de forma estruturada e recuperável
- 🔧 **Automatizar** tarefas repetitivas
- 🔒 **Proteger** dados sensíveis
- 📊 **Rastrear** produtividade e conquistas

### Para quem é o DevBase?

- **Desenvolvedores Solo**: Organize seu caos criativo
- **Freelancers**: Gerencie múltiplos projetos com consistência
- **Estudantes**: Documente aprendizado de forma estruturada
- **Tech Leads**: Estabeleça padrões para equipes

### Filosofia

1. **Convenção sobre Configuração**: Estrutura padronizada reduz decisões
2. **Idempotência**: Execute o setup quantas vezes quiser sem efeitos colaterais
3. **Air-Gap Security**: Dados sensíveis ficam locais, sempre
4. **Documentação como Código**: Tudo versionado e rastreável

---

## 2. Primeiros Passos

### 2.1 Verificando Pré-requisitos

Antes de instalar, verifique se você tem os requisitos mínimos:

**Generic (Bash/Zsh/PowerShell):**
```bash
# Verify Python
python3 --version
# Should be 3.10 or superior (Recommended: 3.13)

# Verify Git
git --version
# Should be 2.25 or superior
```

**Linux/macOS:**
```bash
# Verificar Python
python3 --version
# Deve ser 3.8 ou superior

# Verificar Git
git --version
```

### 2.2 Instalação Passo a Passo

#### **Passo 1: Clone o Repositório**

```powershell
# Escolha um local para o código-fonte do DevBase
cd C:\Projetos  # ou ~/Projetos no Linux/macOS

# Clone o repositório
git clone https://github.com/seu-usuario/devbase-setup.git

# Entre no diretório
cd devbase-setup
```

#### **Passo 2: Instale o CLI**

```bash
# Instale via uv (Recomendado)
uv tool install --force .

# Ou via pip
pip install .
```

#### **Passo 3: Execute o Setup Interativo**

```bash
devbase core setup
```

#### **Passo 4: Verifique a Instalação**

```bash
devbase core doctor
```

Saída esperada:
```
========================================
 DevBase Doctor
========================================
Verificando integridade do DevBase em: C:\Users\Seu\Dev_Workspace

 [+] 00-09_SYSTEM
 [+] 10-19_KNOWLEDGE
 [+] 20-29_CODE
 [+] 30-39_OPERATIONS
 [+] 40-49_MEDIA_ASSETS
 [+] 90-99_ARCHIVE_COLD
...
DevBase está SAUDÁVEL
```

### 2.3 Utilidade do Comando Global

Ao instalar via `uv tool install`, o comando `devbase` fica disponível globalmente no seu terminal (Bash, Zsh ou PowerShell). Não é mais necessário configurar aliases manuais para o script principal.

Você pode usar:
```bash
devbase core doctor
devbase dev new "meu-projeto"
```

---

## 3. Entendendo a Estrutura Johnny.Decimal

### 3.1 O que é Johnny.Decimal?

[Johnny.Decimal](https://johnnydecimal.com/) é um sistema de organização que usa números para categorizar e localizar informações rapidamente.

**Formato:** `XX-XX_AREA/XX_categoria/item`

### 3.2 As Áreas do DevBase

| Range | Área | Propósito | Exemplos |
|-------|------|-----------|----------|
| **00-09** | SYSTEM | Configurações, inbox, templates | `.editorconfig`, dotfiles |
| **10-19** | KNOWLEDGE | Documentação, notas, decisões | ADRs, journal, referências |
| **20-29** | CODE | Código fonte, projetos | Apps, bibliotecas, worktrees |
| **30-39** | OPERATIONS | Automação, backups, IA | CLI, scripts, modelos |
| **40-49** | MEDIA_ASSETS | Mídia e recursos visuais | Imagens, vídeos, exports |
| **90-99** | ARCHIVE_COLD | Arquivo frio | Projetos antigos |

### 3.3 Por que esses números?

- **00-09** = "Sistema" - fundamental, acesso constante
- **10-19** = "Conhecimento" - segunda coisa mais acessada
- **20-29** = "Código" - trabalho diário
- **30-39** = "Operações" - automação e suporte
- **40-49** = "Mídia" - recursos menos acessados
- **90-99** = "Arquivo" - acesso raro, dados históricos

### 3.4 Convenções de Nomenclatura

O DevBase usa **kebab-case** para todos os nomes:

```
✅ CORRETO:
meu-projeto/
componente-usuario/
api-autenticacao/

❌ INCORRETO:
MeuProjeto/
componente_usuario/
apiAutenticacao/
```

Use o comando `devbase audit` para verificar violações.

---

## 4. Usando a CLI do DevBase

### 4.1 Visão Geral dos Comandos

```powershell
devbase help  # Exibe todos os grupos de comandos
devbase core --help # Ajuda para o grupo core
```

### 4.2 Comandos de Diagnóstico

#### `devbase core doctor`

Verifica a saúde do workspace:

```powershell
devbase core doctor
```

**O que verifica:**
- ✅ Existência de todas as áreas (00-09, 10-19, etc.)
- ✅ Arquivos de governança (.editorconfig, .gitignore)
- ✅ Proteção Air-Gap do vault privado
- ✅ Configuração de Git hooks
- ✅ Nomenclatura kebab-case

**Exemplo de saída com problemas:**
```
 [X] 20-29_CODE - NÃO ENCONTRADO
 [!] .editorconfig - NÃO ENCONTRADO
Encontrados 2 problemas
Execute 'devbase core doctor --fix' para tentar corrigir
```

#### `devbase dev audit`

Audita a nomenclatura de pastas:

```powershell
# Apenas verificar
devbase dev audit

# Verificar e corrigir automaticamente
devbase dev audit --fix
```

**Exemplo de saída:**
```
Encontradas 3 violações:

  Atual:     MyProject
  Sugerido:  my-project
  Path:      C:\...\21_monorepo_apps\MyProject

  Atual:     ComponenteUI
  Sugerido:  componente-ui
  Path:      C:\...\22_monorepo_packages\ComponenteUI
```

### 4.3 Comandos de Criação

#### `devbase dev new`

Cria um novo projeto a partir de um template:

```powershell
# Com nome especificado
devbase dev new "api-usuarios"

# Interativo (através do wizard)
devbase dev new
```

**O que acontece:**
1. Copia `__template-clean-arch` para `21_monorepo_apps/seu-projeto`
2. Cria toda a estrutura de pastas DDD/Clean Architecture
3. (Futuro) Substitui placeholders nos arquivos

#### `devbase core hydrate`

Atualiza o workspace com os templates mais recentes:

```powershell
# Atualizar apenas arquivos ausentes
devbase core hydrate

# Forçar atualização de todos os templates
devbase core hydrate --force
```

**Quando usar:**
- Após atualizar o DevBase para nova versão
- Para restaurar templates excluídos acidentalmente
- Para aplicar personalizações nos templates

### 4.4 Comandos de Dotfiles

#### `devbase dev link-dotfiles`

Cria symlinks dos seus dotfiles para `$HOME`:

```powershell
devbase dev link-dotfiles
```

**Como usar:**
1. Coloque seus dotfiles em `00-09_SYSTEM/01_dotfiles/links/`
2. Execute o comando
3. O DevBase criará symlinks em `$HOME`

**Exemplo:**
```powershell
# Estrutura em 01_dotfiles/links/
.gitconfig
.vimrc
.zshrc

# Após devbase dev link-dotfiles, em $HOME:
.gitconfig -> C:\...\01_dotfiles\links\.gitconfig
.vimrc -> C:\...\01_dotfiles\links\.vimrc
.zshrc -> C:\...\01_dotfiles\links\.zshrc
```

### 4.5 Comandos de Manutenção

#### `devbase ops backup`

Executa backup usando estratégia 3-2-1:

```powershell
devbase ops backup
```

**O que faz:**
1. Cria cópia local em `31_backups/local/`
2. Exclui `node_modules`, `.git`, logs
3. Mantém últimos 5 backups (limpa antigos automaticamente)

#### `devbase ops clean`

Remove arquivos temporários:

```powershell
devbase ops clean
```

**O que remove:**
- `*.log`, `*.tmp`, `*~`
- `Thumbs.db`, `.DS_Store`
- Backups antigos (mantém últimos 5)

---

## 5. Gerenciamento de Conhecimento (PKM)

### 5.1 O que é PKM?

**Personal Knowledge Management** é uma metodologia para capturar, organizar e recuperar conhecimento pessoal.

### 5.2 Estrutura do PKM no DevBase

```
10-19_KNOWLEDGE/
├── 11_public_garden/     # Conteúdo para compartilhar
│   ├── posts/            # Blog posts
│   ├── notes/            # Notas avulsas
│   └── til/              # Today I Learned
├── 12_private_vault/     # 🔒 Nunca sincronizar!
│   ├── journal/          # Diário
│   ├── finances/         # Finanças
│   ├── credentials/      # Senhas/chaves
│   └── brag-docs/        # Conquistas
├── 15_references/        # Material de referência
│   ├── patterns/         # Padrões técnicos
│   ├── checklists/       # Checklists
│   └── papers/           # Papers/artigos
└── 18_adr-decisions/     # Decisões arquiteturais
```

### 5.3 Digital Garden (Public Garden)

O "jardim digital" é onde você cultiva ideias públicas:

**TIL (Today I Learned):**
```markdown
<!-- til/2024-12-07-git-rebase-autostash.md -->
# Git Rebase com Autostash

Descobri que você pode configurar o Git para fazer stash automático antes do rebase:

```bash
git config --global rebase.autostash true
```

Agora `git pull --rebase` funciona mesmo com mudanças locais!

Tags: git, produtividade
```

**Posts:**
```markdown
<!-- posts/2024-12-07-clean-architecture-na-pratica.md -->
# Clean Architecture na Prática

## Introdução
...
```

### 5.4 ADRs (Architectural Decision Records)

ADRs documentam decisões técnicas importantes:

```markdown
<!-- 18_adr-decisions/ADR-0001-usar-postgresql.md -->
# [ADR-0001] Escolha do Banco de Dados

## Status
**Aceito**

## Contexto
Precisamos escolher um banco de dados para o projeto X.

## Drivers de Decisão
- Suporte a JSON nativo
- Open source
- Equipe tem experiência

## Opções Consideradas

### Opção 1: PostgreSQL
**Prós:** JSON nativo, extensível, maduro
**Contras:** Curva de aprendizado para DBA

### Opção 2: MySQL
**Prós:** Popular, simples
**Contras:** JSON menos maduro

## Decisão
Escolhemos **PostgreSQL** porque combina recursos avançados com experiência da equipe.

## Consequências
- Precisaremos de DBA com experiência em PG
- Podemos usar JSONB para dados semi-estruturados
```

### 5.5 Brag Documents

Documente suas conquistas para reviews de performance:

```markdown
<!-- 12_private_vault/brag-docs/2024-Q4.md -->
# Brag Document Q4 2024

## Impacto
- Reduzi tempo de build de 15min para 3min (80% melhoria)
- Implementei sistema de cache que economizou $2k/mês em AWS

## Projetos Liderados
- Sistema de autenticação OAuth2 (3 meses)
- Migração de banco legado (1 mês)

## Aprendizado
- Certificação AWS Solutions Architect
- Curso de Kubernetes

## Feedback Recebido
- "Excelente trabalho no sistema de auth" - Tech Lead
```

---

## 6. Trabalhando com Código

### 6.1 Estrutura de Código

```
20-29_CODE/
├── 21_monorepo_apps/         # Aplicações
├── 22_monorepo_packages/     # Bibliotecas
├── 23_worktrees/             # Git worktrees
└── __template-clean-arch/    # Template
```

### 6.2 Template Clean Architecture

O DevBase inclui um template seguindo Clean Architecture + DDD:

```
__template-clean-arch/
├── src/
│   ├── domain/               # 💎 Núcleo do negócio
│   │   ├── entities/         # Entidades
│   │   ├── value-objects/    # Value Objects
│   │   ├── repositories/     # Interfaces de repositório
│   │   ├── services/         # Domain Services
│   │   └── events/           # Domain Events
│   ├── application/          # 📋 Casos de uso
│   │   ├── use-cases/        # Use cases
│   │   ├── dtos/             # Data Transfer Objects
│   │   ├── mappers/          # Mapeadores
│   │   └── interfaces/       # Portas
│   ├── infrastructure/       # 🔧 Implementações
│   │   ├── persistence/      # Banco de dados
│   │   ├── external/         # APIs externas
│   │   └── messaging/        # Mensageria
│   └── presentation/         # 🖥️ Interfaces
│       ├── api/              # REST/GraphQL
│       ├── cli/              # Linha de comando
│       └── web/              # Frontend
└── tests/
    ├── unit/                 # Testes unitários
    ├── integration/          # Testes de integração
    └── e2e/                  # Testes end-to-end
```

### 6.3 Criando um Novo Projeto

```powershell
# 1. Criar projeto
devbase dev new "api-pedidos"

# 2. Navegar até o projeto
devbase nav goto code
cd api-pedidos

# 3. Inicializar Git (se desejar repositório separado)
git init

# 4. Instalar dependências (exemplo Node.js)
npm init -y
npm install

# 5. Começar a desenvolver!
```

### 6.4 Worktrees para Branches Paralelas

Git worktrees permitem trabalhar em múltiplas branches simultaneamente:

```powershell
# No diretório do projeto principal
cd .\21_monorepo_apps\meu-projeto\

# Criar worktree para branch de feature
git worktree add ..\..\23_worktrees\meu-projeto-feature-x feature/PROJ-123

# Agora você tem:
# 21_monorepo_apps/meu-projeto/        -> branch main
# 23_worktrees/meu-projeto-feature-x/  -> branch feature/PROJ-123

# Remover worktree quando terminar
git worktree remove ..\..\23_worktrees\meu-projeto-feature-x
```

---

## 7. Git Hooks e Automação

### 7.1 Hooks Disponíveis

```
06_git_hooks/
├── pre-commit.ps1    # Antes de cada commit
├── commit-msg.ps1    # Valida mensagem do commit
├── pre-push.ps1      # Antes de cada push
└── install-hooks.ps1 # Instalador
```

### 7.2 O que Cada Hook Faz

**pre-commit.ps1:**
- Executa formatação (prettier, eslint)
- Detecta credenciais/secrets no código
- Verifica arquivos grandes

**commit-msg.ps1:**
- Valida formato Conventional Commits
- Exemplos válidos: `feat(auth): add OAuth2 login`
- Bloqueia commits sem padrão

**pre-push.ps1:**
- Executa testes antes do push
- Verifica push para branches protegidas (main, develop)
- Alerta sobre force push

### 7.3 Instalando Hooks em um Projeto

```powershell
# Opção 1: Via bootstrap (já faz automaticamente)
# O bootstrap configura core.hooksPath para apontar para 06_git_hooks

# Opção 2: Manual em projeto específico
cd .\21_monorepo_apps\meu-projeto\
git config core.hooksPath "..\..\00-09_SYSTEM\06_git_hooks"

# Opção 3: Usando o script de instalação
cd .\00-09_SYSTEM\06_git_hooks\
.\install-hooks.ps1
```

### 7.4 Conventional Commits

O DevBase valida commits seguindo o padrão:

```
<type>(<scope>): <description>

[body opcional]

[footer opcional]
```

**Tipos permitidos:**

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `style` | Formatação |
| `refactor` | Refatoração |
| `perf` | Performance |
| `test` | Testes |
| `build` | Build/deps |
| `ci` | CI/CD |
| `chore` | Manutenção |

**Exemplos:**
```bash
feat(auth): add OAuth2 Google provider
fix(cart): resolve quantity calculation bug
docs(api): update endpoint documentation
refactor(user): extract validation service
```

---

## 8. Segurança e Private Vault

### 8.1 O que é Air-Gap?

"Air-Gap" significa uma separação física/lógica que impede vazamento de dados. No DevBase, o `12_private_vault` **NUNCA** deve sair da máquina local.

### 8.2 O que Colocar no Vault

| Conteúdo | Pasta | Nunca Sincronizar |
|----------|-------|:-----------------:|
| Senhas, tokens, chaves | `credentials/` | ✅ |
| Diário pessoal | `journal/` | ✅ |
| Dados financeiros | `finances/` | ✅ |
| Documentos legais | `legal/` | ✅ |
| Conquistas pessoais | `brag-docs/` | ⚠️ Opcional |

### 8.3 Proteções Implementadas

1. **`.gitignore`** inclui `12_private_vault`
2. **`devbase doctor`** verifica se vault está protegido
3. **Pre-commit hook** pode detectar secrets

### 8.4 Backup Seguro do Vault

```powershell
# Use criptografia local!

# Opção 1: 7-Zip com senha
7z a -p -mhe=on vault-backup.7z ".\10-19_KNOWLEDGE\12_private_vault"

# Opção 2: GPG
tar -czf - ".\10-19_KNOWLEDGE\12_private_vault" | gpg -c -o vault-backup.tar.gz.gpg

# Opção 3: VeraCrypt container
# Crie um container e mova/monte o vault nele
```

### 8.5 Recuperação do Vault

```powershell
# Descriptografar 7-Zip
7z x vault-backup.7z -oC:\Temp\restored-vault\

# Descriptografar GPG
gpg -d vault-backup.tar.gz.gpg | tar -xzf - -C C:\Temp\restored-vault\
```

---

## 9. Backup e Recuperação

### 9.1 Estratégia 3-2-1

O DevBase recomenda a estratégia 3-2-1:
- **3** cópias dos dados
- **2** tipos de mídia diferentes
- **1** cópia off-site

### 9.2 Usando `devbase backup`

```powershell
# Executar backup
devbase ops backup
```

**O que acontece:**
1. Cria pasta `devbase_backup_YYYYMMDD_HHMMSS` em `31_backups/local/`
2. Copia todo o workspace (exceto exclusões)
3. Mostra tamanho do backup
4. Limpa backups antigos (mantém 5)

**Exclusões automáticas:**
- `node_modules/`
- `.git/`
- `31_backups/`
- `*.log`

### 9.3 Backup Manual Avançado

```powershell
# Windows - Backup incremental com robocopy
robocopy "C:\Dev_Workspace" "D:\Backups\DevBase" /MIR /XD node_modules .git 31_backups /XF *.log /LOG:backup.log

# Linux/macOS - Backup com rsync
rsync -avz --delete \
  --exclude 'node_modules/' \
  --exclude '.git/' \
  --exclude '31_backups/' \
  --exclude '*.log' \
  ~/Dev_Workspace/ /mnt/backup/DevBase/
```

### 9.4 Sincronização com Nuvem

**IMPORTANTE:** Exclua sempre o vault privado!

```powershell
# Exemplo rclone (configure seu remote antes)
rclone sync ~/Dev_Workspace remote:DevBase \
  --exclude "12_private_vault/**" \
  --exclude "node_modules/**" \
  --exclude ".git/**"
```

### 9.5 Recuperação

```powershell
# 1. Restaurar do backup local
Copy-Item -Recurse "D:\Backups\DevBase\devbase_backup_20241207_143000\*" "C:\Dev_Workspace\"

# 2. Reexecutar setup para garantir integridade
devbase core setup --force

# 3. Verificar
devbase doctor
```

---

## 10. Telemetria Pessoal

### 10.1 O que é Telemetria Pessoal?

É o rastreamento das suas próprias atividades para:
- Gerar relatórios semanais (weeknotes)
- Criar brag documents automaticamente
- Entender padrões de produtividade

### 10.2 Comandos de Telemetria

```powershell
# Registrar atividade
devbase ops track "Implementei autenticação OAuth2"
devbase ops track "Code review do PR #123" --type review

# Ver estatísticas
devbase ops stats

# Gerar relatório semanal
devbase ops weekly
devbase ops weekly --output ./weeknotes/semana-49.md

# Gerar brag document
devbase brag
devbase brag -Output ./brag-2024.md
```

### 10.3 Exemplo de Workflow Diário

```powershell
# Início do dia
devbase core doctor  # Verificar ambiente

# Durante o dia, registrar trabalho significativo
devbase ops track "Corrigido bug de timeout na API"
devbase ops track "Reunião de planning - Sprint 23"
devbase ops track "PR #456 aprovado e merged"

# Final do dia
devbase ops stats  # Ver resumo
```

### 10.4 Exemplo de Relatório Semanal

```markdown
# Weeknotes - Semana 49, 2024

## Resumo
- Total de atividades: 12
- Commits: 8
- PRs: 3
- Reuniões: 4

## Destaques
- Implementei sistema de cache Redis
- Corrigi 3 bugs críticos
- Liderei code review de 5 PRs

## Próxima Semana
- Finalizar migração de banco
- Documentar API v2
```

---

## 11. Módulo de IA Local

### 11.1 Estrutura do Módulo de IA

```
30-39_OPERATIONS/
└── 30_ai/
    ├── 31_ai_local/          # Runtime
    │   ├── context/          # Contextos de projeto
    │   └── logs/             # Logs de inferência
    ├── 32_ai_models/         # Modelos
    │   ├── models/           # Arquivos de modelo
    │   ├── metadata/         # Metadados
    │   └── benchmarks/       # Resultados de benchmark
    └── 33_ai_config/         # Configuração
        └── security/         # Políticas de segurança
```

### 11.2 Propósito

O módulo de IA organiza:
- Modelos locais (LLMs, embeddings)
- Contextos para coding assistants
- Logs e telemetria de uso
- Configurações de privacidade

### 11.3 Uso com Coding Assistants

Coloque arquivos de contexto em `31_ai_local/context/`:

```markdown
<!-- context/project-x.md -->
# Contexto do Projeto X

## Stack
- Backend: Node.js + Express
- Database: PostgreSQL
- Frontend: React + TypeScript

## Convenções
- Usar kebab-case para arquivos
- Conventional Commits
- Clean Architecture

## Regras
- Nunca expor credenciais
- Sempre validar inputs
- Testes obrigatórios para features
```

### 11.4 Segurança de IA

O arquivo `33_ai_config/security/policy.md` define políticas:

```markdown
# Política de IA

## Dados Proibidos
- Nunca enviar conteúdo de 12_private_vault
- Nunca incluir tokens/secrets
- Nunca expor dados de clientes

## Modelos Aprovados
- GPT-4 (via Azure, dados criptografados)
- Claude (via API oficial)
- Modelos locais (Ollama, LM Studio)

## Auditoria
- Logs de uso em 31_ai_local/logs
- Review mensal de prompts
```

---

## 12. Personalização e Extensão

### 12.1 Personalizando Templates

Os templates estão em `src/devbase/templates/`. Para personalizar:

```powershell
# 1. Edite o template desejado
notepad .\src\devbase\templates\code\__template-clean-arch\README.md.template

# 2. Aplique as mudanças
devbase core hydrate --force
```

### 12.2 Adicionando Novos Hooks

Crie um novo hook em `src/devbase/templates/hooks/`:

```powershell
# modules/templates/hooks/post-merge.ps1.template
<#
.SYNOPSIS
    Hook executado após git merge
#>

# Reinstalar dependências se package.json mudou
if (git diff HEAD@{1} --name-only | Select-String "package.json") {
    Write-Host "package.json changed, running npm install..."
    npm install
}
```

### 12.3 Criando Comandos CLI Personalizados

O DevBase v4.0 é baseado em Typer. Para adicionar um comando, crie um novo arquivo em `src/devbase/commands/` ou adicione a um existente:

```python
# src/devbase/commands/custom.py
import typer

app = typer.Typer()

@app.command()
def meu_comando():
    """Meu comando personalizado"""
    print("Olá do DevBase!")
```

### 12.4 Estrutura de Pastas Personalizada

Edite `modules/setup-core.ps1` para adicionar pastas:

```powershell
# Adicione suas pastas personalizadas
New-DirSafe -Path (Join-Path $RootPath "50-59_CUSTOM/51_minha-categoria")
```

---

## 13. Troubleshooting

### 13.1 Problemas Comuns

#### **Erro: "Comando não encontrado"**

Certifique-se de que o `uv` adicionou o binário ao seu PATH (geralmente automático). Tente reiniciar o terminal.

#### **Erro: "Permission denied" (Linux/macOS)**

```bash
# Se estiver rodando do código fonte
chmod +x src/devbase/main.py
```

#### **Erro: "Execution Policy" no Windows**

```powershell
# Execute como administrador
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Erro: "Git hooks não executam"**

```powershell
# Verifique a configuração
git config core.hooksPath

# Deve retornar: 00-09_SYSTEM/06_git_hooks

# Se estiver vazio, configure:
git config core.hooksPath "00-09_SYSTEM/06_git_hooks"
```

#### **Erro: "State file corrompido"**

```powershell
# Remova o arquivo de estado
Remove-Item .\.devbase_state.json

# Reexecute o setup
devbase core setup
```

### 13.2 Comandos de Diagnóstico

```powershell
# Verificação completa
devbase core doctor

# Ver estado atual
Get-Content .\.devbase_state.json | ConvertFrom-Json | Format-List

# Verificar Git hooks
git config --local --list | Select-String "core.hookspath"

# Verificar permissões (Windows)
Get-Acl .\12_private_vault\ | Format-List

# Verificar permissões (Linux/macOS)
ls -la ./10-19_KNOWLEDGE/12_private_vault/
```

### 13.3 Resetando o Workspace

Se tudo mais falhar:

```powershell
# CUIDADO: Isso irá recriar tudo!

# 1. Backup do que importa
Copy-Item -Recurse .\10-19_KNOWLEDGE\ C:\Temp\knowledge-backup\
Copy-Item -Recurse .\20-29_CODE\ C:\Temp\code-backup\

# 2. Limpe e reinstale
Remove-Item -Recurse -Force C:\Dev_Workspace
devbase core setup

# 3. Restaure seus arquivos
Copy-Item -Recurse C:\Temp\knowledge-backup\* .\10-19_KNOWLEDGE\
Copy-Item -Recurse C:\Temp\code-backup\* .\20-29_CODE\
```

### 13.4 Obtendo Ajuda

1. Execute `devbase help` para ver comandos disponíveis
2. Consulte este guia
3. Verifique os logs em `30-39_OPERATIONS/33_monitoring/`
4. Abra uma issue no repositório

---

## 🎉 Próximos Passos

Agora que você conhece o DevBase, sugerimos:

1. ✅ Execute `devbase core doctor` para verificar a instalação
2. ✅ Configure seus dotfiles em `01_dotfiles/links/`
3. ✅ Crie seu primeiro projeto com `devbase dev new`
4. ✅ Escreva seu primeiro ADR em `18_adr-decisions/`
5. ✅ Agende backups semanais

---

<div align="center">

**Dúvidas?** Abra uma issue no repositório!

[⬆️ Voltar ao topo](#-guia-de-uso-completo-do-devbase)

</div>
