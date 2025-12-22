"""
Knowledge System Anti-Corruption Layer Adapter
===============================================
Factory functions that route to legacy or modern Knowledge implementations
based on configuration flags.

USAGE:
    from devbase.adapters.knowledge_adapter import get_knowledge_db, get_knowledge_graph
    
    db = get_knowledge_db(workspace_root)
    graph = get_knowledge_graph(workspace_root)
"""
from pathlib import Path
from typing import Protocol, Any, List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from devbase._deprecated.knowledge.database import KnowledgeDB
    from devbase._deprecated.knowledge.graph import KnowledgeGraph


class IKnowledgeDB(Protocol):
    """Interface contract for knowledge database operations."""
    
    def add_note(self, path: Path, content: str, metadata: Dict[str, Any]) -> None:
        """Add or update a note in the database."""
        ...
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search notes by content or metadata."""
        ...


class IKnowledgeGraph(Protocol):
    """Interface contract for knowledge graph operations."""
    
    def build_graph(self) -> None:
        """Build/rebuild the knowledge graph from notes."""
        ...
    
    def get_connections(self, note_path: Path) -> List[Path]:
        """Get notes connected to the given note."""
        ...


def get_knowledge_db(root_path: str) -> IKnowledgeDB:
    """
    Factory function that returns the appropriate KnowledgeDB implementation.
    
    Args:
        root_path: Path to workspace root directory
        
    Returns:
        IKnowledgeDB: Implementation based on config flags
    """
    from devbase.utils.config import get_config
    
    config = get_config()
    use_legacy = config.get("migration.use_legacy_knowledge", True)
    log_calls = config.get("migration.log_legacy_calls", False)
    
    if use_legacy:
        from devbase._deprecated.knowledge.database import KnowledgeDB
        
        if log_calls:
            import logging
            logger = logging.getLogger("devbase.deprecated")
            logger.warning(
                "DEPRECATED: Using legacy KnowledgeDB. "
                "Set migration.use_legacy_knowledge=false to use modern implementation."
            )
        
        return KnowledgeDB(root_path)
    else:
        import warnings
        warnings.warn(
            "Modern KnowledgeDB not yet implemented. Falling back to legacy.",
            FutureWarning,
            stacklevel=2
        )
        from devbase._deprecated.knowledge.database import KnowledgeDB
        return KnowledgeDB(root_path)


def get_knowledge_graph(root_path: str) -> IKnowledgeGraph:
    """
    Factory function that returns the appropriate KnowledgeGraph implementation.
    
    Args:
        root_path: Path to workspace root directory
        
    Returns:
        IKnowledgeGraph: Implementation based on config flags
    """
    from devbase.utils.config import get_config
    
    config = get_config()
    use_legacy = config.get("migration.use_legacy_knowledge", True)
    log_calls = config.get("migration.log_legacy_calls", False)
    
    if use_legacy:
        from devbase._deprecated.knowledge.graph import KnowledgeGraph
        
        if log_calls:
            import logging
            logger = logging.getLogger("devbase.deprecated")
            logger.warning(
                "DEPRECATED: Using legacy KnowledgeGraph. "
                "Set migration.use_legacy_knowledge=false to use modern implementation."
            )
        
        return KnowledgeGraph(root_path)
    else:
        import warnings
        warnings.warn(
            "Modern KnowledgeGraph not yet implemented. Falling back to legacy.",
            FutureWarning,
            stacklevel=2
        )
        from devbase._deprecated.knowledge.graph import KnowledgeGraph
        return KnowledgeGraph(root_path)
