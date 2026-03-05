## Stage N Implementation Request Template (paste into Codex)

Implement **Stage 0 — [Stage Name]** from the staged plan.

### Scope control

* Do **ONLY** Stage 0. Do **NOT** start Stage 1 or beyond.
* Keep all previous stages working (don’t break Stage 0..).
* If a dependency is missing from earlier stages, **stop** and list what’s missing (don’t workaround by doing future-stage work).

### Required output format (exact)

1. **What changed** (bullets)
2. **Files added/modified** (paths)
3. **Code** (full contents of ONLY touched files)
4. **How to run/test** (exact commands)
5. **Acceptance checks** (checklist)

### Stage 0 Acceptance Criteria (copy from plan)

* [Paste the acceptance checks for Stage N here]

### Notes / constraints

* Stack is fixed: discord.py bot, FastAPI API, Next.js (JS only) web, SQLAlchemy + Alembic, SQLite now → Postgres later, Dockerized.
* Use env vars for secrets; no hardcoded tokens.

Start now.
