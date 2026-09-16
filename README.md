# Deepfold Approvals Desk

Human-in-the-loop newsroom control panel so AI-drafted articles are reviewed before they reach Conservative Post and the UK local titles around it.

This repository used to be a Django “publishing outlets / organisations / addresses” app. That application is gone from the working tree. **Git history is kept.** New work sits on top as a clean scaffold for the desk Mike Rouse actually needs: a journalist spike, a story well, outlet localisation, social packs, and a learning loop.

## Architecture

```
Journalist (apps/desk, Next.js)
        │
        ▼
FastAPI (apps/api)  ── confidence stub
        │
        ├── Postgres  Draft (+ pipeline status, parked), DraftVersion, Outlet,
        │             PublishTarget, Decision, MediaAsset, SocialPost, AuditEvent
        ├── Redis     reserved for queues / locks (optional in v0)
        └── WordPress REST adapter (Application Password, draft-only by default)
```

| Path | What it is |
| --- | --- |
| `apps/desk` | Journalist UI: queue, story, outlets, social stubs, actions |
| `apps/api` | Drafts, decisions, outlets, confidence, WP stub, audit |
| `packages/` | Pointer to the live OpenAPI contract (`/docs`) |
| `AGENTS.md` | How VS Code and cloud agents / Grok Bot should use this repo |

Schema is owned by SQLAlchemy models in `apps/api/app/models.py`. Postgres DDL is also in Alembic (`apps/api/alembic/versions/001_initial.py`).

## How to run locally

### Docker Compose (default)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000/docs
- Desk: http://localhost:3000
- Postgres: `localhost:5432` user/password/db `deepfold`
- Redis: `localhost:6379` (optional for v0; the API does not yet depend on it)

`docker compose up` brings up **db + redis + api**. The desk is included so the seeded review screen is one command away.

### Without Docker (cloud agents, or a laptop without Compose)

The API will boot on SQLite if `DATABASE_URL` points at a file, and will create tables + seed sample copy on startup:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite+pysqlite:///./deepfold.db
export APPROVE_AND_PUBLISH_ENABLED=false
export KILL_SWITCH=false
uvicorn app.main:app --reload --port 8000
```

```bash
cd apps/desk
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

API tests (SQLite):

```bash
cd apps/api
pip install -r requirements.txt
pytest
```

## How Grok Bot / cloud agents and VS Code both use this repo

Same git remote, same layout, same rules.

- **VS Code / Cursor Desktop** — open the repo root, run Compose (or the SQLite fallback), work in `apps/desk` and `apps/api`. Do not recreate the Django `accounts` app.
- **Cloud agents / Grok Bot** — treat this README and `AGENTS.md` as standing instructions. Prefer Compose when Docker exists; otherwise the SQLite fallback is the documented equivalent so the seeded desk still runs. Persist journalist actions only through `POST /drafts/{id}/decisions`. Never auto-publish `single_source`, `caution`, or `defamation_sensitive` copy. Honour `KILL_SWITCH`.
- **Both** — feature work is branches + PRs. The live contract is FastAPI’s OpenAPI at `/openapi.json`.

## Editorial pipeline

The desk is a **newsroom pipeline**, not a flat mixed queue. Abstract comes first; a journalist presses **Go** before anyone writes the article.

| Stage | What you see | What you do |
| --- | --- | --- |
| **Pitch** | Headline, abstract, sources, suggested outlets. Not a draft. | **Go** commissions a draft. **No-go** kills it (confirm + reason). **Leave** parks it on the spike. |
| **Drafting** | Article, image plate, tags, outlet grafs. | Produce the piece, then **Send to checking**. **Back to pitch** undoes Go. |
| **Checking** | Journalist review. | **Approve CMS draft** / **Request changes** (reason) / **Reject** (reason) / **Hold**. |
| **Publication** | WordPress draft-only targets (dry-run unless `WP_LIVE`). | File CMS drafts; **Send to social**. |
| **Social** | X / Facebook stubs. | Approve / edit / hold. Connectors are not wired yet. |

A persistent **stage strip with counts** filters the spike. Leave is not No-go. Approve & publish stays **off** by default. `single_source`, `caution`, and `defamation_sensitive` copy can never auto-publish.

Seeded demo: the Midlands councils story sits in **Pitch** until Go. A burglary appeal is in **Drafting**. Checking holds the A5 Hinckley notice (calm, verified) and the cabinet-member diary gap (defamation-sensitive). Publication and Social start empty.

## Journalist screen (v0)

The desk opens on **Pitch**. Seeded copy:

1. Midlands social-care savings — **Pitch** until Go (verified, multi-outlet)
2. Nuneaton burglary appeal — **Drafting** (**single-source** — human only)
3. Cabinet member / housebuilder diary gap — **Checking** (**defamation-sensitive**)
4. A5 Hinckley night closures — **Checking** (routine, higher confidence)

Checking still localises per outlet and files WordPress **drafts** (dry-run unless `WP_LIVE=true`). Social **connectors are not wired**; stubs appear at the Social stage. Approve & publish remains feature-flagged **off**.

## Learning loop and confidence

Every human decision is a `Decision` row plus an `AuditEvent`. The diff JSON records approve-as-is vs tweak (headline/body), reject + reason, outlet overrides, and social edits.

`app/services/confidence.py` is a **heuristic stub** on purpose. It can later be swapped for a model trained on those rows without changing the schema.

Hard rules, already enforced:

- Never auto-draft or auto-publish `single_source`, `caution`, or `defamation_sensitive`
- Kill switch (`KILL_SWITCH=true`) blocks CMS writes and auto paths
- Approve & publish stays off until a human turns the flag on
- Full audit log at `GET /audit`

v0 does **not** auto-file or auto-publish anything. Confidence is visible on the desk so the bottleneck (humans reviewing obvious copy) can later be opened **only** for high-confidence, verified, multi-source stories.

## Multi-outlet localisation

Variants are **not** synonym spam. Each story has:

- a shared **spine** (the news)
- an outlet-specific **local graf** (what changes on *this* street / in *this* town hall)

`compose_variant(spine, local_graf, outlet)` concatenates those two. Journalists can accept the suggested outlets or change them.

**SEO caveat.** Google will treat near-duplicate town pages as thin or duplicate if the only difference is a swapped place-name. Unique local reporting (named people, a planning reference, a junction, a quote) has to live in the local graf — or the piece should canonicalise to one URL. Do not scale to “every UK town” by spinning the spine.

Outlet registry is a first-class table so the same desk can grow to every UK town; publisher adapters start with **WordPress REST**. Regional desks are a later routing concern, not a second product.

## WordPress Application Password — draft-only flow

1. On the WP site, create an application password for a user who may create posts (Users → Profile → Application Passwords).
2. Set `WP_USERNAME`, `WP_APPLICATION_PASSWORD`, and each outlet’s `cms_base_url`.
3. Set `WP_LIVE=true` only when you intend to hit the real REST API.
4. The adapter POSTs to `{cms_base_url}/wp-json/wp/v2/posts`.
5. Default status is **`draft`**. `publish` is used only when Approve & publish is flagged on, the kill switch is off, and the verification class is not hard-blocked.
6. v0 with `WP_LIVE=false` records a dry-run `remote_post_id` such as `dry-nuneaton-desk` so the desk can be developed without credentials.

## Image policy

Pointer for every agent and journalist:

- Featured art is **Saatchi-style editorial** (mood, civic fabric, a still that could sit in a magazine).
- **No fake documentary incident photos.** Do not generate or commission a picture of the burglary, the crash, the meeting, or the named people “as if a photographer was there.”
- Seeded media assets are labelled plates with caption, alt, credit, and `documentary_incident=false`. If a real staff/agency photograph of an incident is used later, mark `documentary_incident=true` and it must be a real photograph, captioned as such.

## API (minimum)

- `GET /health`
- `GET /settings`
- `GET /pipeline`
- `GET /drafts` (`?stage=pitch|drafting|checking|publication|social`)
- `GET /drafts/{id}`
- `POST /drafts/{id}/decisions`
- `GET /outlets`
- `GET /audit`

## Roadmap (not this pass)

Mentioned so they are not invented here:

- Tip-off portal
- Press-release email ingest
- Street journalism app
- Advertising / commercials

Scale path that **is** in scope for the design: outlet registry → WordPress adapters → regional desks.

## License

The historical `license.md` in this repo is CC0 1.0. Product copy and newsroom policy sit with Conservative Post / Mike Rouse.
