## 2024-05-23 - Visual Polish for CLI Diagnostics
**Learning:** Users perceive CLI tools as more professional and less daunting when dense information (like error lists) is structured in tables rather than plain text lists. Visual hierarchy helps them focus on the "Fix" action.
**Action:** When displaying lists of items with metadata (like ID, Description, Fix) in CLI commands, prefer `rich.table.Table` over loop-printed strings.
