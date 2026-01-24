#!/bin/bash
# Daily Consistency Audit
# Runs devbase audit and outputs to a report file.

OUTPUT_FILE="daily_audit_report.txt"

echo "Running Daily Audit: $(date)" > "$OUTPUT_FILE"
echo "=================================" >> "$OUTPUT_FILE"

# Run audit with --fix and capture output
uv run devbase --root . audit run --fix --days 1 >> "$OUTPUT_FILE" 2>&1

echo "=================================" >> "$OUTPUT_FILE"
echo "Audit complete. Report saved to $OUTPUT_FILE."
cat "$OUTPUT_FILE"
