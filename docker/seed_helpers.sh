#!/usr/bin/env bash
# hermit-bench/docker/seed_helpers.sh — source from per-task seed_post.sh.
#
# Small, idempotent wrappers around the `hermit` CLI for the bootstrap actions
# tasks repeat a lot. Flag placement quirks (hermit 0.6.x):
#   - `hermit config` carries --agent at the TOP level (before the subcommand)
#   - `hermit instructions set` carries --agent on the subcommand itself
#   - `hermit skills register <id> --path ...`, then `hermit skills enable <id> --agent <a>`
#   - `hermit config <--agent A> secrets set KEY VAL`
set -euo pipefail

# Make sure gateway auth + DB env vars set by entrypoint.sh are visible even
# when this file is sourced from a non-login `docker exec bash -c …` shell.
if [ -f /etc/profile.d/hermitbench.sh ]; then
  # shellcheck disable=SC1091
  source /etc/profile.d/hermitbench.sh
fi

hb_seed_agent() {
  local id="${1:-main}"
  # `hermit agents create` errors if the agent already exists; tolerate that for idempotency.
  hermit agents create "$id" >/dev/null 2>&1 || true
  hermit agents enable "$id" >/dev/null 2>&1 || true
}

hb_seed_instruction() {
  local agent="$1" key="$2" content="$3"
  hermit instructions set "$key" "$content" --agent "$agent"
}

hb_seed_skill() {
  local agent="$1" skill_dir="$2"
  local skill_id
  skill_id="$(basename "$skill_dir")"
  hermit skills register "$skill_id" --path "$skill_dir"
  hermit skills enable "$skill_id" --agent "$agent"
}

hb_seed_memory_via_sql() {
  local agent="$1" key="$2" content="$3"
  # psql dollar-quoting tolerates apostrophes and newlines in content without escaping.
  PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -c \
    "INSERT INTO memories (agent_id, memory_key, content, updated_at) VALUES ('$agent', '$key', \$\$${content}\$\$, NOW()::text) ON CONFLICT (agent_id, memory_key) DO UPDATE SET content = EXCLUDED.content, updated_at = EXCLUDED.updated_at;"
}

hb_seed_secret() {
  local agent="$1" key="$2" value="$3"
  hermit config --agent "$agent" secrets set "$key" "$value"
}

hb_seed_openrouter() {
  local agent="$1" key="$2" model="$3"
  hermit config --agent "$agent" secrets set OPENROUTER_API_KEY "$key"
  hermit config --agent "$agent" set model.provider openrouter
  hermit config --agent "$agent" set model.model "$model"
}
