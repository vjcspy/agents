#!/bin/bash
# Install all dependencies and setup the unified CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "=========================================="
echo "  Devtools Installation"
echo "=========================================="
echo ""

# 1. Doctor check
echo "=== Step 1: Environment Check ==="
./scripts/doctor.sh
echo ""

# 2. Python install
echo "=== Step 2: Python Packages ==="
if command -v uv &> /dev/null; then
    echo "Using uv..."
    uv sync
else
    echo "Using pip (fallback)..."
    
    # Create venv if not exists
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    
    # Install from requirements.txt if exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Editable install all CLI packages
    echo "Installing CLI packages in editable mode..."
    for domain in common nab tinybots; do
        cli_dir="$domain/cli"
        if [ -d "$cli_dir" ]; then
            for pkg_dir in "$cli_dir"/*; do
                if [ -d "$pkg_dir" ] && [ -f "$pkg_dir/pyproject.toml" ]; then
                    echo "  Installing $pkg_dir..."
                    pip install -e "$pkg_dir" --no-deps 2>/dev/null || true
                fi
            done
        fi
    done
    
    # Install dependencies for dt-core
    pip install typer rich pyyaml
fi
echo ""

# 3. Node install
echo "=== Step 3: Node Packages ==="
if command -v pnpm &> /dev/null; then
    echo "Installing Node packages..."
    pnpm install
    
    echo "Building Node packages..."
    pnpm -r build 2>/dev/null || echo "  (some packages may not have build script)"
else
    echo "pnpm not found, skipping Node packages"
fi
echo ""

# 4. Generate plugin registry
echo "=== Step 4: Generate Plugin Registry ==="
if command -v uv &> /dev/null; then
    uv run python scripts/generate-registry.py
elif [ -f ".venv/bin/python" ]; then
    .venv/bin/python scripts/generate-registry.py
else
    python3 scripts/generate-registry.py
fi
echo ""

# 5. Link dt CLI
echo "=== Step 5: Link CLI ==="
mkdir -p ~/.local/bin

DT_BIN=""
if [ -f ".venv/bin/dt" ]; then
    DT_BIN="$REPO_ROOT/.venv/bin/dt"
elif command -v uv &> /dev/null; then
    # uv installs to its own location, create a wrapper
    DT_BIN="$REPO_ROOT/.venv/bin/dt"
    if [ ! -f "$DT_BIN" ]; then
        # Create wrapper script
        mkdir -p "$(dirname "$DT_BIN")"
        cat > "$DT_BIN" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$REPO_ROOT" && uv run dt "$@"
EOF
        chmod +x "$DT_BIN"
    fi
fi

if [ -n "$DT_BIN" ]; then
    ln -sf "$DT_BIN" ~/.local/bin/dt
    echo "Linked: ~/.local/bin/dt -> $DT_BIN"
else
    echo "Warning: Could not find dt binary to link"
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Run 'dt --help' to get started."
echo ""
echo "Make sure ~/.local/bin is in your PATH:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
