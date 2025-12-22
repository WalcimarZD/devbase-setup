#!/usr/bin/env bash
# Build academic paper with Pandoc + BibTeX
# Usage: ./build_paper.sh <input.md> [style] [format]
#
# Examples:
#   ./build_paper.sh thesis.md abnt pdf
#   ./build_paper.sh article.md apa docx
#   ./build_paper.sh slides.md ieee html

set -e  # Exit on error

PAPER="$1"
STYLE="${2:-abnt}"    # Default: ABNT
FORMAT="${3:-pdf}"     # Default: PDF

# Validation
if [ -z "$PAPER" ]; then
  echo "❌ Error: No input file specified"
  echo ""
  echo "Usage: $0 <paper.md> [style] [format]"
  echo ""
  echo "Styles: abnt, apa, ieee, chicago"
  echo "Formats: pdf, docx, html"
  exit 1
fi

if [ ! -f "$PAPER" ]; then
  echo "❌ Error: File not found: $PAPER"
  exit 1
fi

# Paths (relative to script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"

BIB="$WORKSPACE_ROOT/10-19_KNOWLEDGE/15_references/library.bib"
CSL_DIR="$WORKSPACE_ROOT/00-09_SYSTEM/05_templates/csl"
CSL="$CSL_DIR/${STYLE}.csl"

# Output file
OUTPUT="${PAPER%.md}.${FORMAT}"

# Validation
if [ ! -f "$BIB" ]; then
  echo "⚠️  Warning: Bibliography not found at $BIB"
  echo "   Continuing without citations..."
  BIB_ARG=""
else
  BIB_ARG="--bibliography=$BIB"
fi

if [ ! -f "$CSL" ]; then
  echo "⚠️  Warning: CSL style not found: $CSL"
  echo "   Using Pandoc default..."
  CSL_ARG=""
else
  CSL_ARG="--csl=$CSL"
fi

# Build command
echo "📄 Building paper..."
echo "   Input: $PAPER"
echo "   Style: $STYLE"
echo "   Format: $FORMAT"
echo ""

pandoc "$PAPER" \
  $BIB_ARG \
  $CSL_ARG \
  --number-sections \
  --toc \
  --standalone \
  -o "$OUTPUT"

if [ $? -eq 0 ]; then
  FILESIZE=$(du -h "$OUTPUT" | cut -f1)
  echo "✅ Success! Built: $OUTPUT ($FILESIZE)"
else
  echo "❌ Build failed"
  exit 1
fi
