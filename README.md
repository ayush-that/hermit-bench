<h1 align="center">HermitBench</h1>

<p align="center"><em>Cost-vs-performance evaluation for LLMs running inside OpenHermit.</em></p>

---

**HermitBench** is a 60-task benchmark that measures how well LLMs (routed through [OpenRouter](https://openrouter.ai)) can operate an [OpenHermit](https://github.com/HCF-S/openhermit) agent — the open-source agent infrastructure platform with durable Postgres state, multi-channel delivery, fleet management, and a sandboxed workspace.

Unlike CLI-agent benchmarks that test file-and-shell skills in isolation, HermitBench evaluates a model's ability to drive a production-grade agent platform: managing memory across sessions, configuring fleet-wide skills, routing across channels, scheduling cron jobs, and approving sensitive tool calls under an access policy.

## Categories

| # | Category | Focus |
|---|----------|-------|
| 01 | CLI Fluency | `hermit ...` command usage, config, secrets, agent lifecycle |
| 02 | Tool Composition | Multi-tool chains (file + exec + web + memory) |
| 03 | Access Control | Policy rows, approval flow, role-based grants |
| 04 | Channel Routing | Cross-channel session continuity, group routing rules |
| 05 | Memory & Introspection | Long-term memory recall, working memory updates |
| 06 | Scheduling & Automation | Cron jobs, one-shot schedules, run history |

## Quick Start

```bash
# 1. Build the test image (Ubuntu + Postgres + OpenHermit gateway)
bash script/prepare.sh

# 2. Set OpenRouter API key
echo 'OPENROUTER_API_KEY=sk-or-...' >> .env

# 3. Run all 60 tasks against a model
bash script/run.sh --category all --parallel 4 \
  --model anthropic/claude-sonnet-4.6
```

Per-task results land under `output/<category>/<task_id>/<model_timestamp_runid>/` with `score.json`, `usage.json`, `gateway.log`, and the seeded Postgres dump.

## How it works

Each task runs in its own Docker container that boots Postgres and an OpenHermit gateway. A per-task `seed.sql` plus workspace files establish a starting agent state. The runner sets `model.provider=openrouter` and `model.model=<args.model>`, then sends the task prompt to the agent via the OpenHermit SDK. After the agent exits (or times out), a grader Python function queries the Postgres state and the filesystem to compute scores. Token usage and cost are extracted from gateway logs.

## License

MIT.
