# DevBase CLI - Guia de Testes Manuais v4.0.5

> **Objetivo:** Testar todas as funcionalidades do DevBase CLI de forma sistemática.
> **Última atualização:** 2025-12-22

---

## 🔧 Pré-requisitos

```powershell
# 1. Atualizar para versão mais recente
cd C:\Users\conta\Downloads\devbase-setup
git pull
uv tool install --force .

# 2. Verificar instalação
devbase --version
# Esperado: devbase 4.0.5

# 3. Criar workspace de teste LIMPO
Remove-Item -Recurse D:\Dev_Test -ErrorAction SilentlyContinue
devbase --root D:\Dev_Test core setup

# 4. Navegar para workspace
cd D:\Dev_Test
```

---

## 📋 1. CORE - Comandos Essenciais

### 1.1 `devbase core setup` ✅

```powershell
# Teste: Setup interativo completo
# Responda: y para PKM, y para AI, y para Operations, y para Air-Gap

# Verificar estrutura criada
ls D:\Dev_Test
# Esperado: 00-09_SYSTEM, 10-19_KNOWLEDGE, 20-29_CODE, 30-39_OPERATIONS, etc.
```

### 1.2 `devbase core doctor`

```powershell
devbase core doctor
# Esperado: Todas as pastas ✓, arquivos de governança ✓, Air-Gap ✓, HEALTHY
```

### 1.3 `devbase core doctor --fix`

```powershell
# Simular problema
Rename-Item D:\Dev_Test\.editorconfig D:\Dev_Test\.editorconfig.bak

# Doctor detecta e corrige
devbase core doctor --fix

# Verificar recriação
Test-Path D:\Dev_Test\.editorconfig
# Esperado: True
```

### 1.4 `devbase core hydrate`

```powershell
devbase core hydrate
# Esperado: Templates atualizados com ✓
```

### 1.5 `devbase core hydrate-icons`

```powershell
devbase core hydrate-icons
# Esperado: "Icon not found" (ícones não estão em ~/.devbase/icons/)
```

---

## 💻 2. DEV - Desenvolvimento

### 2.1 `devbase dev new` (Interativo)

```powershell
devbase dev new meu-projeto
# Preencher: Description, License (Enter), Author (Enter)
# Esperado: Projeto criado em 20-29_CODE/21_monorepo_apps/meu-projeto
```

### 2.2 `devbase dev new --no-interactive`

```powershell
devbase dev new outro-projeto --no-interactive
# Esperado: Projeto criado sem prompts
```

### 2.3 `devbase dev audit`

```powershell
# Criar pasta com nome inválido
mkdir "D:\Dev_Test\20-29_CODE\21_monorepo_apps\BadName_Test"

devbase dev audit
# Esperado: Lista "BadName_Test" como violação
# NÃO deve listar pastas Johnny.Decimal (00-09_SYSTEM, etc.)
```

### 2.4 `devbase dev audit --fix`

> ⚠️ **CUIDADO:** Use com cuidado! NÃO deve renomear estrutura DevBase.

```powershell
devbase dev audit --fix
# Esperado: Renomeia "BadName_Test" → "bad-name-test"
# NÃO deve tocar em 00-09_SYSTEM, 10-19_KNOWLEDGE, etc.
```

---

## 📊 3. OPS - Operações

### 3.1 `devbase ops track`

```powershell
cd D:\Dev_Test\20-29_CODE\21_monorepo_apps\meu-projeto

# Auto-detecta tipo
devbase ops track "Implementando feature X"
# Esperado: [coding] ...

# Tipo específico
devbase ops track "Bug corrigido" --type bugfix
devbase ops track "Estudando arquitetura" --type learning
```

### 3.2 `devbase ops stats`

```powershell
devbase ops stats
# Esperado: Tabela com coding, bugfix, learning
```

### 3.3 `devbase ops weekly`

```powershell
# Teste 1: Auto-gera arquivo
devbase ops weekly
# Esperado: D:\Dev_Test\10-19_KNOWLEDGE\12_private_vault\journal\weekly-YYYY-MM-DD.md

# Teste 2: Nome personalizado
devbase ops weekly --output meu-relatorio.md
# Esperado: D:\Dev_Test\10-19_KNOWLEDGE\12_private_vault\journal\meu-relatorio.md

# Teste 3: Caminho absoluto (escapa workspace)
devbase ops weekly --output C:\Temp\externo.md
# Esperado: C:\Temp\externo.md
```

### 3.4 `devbase ops backup`

```powershell
devbase ops backup
# Esperado: Backup em 30-39_OPERATIONS/31_backups/local/devbase_backup_YYYYMMDD_*
```

### 3.5 `devbase ops clean`

```powershell
# Criar arquivos temporários
New-Item D:\Dev_Test\temp.log -ItemType File
New-Item D:\Dev_Test\temp.tmp -ItemType File

devbase ops clean
# Esperado: Removed 2 temporary file(s)
```

---

## 📝 4. QUICK - Ações Rápidas

### 4.1 `devbase quick note` (TIL padrão)

```powershell
devbase quick note "Python: fstrings suportam = para debug"
# Esperado: Salvo em 10-19_KNOWLEDGE/11_public_garden/til/2025/12-december/*.md
```

### 4.2 `devbase quick note --no-til`

```powershell
devbase quick note "Reunião com equipe" --no-til
# Esperado: Salvo em 10-19_KNOWLEDGE/11_public_garden/notes/*.md
```

### 4.3 `devbase quick note --edit`

```powershell
devbase quick note "Teste com editor" --edit
# Esperado: Abre VS Code (se disponível)
```

### 4.4 `devbase quick quickstart`

```powershell
devbase quick quickstart app-teste
# Esperado: Golden Path completo (7 steps), projeto em 21_monorepo_apps/app-teste
```

### 4.5 `devbase quick sync`

```powershell
devbase quick sync
# Esperado: Step 1/3 Health Check, Step 2/3 Template Sync, Step 3/3 Backup
```

---

## 🧠 5. STUDY - Aprendizado

> ⚠️ **Nota:** Requer notas com 1+ dia de idade para `review`.

### 5.1 `devbase study review`

```powershell
devbase study review
# Esperado: "No notes eligible for review" (notas são de hoje)
```

### 5.2 `devbase study synthesize`

```powershell
# Requer pelo menos 2 notas
devbase quick note "Conceito A sobre Python"
devbase quick note "Conceito B sobre TypeScript"

devbase study synthesize
# Esperado: Mostra 2 conceitos aleatórios, pergunta se quer criar síntese
```

---

## 🔍 6. PKM - Knowledge Management

### 6.1 `devbase pkm find`

```powershell
devbase pkm find python
# Esperado: Lista notas com "python" (primeira execução indexa)

devbase pkm find --tag til
devbase pkm find --type til
devbase pkm find testing --reindex
```

### 6.2 `devbase pkm graph`

```powershell
devbase pkm graph
# Esperado: Estatísticas do grafo de conhecimento

devbase pkm graph --export
# Esperado: knowledge_graph.dot criado

devbase pkm graph --html
# Esperado: knowledge_graph.html criado (requer pyvis)
```

### 6.3 `devbase pkm links`

```powershell
# Primeiro, obter caminho de uma nota existente
$nota = (ls D:\Dev_Test\10-19_KNOWLEDGE\11_public_garden\til\2025\12-december\ -Filter *.md | Select -First 1).Name
devbase pkm links "til/2025/12-december/$nota"
# Esperado: Links de entrada e saída da nota
```

### 6.4 `devbase pkm index`

```powershell
devbase pkm index til
# Esperado: _index.md criado em 10-19_KNOWLEDGE/11_public_garden/til/
```

---

## 📈 7. ANALYTICS

### 7.1 `devbase analytics report`

> ⚠️ **Requer DuckDB:** `uv pip install duckdb`

```powershell
# Instalar dependência opcional
uv pip install duckdb

devbase analytics report
# Esperado: Abre analytics_report.html no navegador
```

### 7.2 `devbase analytics report --no-open`

```powershell
devbase analytics report --no-open
# Esperado: Gera relatório sem abrir navegador
```

---

## 🧭 8. NAV - Navegação

### 8.1 `devbase nav goto`

```powershell
# Listar locais disponíveis
devbase nav goto invalid
# Esperado: Lista de locais válidos

# Testar navegação
devbase nav goto code
devbase nav goto vault
devbase nav goto knowledge
devbase nav goto ai
# Esperado: Imprime caminho absoluto
```

---

## 🧹 9. Limpeza Pós-Testes

```powershell
# Opção 1: Manter workspace de teste
# (útil para mais testes)

# Opção 2: Remover workspace de teste
Remove-Item -Recurse D:\Dev_Test

# Limpar arquivos externos
Remove-Item C:\Temp\externo.md -ErrorAction SilentlyContinue
```

---

## ✅ Checklist de Validação

| # | Comando | Status |
|---|---------|--------|
| 1 | `core setup` | ⬜ |
| 2 | `core doctor` | ⬜ |
| 3 | `core doctor --fix` | ⬜ |
| 4 | `core hydrate` | ⬜ |
| 5 | `core hydrate-icons` | ⬜ |
| 6 | `dev new` | ⬜ |
| 7 | `dev new --no-interactive` | ⬜ |
| 8 | `dev audit` | ⬜ |
| 9 | `dev audit --fix` | ⬜ |
| 10 | `ops track` | ⬜ |
| 11 | `ops stats` | ⬜ |
| 12 | `ops weekly` | ⬜ |
| 13 | `ops weekly --output` | ⬜ |
| 14 | `ops backup` | ⬜ |
| 15 | `ops clean` | ⬜ |
| 16 | `quick note` | ⬜ |
| 17 | `quick note --no-til` | ⬜ |
| 18 | `quick quickstart` | ⬜ |
| 19 | `quick sync` | ⬜ |
| 20 | `study review` | ⬜ |
| 21 | `study synthesize` | ⬜ |
| 22 | `pkm find` | ⬜ |
| 23 | `pkm graph` | ⬜ |
| 24 | `pkm links` | ⬜ |
| 25 | `pkm index` | ⬜ |
| 26 | `analytics report` | ⬜ |
| 27 | `analytics report --no-open` | ⬜ |
| 28 | `nav goto` | ⬜ |

---

## 📋 Notas de Teste

### Dependências Opcionais
- **DuckDB:** Necessário para `analytics report`
- **PyVis:** Necessário para `pkm graph --html`

### Conhecidos
- `study review` só funciona com notas de 1+ dia
- `hydrate-icons` requer ícones em `~/.devbase/icons/`

---

**Versão testada:** DevBase CLI v4.0.4
