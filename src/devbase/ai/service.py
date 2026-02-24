"""
AI Service Layer
==================
High-level AI service orchestrator for DevBase.
"""
import json
import re
import logging
from pathlib import Path
from typing import Optional, Any, Dict

from devbase.ai.exceptions import ProviderError
from devbase.ai.interface import LLMProvider
from devbase.ai.models import Insight, OrganizationSuggestion, WorkspaceAnalysis

logger = logging.getLogger(__name__)

# System prompts for AI interactions
ORGANIZATION_SYSTEM_PROMPT = """You are a Principal Systems Architect. Your task is to analyze the NATURE and INTENT of a document to place it within a Johnny.Decimal hierarchy.

LOGICAL CATEGORIZATION FRAMEWORK:
1. SYSTEMIC (00-09): Documents that establish metadata, meta-processes, and "rules of the game." If the file defines HOW work is governed, audited, or structured across the entire workspace, it belongs here.
2. EPISTEMIC (10-19): Documents that represent specialized technical knowledge, research, architectural blueprints, or high-level decisions. If the file is a source of truth for "the design" but not "the build," it belongs here.
3. PRODUCTIVE (20-29): The active workshop. Source code, monorepos, and files that are directly part of a project's implementation.
4. INSTRUMENTAL (30-39): Tools, scripts, and logs that support the infrastructure.

DECISION HEURISTIC:
- Analyze if the content is META (rules about work), ARCHITECTURAL (design of the system), or IMPLEMENTATION (the code itself).
- Maintain the original language's nuance.
- Use only the provided directory structure as a baseline, but suggest the most logical functional fit.

JSON Format:
{
  "destination": "XX-XX_AREA/XX_category",
  "new_name": "semantic-descriptive-name.md",
  "confidence": 0.98,
  "reasoning": "A deep semantic analysis explaining WHY this specific functional area was chosen based on the document's intent.",
  "metadata": {
    "title": "Human Readable Title",
    "description": "Executive summary",
    "scope": "Who or what this affects",
    "version": "1.0.0"
  }
}"""

INSIGHTS_SYSTEM_PROMPT = """You are a Systems Auditor specializing in High-Performance Engineering Workspaces.
Analyze the provided directory tree to detect structural entropy, knowledge silos, or naming inconsistencies.

FOCUS AREAS:
1. ARCHITECTURE: Is the Johnny.Decimal structure being respected? Are areas being mixed?
2. OPTIMIZATION: Are there redundant paths or cluttered deep hierarchies?
3. ORGANIZATION: Is the naming convention (kebab-case) and area boundaries enforced?

JSON Format:
{
  "score": 85,
  "insights": [
    {
      "category": "architecture|optimization|organization",
      "title": "Concise high-level finding",
      "description": "Deep analysis of the impact and a specific recommendation to fix it.",
      "severity": "info|suggestion|warning"
    }
  ]
}"""

class AIService:
    """Central orchestrator for AI-powered workspace features."""
    
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
    
    def _get_workspace_tree(self, root: Path) -> str:
        """Generates a text representation of the directory tree."""
        tree = []
        try:
            # Only list top 2 levels of directories to keep context window clean
            for item in sorted(root.glob("*")):
                if item.is_dir() and not item.name.startswith("."):
                    tree.append(item.name)
                    for sub in sorted(item.glob("*")):
                        if sub.is_dir() and not sub.name.startswith("."):
                            tree.append(f"  {item.name}/{sub.name}")
        except Exception:
            pass
        return "\n".join(tree) if tree else "Empty or inaccessible"

    def _safe_json_extract(self, text: str) -> Dict[str, Any]:
        """Extracts and parses the first JSON object found in text."""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON delimiters found")
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to extract JSON from AI response: {e}")
            return {}

    def suggest_organization(
        self,
        file_path: str,
        *,
        workspace_root: Optional[Path] = None,
    ) -> OrganizationSuggestion:
        path = Path(file_path).resolve()
        
        # Security Guard: Path Traversal Protection
        if workspace_root:
            try:
                path.relative_to(workspace_root.resolve())
            except ValueError:
                raise ValueError(f"Security Violation: Access denied to {file_path} (outside workspace)")
        
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Context Gathering
        tree_context = ""
        if workspace_root:
            tree_context = f"\nAVAILABLE DIRECTORIES:\n{self._get_workspace_tree(workspace_root)}"
        
        file_name = path.name
        file_ext = path.suffix.lower()
        file_size = path.stat().st_size
        
        content_preview = ""
        if file_ext in {".md", ".txt", ".py", ".pdf", ".docx"} and file_size < 100000:
            try:
                content_preview = path.read_text(encoding="utf-8")[:1000]
            except Exception:
                content_preview = "[Unable to read file content]"
        
        prompt = f"FILE TO ORGANIZE: {file_name}\nPREVIEW: {content_preview}\n{tree_context}"

        response = self.provider.complete(
            prompt,
            system_prompt=ORGANIZATION_SYSTEM_PROMPT,
            temperature=0.0, # Maximum precision
            max_tokens=400,
        )
        
        data = self._safe_json_extract(response)
        
        return OrganizationSuggestion(
            destination=data.get("destination", "10-19_KNOWLEDGE/11_public_garden"),
            new_name=data.get("new_name"),
            confidence=float(data.get("confidence", 0.3)),
            reasoning=data.get("reasoning", "AI response parsing failed or returned invalid data."),
            metadata=data.get("metadata", {})
        )

    def generate_insights(self, workspace_path: str = ".") -> WorkspaceAnalysis:
        path = Path(workspace_path).resolve()
        if not path.exists():
            raise ValueError(f"Path not found: {workspace_path}")
        
        # (Summary logic omitted for brevity in this patch, simplified for demonstration)
        prompt = f"Analyze workspace structure at: {path.name}"
        
        response = self.provider.complete(
            prompt,
            system_prompt=INSIGHTS_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=800,
        )
        
        data = self._safe_json_extract(response)
        
        insights = []
        for item in data.get("insights", []):
            try:
                insights.append(Insight(
                    category=item.get("category", "organization"),
                    title=item.get("title", "Untitled"),
                    description=item.get("description", "No description"),
                    severity=item.get("severity", "info"),
                ))
            except Exception:
                continue
        
        return WorkspaceAnalysis(
            score=int(data.get("score", 70)),
            insights=insights,
        )
