# Academic Workflow with DevBase

**Target Audience:** Researchers, PhD students, technical writers

DevBase supports rigorous academic writing by integrating with industry-standard tools (Zotero, Pandoc, BibTeX) while maintaining full version control over both text and references.

---

## The Problem: Citation Management in Plain Text

Traditional Markdown workflows struggle with:
- **No automatic bibliography generation**
- **Manual citation formatting** (prone to errors)
- **Broken references** when files move
- **No integration** with reference managers

**Solution:** BibTeX + Pandoc integration

---

## Setup

### 1. Install Required Tools

```bash
# Zotero (Reference Manager)
# Download from: https://www.zotero.org/download

# Better BibTeX Plugin (Auto-export)
# Install from: https://retorque.re/zotero-better-bibtex/

# Pandoc (Document Converter)
choco install pandoc        # Windows
brew install pandoc         # macOS
sudo apt install pandoc     # Linux

# Pandoc Citer (VS Code Extension)
# Install from VS Code Marketplace: "Pandoc Citer"
```

### 2. Configure Zotero Auto-Export

1. **In Zotero:** `Edit > Preferences > Better BibTeX`
2. **Set Auto-Export Location:**
   ```
   D:\Dev_Workspace\10-19_KNOWLEDGE\15_references\library.bib
   ```
3. **Enable "Automatic Export"**
4. **Citation Key Format:** `[auth:lower][year]` (e.g., `silva2023`)

Now every reference you add to Zotero will automatically update `library.bib`.

---

## Writing Workflow

### Step 1: Write in Markdown

Create your paper in `20-29_CODE/21_drafts/`:

```markdown
# My Research Paper

## Introduction

Previous research on distributed systems [@lamport1978] established 
the fundamental principles. However, recent work [@dean2008] shows...

## Methodology

Our approach builds on the CAP theorem [@brewer2000cap]...

## References

<!-- Bibliography will be auto-generated here -->
```

### Step 2: Cite References

In VS Code, with Pandoc Citer extension:
- Type `@` to trigger autocomplete
- Select reference from `library.bib`
- Citation key inserted: `@silva2023`

**Citation Styles:**
```markdown
[@silva2023]              → (Silva, 2023)
@silva2023 argues that... → Silva (2023) argues that...
[@silva2023, p. 42]       → (Silva, 2023, p. 42)
[@silva2023; @doe2024]    → (Silva, 2023; Doe, 2024)
```

### Step 3: Build Paper with Pandoc

```bash
# Navigate to your draft
cd 20-29_CODE/21_drafts

# Generate PDF (ABNT style)
pandoc my-paper.md \
  --bibliography=../../10-19_KNOWLEDGE/15_references/library.bib \
  --csl=../../00-09_SYSTEM/05_templates/csl/abnt.csl \
  -o my-paper.pdf

# Generate DOCX (for journal submission)
pandoc my-paper.md \
  --bibliography=../../10-19_KNOWLEDGE/15_references/library.bib \
  --csl=apa.csl \
  -o my-paper.docx

# Generate HTML (for blog/website)
pandoc my-paper.md \
  --bibliography=../../10-19_KNOWLEDGE/15_references/library.bib \
  --csl=ieee.csl \
  --standalone \
  -o my-paper.html
```

---

## Citation Style Languages (CSL)

DevBase includes common styles in `00-09_SYSTEM/05_templates/csl/`:

- `abnt.csl` - Brazilian Academic Norms
- `apa.csl` - American Psychological Association
- `ieee.csl` - Institute of Electrical and Electronics Engineers
- `chicago.csl` - Chicago Manual of Style

**Find more:** https://www.zotero.org/styles

---

## Advanced: Custom Build Script

Create `scripts/build_paper.sh`:

```bash
#!/usr/bin/env bash
# Build academic paper with DevBase conventions

PAPER="$1"
STYLE="${2:-abnt}"  # Default to ABNT
FORMAT="${3:-pdf}"   # Default to PDF

if [ -z "$PAPER" ]; then
  echo "Usage: ./build_paper.sh <paper.md> [style] [format]"
  echo "Example: ./build_paper.sh thesis.md apa docx"
  exit 1
fi

BIB="../../10-19_KNOWLEDGE/15_references/library.bib"
CSL="../../00-09_SYSTEM/05_templates/csl/${STYLE}.csl"
OUTPUT="${PAPER%.md}.${FORMAT}"

pandoc "$PAPER" \
  --bibliography="$BIB" \
  --csl="$CSL" \
  --number-sections \
  --toc \
  -o "$OUTPUT"

echo "✓ Built: $OUTPUT"
```

**Usage:**
```bash
chmod +x scripts/build_paper.sh
./scripts/build_paper.sh thesis.md apa pdf
```

---

## File Organization

```
Dev_Workspace/
├── 10-19_KNOWLEDGE/
│   └── 15_references/
│       ├── library.bib           ← Auto-exported from Zotero
│       ├── papers/
│       │   ├── lamport1978.pdf
│       │   └── dean2008.pdf
│       └── notes/
│           └── lit-review.md
├── 20-29_CODE/
│   └── 21_drafts/
│       ├── thesis.md             ← Your writing
│       └── chapter1.md
└── 00-09_SYSTEM/
    └── 05_templates/
        └── csl/
            ├── abnt.csl
            ├── apa.csl
            └── ieee.csl
```

---

## Git Integration

**Benefits:**
- **Version control** on both text AND references
- **Diff citations:** See which references were added/removed
- **Collaborate** with co-authors using pull requests

```bash
cd 20-29_CODE/21_drafts
git add thesis.md
git commit -m "feat: Add methodology section with 3 new citations"

# References are tracked too
cd ../../10-19_KNOWLEDGE/15_references
git add library.bib
git commit -m "chore: Add 5 papers from systematic review"
```

---

## Comparison: DevBase vs Traditional Tools

| Feature | Word/Google Docs | LaTeX | DevBase + Pandoc |
|---------|------------------|-------|------------------|
| **Plaintext** | ❌ Binary | ✅ Yes | ✅ Yes |
| **Version Control** | ⚠️ Limited | ✅ Excellent | ✅ Excellent |
| **Citation Management** | ⚠️ Manual | ✅ BibTeX | ✅ BibTeX |
| **Format Flexibility** | ❌ Locked | ⚠️ PDF-centric | ✅ PDF/DOCX/HTML |
| **Learning Curve** | ✅ Easy | ❌ Steep | ✅ Moderate |
| **Collaboration** | ✅ Good | ⚠️ Complex | ✅ Git-based |

---

## Troubleshooting

### "Citation not found"
- **Cause:** BibTeX key mismatch
- **Fix:** Check `library.bib` for exact key (case-sensitive)

### "Bibliography not generated"
- **Cause:** Missing `--bibliography` flag
- **Fix:** Ensure command includes `--bibliography=path/to/library.bib`

### "CSL style not working"
- **Cause:** Invalid or missing CSL file
- **Fix:** Download from Zotero Style Repository

---

## Next Steps

1. **Import your existing Zotero library** (if any)
2. **Configure Better BibTeX auto-export**
3. **Create your first `.md` paper**
4. **Build with Pandoc** and iterate

**Pro Tip:** Use `devbase quick note` to capture literature review insights during reading!
