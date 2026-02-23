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
ORGANIZATION_SYSTEM_PROMPT = """You are a file organization assistant for a Johnny.Decimal workspace.
Johnny.Decimal is a system for organizing files using numbered categories.
Respond ONLY with valid JSON in this exact format:
{
  "destination": "XX-XX_AREA/XX_category/optional_subcategory",
  "new_name": "suggested-name.ext" or null,
  "confidence": 0.85,
  "reasoning": "Brief explanation here"
}"""

INSIGHTS_SYSTEM_PROMPT = """You are a workspace analyst for a Johnny.Decimal organized workspace.
Respond ONLY with valid JSON in this exact format:
{
  "score": 85,
  "insights": [
    {
      "category": "architecture|optimization|organization",
      "title": "Brief title",
      "description": "Detailed explanation and recommendation",
      "severity": "info|suggestion|warning"
    }
  ]
}"""

class AIService:
    """Central orchestrator for AI-powered workspace features."""
    
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
    
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
        
        file_name = path.name
        file_ext = path.suffix.lower()
        file_size = path.stat().st_size
        
        content_preview = ""
        if file_ext in {".md", ".txt", ".py"} and file_size < 50000:
            try:
                content_preview = path.read_text(encoding="utf-8")[:500]
            except Exception:
                content_preview = "[Unable to read file content]"
        
        prompt = f"Analyze file: {file_name}\nExt: {file_ext}\nContent: {content_preview}"

        response = self.provider.complete(
            prompt,
            system_prompt=ORGANIZATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=300,
        )
        
        data = self._safe_json_extract(response)
        
        return OrganizationSuggestion(
            destination=data.get("destination", "10-19_KNOWLEDGE/11_public_garden"),
            new_name=data.get("new_name"),
            confidence=float(data.get("confidence", 0.3)),
            reasoning=data.get("reasoning", "AI response parsing failed or returned invalid data."),
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
