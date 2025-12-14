"""
DevBase AI Module - Lightweight Local AI Assistant
================================================================
Integration with Ollama for local LLM inference.
Optimized for low-resource machines (Intel i7 8th gen, 8-16GB RAM).

Features:
    - Chat: General conversation
    - Summarize: Summarize documents
    - Explain: Explain concepts
    - ADR/TIL: Generate documentation

Author: DevBase Team
Version: 3.2.0
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, Generator


# Default model (lightweight, good quality)
DEFAULT_MODEL = "phi"
OLLAMA_API = "http://localhost:11434"


class OllamaClient:
    """Client for Ollama API."""
    
    def __init__(self, base_url: str = OLLAMA_API, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    def list_models(self) -> list:
        """List available models."""
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
    
    def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """Generate text from prompt."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        
        if system:
            payload["system"] = system
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                if stream:
                    return self._stream_response(resp)
                else:
                    result = json.loads(resp.read().decode())
                    return result.get("response", "")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def _stream_response(self, resp) -> Generator[str, None, None]:
        """Stream response tokens."""
        for line in resp:
            if line:
                data = json.loads(line.decode())
                if "response" in data:
                    yield data["response"]
                if data.get("done"):
                    break
    
    def chat(
        self, 
        messages: list,
        system: Optional[str] = None
    ) -> str:
        """Chat completion with message history."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        
        if system:
            payload["messages"].insert(0, {"role": "system", "content": system})
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode())
                return result.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")


# System prompts
SYSTEM_PROMPTS = {
    "default": """You are a helpful assistant for the DevBase workspace.
DevBase is a Personal Engineering Operating System using Johnny.Decimal structure.
Keep responses concise and practical. Respond in the same language as the user.""",

    "summarize": """You are a summarization assistant. 
Create concise summaries that capture key points.
Use bullet points for multiple items.
Respond in the same language as the input text.""",

    "explain": """You are a teaching assistant.
Explain concepts clearly and simply.
Use analogies when helpful.
Respond in the same language as the user.""",

    "adr": """You are a technical documentation assistant.
Generate Architectural Decision Records (ADR) following this format:

# ADR-XXX: [Title]

**Status**: Proposed
**Date**: [Today]

## Context
[Problem description]

## Decision
[What was decided]

## Consequences
### Positive
- [Benefits]

### Negative
- [Drawbacks]""",

    "til": """You are a learning documentation assistant.
Generate Today I Learned (TIL) entries following this format:

# TIL: [Title]

**Date**: [Today]
**Tags**: [relevant, tags]

## What I Learned
[Brief explanation]

## Example
[Code or practical example]

## References
- [Source]""",

    "quiz": """You are a quiz generator for learning reinforcement.
Based on the content provided, generate 5 multiple-choice questions.
Format each question as:

Q1. [Question]
A) [Option]
B) [Option]
C) [Option]
D) [Option]
Answer: [Letter]

After all questions, provide a section with all answers explained.""",

    "flashcards": """You are a flashcard generator for spaced repetition learning.
Based on the content provided, generate flashcards in this format:

---
**Front:** [Question or concept]
**Back:** [Answer or explanation]
---

Generate 10 flashcards covering the key concepts.""",

    "readme": """You are a README generator for software projects.
Based on the project structure provided, generate a professional README.md with:

# [Project Name]

[Brief description]

## Features

- [Feature 1]
- [Feature 2]

## Installation

```bash
[Installation commands]
```

## Usage

```bash
[Usage examples]
```

## License

[License info]"""
}


def get_workspace_context(root: Path) -> str:
    """Build comprehensive context about the workspace."""
    import json
    from datetime import datetime, timedelta
    
    context_parts = ["## DevBase Workspace Context\n"]
    
    # 1. Workspace structure
    context_parts.append("### Structure (Johnny.Decimal)")
    areas = [
        ("00-09_SYSTEM", "System configs, dotfiles, templates"),
        ("10-19_KNOWLEDGE", "Documentation, ADRs, TILs, notes"),
        ("20-29_CODE", "Source code, monorepo, worktrees"),
        ("30-39_OPERATIONS", "Automation, backups, CLI, AI"),
        ("40-49_MEDIA_ASSETS", "Images, videos, exports"),
        ("90-99_ARCHIVE_COLD", "Archived projects")
    ]
    
    for area, desc in areas:
        area_path = root / area
        if area_path.exists():
            try:
                subdirs = [d.name for d in area_path.iterdir() 
                          if d.is_dir() and not d.name.startswith(".")]
                context_parts.append(f"- **{area}**: {desc}")
                if subdirs:
                    context_parts.append(f"  Folders: {', '.join(subdirs[:5])}")
            except PermissionError:
                pass
    
    # 2. Recent activity (from telemetry)
    events_file = root / ".telemetry" / "events.jsonl"
    if events_file.exists():
        try:
            context_parts.append("\n### Recent Activity (last 7 days)")
            week_ago = datetime.now() - timedelta(days=7)
            recent = []
            
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            ts = datetime.fromisoformat(event.get("timestamp", ""))
                            if ts >= week_ago:
                                recent.append(event)
                        except (json.JSONDecodeError, ValueError):
                            pass
            
            if recent:
                context_parts.append(f"Total activities: {len(recent)}")
                for event in recent[-5:]:  # Last 5
                    context_parts.append(f"- [{event.get('type', 'work')}] {event.get('message', '')}")
        except Exception:
            pass
    
    # 3. Project stats
    context_parts.append("\n### Quick Stats")
    
    # Count projects
    code_dir = root / "20-29_CODE" / "21_monorepo_apps"
    if code_dir.exists():
        try:
            projects = [d for d in code_dir.iterdir() 
                       if d.is_dir() and not d.name.startswith(".")]
            context_parts.append(f"- Projects: {len(projects)}")
        except PermissionError:
            pass
    
    # Count ADRs
    adr_dir = root / "10-19_KNOWLEDGE" / "18_adr-decisions"
    if adr_dir.exists():
        try:
            adrs = list(adr_dir.glob("*.md"))
            context_parts.append(f"- ADRs: {len(adrs)}")
        except PermissionError:
            pass
    
    return "\n".join(context_parts)


def get_project_context(project_path: Path) -> str:
    """Build context about a specific project."""
    context_parts = [f"## Project: {project_path.name}\n"]
    
    # Check for common files
    files_to_check = [
        ("README.md", "Has README"),
        ("package.json", "Node.js project"),
        ("requirements.txt", "Python project"),
        ("Cargo.toml", "Rust project"),
        ("*.csproj", "C# project"),
        (".git", "Git repository"),
    ]
    
    for pattern, label in files_to_check:
        if pattern.startswith("*"):
            if list(project_path.glob(pattern)):
                context_parts.append(f"- {label}")
        elif (project_path / pattern).exists():
            context_parts.append(f"- {label}")
    
    # List main directories
    context_parts.append("\n### Directories:")
    try:
        for item in sorted(project_path.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                context_parts.append(f"- {item.name}/")
    except PermissionError:
        pass
    
    return "\n".join(context_parts)

