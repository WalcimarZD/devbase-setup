# 🧪 Guia de Teste e Validação

Este guia detalha como validar o projeto DevBase após a migração para Python. Cobre desde testes unitários automatizados até verificações manuais de integração.

## 📋 Pré-requisitos

Certifique-se de estar na raiz do projeto (`devbase-setup`) e ter o Python 3.8+ instalado.

```bash
# Verificar versão do Python
python --version
```

### Instalar Dependências de Teste

O projeto usa `pytest` para testes unitários. Se você tiver um arquivo `requirements.txt` (ou similar), instale-o. Caso contrário:

```bash
pip install pytest
```

---

## ⚡ 1. Testes Automatizados (Unit Tests)

Os testes estão localizados na pasta `tests/` e cobrem os módulos principais isoladamente.

### Executar todos os testes

```bash
python -m pytest tests/
```

**Saída esperada:**
```
tests/test_ui.py ....           [ 20%]
tests/test_state.py ....        [ 40%]
tests/test_setup_core.py ....   [ 60%]
tests/test_setup_code.py ....   [ 80%]
tests/test_devbase_cli.py ..    [100%]

===== 18 passed in 0.42s =====
```

### Executar testes de um módulo específico

```bash
# Testar apenas o setup de Code
python -m pytest tests/test_setup_code.py -v
```

---

## 🛠️ 2. Teste Manual (End-to-End)

Para verificar se a CLI está criando a estrutura corretamente no disco, executamos o script principal apontando para uma pasta de saída temporária (para não bagunçar seu workspace real).

### Passos de Validação

1.  **Limpar/Criar pasta de teste**
    Verifique se não há lixo de testes anteriores (opcional, pois o script sobrescreve).

2.  **Executar o Script**
    Rodamos com `--root` para definir o destino e `--force` para garantir que templates sejam escritos.

    ```bash
    python devbase.py --root test_output --force
    ```

3.  **Verificar a Saída no Console**
    O script deve imprimir os passos em verde (`[OK]`), amarelo (`[WARN]`) ou azul (`[INFO]`).
    *   Verifique se não há mensagens vermelhas (`[ERROR]`).
    *   Confirme se a mensagem final é: `[+] DevBase v3.X.X installed successfully!`

4.  **Inspecionar os Arquivos Gerados**
    Navegue até a pasta `test_output` e verifique a estrutura:

    ```text
    test_output/
    ├── .devbase_state.json        <-- Arquivo de estado
    ├── 00-09_SYSTEM/
    ├── 10-19_KNOWLEDGE/
    │   └── 12_private_vault/      <-- Deve existir
    ├── 20-29_CODE/
    │   └── __template-clean-arch/ <-- Deve conter src/, tests/, etc.
    ├── 30-39_OPERATIONS/
    │   ├── 30_ai/                 <-- Módulo AI
    │   └── 35_devbase_cli/        <-- Deve conter cópia do devbase.py
    ```

---

## 🐛 3. Cenários de Erro Comuns

Teste também como o script se comporta em situações adversas:

### Caminho inválido (Permissões)
Tente rodar em um diretório onde você não tem permissão de escrita (ex: `/root` no Linux ou `C:\Windows` no Windows, sem admin).
*   **Esperado:** O script deve falhar graciosamente com uma mensagem de erro (`[ERROR]`), sem "explodir" um stack trace gigante na cara do usuário.

### Templates ausentes
Renomeie temporariamente a pasta `modules/templates`.
*   **Comando:** `mv modules/templates modules/templates_bkp`
*   **Execução:** `python devbase.py --root test_output`
*   **Esperado:** O script deve avisar `[WARN] Templates dir not found`, mas continuar a execução criando as pastas vazias.
*   **Restaurar:** `mv modules/templates_bkp modules/templates`

---

## 🔄 4. Compatibilidade Cross-Platform

Se possível, teste em ambientes diferentes:

*   **Windows:** PowerShell ou CMD.
*   **WSL / Linux:** Bash/Zsh.
*   **macOS:** Terminal.

O código usa `pathlib` para garantir que barras (`/` vs `\`) sejam tratadas corretamente.
