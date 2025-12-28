"""
AI Service Layer
==================
High-level AI service orchestrator for DevBase.

This service provides workspace-aware AI functionality,
abstracting LLM interactions behind domain-specific methods.

Example:
    >>> from devbase.ai import AIService
    >>> from devbase.ai.providers import GroqProvider
    >>> 
    >>> provider = GroqProvider()
    >>> service = AIService(provider)
    >>> suggestion = service.suggest_organization("inbox/notes.md")
    >>> print(suggestion.destination)
"""
import json
import re
from pathlib import Path
from typing import Optional

from devbase.ai.exceptions import ProviderError
from devbase.ai.interface import LLMProvider
from devbase.ai.models import Insight, OrganizationSuggestion, WorkspaceAnalysis


# System prompts for AI interactions
ORGANIZATION_SYSTEM_PROMPT = """You are a file organization assistant for a Johnny.Decimal workspace.

Johnny.Decimal is a system for organizing files using numbered categories:
- 00-09: SYSTEM (config, templates, governance)
- 10-19: KNOWLEDGE (notes, documentation, learning)
- 20-29: CODE (projects, libraries, experiments)
- 30-39: OPERATIONS (automation, backup, logs)
- 40-49: MEDIA_ASSETS (images, videos, audio)
- 90-99: ARCHIVE_COLD (archived/inactive content)

Your task is to analyze a file and suggest:
1. The best destination folder
2. An optional better filename (kebab-case, descriptive)
3. Your confidence level (0.0-1.0)
4. Brief reasoning for your suggestion

Respond ONLY with valid JSON in this exact format:
{
  "destination": "XX-XX_AREA/XX_category/optional_subcategory",
  "new_name": "suggested-name.ext" or null,
  "confidence": 0.85,
  "reasoning": "Brief explanation here"
}"""


INSIGHTS_SYSTEM_PROMPT = """You are a workspace analyst for a Johnny.Decimal organized workspace.

Analyze the workspace structure and provide actionable insights about:
1. Architecture: Structure, hierarchy, separation of concerns
2. Optimization: Performance, cleanup, consolidation opportunities
3. Organization: Naming conventions, categorization, accessibility

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
}

Provide 3-5 insights, prioritizing actionable recommendations."""


class AIService:
    """Central orchestrator for AI-powered workspace features.
    
    This service encapsulates all AI interactions, providing
    high-level methods for common DevBase workflows.
    
    Attributes:
        provider: The LLM provider to use for completions.
    """
    
    def __init__(self, provider: LLMProvider) -> None:
        """Initialize AI service with a provider.
        
        Args:
            provider: LLM provider implementation (e.g., GroqProvider).
        """
        self.provider = provider
    
    def suggest_organization(
        self,
        file_path: str,
        *,
        workspace_root: Optional[Path] = None,
    ) -> OrganizationSuggestion:
        """Analyze a file and suggest its optimal location.
        
        Examines the file's name, extension, and content preview
        to determine the best Johnny.Decimal destination.
        
        Args:
            file_path: Path to the file to organize.
            workspace_root: Optional workspace root for context.
        
        Returns:
            OrganizationSuggestion with destination, confidence, and reasoning.
        
        Raises:
            ProviderError: If AI analysis fails.
            ValueError: If file doesn't exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Gather file information for the prompt
        file_name = path.name
        file_ext = path.suffix.lower()
        file_size = path.stat().st_size
        
        # Read content preview for text files
        content_preview = ""
        text_extensions = {".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml"}
        if file_ext in text_extensions and file_size < 50000:  # < 50KB
            try:
                content_preview = path.read_text(encoding="utf-8")[:500]
            except Exception:
                content_preview = "[Unable to read file content]"
        
        # Build the user prompt
        prompt = f"""Analyze this file for organization:

Filename: {file_name}
Extension: {file_ext}
Size: {file_size} bytes
Content Preview:
---
{content_preview[:500] if content_preview else "[Binary or large file]"}
---

Suggest the best Johnny.Decimal location."""

        # Get AI response
        response = self.provider.complete(
            prompt,
            system_prompt=ORGANIZATION_SYSTEM_PROMPT,
            temperature=0.2,  # Low temperature for consistent suggestions
            max_tokens=300,
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_match.group())
            
            return OrganizationSuggestion(
                destination=data.get("destination", "10-19_KNOWLEDGE/11_public_garden"),
                new_name=data.get("new_name"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "AI could not provide reasoning."),
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback response on parse error
            return OrganizationSuggestion(
                destination="10-19_KNOWLEDGE/11_public_garden",
                new_name=None,
                confidence=0.3,
                reasoning=f"AI response parsing failed: {e}. Defaulting to knowledge area.",
            )
    
    def generate_insights(
        self,
        workspace_path: str = ".",
    ) -> WorkspaceAnalysis:
        """Analyze workspace structure and generate insights.
        
        Examines the folder hierarchy and provides recommendations
        for improving organization, architecture, and efficiency.
        
        Args:
            workspace_path: Path to the workspace root.
        
        Returns:
            WorkspaceAnalysis with score and list of insights.
        
        Raises:
            ProviderError: If AI analysis fails.
            ValueError: If path doesn't exist.
        """
        path = Path(workspace_path)
        if not path.exists():
            raise ValueError(f"Path not found: {workspace_path}")
        
        # Build workspace structure summary
        structure_lines = []
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith("."):
                    continue
                
                if item.is_dir():
                    # Count children
                    try:
                        child_count = sum(1 for _ in item.iterdir())
                    except PermissionError:
                        child_count = 0
                    structure_lines.append(f"📁 {item.name}/ ({child_count} items)")
                else:
                    size_kb = item.stat().st_size / 1024
                    structure_lines.append(f"📄 {item.name} ({size_kb:.1f}KB)")
        except PermissionError:
            structure_lines.append("[Permission denied]")
        
        structure_summary = "\n".join(structure_lines[:50])  # Limit to 50 items
        
        # Build prompt
        prompt = f"""Analyze this Johnny.Decimal workspace structure:

Workspace: {path.name}
Contents:
{structure_summary}

Provide insights on organization, architecture, and optimization opportunities."""

        # Get AI response
        response = self.provider.complete(
            prompt,
            system_prompt=INSIGHTS_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=800,
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_match.group())
            
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
                    continue  # Skip malformed insights
            
            return WorkspaceAnalysis(
                score=int(data.get("score", 70)),
                insights=insights,
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback response on parse error
            return WorkspaceAnalysis(
                score=70,
                insights=[
                    Insight(
                        category="organization",
                        title="Analysis Incomplete",
                        description=f"AI response parsing failed: {e}. Please try again.",
                        severity="warning",
                    )
                ],
            )
