#!/usr/bin/env bash
# Creates (or updates) a team in the LiteLLM gateway and a new virtual key for Claude Code.
# Team and key may only use the given MCP servers. Prints only the key.
#
#   demos/litellm/create-team-key.sh                                   # team-workplace: knowledge_base + issue_tracker
#   demos/litellm/create-team-key.sh team-website knowledge_base       # another team: knowledge base only
#
#   LITELLM_TEAM_KEY=$(demos/litellm/create-team-key.sh)
set -euo pipefail

DEMOS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY="${LITELLM_URL:-http://localhost:4000}"
TEAM_ALIAS="${1:-team-workplace}"
shift || true
SERVER_NAMES=("$@")
if [[ ${#SERVER_NAMES[@]} -eq 0 ]]; then
  SERVER_NAMES=(knowledge_base issue_tracker)
fi

# Master key: from the environment, demos/.env or the default of docker-compose.yml
MASTER_KEY="${LITELLM_MASTER_KEY:-}"
if [[ -z "$MASTER_KEY" && -f "$DEMOS_DIR/.env" ]]; then
  MASTER_KEY="$(grep -E '^LITELLM_MASTER_KEY=' "$DEMOS_DIR/.env" | cut -d= -f2- || true)"
fi
MASTER_KEY="${MASTER_KEY:-sk-litellm-demo-master-key}"

api() {  # api METHOD PATH [JSON]
  curl -sf -X "$1" "$GATEWAY$2" -H "Authorization: Bearer $MASTER_KEY" -H "Content-Type: application/json" ${3:+-d "$3"}
}

curl -sf "$GATEWAY/health/liveliness" >/dev/null || {
  echo "LiteLLM is not running - start it with: docker compose --profile gateway up -d" >&2; exit 1; }

# Server names -> server ids (JSON list)
SERVER_IDS="$(api GET /v1/mcp/server | python3 -c "
import json, sys
servers = {s['server_name']: s['server_id'] for s in json.load(sys.stdin)}
wanted = sys.argv[1:]
missing = [name for name in wanted if name not in servers]
if missing:
    sys.exit(f'Unknown MCP server(s): {missing}. Registered: {sorted(servers)}')
print(json.dumps([servers[name] for name in wanted]))" "${SERVER_NAMES[@]}")"
PERMISSION="{\"mcp_servers\": $SERVER_IDS}"

TEAM_ID="$(api GET /team/list | python3 -c "
import json, sys
print(next((t['team_id'] for t in json.load(sys.stdin) if t.get('team_alias') == '$TEAM_ALIAS'), ''))")"
if [[ -z "$TEAM_ID" ]]; then
  TEAM_ID="$(api POST /team/new "{\"team_alias\": \"$TEAM_ALIAS\", \"object_permission\": $PERMISSION}" \
    | python3 -c "import json, sys; print(json.load(sys.stdin)['team_id'])")"
  echo "Created team $TEAM_ALIAS with MCP servers: ${SERVER_NAMES[*]}" >&2
else
  api POST /team/update "{\"team_id\": \"$TEAM_ID\", \"object_permission\": $PERMISSION}" >/dev/null
  echo "Updated team $TEAM_ALIAS, MCP servers: ${SERVER_NAMES[*]}" >&2
fi

api POST /key/generate "{\"team_id\": \"$TEAM_ID\", \"key_alias\": \"claude-code-$TEAM_ALIAS-$(date +%Y%m%d-%H%M%S)\",
  \"object_permission\": $PERMISSION}" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['key'])"
