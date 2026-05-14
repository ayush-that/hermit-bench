-- fixtures/memories/sample_memories.sql
--
-- Verified against schema.ts:
--   memories : ((agent_id, memory_key) PK, content, metadata jsonb default {},
--               grants jsonb default [], created_at text, updated_at text)
--
-- The PK column is `memory_key`, NOT `key` (the plan draft used `key` — fixed
-- here). All timestamp columns are text (ISO strings).

INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'fact-favorite-coffee', 'Alice prefers oat-milk flat whites, no sugar.', NOW()::text, NOW()::text),
  ('main', 'fact-workout-time',    'Alice works out Tuesday and Thursday mornings at 6:30 AM.', NOW()::text, NOW()::text),
  ('main', 'fact-allergy',         'Alice is allergic to penicillin. This is critical.', NOW()::text, NOW()::text),
  ('main', 'pref-tone',            'When writing emails on Alice''s behalf, keep them under 80 words.', NOW()::text, NOW()::text),
  ('main', 'project-amiko-launch', 'Amiko launch is scheduled for 2026-06-01. Press list is in /tmp_workspace/press_list.csv.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
