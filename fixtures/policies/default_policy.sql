-- fixtures/policies/default_policy.sql
--
-- Table is `agent_policies`. `effect` recognises 'allow' / 'deny' / 'require_approval'.
-- Deterministic `id` values make the inserts idempotent across reruns.

INSERT INTO agent_policies (id, agent_id, resource_type, resource_key, effect, created_at, updated_at) VALUES
  ('pol_main_exec_approve',          'main', 'tool', 'exec',          'require_approval', NOW()::text, NOW()::text),
  ('pol_main_file_delete_approve',   'main', 'tool', 'file_delete',   'require_approval', NOW()::text, NOW()::text),
  ('pol_main_user_role_set_deny',    'main', 'tool', 'user_role_set', 'deny',             NOW()::text, NOW()::text)
ON CONFLICT (id) DO NOTHING;
