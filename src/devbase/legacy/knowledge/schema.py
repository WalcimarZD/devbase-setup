"""
Knowledge Management Module - Core Schema
==========================================
Pydantic models for YAML frontmatter validation and knowledge graph nodes.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class BaseNote(BaseModel):
    """Common metadata for all knowledge base notes."""
    
    id: Optional[str] = Field(
        None,
        description="Unique identifier (UUID or timestamp-based)"
    )
    type: Literal["project", "reference", "journal", "concept", "til"] = Field(
        ...,
        description="Note type for categorization"
    )
    status: Literal["draft", "active", "archived"] = Field(
        "active",
        description="Note lifecycle status"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for faceted search"
    )
    created: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp"
    )
    updated: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )


class ProjectNote(BaseNote):
    """Project documentation metadata."""
    
    type: Literal["project"] = "project"
    priority: Literal["high", "medium", "low"] = "medium"
    stack: List[str] = Field(default_factory=list, description="Technology stack")
    owner: Optional[str] = None
    started: Optional[datetime] = None
    due: Optional[datetime] = None


class ReferenceNote(BaseNote):
    """Literature notes, papers, books, articles."""
    
    type: Literal["reference"] = "reference"
    source_type: Literal["book", "article", "video", "repo", "paper"] = Field(
        ...,
        description="Type of reference material"
    )
    author: Optional[str] = None
    url: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5, description="Quality rating")


class JournalNote(BaseNote):
    """Daily logs, daybook entries."""
    
    type: Literal["journal"] = "journal"
    entry_date: datetime = Field(default_factory=datetime.now)
    mood: Optional[int] = Field(None, ge=1, le=10, description="Daily mood score")
    focus_hours: Optional[float] = None


class TILNote(BaseNote):
    """Today I Learned - quick knowledge captures."""
    
    type: Literal["til"] = "til"
    source: Optional[str] = Field(None, description="Where you learned this")
    related_to: List[str] = Field(
        default_factory=list,
        description="Related notes (wikilinks)"
    )


class ConceptNote(BaseNote):
    """Evergreen notes, concepts, ideas."""
    
    type: Literal["concept"] = "concept"
    maturity: Literal["seedling", "budding", "evergreen"] = Field(
        "seedling",
        description="Note maturity level (Zettelkasten-inspired)"
    )
    connections: List[str] = Field(
        default_factory=list,
        description="Linked concepts (wikilinks)"
    )
