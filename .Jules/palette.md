## 2025-10-27 - Search Result Highlighting
**Learning:** Adding visual highlighting to search results significantly improves scanability in CLI tools. Using `rich.markup.escape` before applying highlighting tags is critical to prevent markup injection if the content contains characters like `[` or `]`.
**Action:** Always escape user content before applying Rich styling tags in CLI outputs.
