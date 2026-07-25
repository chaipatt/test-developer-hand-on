# Security notes

**This repository is public.** Treat everything in it as world-readable.

## Rules
- **No secrets.** No API keys, tokens, passwords, or private DSNs in the repo or
  its history. `.env.example` holds names + local-only defaults only; real
  values go in an un-tracked `.env` (git-ignored).
- **No internal/real data.** No internal hostnames, private URLs, real service
  names, customer data, or infrastructure detail.
- The seeded users share one **local-only, non-secret demo password**
  (`LiqflowDemo!23`), documented in the README. Its bcrypt hash is committed on
  purpose — it only guards throwaway local accounts.
- The JWT secret and Postgres password in `compose.yaml` are **local demo
  values**. They are not used anywhere real.