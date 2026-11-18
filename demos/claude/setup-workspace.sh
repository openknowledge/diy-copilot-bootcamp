#!/usr/bin/env bash
# Creates a fresh Roomie workspace for the Claude Code demos (levels 4 and 5).
#
#   demos/claude/setup-workspace.sh 4 [target]   # MCP servers directly (:8100 knowledge base, :8101 tickets)
#   demos/claude/setup-workspace.sh 5 [target]   # MCP via the LiteLLM gateway (http://localhost:4000/mcp/)
#
# The workspace is a copy of demos/app in its own git repository (default: ~/roomie-workspace),
# so Claude Code never changes the demo sources, and every demo starts from the same state.
# Run it again to reset the workspace.
set -euo pipefail

LEVEL="${1:-}"
TARGET="${2:-$HOME/roomie-workspace}"
DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKER=".roomie-workspace"

if [[ "$LEVEL" != "4" && "$LEVEL" != "5" ]]; then
  echo "Usage: $0 <4|5> [target directory]" >&2
  exit 1
fi

# Level 5: get a key of team-workplace from the gateway first - if the gateway is not
# running, stop before the existing workspace is touched.
if [[ "$LEVEL" == "5" ]]; then
  TEAM_KEY="$("$DEMOS_DIR/litellm/create-team-key.sh")" || {
    echo "Could not create a key - is the gateway running? (docker compose --profile gateway up -d)" >&2
    exit 1
  }
fi

# Only ever delete directories this script created
if [[ -e "$TARGET" ]]; then
  if [[ ! -f "$TARGET/$MARKER" ]]; then
    echo "$TARGET exists and is not a Roomie workspace - not touching it." >&2
    exit 1
  fi
  rm -rf "$TARGET"
fi

mkdir -p "$TARGET"
tar -C "$DEMOS_DIR/app" \
  --exclude=.venv --exclude=__pycache__ --exclude=.pytest_cache --exclude=Dockerfile --exclude=.dockerignore \
  -cf - . | tar -C "$TARGET" -xf -

cat > "$TARGET/.gitignore" <<'EOF'
.venv/
__pycache__/
.pytest_cache/
.roomie-workspace
.litellm-key
EOF
touch "$TARGET/$MARKER"

# MCP configuration for Claude Code (project scope - Claude Code asks once to approve it).
# Level 5: Claude Code only knows the gateway; which servers it gets is decided by the key.
if [[ "$LEVEL" == "4" ]]; then
  cat > "$TARGET/.mcp.json" <<'EOF'
{
  "mcpServers": {
    "knowledge-base": {
      "type": "http",
      "url": "http://localhost:8100/mcp"
    },
    "issue-tracker": {
      "type": "http",
      "url": "http://localhost:8101/mcp"
    }
  }
}
EOF
else
  cat > "$TARGET/.mcp.json" <<'EOF'
{
  "mcpServers": {
    "litellm-gateway": {
      "type": "http",
      "url": "http://localhost:4000/mcp/",
      "headers": {
        "x-litellm-api-key": "Bearer ${LITELLM_TEAM_KEY}"
      }
    }
  }
}
EOF
fi

# Level 5: store the key. .mcp.json only references the environment variable - the key
# itself is not committed.
if [[ "$LEVEL" == "5" ]]; then
  echo "$TEAM_KEY" > "$TARGET/.litellm-key"
fi

cd "$TARGET"
git init -q -b main
git add -A
git -c user.name="Team Workplace" -c user.email="workplace@example.com" commit -q -m "Roomie 2.3.1"
uv sync -q 2>/dev/null || echo "(uv sync failed - Claude Code can run it later)"

echo "Roomie workspace for level $LEVEL: $TARGET"
if [[ "$LEVEL" == "5" ]]; then
  echo '  cd '"$TARGET"' && LITELLM_TEAM_KEY=$(cat .litellm-key) claude'
else
  echo "  cd $TARGET && claude"
fi
