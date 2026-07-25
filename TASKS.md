# Hands-on test — tasks

Welcome, Liqflow candidate. Do the tasks for **your applied role**. Give a short
explanation of each result, and answer the questions in a paragraph or several.
Bonus items are optional. If you've never seen a "common question", answer it
anyway. We're happy to answer questions about the test.

**Keep us posted** (a short text is fine):
- What progressed in the last period?
- What are you doing / will you do next?
- Any blockers?

## The system

```
Binance TH order book → API → Postgres DB → API → BFF → Basic Frontend
```

This repo is a runnable baseline of exactly that. Get it up first.

### Checklist
- [ ] Run Next.js locally
- [ ] Run the Python API locally
- [ ] Run Postgres locally
- [ ] Run the database seeding (migrations)
- [ ] Submit your finished work to run as a microservice, to GitHub as a public repo
- [ ] Prepare for the live demo and review — **we will go deep**

See [`README.md`](README.md) for how to run everything (`docker compose up`).

---

## Software Testing & QA

- Write an **SOP** for manual testing of this deployment when adding a new
  feature to Stage and Production.
- Write tests for these services and submit a **report**.
- Pick at least one (more than one for senior level):
  - Make the **percentile response time** of a microservice a feature / service / monitor.
  - Application **performance testing** or a report.
  - Show strong **Linux command** or **SQL** skills.
  - A demo of any analysis: user funnel, session analysis, error tracing,
    session replay, API analysis, a SQL-funnel UI, or a BI dashboard.

**Q&A**
- How do you make this good-quality software and achieve a high SLA score?
- You find a small but high-priority bug — what happens? Can you fix it yourself?
- If this integrated with HFT, what would you reinforce?

---

## Backend Developer

- Add more of the **Binance TH public API** (another REST endpoint and/or a
  WebSocket stream). `api/components/lf_tool/binance_client` is the place to start.
- Make a **database change via a migration script** (`db/NNNNNN_*.{up,down}.sql`).
- Show a **before/after migration report** using
  `github.com/golang-migrate/migrate/v4/database/postgres`.
- Surface your new API/WebSocket + migration data on the **frontend** (basic is fine).
- **Test your code.**
- (Bonus/require for senior level): automate your tests.
- (Bonus/require for senior level): play with the new API.
- (Bonus/require for senior level): show software craftsmanship or your quant-trade skill.
- (Bonus/require for senior level): a UML of your choice explaining the system design and data.

**Q&A**
- The highest transaction volume of a system/DB you've worked on or maintained?
- Comment on and analyze the system you just finished.
- List optimization ideas for this system (we'll ask you to defend one or two —
  please don't paste an AI essay).

---

## Full Stack Developer

- Implement a **best-practice login with the seeded DB + RBAC** (see the role
  description). The baseline already has one — improve it or justify the design.
- Make a feature that **passes through all microservices, including the DB**.
- Add **tiny contract tests** on each hop.
- Host something (your own or open-source) that **integrates with this project**;
  summarize the decision and prepare to pitch and defend it.
- Pick one or more **(Bonus/require for senior level)** items from Backend or Tester.

**Q&A**
- Your proudest project or feature?
- We'd position you as a **feature maker** — your opinion? Hardest thing about
  making a product? What are you best at?
- What's the future potential of this project? Summarize an action plan.
- (Bonus/require for senior level): if you're the project leader with a posted
  deadline and full autonomy, how do you manage yourself and your team?
- (Bonus/require for senior level): a basic feasibility study, risk assessment,
  and CVE analysis of what you built.

---

## Bonus (any role)
- Fix a CVE(s), fix a bug(s), harden security, or pay down technical debt — with an explanation.
- Describe the future potential of this project.
- Anything on automation or "AI loop" engineering.
- An executive summary or a nice BI dashboard.
- A demo of any analysis (funnel, sessions, error tracing, session replay, API).
- Build and demo the stack on **Minikube** (the baseline ships Docker Compose;
  your own k8s manifests are a fair bonus).

## Common questions (everyone)
- Your experience in FinTech, exchanges, crypto, and/or banking?
- Your experience in quant trading? In HFT?
- How do you react under pressure (tight deadline, a 100%-uptime SLA ask)?
- On a 0–10 scale (10 = full autonomy, 0 = conformity), what's your score?
- Any competitive programming background?
- Tell us about your AI skills.
- Share your 16personalities result.

---

### Ideas this baseline deliberately leaves open
- The **poller runs inside the API replica** — how would you scale it out?
- Auth is **self-contained JWT** (no external IdP) and BFF↔API calls are
  **unsigned** — what would you add for production? (See `.ai/SECURITY.md`.)
- Only the **latest** snapshot per symbol is kept — how would you store history?
