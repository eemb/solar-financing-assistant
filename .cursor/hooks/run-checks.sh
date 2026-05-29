#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtualenv if present
if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
fi

echo "=== ruff check ==="
ruff check .

echo ""
echo "=== ruff format --check ==="
ruff format --check .

echo ""
echo "=== pytest ==="
pytest
