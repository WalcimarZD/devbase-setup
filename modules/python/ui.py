"""
DevBase UI Module
================================================================
PROPÓSITO:
    Fornece funções de formatação de saída para o CLI do DevBase.
    Equivalente ao common-functions.ps1 (Write-Header, Write-Step).

FUNCIONALIDADES:
    - Write-Header: Títulos de seção formatados
    - Write-Step: Status steps com cores e prefixos ([+], [!], [X])
    - Cores ANSI para terminais compatíveis

USO:
    from ui import UI

    ui = UI()
    ui.print_header("My Section")
    ui.print_step("Operation successful", "OK")
    ui.print_step("Warning message", "WARN")

Autor: DevBase Team
Versão: 3.1.0
"""

import sys
from typing import Optional


class UI:
    """
    Controla a saída do console com formatação e cores.
    """

    # ANSI Color Codes
    # Redefine cores para coincidir com o script PowerShell
    # PowerShell: Green, Yellow, Red, Cyan, Magenta
    COLOR_RESET = "\033[0m"
    COLOR_SUCCESS = "\033[92m"  # Green
    COLOR_WARNING = "\033[93m"  # Yellow
    COLOR_ERROR = "\033[91m"    # Red
    COLOR_INFO = "\033[96m"     # Cyan
    COLOR_HEADER = "\033[95m"   # Magenta
    COLOR_WHITE = "\033[97m"

    def __init__(self, no_color: bool = False):
        """
        Inicializa o UI helper.

        Args:
            no_color: Se True, desabilita códigos ANSI de cor.
        """
        self.no_color = no_color
        # Detecção simples se estamos num terminal interativo
        if not sys.stdout.isatty():
            self.no_color = True

    def _color(self, text: str, color_code: str) -> str:
        """Aplica cor ao texto se cores estiverem habilitadas."""
        if self.no_color:
            return text
        return f"{color_code}{text}{self.COLOR_RESET}"

    def print_header(self, title: str) -> None:
        """
        Exibe um cabeçalho de seção formatado.

        Args:
            title: O título da seção.

        Equivalente: Write-Header
        """
        line = "=" * 40
        print(f"\n{self._color(line, self.COLOR_HEADER)}")
        print(f" {self._color(title, self.COLOR_HEADER)}")
        print(f"{self._color(line, self.COLOR_HEADER)}")

    def print_step(self, message: str, status: str = "INFO") -> None:
        """
        Exibe uma mensagem de status com prefixo colorido.

        Args:
            message: A mensagem a ser exibida.
            status: O tipo de status (OK, WARN, ERROR, INFO).

        Equivalente: Write-Step
        """
        status_upper = status.upper()
        
        if status_upper == "OK":
            prefix = "[+]"
            color = self.COLOR_SUCCESS
        elif status_upper == "WARN":
            prefix = "[!]"
            color = self.COLOR_WARNING
        elif status_upper == "ERROR":
            prefix = "[X]"
            color = self.COLOR_ERROR
        else:  # INFO
            prefix = "[i]"
            color = self.COLOR_INFO

        formatted_prefix = self._color(f" {prefix}", color)
        # A mensagem em si segue a cor do status para consistência com o PS1
        formatted_message = self._color(message, color)
        
        print(f"{formatted_prefix} {formatted_message}")

    def print_banner(self, version: str) -> None:
        """Exibe o banner ASCII do DevBase."""
        ascii_art = f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ██████╗ ███████╗██╗   ██╗██████╗  █████╗ ███████╗███████╗
║     ██╔══██╗██╔════╝██║   ██║██╔══██╗██╔══██╗██╔════╝██╔════╝
║     ██║  ██║█████╗  ██║   ██║██████╔╝███████║███████╗█████╗
║     ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██╗██╔══██║╚════██║██╔══╝
║     ██████╔╝███████╗ ╚████╔╝ ██████╔╝██║  ██║███████║███████╗
║     ╚═════╝ ╚══════╝  ╚═══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
║                                                           ║
║              Personal Engineering Operating System        ║
║                      Version {version:<28} ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(self._color(ascii_art, self.COLOR_INFO))
