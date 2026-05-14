-- fixtures/policies/default_policy.sql
--
-- Verified against schema.ts: the table is `agent_policies` (NOT
-- `access_policies` as the plan draft suggested), with columns:
--   (id PK text, agent_id, resource_type, resource_key,
--    effect default 'allow', grants jsonb default [], scope jsonb default {},
--    created_at text, updated_at text)
--
-- `effect` is free text in the schema; the runtime currently recognises
-- 'allow' / 'deny' / 'require_approval'. We mint deterministic ids so the
-- inserts are idempotent across reruns.

INSERT INTO agent_policies (id, agent_id, resource_type, resource_key, effect, created_at, updated_at) VALUES
  ('pol_main_exec_approve',          'main', 'tool', 'exec',          'require_approval', NOW()::text, NOW()::text),
  ('pol_main_file_delete_approve',   'main', 'tool', 'file_delete',   'require_approval', NOW()::text, NOW()::text),
  ('pol_main_user_role_set_deny',    'main', 'tool', 'user_role_set', 'deny',             NOW()::text, NOW()::text)
ON CONFLICT (id) DO NOTHING;
