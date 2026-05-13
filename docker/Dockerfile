# hermit-bench/docker/Dockerfile
# Ubuntu 22.04 + Node 20 + Bun + Postgres 16 + openhermit npm package
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PATH=/root/.bun/bin:/usr/local/node/bin:/usr/lib/postgresql/16/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl wget git ca-certificates gnupg lsb-release sudo unzip openssl \
        build-essential python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# PGDG apt repo — Ubuntu jammy only ships postgresql-14, but the plan targets 16.
RUN install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16 postgresql-contrib-16 \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Bun (openhermit dev runtime; published npm package is fine too)
RUN curl -fsSL https://bun.sh/install | bash

# OpenHermit (provides `hermit` and `openhermit` bins)
RUN npm install -g openhermit@latest

# Postgres data + socket dirs need to be writable at runtime; cluster init is done by the apt postinst.
# We intentionally do NOT `service postgresql start` here — buildkit rootless sandbox blocks systemd/sysvinit.
# The createuser/createdb step happens at entrypoint runtime, guarded by a flag file.

ENV DATABASE_URL=postgres://hermit:hermit@127.0.0.1:5432/hermit
ENV GATEWAY_HOST=0.0.0.0
ENV GATEWAY_PORT=4000
ENV OPENHERMIT_GATEWAY_URL=http://127.0.0.1:4000
ENV OPENHERMIT_AGENT_ID=main
ENV TMP_WORKSPACE=/tmp_workspace

RUN mkdir -p /tmp_workspace /root/.openhermit /var/lib/postgresql-state

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY docker/seed.sh /usr/local/bin/seed.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/healthcheck.sh /usr/local/bin/seed.sh

EXPOSE 4000

# Default to a shell; entrypoint is invoked explicitly by the runner.
CMD ["/bin/bash"]
