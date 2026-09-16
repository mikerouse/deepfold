# Agent notes — Deepfold Approvals Desk

This repository is the **newsroom control panel** for Mike Rouse’s UK local-news / Conservative Post operation. It is not the legacy Django outlet-manager.

## Do not resurrect

The old `app/accounts` Django project (organisations, addresses, profile tasks, publishing-outlet CRUD) was removed from the working tree on purpose. Git history is intact; do not restore that application unless a human explicitly asks to recover a historical file.

## Layout

| Path | Role |
| --- | --- |
| `apps/desk` | Next.js journalist UI |
| `apps/api` | FastAPI: drafts, outlets, decisions, confidence stub, WordPress adapter stub |
| `packages/` | Shared notes / contracts (OpenAPI is served live at `/docs`) |

## How humans and agents use this repo

**VS Code / Cursor Desktop.** Open the repo root. Copy `.env.example` to `.env`. Run `docker compose up --build` for Postgres, Redis, API, and the desk. API: `http://localhost:8000/docs`. Desk: `http://localhost:3000`.

**Cloud agents / Grok Bot.** Same repo, same branch model. Prefer Docker Compose when the environment has Docker. If Docker is missing, use the SQLite fallback documented in the README (`DATABASE_URL=sqlite+pysqlite:///./apps/api/deepfold.db`) so the API still boots and the desk can review seeded drafts. Do not invent a third product surface.

**Both.** Schema lives in `apps/api/app/models.py` and Alembic. Persist every journalist decision through `POST /drafts/{id}/decisions`. Never auto-publish `single_source`, `caution`, or `defamation_sensitive` copy. Honour `KILL_SWITCH` and `APPROVE_AND_PUBLISH_ENABLED` (off by default).
