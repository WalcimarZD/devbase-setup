# 🎯 Seu Primeiro Dia com DevBase

> **Tempo estimado:** 15 minutos  
> **Objetivo:** Confiança com os 3 comandos essenciais

---

## O Que Você Vai Aprender

Ao final deste tutorial, você saberá:

- ✅ Verificar se seu workspace está saudável
- ✅ Criar um projeto novo
- ✅ Navegar para qualquer pasta rapidamente

> [!TIP]
> **Regra de ouro:** Na primeira semana, **ignore** todos os outros comandos.  
> Foco total nesses 3.

---

## Passo 1: Verificar Saúde (2 min)

O comando `doctor` é seu melhor amigo. Ele verifica se tudo está funcionando.

```bash
devbase core doctor
```

**O que você deve ver:**

```
DevBase Health Check
Workspace: C:\Users\você\Dev_Workspace

Checking folder structure...
  ✓ 00-09_SYSTEM
  ✓ 10-19_KNOWLEDGE
  ✓ 20-29_CODE
  ✓ 30-39_OPERATIONS
  ✓ 40-49_MEDIA_ASSETS
  ✓ 90-99_ARCHIVE_COLD

✓ DevBase is HEALTHY
```

**Se algo estiver vermelho:**

```bash
devbase core doctor --fix
```

O DevBase corrige automaticamente!

---

## Passo 2: Criar Projeto (5 min)

Hora de criar seu primeiro projeto. O nome deve ser em `kebab-case` (letras minúsculas, palavras separadas por hífen).

```bash
devbase dev new meu-primeiro-app
```

**O wizard vai perguntar:**

```
Project Configuration

Description [MeuPrimeiroApp Application]: Meu app de teste
License [MIT]: MIT
Author [Seu Nome]: Seu Nome

Creating project 'meu-primeiro-app'...

  ✓ README.md
  ✓ .gitignore
  ✓ LICENSE

✅ Project created!

Location: C:\Users\você\Dev_Workspace\20-29_CODE\21_monorepo_apps\meu-primeiro-app
```

**Onde o projeto foi criado?**

```
Dev_Workspace/
└── 20-29_CODE/           ← Área de código
    └── 21_monorepo_apps/ ← Subcategoria de apps
        └── meu-primeiro-app/  ← Seu projeto!
```

---

## Passo 3: Navegar Rápido (3 min)

Lembrar caminhos como `20-29_CODE/21_monorepo_apps` é chato. Use atalhos!

```bash
devbase nav goto code
```

**Saída:**

```
C:\Users\você\Dev_Workspace\20-29_CODE\21_monorepo_apps
```

**Para navegar de verdade:**

```bash
cd $(devbase nav goto code)   # Linux/macOS
cd (devbase nav goto code)    # PowerShell
```

**Outros atalhos úteis:**

| Atalho | Destino |
|--------|---------|
| `code` | Seus projetos |
| `knowledge` | Suas notas |
| `inbox` | Arquivos temporários |

---

## ✅ Checkpoint

Você completou o Day 1 se consegue responder:

- [ ] Qual comando verifica a saúde do workspace?
- [ ] Onde ficam os projetos criados com `devbase dev new`?
- [ ] Como chegar rápido na pasta de código?

<details>
<summary>Respostas</summary>

1. `devbase core doctor`
2. `20-29_CODE/21_monorepo_apps/`
3. `devbase nav goto code`

</details>

---

## O Que Ignorar (Por Enquanto)

Você vai ver outros comandos no `--help`. **Ignore todos estes na Semana 1:**

- `pkm` - Gestão de conhecimento (Semana 2)
- `ops track` - Tracking de atividades (Semana 2)
- `analytics` - Insights (Semana 4)
- `study` - Aprendizado (Semana 4)

---

## Próximos Passos

Quando se sentir confortável com esses 3 comandos (geralmente após 3-5 dias):

→ [Semana 2: Fluxo de Trabalho Diário](../getting-started/workflow.md)

---

> [!NOTE]
> **Lembre-se:** Maestria vem da repetição, não da quantidade de comandos.  
> Use `doctor`, `new` e `goto` até virarem automáticos.
