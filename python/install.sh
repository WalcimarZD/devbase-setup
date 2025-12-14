#!/bin/bash
# DevBase Installer (Python Version)
# Installs DevBase Engineering Operating System

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}>>> DevBase Installer${NC}"

# Check requirements
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 could not be found.${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}[ERROR] Git could not be found.${NC}"
    exit 1
fi

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEVBASE_DIR="$SCRIPT_DIR"

# Install dependencies
if [ -f "$DEVBASE_DIR/requirements.txt" ]; then
    echo -e "${BLUE}>>> Installing Python dependencies...${NC}"
    pip3 install -r "$DEVBASE_DIR/requirements.txt" --user --quiet
fi

# Run Setup
echo -e "${BLUE}>>> Running DevBase Setup...${NC}"
python3 "$DEVBASE_DIR/devbase.py" setup "$@"

echo -e "${GREEN}>>> Installation Complete!${NC}"
echo -e "Run 'python3 devbase.py doctor' to verify."
