<h1 align="center">HermitBench</h1>

<p align="center">
  <img src="docs/assets/hermitbench.png" alt="HermitBench" width="480">
</p>

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
| 07 | Amiko Social | Post drafting, comment voice, AI-twin DMs, feed rank, privacy, group dynamics — Opus-judged for quality |

## Quick Start

```bash
# 1. Build the test image (Ubuntu + Postgres + OpenHermit gateway)
bash script/prepare.sh

# 2. Set OpenRouter API key
echo 'OPENROUTER_API_KEY=sk-or-...' >> .env

# 3. (Optional) Pick a judge model for category 07_Amiko_Social.
#    Tasks in 07 grade prose quality via an LLM-as-judge call to OpenRouter
#    using JUDGE_MODEL (default: anthropic/claude-opus-4.7).
echo 'JUDGE_MODEL=anthropic/claude-opus-4.7' >> .env

# 4. Run all tasks against a model
bash script/run.sh --category all --parallel 4 \
  --model anthropic/claude-sonnet-4.6
```

> Category 07 requires `OPENROUTER_API_KEY` (for the judge call) and reads
> `JUDGE_MODEL` from the environment. Each judge call costs roughly $0.01
> with `anthropic/claude-opus-4.7`; if you want to bench-test on the cheap,
> set `JUDGE_MODEL=anthropic/claude-haiku-4.7` or similar.

Per-task results land under `output/<category>/<task_id>/<model_timestamp_runid>/` with `score.json`, `usage.json`, `gateway.log`, and the seeded Postgres dump.

## How it works

Each task runs in its own Docker container that boots Postgres and an OpenHermit gateway. A per-task `seed.sql` plus workspace files establish a starting agent state. The runner sets `model.provider=openrouter` and `model.model=<args.model>`, then sends the task prompt to the agent via the OpenHermit SDK. After the agent exits (or times out), a grader Python function queries the Postgres state and the filesystem to compute scores. Token usage and cost are extracted from gateway logs.

## Acknowledgements

HermitBench's harness — Dockerized per-task containers, markdown task format with embedded graders, OpenRouter-driven cost-vs-performance reporting — is derived from [WildClawBench](https://github.com/InternLM/WildClawBench), which benchmarks the same kind of evaluation against [OpenClaw](https://github.com/openclaw/openclaw). If you use HermitBench in research, please also cite the upstream work:

```bibtex
@article{ding2026wildclawbench,
  title={WildClawBench: A Benchmark for Real-World, Long-Horizon Agent Evaluation},
  author={Ding, Shuangrui and Dai, Xuanlang and Xing, Long and Ding, Shengyuan and Liu, Ziyu and JingYi, Yang and Yang, Penghui and Zhang, Zhixiong and Wei, Xilin and Fang, Xinyu and others},
  journal={arXiv preprint arXiv:2605.10912},
  year={2026}
}
```

For machine-readable HermitBench citation metadata see [`CITATION.cff`](CITATION.cff) — GitHub will use this file to populate the repository's "Cite this repository" panel.

## License

MIT.
