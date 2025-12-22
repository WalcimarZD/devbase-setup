# 🤝 Contribuindo

Contribuições são bem-vindas! Este guia explica como contribuir para o DevBase.

## Como Contribuir

### 1. Fork e Clone

```bash
git clone https://github.com/SEU-USUARIO/devbase-setup.git
cd devbase-setup
uv sync
```

### 2. Crie uma Branch

```bash
git checkout -b feature/minha-feature
```

### 3. Faça suas Alterações

- Siga as convenções de código existentes
- Adicione testes para novas funcionalidades
- Atualize a documentação se necessário

### 4. Rode os Testes

```bash
uv run pytest
```

### 5. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new command"
git commit -m "fix: resolve path issue on Windows"
git commit -m "docs: update CLI reference"
```

### 6. Push e Pull Request

```bash
git push origin feature/minha-feature
```

Abra um Pull Request no GitHub.

## Estrutura do Projeto

```
devbase-setup/
├── src/
│   └── devbase/         # Pacote principal
│       ├── legacy/      # Módulos legados
│       └── commands/    # Comandos CLI
├── tests/               # Testes unitários
├── docs/                # Documentação MkDocs
└── completions/         # Shell completion scripts
```

## Código de Conduta

Seja respeitoso e inclusivo. Veja [CODE_OF_CONDUCT.md](https://github.com/WalcimarZD/devbase-setup/blob/main/CODE_OF_CONDUCT.md).

## Dúvidas?

Abra uma [Issue](https://github.com/WalcimarZD/devbase-setup/issues) no GitHub.
