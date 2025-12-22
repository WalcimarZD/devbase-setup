# 📋 DevBase Cheatsheet

> Referência rápida de página única - resolva 80% das dúvidas aqui.

---

## 🧭 Navegação Rápida

| Preciso de... | Comando |
|---------------|---------|
| Meu código | `devbase nav goto code` |
| Minhas notas | `devbase nav goto knowledge` |
| Cofre privado | `devbase nav goto vault` |
| Templates | `devbase nav goto templates` |
| Inbox (temp) | `devbase nav goto inbox` |

---

## ⚡ Top 5 Comandos Diários

| Comando | O Que Faz |
|---------|-----------|
| `devbase core doctor` | Verifica saúde do workspace |
| `devbase dev new <nome>` | Cria projeto novo |
| `devbase ops track "msg"` | Registra atividade |
| `devbase ops weekly` | Gera relatório semanal |
| `devbase quick sync` | Manutenção completa |

---

## 🔧 Resolução de Problemas

| Problema | Solução |
|----------|---------|
| Workspace não encontrado | `devbase core setup` |
| Pastas faltando | `devbase core doctor --fix` |
| Templates desatualizados | `devbase core hydrate` |
| Nome fora do padrão | `devbase dev audit --fix` |
| Limpar temporários | `devbase ops clean --dry-run` |

---

## 📂 Estrutura Johnny.Decimal

```
~/Dev_Workspace/
├── 00-09_SYSTEM/       → Configs, inbox, templates
├── 10-19_KNOWLEDGE/    → Notas, vault
├── 20-29_CODE/         → Seus projetos
├── 30-39_OPERATIONS/   → AI, backups, scripts
├── 40-49_MEDIA_ASSETS/ → Imagens, vídeos
└── 90-99_ARCHIVE_COLD/ → Arquivados
```

---

## 🎯 Flags Úteis

| Flag | Efeito |
|------|--------|
| `--dry-run` | Mostra sem executar |
| `--fix` | Corrige automaticamente |
| `--force` | Sobrescreve existente |
| `--verbose` | Mais detalhes |
| `--help` | Ajuda do comando |

---

## 📖 Ajuda

```bash
devbase --help           # Lista todos comandos
devbase <cmd> --help     # Ajuda específica
```

**Docs:** [walcimarzd.github.io/devbase-setup](https://walcimarzd.github.io/devbase-setup/)
