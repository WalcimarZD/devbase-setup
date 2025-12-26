# DevBase v5.0 — Product Brief

**Versão:** 1.0  
**Data:** 2025-12-26  
**Status:** Aprovado

---

## 1. Visão do Produto

**DevBase** é um sistema operacional pessoal para engenheiros de software. Transforma o caos do ambiente de desenvolvimento em um workspace estruturado e de alta performance, baseado na metodologia [Johnny.Decimal](https://johnnydecimal.com).

> _"Zero-config, maximum velocity."_

---

## 2. Problema

| Problema | Impacto | Frequência |
|----------|---------|------------|
| Projetos espalhados em diretórios aleatórios | Tempo perdido navegando | Diário |
| Falta de estrutura padronizada | Onboarding lento, inconsistência | Por projeto |
| Notas e conhecimento não linkados | Conhecimento perdido | Semanal |
| Setup manual de cada projeto | Repetição de boilerplate | Por projeto |
| Falta de visibilidade do próprio trabalho | Burnout, dificuldade em reportar | Semanal |

---

## 3. Público-Alvo

### Persona Primária: Dev Solo / Indie Hacker
- Trabalha em múltiplos projetos simultaneamente
- Valoriza automação e produtividade
- Prefere terminal sobre GUIs
- Usa Python, Node, ou múltiplas stacks

### Persona Secundária: Dev em Transição Jr → Pleno
- Busca estruturar workflow profissional
- Quer aprender boas práticas (Clean Architecture, ADRs)
- Precisa de guardrails para decisões

---

## 4. Requisitos Funcionais

### 4.1 Core (Essencial)

| RF | Descrição | Critério de Aceitação |
|----|-----------|----------------------|
| RF01 | Criar workspace Johnny.Decimal | `devbase core setup` gera estrutura 00-99 em <5s |
| RF02 | Diagnóstico de saúde | `devbase core doctor` lista issues com severidade |
| RF03 | Auto-correção de problemas | `devbase core doctor --fix` corrige 80%+ dos issues |

### 4.2 Development

| RF | Descrição | Critério de Aceitação |
|----|-----------|----------------------|
| RF04 | Scaffolding de projetos | `devbase dev new X` cria projeto com git, .gitignore, estrutura |
| RF05 | Templates customizáveis | Suporte a Jinja2 e Copier |
| RF06 | Auditoria de naming | `devbase dev audit` detecta violações kebab-case |

### 4.3 Operations

| RF | Descrição | Critério de Aceitação |
|----|-----------|----------------------|
| RF07 | Tracking de atividade | `devbase ops track "msg"` persiste em <50ms |
| RF08 | Dashboard de produtividade | `devbase ops stats` mostra métricas da semana |
| RF09 | Relatório semanal | `devbase ops weekly` gera Markdown exportável |
| RF10 | Backup incremental | `devbase ops backup` exclui node_modules, .venv |

### 4.4 Knowledge (PKM)

| RF | Descrição | Critério de Aceitação |
|----|-----------|----------------------|
| RF11 | Captura rápida de notas | `devbase quick note "X"` salva em <50ms |
| RF12 | Busca full-text | `devbase pkm find "X"` retorna resultados em <200ms |
| RF13 | Grafo de conhecimento | `devbase pkm graph` mostra conexões entre notas |

### 4.5 Navigation

| RF | Descrição | Critério de Aceitação |
|----|-----------|----------------------|
| RF14 | Navegação semântica | `devbase nav goto code` retorna path de 20-29_CODE |
| RF15 | Auto-detecção de workspace | Funciona de qualquer subdiretório |

---

## 5. Requisitos Não-Funcionais

| RNF | Categoria | Spec | Justificativa |
|-----|-----------|------|---------------|
| RNF01 | Performance | Cold start < 50ms | UX de engenheiro sênior |
| RNF02 | Performance | Busca < 200ms | Interativo |
| RNF03 | Disponibilidade | 100% offline | Soberania de dados |
| RNF04 | Segurança | Zero telemetria externa | Privacidade |
| RNF05 | Portabilidade | Windows, Linux, macOS | Universal |
| RNF06 | Manutenibilidade | Cobertura testes > 80% | Qualidade |

---

## 6. Fora de Escopo (v5.0)

- GUI/Interface web
- Sincronização cloud
- Colaboração multi-usuário
- Plugins de terceiros
- Integração com IDEs (além de VS Code básico)

---

## 7. Métricas de Sucesso

| Métrica | Target | Medição |
|---------|--------|---------|
| Tempo de setup inicial | < 30s | `time devbase core setup` |
| Tempo para criar projeto | < 5s | `time devbase dev new X` |
| Adoção de tracking | 3+ eventos/dia | `devbase ops stats` |
| Satisfação (NPS) | > 8/10 | Survey pós-uso |

---

## 8. Roadmap Simplificado

| Fase | Entregável | Status |
|------|------------|--------|
| v5.0 | Core + Dev + Ops + Nav + PKM básico | ✅ Done |
| v5.1 | Hot/Cold FTS + Workflow IA | 🔄 In Progress |
| v6.0 | AI-assisted search + tagging | 📋 Planned |

---

## Referências

- [Johnny.Decimal Methodology](https://johnnydecimal.com)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Diátaxis Documentation Framework](https://diataxis.fr)
