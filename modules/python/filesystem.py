"""
DevBase Core Filesystem Module
================================================================

PROPÓSITO:
    Implementa operações de filesystem seguras e atômicas para o DevBase.
    Este módulo é o equivalente Python das funções em common-functions.ps1
    (New-DirSafe, Write-FileAtomic, Assert-SafePath).

PRINCÍPIOS DE DESIGN:
    1. ATOMICIDADE: Operações de escrita usam write-to-temp-then-rename
       para garantir que arquivos nunca fiquem em estado inconsistente

    2. SEGURANÇA: Validação de path traversal impede acesso fora do root

    3. IDEMPOTÊNCIA: Operações podem ser executadas múltiplas vezes
       sem efeitos colaterais (mkdir com exist_ok=True)

    4. PORTABILIDADE: Funciona em Windows, Linux e macOS

PADRÃO ATÔMICO (Write-Replace):
    Problema: Escrita direta em arquivo pode corromper se interrompida

    Escrita Direta (RUIM):
        1. Abre arquivo existente
        2. Trunca conteúdo
        3. Escreve novo conteúdo   ← Se falhar aqui, arquivo corrupto!
        4. Fecha arquivo

    Write-Replace (BOM):
        1. Escreve em arquivo temporário (.tmp)
        2. Sincroniza com disco (fsync)
        3. Rename atômico (substitui o original)

    Por que funciona? O rename é uma operação atômica no sistema de arquivos.
    Ou o arquivo antigo existe, ou o novo. Nunca um estado intermediário.

USO:
    from filesystem import FileSystem

    fs = FileSystem("/home/user/Dev_Workspace")
    fs.ensure_dir("10-19_KNOWLEDGE/11_public_garden")
    fs.write_atomic("README.md", "# Hello World")

EQUIVALÊNCIA POWERSHELL:
    - FileSystem.ensure_dir()    → New-DirSafe
    - FileSystem.write_atomic()  → Write-FileAtomic / New-FileSafe
    - FileSystem.assert_safe_path() → Assert-SafePath

Autor: DevBase Team
Versão: 3.1.0
"""

import os
import uuid
from pathlib import Path


class FileSystem:
    """
    Classe principal para operações de filesystem seguras no DevBase.

    Todas as operações são relativas ao diretório root, e validações
    de segurança impedem acesso fora deste diretório.

    Attributes:
        root (Path): Caminho absoluto do diretório raiz do DevBase

    Example:
        >>> fs = FileSystem("~/Dev_Workspace")
        >>> fs.ensure_dir("00-09_SYSTEM/00_inbox")
        >>> fs.write_atomic("README.md", "# My Workspace")
    """

    def __init__(self, root_path: str):
        """
        Inicializa o FileSystem com o diretório raiz.

        Args:
            root_path: Caminho para o diretório raiz do DevBase.
                       Pode ser relativo (será resolvido para absoluto).

        Note:
            O path é resolvido (.resolve()) para obter caminho absoluto
            e normalizado, prevenindo problemas com symlinks e ..
        """
        self.root = Path(root_path).resolve()

    def assert_safe_path(self, target_path: Path) -> bool:
        """
        Valida que o caminho está dentro do diretório root.

        Esta é uma proteção crítica contra PATH TRAVERSAL, um tipo
        de vulnerabilidade onde um atacante tenta acessar arquivos
        fora do diretório permitido usando "../" ou caminhos absolutos.

        Exemplo de ataque que isto previne:
            write_atomic("../../etc/passwd", "malicious content")

        Args:
            target_path: Path a ser validado

        Returns:
            bool: True se o path é seguro

        Raises:
            ValueError: Se o path estiver fora do root (SECURITY VIOLATION)

        Example:
            >>> fs = FileSystem("/home/user/workspace")
            >>> fs.assert_safe_path(Path("/home/user/workspace/docs"))  # OK
            >>> fs.assert_safe_path(Path("/etc/passwd"))  # ValueError!
        """
        # .resolve() normaliza o path (remove .., resolve symlinks)
        resolved_target = target_path.resolve()

        # Verifica se o path resolvido começa com o root
        # str() é necessário para comparação string-prefix
        if not str(resolved_target).startswith(str(self.root)):
            raise ValueError(
                f"SECURITY VIOLATION: Path '{target_path}' is outside root '{self.root}'"
            )
        return True

    def ensure_dir(self, path: str) -> Path:
        """
        Cria diretório de forma idempotente e segura.

        Esta função implementa o mesmo comportamento de New-DirSafe
        do PowerShell: cria o diretório se não existir, não faz nada
        se já existir.

        Idempotência é importante porque permite que o bootstrap
        seja executado múltiplas vezes sem erros.

        Args:
            path: Caminho do diretório (relativo ao root ou absoluto)

        Returns:
            Path: Objeto Path do diretório criado

        Raises:
            ValueError: Se o path estiver fora do root

        Example:
            >>> fs = FileSystem("/workspace")
            >>> fs.ensure_dir("10-19_KNOWLEDGE/11_public_garden")
            # Cria /workspace/10-19_KNOWLEDGE/11_public_garden
        """
        target = Path(path)

        # Se não for absoluto, torna relativo ao root
        if not target.is_absolute():
            target = self.root / target

        # Validação de segurança
        self.assert_safe_path(target)

        # Cria diretório se não existir
        # parents=True: cria diretórios intermediários (como mkdir -p)
        # exist_ok=True: não falha se já existir (idempotente)
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f" [+] Created directory: {target}")

        return target

    def write_atomic(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """
        Escreve arquivo usando padrão Write-Replace (Atômico).

        ALGORITMO WRITE-REPLACE:
        1. Escreve conteúdo em arquivo temporário (.tmp) no mesmo diretório
        2. Força sincronização com disco (fsync)
        3. Renomeia atomicamente para o destino final

        POR QUE O MESMO DIRETÓRIO?
        O rename só é atômico se origem e destino estão no mesmo
        filesystem. Por isso o .tmp é criado na mesma pasta.

        SANITIZAÇÃO BOM:
        BOM (Byte Order Mark) é um caractere especial (U+FEFF) que
        alguns editores adicionam no início de arquivos UTF-8.
        Removemos para evitar problemas de compatibilidade.

        NEWLINE NO FINAL:
        Arquivos POSIX devem terminar com newline. Isso garante
        compatibilidade com ferramentas Unix (cat, grep, etc.)

        Args:
            path: Caminho do arquivo (relativo ao root ou absoluto)
            content: Conteúdo a ser escrito
            encoding: Encoding do arquivo (padrão: utf-8)

        Raises:
            ValueError: Se o path estiver fora do root
            Exception: Se a escrita falhar (arquivo .tmp é limpo)

        Example:
            >>> fs = FileSystem("/workspace")
            >>> fs.write_atomic("README.md", "# Hello World")
        """
        target = Path(path)

        # Resolve path relativo
        if not target.is_absolute():
            target = self.root / target

        # Validações de segurança
        self.assert_safe_path(target)

        # Garante que o diretório pai existe
        self.ensure_dir(target.parent)

        # Arquivo temporário no MESMO diretório (importante para atomicidade!)
        # Formato: .filename.uuid.tmp
        # O . no início esconde o arquivo em sistemas Unix
        tmp_name = f".{target.name}.{uuid.uuid4()}.tmp"
        tmp_path = target.parent / tmp_name

        try:
            # === PASSO 1: Escreve em arquivo temporário ===
            with open(tmp_path, "w", encoding=encoding, newline="\n") as f:
                # Remove BOM se presente (sanitização)
                # U+FEFF é o caractere BOM em Unicode
                if content.startswith("\ufeff"):
                    content = content[1:]

                f.write(content)

                # Garante newline no final (padrão POSIX)
                if not content.endswith("\n"):
                    f.write("\n")

                # === PASSO 2: Força escrita no disco ===
                # flush() envia buffer do Python para o OS
                # fsync() força o OS a escrever no disco físico
                f.flush()
                os.fsync(f.fileno())

            # === PASSO 3: Rename atômico ===
            # Path.replace() usa os.replace() internamente
            # Esta operação é atômica em POSIX e Windows (Python 3.3+)
            tmp_path.replace(target)
            print(f" [OK] Wrote atomic: {target.name}")

            # === PASSO 4: Proteção extra para vault privado ===
            # No Linux/Mac, arquivos sensíveis recebem chmod 600
            # (apenas dono pode ler/escrever)
            if "12_private_vault" in str(target) and os.name == "posix":
                os.chmod(target, 0o600)  # rw-------

        except Exception as e:
            # Em caso de erro, limpa o arquivo temporário
            print(f" [ERR] Failed to write {target}: {e}")
            if tmp_path.exists():
                os.unlink(tmp_path)  # Remove arquivo temporário
            raise  # Re-lança a exceção para o chamador tratar
