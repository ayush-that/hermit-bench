---
title: working notes — me, april 2026
tags: [self, work, stack, relationships]
---

# how i actually work

i write best between 10pm and 2am. mornings are for meetings and admin, not real work. anyone who tries to schedule me before 11am will get vague answers.

i ship better in long uninterrupted blocks than in pomodoro intervals. 4-hour blocks are the unit.

caffeine is for the morning slog only. nothing after 2pm or i don't sleep.

# stack i've settled on (as of this month)

- amiko-web: next.js 16 app router, deployed to vercel
- amiko-backend: node + drizzle, deployed to railway
- db: postgres on railway, primary in us-east, read replica in eu-west
- package manager across the monorepo: pnpm (settled this for the 3rd time, finally writing it down)
- monorepo orchestration: turborepo
- testing: vitest for new code, leaving the legacy jest suite alone
- error monitoring: sentry
- analytics: nothing yet, intentional

things i tried and ruled out: nx (too heavy for our scale), prisma (partial-select inference), pnpm-workspaces alone without turborepo (cache story too weak).

# code conventions i keep forgetting and then re-establishing

- api error responses follow `{ error: { code, message, hint } }` — no exceptions
- commit messages focus on the WHY, never the WHAT
- never destructure props in a component signature when there are more than 4 — prefer `props.x` for grep-ability
- never use barrel files (`index.ts` re-exports) inside features — only at the module boundary

# relationships

priya is my closest friend at work. we did the v2 redesign together. she handles eng, i handle design, but neither of us respects the line and that's why it works.

sasha is the friend i go to for non-work things. we met at a small indie show two years ago. she plans, i flow.

i don't keep more than ~4 close friends at a time. i've tried to expand the circle twice and it didn't take. accepting this.

# what i'm not doing

- not joining twitter again. amiko is enough.
- not going to YC even if invited.
- not building a course or a newsletter. those are tax-on-attention engines.

# random things i learned this month

- duckdb on postgres foreign tables is fast enough for our analytics dashboards
- the gemini 2.5 flash model is good enough for memory extraction at 1/10 the cost of opus
- "tail-truncate to 80 messages" is the right ceiling for memory extraction from chats — most signal lives at the end
- if you ship at 1am on a sunday, no one notices until tuesday

# pointer index (do not extract these)

- [stack details](./stack.md) — the long form
- [code style](./style.md) — repo conventions
- [people i've worked with](./people.md) — index
