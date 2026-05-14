#!/usr/bin/env bash
# hermit-bench/docker/entrypoint.sh — boot postgres + gateway, then idle.
set -euo pipefail

# Start Postgres (the postgresql-16 apt package already initialised /var/lib/postgresql/16/main)
service postgresql start

for _ in $(seq 1 60); do
  if pg_isready -h 127.0.0.1 -p 5432 -q; then
    break
  fi
  sleep 1
done

# One-time DB bootstrap (idempotent via flag file)
if [ ! -f /var/lib/postgresql-state/.bootstrapped ]; then
  echo "[entrypoint] creating hermit role + database"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE USER hermit WITH PASSWORD 'hermit' SUPERUSER;" || true
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE hermit OWNER hermit;" || true
  touch /var/lib/postgresql-state/.bootstrapped
fi

export GATEWAY_ADMIN_TOKEN="${GATEWAY_ADMIN_TOKEN:-$(openssl rand -hex 32)}"
export GATEWAY_JWT_SECRET="${GATEWAY_JWT_SECRET:-$(openssl rand -hex 32)}"
# OPENHERMIT_SECRETS_KEY must decode to exactly 32 bytes (base64-encoded), per the gateway.
export OPENHERMIT_SECRETS_KEY="${OPENHERMIT_SECRETS_KEY:-$(openssl rand -base64 32)}"
export OPENHERMIT_TOKEN="$GATEWAY_ADMIN_TOKEN"

echo "$GATEWAY_ADMIN_TOKEN" > /root/.openhermit/admin_token
echo "$OPENHERMIT_SECRETS_KEY" > /root/.openhermit/secrets_key

# Persist auth + DB env vars so `docker exec` shells see them (entrypoint exports
# don't propagate to later exec sessions).
cat > /etc/profile.d/hermitbench.sh <<EOF
export GATEWAY_ADMIN_TOKEN="$GATEWAY_ADMIN_TOKEN"
export GATEWAY_JWT_SECRET="$GATEWAY_JWT_SECRET"
export OPENHERMIT_SECRETS_KEY="$OPENHERMIT_SECRETS_KEY"
export OPENHERMIT_TOKEN="$OPENHERMIT_TOKEN"
export DATABASE_URL="$DATABASE_URL"
export GATEWAY_HOST="$GATEWAY_HOST"
export GATEWAY_PORT="$GATEWAY_PORT"
export OPENHERMIT_GATEWAY_URL="$OPENHERMIT_GATEWAY_URL"
export OPENHERMIT_AGENT_ID="$OPENHERMIT_AGENT_ID"
EOF
# Also write to /etc/environment for non-shell exec contexts.
{
  echo "GATEWAY_ADMIN_TOKEN=$GATEWAY_ADMIN_TOKEN"
  echo "OPENHERMIT_TOKEN=$OPENHERMIT_TOKEN"
  echo "OPENHERMIT_SECRETS_KEY=$OPENHERMIT_SECRETS_KEY"
  echo "DATABASE_URL=$DATABASE_URL"
  echo "OPENHERMIT_GATEWAY_URL=$OPENHERMIT_GATEWAY_URL"
} > /etc/environment

if [ -f /tmp_workspace/seed.sql ]; then
  echo "[entrypoint] applying seed.sql"
  PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -f /tmp_workspace/seed.sql
fi

# Start the gateway. `hermit gateway run` is the foreground command (no flags;
# it reads GATEWAY_HOST / GATEWAY_PORT from the environment).
hermit gateway run &
GATEWAY_PID=$!

/usr/local/bin/healthcheck.sh

# Apply post-gateway seeds (need the gateway running, e.g. `hermit agents create`)
if [ -f /tmp_workspace/seed_post.sh ]; then
  echo "[entrypoint] applying seed_post.sh"
  bash /tmp_workspace/seed_post.sh
fi

if [ "$#" -gt 0 ]; then
  exec "$@"
else
  wait "$GATEWAY_PID"
fi
