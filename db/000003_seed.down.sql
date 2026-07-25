-- 000003_seed (down): remove the seeded demo users.

DELETE FROM liqflow.users
WHERE email IN (
    'unauthorized@liqflow.test',
    'user@liqflow.test',
    'admin@liqflow.test'
);
