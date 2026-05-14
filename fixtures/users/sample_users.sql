-- fixtures/users/sample_users.sql
--
-- Verified against /Users/shydev/Amiko/openhermit/packages/store/src/schema.ts
-- (commit at time of authoring):
--   users           : (user_id PK, name, merged_into, created_at, updated_at)
--   user_identities : ((channel, channel_user_id) PK, user_id, created_at)
--
-- NOTE: there is no role column on users. Owner / member / guest are encoded
-- via channels (e.g. `cli` for owner) and/or `agent_policies` rows when
-- tasks need policy enforcement. Use this fixture as a baseline cast.

INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_owner',  'Alice (Owner)', NOW()::text, NOW()::text),
  ('u_member', 'Bob (User)',    NOW()::text, NOW()::text),
  ('u_guest',  'Eve (Guest)',   NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_identities (user_id, channel, channel_user_id, created_at) VALUES
  ('u_owner',  'cli',      'alice',          NOW()::text),
  ('u_owner',  'telegram', '111111',         NOW()::text),
  ('u_member', 'web',      'bob-device-abc', NOW()::text),
  ('u_member', 'slack',    'U02BOB',         NOW()::text),
  ('u_guest',  'web',      'eve-device-xyz', NOW()::text)
ON CONFLICT (channel, channel_user_id) DO NOTHING;
