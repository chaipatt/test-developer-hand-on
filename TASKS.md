# Hands-on test — tasks

Welcome, Liqflow candidate. Do the tasks for **your applied role**. Give a short
explanation of each result, and answer the questions in a paragraph or several.
Bonus items are optional. If you've never seen a "common question", answer it
anyway. We're happy to answer questions about the test.

**Keep us posted** (a short text is fine):
- What progressed in the last period?
- What are you doing / will you do next?
- Any blockers?

> **Answer**
> - **Last period:** developed a custom trading journal dashboard, and researched
>   and implemented performance improvements for trading bots.
> - **Next:** focusing on securing a Python backend role while actively trading
>   and exploring trading opportunities.
> - **Blockers:** none.

## The system

```
Binance TH order book → API → Postgres DB → API → BFF → Basic Frontend
```

This repo is a runnable baseline of exactly that. Get it up first.

### Checklist
- [x] Run Next.js locally
- [x] Run the Python API locally
- [x] Run Postgres locally
- [x] Run the database seeding (migrations)
- [x] Submit your finished work to run as a microservice, to GitHub as a public repo
      (`github.com/chaipatt/test-developer-hand-on` — confirm the repo is public)
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

Done:
- [x] More Binance TH public API — `GET /api/v1/ticker/24hr` added in
      `api/components/lf_tool/binance_client/core.py` (`get_ticker_24hr`),
      polled by `orderbook_poller`.
- [x] Migration — `db/000004_market_stats.{up,down}.sql`.
- [x] Before/after migration report — `tools/migration-report/main.go` via
      `github.com/golang-migrate/migrate/v4/database/postgres`; write-up in
      `docs/migration-report.md`.
- [x] Frontend surfacing — `web/src/features/orderbook/components/market-stats.tsx`,
      API `/market-stats/{symbol}` + BFF route.
- [x] Tests — pytest (`api/test/`), vitest BFF route tests, Playwright smoke.
- [x] (Bonus) Automated tests — `.forgejo/workflows/ci.yml`, incl. a
      `db-integration` job that migrates real Postgres and runs the report.
- [x] (Bonus) Play with the new API — `api/scripts/play_ticker.py`.
- [x] (Bonus) Craftsmanship — second exchange client (`bitkub_client`) +
      admin cross-exchange compare feature.
- [x] (Bonus) UML — `docs/design.md` (component, sequence, ER).

**Q&A**
- The highest transaction volume of a system/DB you've worked on or maintained?
- Comment on and analyze the system you just finished.
- List optimization ideas for this system (we'll ask you to defend one or two —
  please don't paste an AI essay).

> ### Answers
> - **The highest transaction volume of a system/DB you've worked on or maintained?**
>   - Mainly handled create/read/write/delete operations rather than full system maintenance. Estimated order/trade volume is relatively low, around 100–200 transactions per minute.
>
> - **Comment on and analyze the system you just finished.**
>   - **Overview:** Added a 24-hour market stats feed from Binance TH, integrated end-to-end from the backend to a real-time frontend widget.
>   - **Key Analysis:**
>     - **Latest-only Storage:** Overwrites old data to keep only the latest stats per symbol. Fast and lightweight, but lacks historical data for charting.
>     - **Live Cross-Exchange:** Built an admin feature comparing Binance TH and Bitkub prices in real-time for arbitrage, bypassing the DB.
>     - **Reliability:** Fixed a bid/ask swap bug and added HTTP timeouts to prevent the system from hanging if external APIs fail.
>
> - **List optimization ideas for this system.**
>   - 1. **Implement WebSockets for real-time data streaming.** 
>   - 2. **Enhance frontend UX.**
>     - Display the spread (ask matching bid) with the last price in the center.
>     - Add recent trade history features.
>   - 3. **Introduce relational tables for symbols and exchanges to facilitate cross-price comparisons.**

### Status — Backend Developer (audit 2026-07-26)

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

> ### Answers
>
> - **FinTech, exchanges, crypto, banking.**
>   - I build trading systems and API integrations against crypto exchanges — Binance,
>     Deribit, Bybit, Binance TH and Bitkub — and against the Thai stock market (SET,
>     via the Settrade SDK), including Sector Rotation momentum strategies. 
> 
> - **Quant trading and HFT.**
>   - Algorithmic strategies: Rebalancing, Inverse Contract Rebalancing, Grid Trading.
>   - Arbitrage: exchange (cross-venue), triangular, and cash-and-carry. 
> 
> - **Under pressure (tight deadline, 100%-uptime SLA).**
>   - Stay calm, prioritize tasks systematically, and tackle problems step-by-step to meet tight deadlines and high-uptime SLAs.
> 
> - **Autonomy score: 7.**
>   - Capable of end-to-end ownership (from research to deployment), while remaining open to refining workflows to match global standards.
> 
> - **Competitive programming.** 
>   - No direct competitive programming background.
> 
> - **AI skills.**
>   - Utilize AI tools and subagents with standardized company configurations. Focused on workflow customization and token-efficient practices (such as optimizing with compact tooling).
> 
> - **16Personalities: INTJ.**

---

### Ideas this baseline deliberately leaves open
- The **poller runs inside the API replica** — how would you scale it out?
- Auth is **self-contained JWT** (no external IdP) and BFF↔API calls are
  **unsigned** — what would you add for production? (See `.ai/SECURITY.md`.)
- Only the **latest** snapshot per symbol is kept — how would you store history?
