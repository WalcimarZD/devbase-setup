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
            with urllib.request.urlopen(req, timeout=120) as resp:
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
            with urllib.request.urlopen(req, timeout=120) as resp:
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
- [Source]"""
}


def get_workspace_context(root: Path) -> str:
    """Build context about the workspace structure."""
    context_parts = ["## DevBase Workspace Structure\n"]
    
    # List top-level areas
    areas = [
        "00-09_SYSTEM",
        "10-19_KNOWLEDGE", 
        "20-29_CODE",
        "30-39_OPERATIONS",
        "40-49_MEDIA_ASSETS",
        "90-99_ARCHIVE_COLD"
    ]
    
    for area in areas:
        area_path = root / area
        if area_path.exists():
            context_parts.append(f"- {area}/")
            # List first-level subdirs
            try:
                for subdir in sorted(area_path.iterdir()):
                    if subdir.is_dir() and not subdir.name.startswith("."):
                        context_parts.append(f"  - {subdir.name}/")
            except PermissionError:
                pass
    
    return "\n".join(context_parts)
