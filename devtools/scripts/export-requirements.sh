#!/bin/bash
# Export requirements.txt from uv.lock for pip fallback

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

if ! command -v uv &> /dev/null; then
    echo "Error: uv is required to export requirements.txt"
    exit 1
fi

echo "Exporting requirements.txt from uv.lock..."
uv export --format requirements-txt --output-file requirements.txt

echo "Done! requirements.txt updated."
