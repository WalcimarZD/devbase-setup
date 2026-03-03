"""
Markdown Processing Utilities
==============================
Reusable Markdown helpers extracted from the search engine layer.
"""
from __future__ import annotations

import re
from typing import List


class MarkdownSplitter:
    """Split Markdown content into header-bounded chunks.

    Strategy:
    1. Split on H1/H2/H3 headers to preserve document structure.
    2. Further split by paragraph when a chunk exceeds ``max_words``.

    Args:
        max_words: Word budget per chunk (default 500).
    """

    def __init__(self, max_words: int = 500) -> None:
        self.max_words = max_words

    def split(self, text: str) -> List[str]:
        """Split *text* into a list of non-empty, header-bounded chunks.

        Args:
            text: Raw Markdown content.

        Returns:
            List of chunk strings, each within the word budget.
        """
        # Capture delimiters so we can prepend headers to their chunks.
        parts = re.split(r"(^#{1,3} .*)", text, flags=re.MULTILINE)

        chunks: List[str] = []
        current_chunk = ""

        for part in parts:
            if not part.strip():
                continue

            if re.match(r"^#{1,3} ", part):
                # Start a new chunk at every header boundary.
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                # Append content unless it would bust the word budget.
                combined_words = len(current_chunk.split()) + len(part.split())
                if combined_words > self.max_words:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = part
                else:
                    current_chunk += "\n" + part

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
