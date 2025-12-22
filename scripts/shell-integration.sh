#!/usr/bin/env bash
# DevBase Shell Integration
# ==========================
# Add to ~/.bashrc or ~/.zshrc for enhanced navigation

# Quick navigation using semantic aliases
goto() {
    local target=$(devbase nav goto "$1" 2>/dev/null)
    if [ $? -eq 0 ] && [ -d "$target" ]; then
        cd "$target"
        echo "📁 $(pwd)"
    else
        echo "Location not found: $1"
        devbase nav goto --help
    fi
}

# Environment variables for direct access
if command -v devbase &> /dev/null; then
    export DEVBASE_ROOT=$(devbase nav goto root 2>/dev/null || echo "$HOME/Dev_Workspace")
    export DEVBASE_CODE=$(devbase nav goto code 2>/dev/null || echo "$DEVBASE_ROOT/20-29_CODE/21_monorepo_apps")
    export DEVBASE_VAULT=$(devbase nav goto vault 2>/dev/null || echo "$DEVBASE_ROOT/10-19_KNOWLEDGE/12_private_vault")
fi

# Aliases for common operations
alias db='devbase'
alias db-doctor='devbase core doctor'
alias db-track='devbase ops track'
alias db-stats='devbase ops stats'

# Quick project creation
db-new() {
    devbase dev new "$1"
}

# Context-aware tracking (automatically detects project)
t() {
    devbase ops track "$*"
}

echo "✨ DevBase shell integration loaded!"
echo "   Try: goto code, goto vault, t \"your message\""
