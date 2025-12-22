# DevBase CLI - Guia de Testes Manuais v4.0.3

> **Objetivo:** Testar todas as funcionalidades do DevBase CLI de forma sistemática.

---

## 🔧 Pré-requisitos

```powershell
# 1. Atualizar para versão mais recente
cd C:\Users\conta\Downloads\devbase-setup
git pull
uv tool install --force .

# 2. Verificar instalação
devbase --version
# Esperado: devbase 4.0.3

# 3. Navegar para workspace de teste
cd D:\Dev_OS
```

---

## 📋 1. CORE - Comandos Essenciais

### 1.1 `devbase core setup`

```powershell
# Teste: Criar novo workspace (use diretório temporário)
devbase --root D:\Test_Workspace core setup

# Verificar estrutura criada
ls D:\Test_Workspace
# Esperado: 00-09_SYSTEM, 10-19_KNOWLEDGE, 20-29_CODE, 30-39_OPERATIONS, etc.

# Limpar após teste
Remove-Item -Recurse D:\Test_Workspace
```

### 1.2 `devbase core doctor`

```powershell
cd D:\Dev_OS
devbase core doctor

# Esperado: Tabela de pastas ✓, arquivos de governança ✓, Air-Gap ✓
```

### 1.3 `devbase core doctor --fix`

```powershell
# Primeiro, simular problema (renomear arquivo)
Rename-Item D:\Dev_OS\.editorconfig D:\Dev_OS\.editorconfig.bak

# Rodar doctor com fix
devbase core doctor --fix

# Verificar se recriou o arquivo
ls D:\Dev_OS\.editorconfig
# Esperado: Arquivo recriado

# Restaurar backup se preferir a versão original
# Move-Item D:\Dev_OS\.editorconfig.bak D:\Dev_OS\.editorconfig -Force
```

### 1.4 `devbase core hydrate`

```powershell
devbase core hydrate

# Esperado: Templates atualizados
```

### 1.5 `devbase core hydrate-icons`

```powershell
devbase core hydrate-icons

# Nota: Requer ícones em ~/.devbase/icons/
# Esperado: Ícones aplicados às pastas (Windows)
```

---

## 💻 2. DEV - Desenvolvimento

### 2.1 `devbase dev new`

```powershell
cd D:\Dev_OS

# Teste interativo
devbase dev new test-project

# Preencher:
# - Description: Test Project
# - License: MIT
# - Author: (Enter para aceitar)

# Verificar projeto criado
ls D:\Dev_OS\20-29_CODE\21_monorepo_apps\test-project
# Esperado: README.md, .cursorrules, src/, etc.
```

### 2.2 `devbase dev new --no-interactive`

```powershell
devbase dev new test-project-2 --no-interactive

# Esperado: Projeto criado com valores padrão, sem prompts
```

### 2.3 `devbase dev audit`

```powershell
# Primeiro, criar pasta com nome inválido
mkdir "D:\Dev_OS\20-29_CODE\21_monorepo_apps\TestCamelCase"

devbase dev audit

# Esperado: Lista violação de naming convention (TestCamelCase)

# Limpar
Remove-Item "D:\Dev_OS\20-29_CODE\21_monorepo_apps\TestCamelCase"
```

### 2.4 `devbase dev audit --fix`

```powershell
mkdir "D:\Dev_OS\20-29_CODE\21_monorepo_apps\BadName_Test"

devbase dev audit --fix

# Esperado: Renomeado para bad-name-test
```

---

## 📊 3. OPS - Operações

### 3.1 `devbase ops track`

```powershell
cd D:\Dev_OS\20-29_CODE\21_monorepo_apps\my-project

# Rastrear atividade (auto-detecta tipo)
devbase ops track "Testando tracking de atividades"

# Rastrear com tipo específico
devbase ops track "Corrigindo bug X" --type bugfix
devbase ops track "Estudando Clean Architecture" --type learning

# Esperado: ✓ Tracked: [coding] ...
```

### 3.2 `devbase ops stats`

```powershell
devbase ops stats

# Esperado:
# - Total events: N
# - Tabela por tipo (coding, bugfix, learning, etc.)
# - Atividades recentes
```

### 3.3 `devbase ops weekly`

```powershell
# Teste 1: Sem argumentos (auto-gera arquivo)
devbase ops weekly
# Esperado: Salvo em D:\Dev_OS\10-19_KNOWLEDGE\12_private_vault\journal\weekly-YYYY-MM-DD.md

# Teste 2: Com nome personalizado
devbase ops weekly --output meu-relatorio.md
# Esperado: Salvo em .../journal/meu-relatorio.md

# Teste 3: Caminho absoluto (escapa workspace)
devbase ops weekly --output C:\Temp\relatorio-externo.md
# Esperado: Salvo em C:\Temp\relatorio-externo.md

# Verificar arquivos criados
ls D:\Dev_OS\10-19_KNOWLEDGE\12_private_vault\journal\
```

### 3.4 `devbase ops backup`

```powershell
devbase ops backup

# Esperado: Backup criado em 30-39_OPERATIONS\31_backups\local\

# Verificar
ls D:\Dev_OS\30-39_OPERATIONS\31_backups\local\
```

### 3.5 `devbase ops clean`

```powershell
# Criar arquivos temporários para limpeza
New-Item D:\Dev_OS\temp_test.log -ItemType File
New-Item D:\Dev_OS\temp_test.tmp -ItemType File

devbase ops clean

# Esperado: Removed 2 temporary file(s)
```

---

## 📝 4. QUICK - Ações Rápidas

### 4.1 `devbase quick note`

```powershell
# Criar TIL rápido
devbase quick note "Python: fstrings suportam = para debug"

# Esperado: Note saved: 10-19_KNOWLEDGE/11_public_garden/til/2025/12.../2025-12-22-python-fstrings...

# Com flag --edit (abre VS Code se disponível)
devbase quick note "Aprendi sobre Typer callbacks" --edit

# Nota não-TIL
devbase quick note "Reunião com equipe sobre arquitetura" --no-til
```

### 4.2 `devbase quick quickstart`

```powershell
devbase quick quickstart meu-app-golden

# Esperado:
# - Step 1/7: Generating project...
# - Step 2/7: Initializing Git...
# - Step 3/7: Installing dependencies...
# - ...
# - ✅ Golden Path Complete!
```

### 4.3 `devbase quick sync`

```powershell
devbase quick sync

# Esperado:
# - Step 1/3: Health Check (doctor)
# - Step 2/3: Template Sync (hydrate)
# - Step 3/3: Backup
# - ✅ Sync complete!
```

---

## 🧠 5. STUDY - Aprendizado

### 5.1 `devbase study review`

```powershell
# Requer notas existentes com frontmatter
devbase study review

# Esperado: Sessão de revisão espaçada
# - Mostra título, pede para lembrar, mostra resposta
# - Atualiza last_reviewed no frontmatter

# Com contagem específica
devbase study review --count 3
```

### 5.2 `devbase study synthesize`

```powershell
# Requer pelo menos 2 notas no knowledge base
devbase study synthesize

# Esperado:
# - Seleciona 2 notas aleatórias
# - Mostra perguntas de síntese
# - Opção de criar nota de síntese
```

---

## 🔍 6. PKM - Knowledge Management

### 6.1 `devbase pkm find`

```powershell
# Busca em todas as notas
devbase pkm find python

# Com filtro de tipo
devbase pkm find architecture --type til

# Forçar reindexação
devbase pkm find testing --reindex

# Esperado: Lista de notas com matches
```

### 6.2 `devbase pkm graph`

```powershell
# Estatísticas do grafo
devbase pkm graph

# Esperado:
# - Total nodes, edges
# - Hub notes (mais conexões)
# - Orphan notes (sem conexões)

# Exportar para DOT
devbase pkm graph --export

# Gerar HTML interativo
devbase pkm graph --html
```

### 6.3 `devbase pkm links`

```powershell
# Ver conexões de uma nota específica
devbase pkm links til/2025-12-22-python-fstrings.md

# Esperado:
# - Outgoing links (notas referenciadas)
# - Incoming links (backlinks)
```

### 6.4 `devbase pkm index`

```powershell
# Gerar índice para pasta
devbase pkm index til

# Esperado: _index.md criado em 10-19_KNOWLEDGE/11_public_garden/til/
```

---

## 📈 7. ANALYTICS

### 7.1 `devbase analytics report`

```powershell
devbase analytics report

# Esperado:
# - Report generated: 30-39_OPERATIONS/33_monitoring/analytics_report.html
# - Abre no navegador

# Sem abrir navegador
devbase analytics report --no-open
```

---

## 🧭 8. NAV - Navegação

### 8.1 `devbase nav goto`

```powershell
# Listar locais disponíveis (erro proposital)
devbase nav goto invalid

# Esperado: Lista de locais válidos

# Testar cada local
devbase nav goto code
devbase nav goto vault
devbase nav goto knowledge
devbase nav goto ai

# Esperado: Imprime caminho absoluto
```

---

## 🔒 9. Segurança (Implícito no Doctor)

O `devbase core doctor` já executa verificações de segurança:
- Arquivos sensíveis não protegidos
- Backups com segredos
- Private Vault em pastas de cloud sync

---

## 🧹 Limpeza Pós-Testes

```powershell
# Remover projetos de teste
Remove-Item -Recurse D:\Dev_OS\20-29_CODE\21_monorepo_apps\test-project
Remove-Item -Recurse D:\Dev_OS\20-29_CODE\21_monorepo_apps\test-project-2
Remove-Item -Recurse D:\Dev_OS\20-29_CODE\21_monorepo_apps\meu-app-golden

# Limpar relatórios de teste
Remove-Item C:\Temp\relatorio-externo.md -ErrorAction SilentlyContinue
```

---

## ✅ Checklist de Validação

| Comando | Status |
|---------|--------|
| `core setup` | ⬜ |
| `core doctor` | ⬜ |
| `core doctor --fix` | ⬜ |
| `core hydrate` | ⬜ |
| `core hydrate-icons` | ⬜ |
| `dev new` | ⬜ |
| `dev new --no-interactive` | ⬜ |
| `dev audit` | ⬜ |
| `dev audit --fix` | ⬜ |
| `ops track` | ⬜ |
| `ops stats` | ⬜ |
| `ops weekly` | ⬜ |
| `ops weekly --output` | ⬜ |
| `ops backup` | ⬜ |
| `ops clean` | ⬜ |
| `quick note` | ⬜ |
| `quick quickstart` | ⬜ |
| `quick sync` | ⬜ |
| `study review` | ⬜ |
| `study synthesize` | ⬜ |
| `pkm find` | ⬜ |
| `pkm graph` | ⬜ |
| `pkm links` | ⬜ |
| `pkm index` | ⬜ |
| `analytics report` | ⬜ |
| `nav goto` | ⬜ |

---

**Última atualização:** 2025-12-22  
**Versão testada:** DevBase CLI v4.0.3
