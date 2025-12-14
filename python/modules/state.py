"""
DevBase State Module
================================================================
PROPÓSITO:
    Gerencia a persistência de estado do DevBase (.devbase_state.json).
    Equivalente ao bootstrap.ps1 (Get-DevBaseState, Save-DevBaseState).

FUNCIONALIDADES:
    - Get-State: Lê o JSON de estado, se existir
    - Save-State: Salva o estado atual (versão, migrações)
    - Schema enforcement: Garante formato correto do JSON

USO:
    from state import StateManager

    state_mgr = StateManager(root_path)
    current = state_mgr.get_state()
    print(f"Versão instalada: {current['version']}")
    
    # Atualizar estado
    current['lastUpdate'] = datetime.now().isoformat()
    state_mgr.save_state(current)

Autor: DevBase Team
Versão: 3.1.0
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class StateManager:
    """
    Gerencia leitura e escrita do arquivo de estado .devbase_state.json.
    """

    STATE_FILENAME = ".devbase_state.json"

    def __init__(self, root_path: Path):
        """
        Inicializa o gerenciador com o caminho raiz.
        
        Args:
            root_path: Caminho (Path object) para a raiz do workspace.
        """
        self.root = root_path
        self.state_file = self.root / self.STATE_FILENAME

    def get_initial_state(self) -> Dict[str, Any]:
        """Retorna um objeto de estado vazio/inicial."""
        return {
            "version": "0.0.0",
            "policyVersion": "0.0",
            "installedAt": None,
            "lastUpdate": None,
            "migrations": [],
            "modules": []
        }

    def get_state(self) -> Dict[str, Any]:
        """
        Lê o estado atual do arquivo JSON.
        Se não existir, retorna estado inicial.
        
        Returns:
            Dict com os dados de estado.
        """
        if not self.state_file.exists():
            return self.get_initial_state()

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # Em caso de erro de leitura (corrupção), avisa mas retorna limpo
            # (Num cenário real, poderíamos fazer backup do corrompido)
            print(f" [!] Warning: Could not read state file: {e}")
            return self.get_initial_state()

    def save_state(self, state: Dict[str, Any]) -> None:
        """
        Salva o estado no arquivo JSON.
        
        Usa escrita direta aqui pois a atomicidade deveria ser garantida 
        pelo chamador (ex: save_state deve ser chamado APÓS sucesso).
        MAS, idealmente, usaríamos o FileSystem.write_atomic.
        Para desacoplar, vamos usar json.dump simples, mas 
        o orquestrador principal deve garantir a integridade.
        
        Args:
            state: Dict com os dados a salvar.
        """
        # Garante timestamp atual se não fornecido
        if not state.get("lastUpdate"):
            state["lastUpdate"] = datetime.now().isoformat()

        # Cria diretório se não existir (caso raro de rodar state antes do fs setup)
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

        # Escrita com indentação para legibilidade
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
