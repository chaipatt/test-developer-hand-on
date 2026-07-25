-- 000003_seed (up): three demo users, each with a description explaining the
-- auth/RBAC path it demonstrates. They share one bcrypt-hashed demo password.
--
-- Demo password (LOCAL-ONLY, NON-SECRET, documented in README): LiqflowDemo!23
-- The hash below is bcrypt(cost=12) of that password. It is safe to publish
-- because it only guards throwaway local accounts on a public test repo.

INSERT INTO liqflow.users (email, password_hash, role, is_active, description)
VALUES
    (
        'unauthorized@liqflow.test',
        '$2b$12$mx5dnLGHvIHPbHzisNKeQ.1OeAX9ief5elKEfvph9MNYtzUhyJcPG',
        'user',
        FALSE,
        'Account exists but disabled — login is rejected (demonstrates the unauthorized path).'
    ),
    (
        'user@liqflow.test',
        '$2b$12$mx5dnLGHvIHPbHzisNKeQ.1OeAX9ief5elKEfvph9MNYtzUhyJcPG',
        'user',
        TRUE,
        'Standard user — sees common/public order-book data only.'
    ),
    (
        'admin@liqflow.test',
        '$2b$12$mx5dnLGHvIHPbHzisNKeQ.1OeAX9ief5elKEfvph9MNYtzUhyJcPG',
        'admin',
        TRUE,
        'Admin — sees everything a user sees plus admin-only views (user list, poller status).'
    )
ON CONFLICT (email) DO NOTHING;
