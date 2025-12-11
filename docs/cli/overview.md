# 🖥️ CLI Reference

O DevBase CLI oferece comandos para gerenciar seu workspace de desenvolvimento.

## Uso

```bash
devbase <command> [options]
```

## Comandos Disponíveis

### Gestão

| Comando | Descrição |
|---------|-----------|
| [setup](setup.md) | Inicializa ou atualiza estrutura DevBase |
| [doctor](doctor.md) | Verifica integridade do workspace |
| [audit](audit.md) | Audita nomenclatura (kebab-case) |
| [new](new.md) | Cria novo projeto a partir do template |
| [hydrate](hydrate.md) | Atualiza templates |
| [backup](backup.md) | Executa backup 3-2-1 |
| [clean](clean.md) | Limpa arquivos temporários |

### Telemetria

| Comando | Descrição |
|---------|-----------|
| [track](telemetry.md#track) | Registra atividade |
| [stats](telemetry.md#stats) | Mostra estatísticas |
| [weekly](telemetry.md#weekly) | Gera relatório semanal |

## Opções Globais

Estas opções funcionam com todos os comandos:

| Opção | Descrição |
|-------|-----------|
| `--root <path>` | Especifica o diretório root do DevBase |
| `--no-color` | Desabilita saída colorida |
| `--dry-run` | Mostra o que seria feito sem executar |
| `--help` | Mostra ajuda |

## Exemplos

```bash
# Verificar integridade
devbase doctor

# Criar projeto
devbase new minha-api

# Registrar atividade
devbase track "Implementei feature X"

# Ver o que seria feito (dry-run)
devbase clean --dry-run

# Usar root personalizado
devbase doctor --root ~/OutroWorkspace
```

## Autocompletion

O DevBase suporta autocompletion em bash, zsh e PowerShell.

### Instalação

=== "Bash/Zsh"

    ```bash
    # Com argcomplete
    pip install argcomplete
    eval "$(register-python-argcomplete devbase)"
    
    # Ou use o script fornecido
    source completions/devbase.bash
    ```

=== "PowerShell"

    ```powershell
    Import-Module ./completions/_devbase.ps1
    ```

## Próximas Páginas

Veja a documentação detalhada de cada comando:

- [setup](setup.md) - Inicialização do workspace
- [doctor](doctor.md) - Diagnóstico de saúde
- [audit](audit.md) - Auditoria de nomenclatura
