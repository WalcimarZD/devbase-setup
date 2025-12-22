# DevBase v4.0 - Guia Completo do Usuário

**Do Iniciante ao Avançado**

---

## 📚 Índice

1. [Nível Iniciante: Primeiros Passos](#nivel-iniciante)
2. [Nível Intermediário: Fluxos de Trabalho](#nivel-intermediario)
3. [Nível Avançado: Personalização e Automação](#nivel-avancado)
4. [Referência Completa de Comandos](#referencia-comandos)
5. [Solução de Problemas](#solucao-problemas)
6. [Boas Práticas](#boas-praticas)

---

# Nível Iniciante

## O que é o DevBase?

O **DevBase** é seu "Sistema Operacional de Engenharia Pessoal" - uma ferramenta que organiza todo o seu trabalho de desenvolvimento em uma estrutura lógica e padronizada chamada **Johnny.Decimal**.

**Analogia:** Se o seu computador fosse uma cidade, o DevBase seria o plano urbanístico que garante que:
- Sua casa (código) está no bairro residencial
- Sua biblioteca (conhecimento) está no bairro educacional  
- Suas ferramentas (operações) estão organizadas

### Por que usar o DevBase?

**Antes do DevBase:**
```
~/Projects/
├── app1/
├── old_project_backup_final_v2/
├── Downloads/code-from-email/
└── Desktop/quick-test/
```
😵 Caos total!

**Com DevBase:**
```
~/Dev_Workspace/
├── 20-29_CODE/21_monorepo_apps/app1/
├── 90-99_ARCHIVE_COLD/old_project/
└── 00-09_SYSTEM/00_inbox/quick-test/
```
✨ Organização clara!

---

## Parte 1: Instalação (5 minutos)

### Pré-requisitos

Você precisa ter instalado:
- **Python 3.8+** ([baixar aqui](https://www.python.org/downloads/))
- **Git** ([baixar aqui](https://git-scm.com/downloads))

**Verificar instalação:**
```bash
python --version  # Deve mostrar 3.8 ou superior
git --version     # Qualquer versão recente
```

### Instalar DevBase

**Opção 1: Com `uv` (recomendado - mais rápido):**
```bash
# Instalar uv primeiro (se não tiver)
pip install uv

# Instalar DevBase globalmente
uv tool install devbase
```

**Opção 2: Com `pipx` (alternativa estável):**
```bash
pipx install devbase
```

**Verificar instalação:**
```bash
devbase --help
```

Se aparecer uma tela de ajuda bonita com cores, está tudo certo! 🎉

---

## Parte 2: Primeiro Setup (10 minutos)

### Criando seu Workspace

Execute o comando mágico:
```bash
devbase core setup
```

**O que vai acontecer:**

#### Passo 1: Verificação de Pré-requisitos
```
Checking prerequisites...

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool   ┃ Status                 ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Python │ ✅ Python 3.12.1       │
│ Git    │ ✅ git version 2.45.0  │
└────────┴────────────────────────┘
```

✅ Se tudo estiver verde, prossiga!  
❌ Se algo estiver vermelho, instale a ferramenta indicada.

#### Passo 2: Escolher Localização
```
Workspace location [C:\Users\você\Dev_Workspace]:
```

**💡 Dica:** Apenas aperte Enter para aceitar o padrão (recomendado).

#### Passo 3: Selecionar Módulos
```
📚 PKM (Personal Knowledge Management) [Y/n]: y
🤖 AI (Local AI tools) [y/N]: n
🔧 Operations (Automation, backups) [Y/n]: y
```

**Para iniciantes, recomendo:**
- PKM: **Sim** (para documentar seu aprendizado)
- AI: **Não** (pode adicionar depois)
- Operations: **Sim** (para backups e tracking)

#### Passo 4: Air-Gap (Segurança)
```
🔒 Enable Air-Gap protection for private vault? [Y/n]: y
```

**O que é isso?** Impede que seu cofre privado (`12_private_vault`) seja sincronizado para a nuvem acidentalmente.

**Recomendação:** **Sim** (segurança nunca é demais).

#### Passo 5: Confirmação
```
Workspace  │ C:\Users\você\Dev_Workspace
Modules    │ PKM, OPERATIONS
Air-Gap    │ Enabled

Proceed with setup? [Y/n]:
```

Digite `y` e Enter. Aguarde enquanto o DevBase cria toda a estrutura! ⚙️

---

## Parte 3: Entendendo a Estrutura

Após o setup, você terá:

```
~/Dev_Workspace/
├── 00-09_SYSTEM/          # Configurações e arquivos de sistema
│   ├── 00_inbox/          # Arquivos temporários
│   ├── 01_dotfiles/       # Suas configurações (.bashrc, etc.)
│   └── 05_templates/      # Templates de projeto
│
├── 10-19_KNOWLEDGE/       # Seu conhecimento
│   ├── 11_public_garden/  # Notas públicas
│   └── 12_private_vault/  # Notas privadas (protegidas)
│
├── 20-29_CODE/            # Seus projetos de código
│   ├── 21_monorepo_apps/  # Aplicações completas
│   └── 22_monorepo_packages/ # Bibliotecas e pacotes
│
├── 30-39_OPERATIONS/      # Operações e automação
│   ├── 30_ai/             # Modelos de IA locais
│   └── 31_backups/        # Backups automáticos
│
├── 40-49_MEDIA_ASSETS/    # Assets de mídia
└── 90-99_ARCHIVE_COLD/    # Projetos arquivados
```

### Sistema Johnny.Decimal Explicado

**Formato:** `XX-YY_CATEGORIA/ZZ_subcategoria`

- **XX-YY:** Área (ex: 20-29 = CODE)
- **ZZ:** Categoria específica (ex: 21 = monorepo_apps)

**Por que isso é útil?**
- Você **sempre** sabe onde está algo
- Navegar fica **previsível**
- Backups ficam **organizados**

---

## Parte 4: Primeiro Health Check

Verifique se está tudo OK:

```bash
devbase core doctor
```

**Saída esperada:**
```
DevBase Health Check
Workspace: C:\Users\você\Dev_Workspace

Checking folder structure...
  ✓ 00-09_SYSTEM
  ✓ 10-19_KNOWLEDGE
  ✓ 20-29_CODE
  ...

✅ DevBase is HEALTHY
```

Se ver isso, parabéns! Você completou o setup! 🎊

---

## Parte 5: Seu Primeiro Projeto

Vamos criar um projeto de verdade:

```bash
devbase dev new meu-primeiro-app
```

**O que vai acontecer:**

1. **Customização Interativa:**
```
Project Configuration

Description [MeuPrimeiroApp Application]: Meu app de teste
License [MIT]: MIT
Author [Seu Nome]: Seu Nome
```

2. **Criação Automática:**
```
Creating project 'meu-primeiro-app'...

  ✓ README.md
  ✓ .gitignore
  → LICENSE
  
✅ Project created!

Location: C:\Users\você\Dev_Workspace\20-29_CODE\21_monorepo_apps\meu-primeiro-app

Next steps:
  1. cd 20-29_CODE\21_monorepo_apps\meu-primeiro-app
  2. git init
  3. code .
```

### Entrando no Projeto

**Maneira tradicional:**
```bash
cd ~/Dev_Workspace/20-29_CODE/21_monorepo_apps/meu-primeiro-app
```

**Maneira DevBase (muito mais fácil!):**
```bash
# Navegue até a área de código
devbase nav goto code

# Agora você está em 21_monorepo_apps
cd meu-primeiro-app
```

---

## Parte 6: Tracking do seu Trabalho

O DevBase pode rastrear suas atividades:

```bash
devbase ops track "Criei meu primeiro projeto com DevBase"
```

**Saída:**
```
✓ Tracked: [coding:meu-primeiro-app] Criei meu primeiro projeto com DevBase
```

**Note:** O DevBase automaticamente detectou:
- Que você está dentro de um projeto (`meu-primeiro-app`)
- Que é uma atividade de código (`coding`)

### Ver suas Estatísticas

```bash
devbase ops stats
```

```
Activity Statistics
Total events: 1

┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Type                    ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ coding:meu-primeiro-app │ 1     │
└─────────────────────────┴───────┘
```

---

## ✅ Checkpoint Iniciante

Você agora sabe:
- ✅ Instalar o DevBase
- ✅ Criar um workspace organizado
- ✅ Entender a estrutura Johnny.Decimal
- ✅ Criar projetos
- ✅ Navegar com `goto`
- ✅ Fazer tracking de atividades

**Próximo nível:** Fluxos de trabalho do dia a dia →

---

# Nível Intermediário

## Fluxos de Trabalho Reais

### Cenário 1: Desenvolvendo uma API

**Dia 1: Criação do Projeto**
```bash
# Criar projeto com template específico
devbase dev new minha-api --template api

# Navegar e inicializar Git
devbase nav goto code
cd minha-api
git init
git add .
git commit -m "Initial commit"

# Registrar a criação
devbase ops track "Iniciei projeto minha-api"
```

**Dia 2-5: Desenvolvimento**
```bash
cd minha-api

# Trabalhar...
# Fazer commits...

# Ao final do dia, trackear progresso
devbase ops track "Implementei endpoints de autenticação"
devbase ops track "Configurei banco de dados PostgreSQL"
devbase ops track "Escrevi testes unitários"
```

**Sexta-feira: Relatório Semanal**
```bash
devbase ops weekly --output ~/weeknotes.md
```

**Conteúdo gerado (`weeknotes.md`):**
```markdown
# Weekly Report - 2025-12-22

## Activity Summary
- Total events: 4
- Projects worked on: minha-api

## Events by Type
- coding:minha-api: 4 events

## Detailed Timeline
- 2025-12-19: Iniciei projeto minha-api
- 2025-12-20: Implementei endpoints de autenticação
- 2025-12-21: Configurei banco de dados PostgreSQL
- 2025-12-22: Escrevi testes unitários
```

---

### Cenário 2: Gerenciando Conhecimento

O DevBase tem dois espaços para conhecimento:
- **11_public_garden:** Notas públicas (OK para compartilhar)
- **12_private_vault:** Notas privadas (protegidas por Air-Gap)

**Criando uma nota de aprendizado:**
```bash
# Navegar para área de conhecimento
devbase nav goto knowledge

# Criar nota
echo "# Aprendizado: Git Rebase" > git-rebase.md
echo "Data: $(date)" >> git-rebase.md
echo "" >> git-rebase.md
echo "## O que aprendi..." >> git-rebase.md
```

**Criando uma ADR (Architecture Decision Record):**
```bash
devbase nav goto knowledge
cd ADRs/
echo "# ADR 001: Escolha do Banco de Dados" > adr-001-database.md
```

**💡 Dica:** Use templates para padronizar suas notas!

---

### Cenário 3: Backup e Manutenção

**Backup Manual:**
```bash
devbase ops backup
```

**Saída:**
```
Creating backup...
  ✓ Compressing workspace
  ✓ Saved to: 30-39_OPERATIONS/31_backups/devbase_2025-12-22.tar.gz

Backup complete! (425 MB)
```

**Limpeza de Arquivos Temporários:**
```bash
devbase ops clean
```

```
Cleaning temporary files...
  ✓ Removed 15 files from 00_inbox
  ✓ Removed cache files
  ✓ Freed 120 MB

Cleanup complete!
```

---

## Comandos Context-Aware

Uma das melhores features do DevBase v4.0 é a **detecção automática de contexto**.

### Tracking Inteligente

**Sem contexto (workspace root):**
```bash
cd ~/Dev_Workspace
devbase ops track "Revisei documentação"
✓ Tracked: [work] Revisei documentação
```

**Com contexto (dentro de um projeto):**
```bash
cd ~/Dev_Workspace/20-29_CODE/21_monorepo_apps/minha-api
devbase ops track "Corrigi bug de autenticação"
✓ Tracked: [coding:minha-api] Corrigi bug de autenticação
              ^^^^^^^^^^^^^^^ AUTO-DETECTADO!
```

**Com contexto (área de conhecimento):**
```bash
cd ~/Dev_Workspace/10-19_KNOWLEDGE/11_public_garden
devbase ops track "Estudei design patterns"
✓ Tracked: [learning] Estudei design patterns
              ^^^^^^^^ AUTO-DETECTADO!
```

### Override Manual (quando necessário)

```bash
devbase ops track "Reunião com cliente" --type meeting
✓ Tracked: [meeting] Reunião com cliente
```

---

## Navegação Semântica Avançada

Além de `goto code`, existem 9 atalhos:

| Atalho | Destino |
|--------|---------|
| `code` | 20-29_CODE/21_monorepo_apps |
| `packages` | 20-29_CODE/22_monorepo_packages |
| `knowledge` | 10-19_KNOWLEDGE/11_public_garden |
| `vault` | 10-19_KNOWLEDGE/12_private_vault |
| `ai` | 30-39_OPERATIONS/30_ai |
| `backups` | 30-39_OPERATIONS/31_backups |
| `inbox` | 00-09_SYSTEM/00_inbox |
| `templates` | 00-09_SYSTEM/05_templates |
| `dotfiles` | 00-09_SYSTEM/01_dotfiles |

**Exemplo de uso:**
```bash
# Ver onde templates estão armazenados
devbase nav goto templates
/home/user/Dev_Workspace/00-09_SYSTEM/05_templates

# Navegar para lá
cd $(devbase nav goto templates)
```

---

## Shell Integration (Power User)

Para tornar a navegação ainda mais rápida, adicione ao seu `~/.bashrc` ou `~/.zshrc`:

```bash
# Copie o script de integração
cp ~/Dev_Workspace/devbase-setup/scripts/shell-integration.sh ~/.devbase/

# Adicione ao seu RC file
echo 'source ~/.devbase/shell-integration.sh' >> ~/.bashrc
source ~/.bashrc
```

**Agora você tem novos comandos:**

```bash
# Navegação direta (sem 'devbase nav')
goto code
goto vault

# Tracking rápido
t "Implementei feature X"

# Outros aliases
db-doctor     # = devbase core doctor
db-new app1   # = devbase dev new app1
```

---

## ✅ Checkpoint Intermediário

Você agora domina:
- ✅ Fluxos completos de desenvolvimento
- ✅ Gerenciamento de conhecimento (PKM)
- ✅ Tracking context-aware
- ✅ Navegação semântica
- ✅ Backup e manutenção
- ✅ Shell integration

**Próximo nível:** Personalização e automação avançadas →

---

# Nível Avançado

## Customização de Templates

### Anatomia de um Template

Templates ficam em `00-09_SYSTEM/05_templates/__template-NOME/`.

**Estrutura básica:**
```
__template-meu-custom/
├── README.md.template
├── src/
│   └── main.py.template
├── tests/
│   └── test_main.py.template
└── .gitignore
```

### Usando Variáveis Jinja2

Arquivos `.template` suportam variáveis:

**README.md.template:**
```markdown
# {{project_name_pascal}}

{{description}}

**Author:** {{author}}
**License:** {{license}}
**Created:** {{date}}

## Installation

\`\`\`bash
pip install {{project_name}}
\`\`\`

## Usage

\`\`\`python
from {{project_name_snake}} import main

main()
\`\`\`
```

**Variáveis disponíveis:**
- `{{project_name}}` - Nome original (kebab-case): `meu-projeto`
- `{{project_name_pascal}}` - PascalCase: `MeuProjeto`
- `{{project_name_snake}}` - snake_case: `meu_projeto`
- `{{project_name_camel}}` - camelCase: `meuProjeto`
- `{{author}}` - Autor (do git config)
- `{{year}}` - Ano atual
- `{{date}}` - Data (YYYY-MM-DD)
- `{{timestamp}}` - ISO timestamp
- `{{description}}` - Descrição (prompt interativo)
- `{{license}}` - Licença (MIT, Apache, etc.)

### Criar seu Próprio Template

```bash
# Ir para área de templates
devbase nav goto templates

# Criar novo template
mkdir __template-fastapi
cd __template-fastapi

# Criar estrutura
mkdir src tests
touch README.md.template
touch src/main.py.template
touch tests/test_api.py.template
```

**src/main.py.template:**
```python
"""
{{project_name_pascal}} - {{description}}
Author: {{author}}
"""
from fastapi import FastAPI

app = FastAPI(title="{{project_name_pascal}}")

@app.get("/")
def read_root():
    return {"message": "Welcome to {{project_name_pascal}}!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Usar o template:**
```bash
devbase dev new minha-api --template fastapi
```

---

## Arquivo de Configuração

Crie `~/.devbase/config.toml` para personalizar comportamentos:

```toml
[workspace]
# Onde criar workspace por padrão
root = "~/Dev_Workspace"
# Auto-detectar workspace ao rodar comandos
auto_detect = true

[behavior]
# Modo expert (menos prompts)
expert_mode = false
# Saída colorida
color_output = true

[telemetry]
# Habilitar tracking
enabled = true
# Auto-track commits do Git
auto_track_commits = false

[templates]
# Template padrão para 'devbase dev new'
default_template = "clean-arch"

[aliases]
# Aliases customizados
work = "coding"
study = "learning"
```

**Usar configuração:**
```bash
# Agora 'devbase dev new' usa 'clean-arch' por padrão
devbase dev new projeto-x  # Usa clean-arch automaticamente

# Ou especifique outro
devbase dev new api-y --template fastapi
```

---

## Quick Actions (Automação)

### Quickstart: Setup Completo em 1 Comando

Criar projeto + Git + VS Code:
```bash
devbase quick quickstart meu-app-completo
```

**O que acontece:**
1. Cria projeto com template padrão
2. `git init`
3. `git add .`
4. `git commit -m "Initial commit from DevBase"`
5. `code .` (abre VS Code)

**Tudo em ~5 segundos!** ⚡

### Sync: Manutenção Completa

Manutenção semanal em 1 comando:
```bash
devbase quick sync
```

**O que acontece:**
1. `devbase core doctor` (health check)
2. `devbase core hydrate` (atualiza templates)
3. `devbase ops backup` (cria backup)

---

## Integração com Git Hooks

Automatize tracking ao fazer commits:

**`.git/hooks/post-commit`:**
```bash
#!/bin/bash
# Auto-track commits

# Pegar mensagem do commit
COMMIT_MSG=$(git log -1 --pretty=%B)

# Trackear automaticamente
devbase ops track "Commit: $COMMIT_MSG" --type coding

echo "✓ Tracked commit activity"
```

**Tornar executável:**
```bash
chmod +x .git/hooks/post-commit
```

**Agora todo commit é trackeado automaticamente!**

---

## Auditoria de Código

### Verificar Convenções de Nomes

```bash
devbase dev audit
```

**Saída:**
```
Code Audit Report
Workspace: ~/Dev_Workspace

Checking naming conventions...

20-29_CODE/21_monorepo_apps:
  ✓ minha-api (kebab-case)
  ✗ MyOldApp (should be: my-old-app)
  ✓ projeto-teste (kebab-case)

1 violation found.
```

### Auto-Correção

```bash
devbase dev audit --fix
```

```
Renaming:
  MyOldApp → my-old-app

Continue? [y/N]: y

✓ Renamed 1 project
```

---

## Advanced Analytics

### Relatório Custom com Filtros

```bash
# Apenas eventos de coding
devbase ops stats --type coding

# Estatísticas de um projeto específico
cd meu-projeto
devbase ops stats

# Relatório mensal
devbase ops weekly --days 30 --output monthly-report.md
```

---

## Integração com VS Code

Crie tasks personalizadas em `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "DevBase: Health Check",
      "type": "shell",
      "command": "devbase core doctor",
      "problemMatcher": []
    },
    {
      "label": "DevBase: Track Progress",
      "type": "shell",
      "command": "devbase ops track \"${input:trackMessage}\"",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "trackMessage",
      "type": "promptString",
      "description": "Activity to track"
    }
  ]
}
```

**Uso:** `Ctrl+Shift+P` → "Tasks: Run Task" → "DevBase: Track Progress"

---

## ✅ Checkpoint Avançado

Você agora é um expert em:
- ✅ Criar templates customizados com Jinja2
- ✅ Configuração global (config.toml)
- ✅ Quick actions para automação
- ✅ Git hooks para tracking automático
- ✅ Auditoria e correção de código
- ✅ Integração com IDEs

---

# Referência Completa de Comandos

## Core (Gerenciamento do Workspace)

### `devbase core setup`
**O que faz:** Cria ou atualiza estrutura do workspace  
**Quando usar:** Primeira instalação ou após mudanças de versão  
**Opções:**
- `--interactive / --no-interactive` - Wizard (padrão: sim)
- `--force` - Sobrescrever arquivos existentes
- `--dry-run` - Mostrar o que seria feito

**Exemplos:**
```bash
devbase core setup                    # Setup completo com wizard
devbase core setup --no-interactive   # Usar padrões sem perguntas
devbase core setup --force            # Recriar estrutura
```

---

### `devbase core doctor`
**O que faz:** Verifica saúde do workspace  
**Quando usar:** Ao suspeitar de problemas, ou semanalmente  
**Checks realizados:**
- Estrutura de pastas Johnny.Decimal
- Arquivos de governança (.editorconfig, .gitignore)
- Proteção Air-Gap
- Integridade do `.devbase_state.json`

**Exemplo:**
```bash
devbase core doctor
```

---

### `devbase core hydrate`
**O que faz:** Atualiza templates do repositório  
**Quando usar:** Após atualizar DevBase ou ao adicionar novos templates  
**Opções:**
- `--force` - Sobrescrever templates modificados

**Exemplo:**
```bash
devbase core hydrate --force
```

---

## Dev (Desenvolvimento)

### `devbase dev new <nome>`
**O que faz:** Cria novo projeto a partir de template  
**Quando usar:** Ao iniciar qualquer novo projeto  
**Opções:**
- `--template <nome>` - Template específico (padrão: clean-arch)
- `--interactive / --no-interactive` - Customização (padrão: sim)

**Exemplos:**
```bash
devbase dev new meu-app                     # Interativo com template padrão
devbase dev new api --template fastapi      # Template específico
devbase dev new lib --no-interactive        # Sem prompts (usa defaults)
```

---

### `devbase dev audit`
**O que faz:** Verifica convenções de nomes (kebab-case)  
**Quando usar:** Antes de commits importantes ou periodicamente  
**Opções:**
- `--fix` - Auto-corrigir violações

**Exemplos:**
```bash
devbase dev audit        # Apenas reportar
devbase dev audit --fix  # Corrigir automaticamente
```

---

## Ops (Operações)

### `devbase ops track <mensagem>`
**O que faz:** Registra atividade para analytics  
**Quando usar:** Ao completar tarefas significativas  
**Opções:**
- `--type <tipo>` - Tipo manual (padrão: auto-detectado)

**Auto-detecção de tipo por localização:**
- `code/packages` → `coding`
- `knowledge` → `learning`
- `vault` → `personal`
- Outros → `work`

**Exemplos:**
```bash
cd meu-projeto
devbase ops track "Implementei login OAuth"
# → [coding:meu-projeto] Implementei login OAuth

devbase ops track "Reunião de planejamento" --type meeting
# → [meeting] Reunião de planejamento
```

---

### `devbase ops stats`
**O que faz:** Mostra estatísticas de atividades  
**Quando usar:** Para ver resumo do trabalho realizado  

**Exemplo:**
```bash
devbase ops stats
```

**Saída:**
```
Activity Statistics
Total events: 42

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Type              ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ coding:minha-api  │ 15    │
│ learning          │ 8     │
│ meeting           │ 3     │
│ work              │ 16    │
└───────────────────┴───────┘
```

---

### `devbase ops weekly`
**O que faz:** Gera relatório semanal em Markdown  
**Quando usar:** Sexta-feira para resumo da semana  
**Opções:**
- `--output <arquivo>` - Salvar em arquivo (padrão: stdout)
- `--days <N>` - Período (padrão: 7)

**Exemplos:**
```bash
devbase ops weekly                          # Ver no terminal
devbase ops weekly --output weeknotes.md    # Salvar arquivo
devbase ops weekly --days 30 --output monthly.md  # Relatório mensal
```

---

### `devbase ops backup`
**O que faz:** Cria backup compactado do workspace  
**Quando usar:** Antes de mudanças críticas, ou semanalmente  

**Exemplo:**
```bash
devbase ops backup
```

**Destino:** `30-39_OPERATIONS/31_backups/devbase_YYYY-MM-DD.tar.gz`

---

### `devbase ops clean`
**O que faz:** Remove arquivos temporários  
**Quando usar:** Quando workspace parecer "pesado"  

**Remove:**
- Arquivos em `00_inbox` (após 30 dias)
- Caches
- Arquivos `.DS_Store`, `Thumbs.db`

**Exemplo:**
```bash
devbase ops clean
```

---

## Nav (Navegação)

### `devbase nav goto <localização>`
**O que faz:** Imprime caminho para localização semântica  
**Quando usar:** Para navegação rápida ou scripts  

**Localizações disponíveis:**
- `code` - Aplicações principais
- `packages` - Bibliotecas/pacotes
- `knowledge` - Notas públicas
- `vault` - Notas privadas
- `ai` - Modelos de IA
- `backups` - Backups
- `inbox` - Temp files
- `templates` - Templates de projeto
- `dotfiles` - Configurações

**Exemplos:**
```bash
# Ver caminho
devbase nav goto code
/home/user/Dev_Workspace/20-29_CODE/21_monorepo_apps

# Navegar
cd $(devbase nav goto code)

# Com shell integration
goto code  # Navega diretamente!
```

---

## Quick (Ações Rápidas)

### `devbase quick quickstart <nome>`
**O que faz:** Cria projeto + Git + abre VS Code  
**Quando usar:** Para setup instantâneo de projeto  

**Executa:**
1. `devbase dev new <nome> --no-interactive`
2. `git init && git add . && git commit`
3. `code .`

**Exemplo:**
```bash
devbase quick quickstart minha-startup
```

---

### `devbase quick sync`
**O que faz:** Manutenção completa do workspace  
**Quando usar:** Rotina semanal de manutenção  

**Executa:**
1. `devbase core doctor`
2. `devbase core hydrate`
3. `devbase ops backup`

**Exemplo:**
```bash
devbase quick sync
```

---

# Solução de Problemas

## Problema: "Workspace not found"

**Sintoma:**
```
Error: No DevBase workspace found
```

**Causas possíveis:**
1. Você nunca executou `devbase core setup`
2. Está fora do workspace e sem padrão configurado
3. `.devbase_state.json` foi deletado

**Soluções:**
```bash
# Opção 1: Criar workspace
devbase core setup

# Opção 2: Especificar root manualmente
export DEVBASE_ROOT=~/Dev_Workspace
devbase core doctor

# Opção 3: Recriar state file
cd ~/Dev_Workspace
devbase core setup --force
```

---

## Problema: Templates não aparecem

**Sintoma:**
```bash
devbase dev new app --template api
Error: Template 'api' not found
```

**Solução:**
```bash
# Atualizar templates
devbase core hydrate --force

# Verificar templates disponíveis
devbase nav goto templates
ls
# Deve haver pastas __template-*
```

---

## Problema: Tracking não detecta projeto

**Sintoma:**
```bash
cd meu-projeto
devbase ops track "teste"
✓ Tracked: [work] teste  # <-- Deveria ser [coding:meu-projeto]
```

**Causas:**
- Pasta do projeto não está em `21_monorepo_apps/`
- Nome do projeto não segue convenção

**Solução:**
```bash
# Verificar estrutura
pwd
# Deve ser: ~/Dev_Workspace/20-29_CODE/21_monorepo_apps/meu-projeto

# Verificar nome (deve ser kebab-case)
devbase dev audit
```

---

## Problema: Comandos lentos

**Sintoma:** Comandos demoram >3 segundos

**Possíveis causas:**
1. Workspace muito grande (>100GB)
2. Muitos eventos em telemetria (>10.000)
3. Problemas de disco

**Soluções:**
```bash
# Limpar eventos antigos
cd ~/Dev_Workspace/.telemetry
# Backup
cp events.jsonl events.jsonl.bak
# Manter apenas últimos 1000
tail -n 1000 events.jsonl > events.jsonl.tmp
mv events.jsonl.tmp events.jsonl

# Arquivar projetos antigos
devbase nav goto code
mv projeto-velho ~/Dev_Workspace/90-99_ARCHIVE_COLD/

# Limpar temporários
devbase ops clean
```

---

## Problema: Git hooks não funcionam

**Sintoma:** Commits não são trackeados automaticamente

**Solução:**
```bash
# Verificar permissões
chmod +x .git/hooks/post-commit

# Testar manualmente
.git/hooks/post-commit
```

---

# Boas Práticas

## Organização de Código

### ✅ Faça
- Projetos em `21_monorepo_apps/`
- Bibliotecas em `22_monorepo_packages/`
- Nomes em kebab-case: `meu-projeto`
- Um commit = um track event

### ❌ Evite
- Misturar apps e libs na mesma pasta
- Nomes tipo `MyProject` ou `my_project`
- Acumular muitos dias sem tracking

---

## Gerenciamento de Conhecimento

### ✅ Faça
- ADRs (Architecture Decision Records) em `knowledge/ADRs/`
- TILs (Today I Learned) em `knowledge/TILs/`
- README em todo projeto
- Use templates para consistência

### ❌ Evite
- Notas sem data ou contexto
- Misturar público e privado
- Documentação desatualizada

---

## Manutenção

### Rotina Diária
```bash
# Ao terminar o dia
devbase ops track "Resumo do dia de trabalho"
```

### Rotina Semanal
```bash
# Sexta-feira
devbase quick sync
devbase ops weekly --output ~/weeknotes/$(date +%Y-%W).md
```

### Rotina Mensal
```bash
# Último dia do mês
devbase ops backup
devbase dev audit --fix
```

---

## Segurança

### ✅ Faça
- Habilitar Air-Gap para vault privado
- Backups regulares (automáticos se possível)
- Revisar `.gitignore` antes de commits
- Separar chaves/secrets do código

### ❌ Evite
- Commitar arquivos de `12_private_vault/`
- Versionar arquivos grandes (use Git LFS)
- Expor credenciais em templates

---

## Performance

### ✅ Faça
- Limpar `00_inbox/` regularmente
- Arquivar projetos inativos
- Usar `.gitignore` apropriado
- Comprimir backups antigos

### ❌ Evite
- Ter >100 projetos ativos
- Manter >10.000 eventos em telemetria
- Duplicar grandes arquivos

---

# Comandos Rápidos (Cheatsheet)

```bash
# Setup inicial
devbase core setup

# Health check
devbase core doctor

# Novo projeto
devbase dev new meu-app

# Navegação rápida
devbase nav goto code
cd $(devbase nav goto vault)

# Tracking
devbase ops track "Tarefa completa"
devbase ops stats
devbase ops weekly --output report.md

# Manutenção
devbase ops backup
devbase ops clean
devbase quick sync

# Quick start
devbase quick quickstart meu-novo-projeto
```

---

# Recursos Adicionais

## Documentação Oficial
- GitHub: https://github.com/walcimarzd/devbase-setup
- Issues: Report bugs e sugestões
- Discussions: Perguntas e ideias

## Comunidade
- Stack Overflow: Tag `devbase`
- Discord: [link se houver]

## Aprendizado Contínuo
- Johnny.Decimal: https://johnnydecimal.com/
- Clean Architecture: Uncle Bob's blog
- PKM (Personal Knowledge Management): Zettelkasten method

---

**Parabéns!** 🎉 Você agora domina o DevBase do iniciante ao avançado!

Continue praticando e adapte o sistema às suas necessidades. O DevBase cresce com você!
