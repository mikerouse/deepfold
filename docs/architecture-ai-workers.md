# Architecture — AI workers (Grok Bot, not in-app LLM keys)

Deepfold is the **newsroom control panel**: journalist UI, editorial state machine, audit, and CMS adapters. It is not an LLM application. The v1 path of record does **not** hold OpenAI, xAI, or other model API keys for drafting, featured images, localisation, or social stubs.

Credits and usage live on **Grok Bot**. Deepfold stores results and the audit trail.

## What Deepfold owns

```
Journalist (apps/desk)
        │
        ▼
FastAPI (apps/api)
        │
        ├── Postgres   Draft, DraftVersion, Outlet, OutletPackage,
        │              PublishTarget, Decision, MediaAsset, SocialPost,
        │              Job, AuditEvent
        ├── Redis      reserved for locks / fan-out (optional; jobs work on Postgres)
        └── WordPress  Application Password, draft-only by default
```

Pipeline stages stay Pitch → Drafting → Checking → Publication → Social. Pitch is an abstract. **Go** commissions work; it does not call a model from the API process.

## Job queue

Jobs are rows on `jobs`. Kinds:

| Kind | When | Worker result written back as |
| --- | --- | --- |
| `draft_article` | **Go** | `Draft.spine_body` + `DraftVersion` |
| `featured_image` | **Go** | `MediaAsset` (Saatchi-style plate; never a fake incident photo) |
| `localize_outlets` | **Go** | `PublishTarget.local_graf` per selected title |
| `social_stubs` | Send to social | `SocialPost` bodies |

Statuses: `queued` → `claimed` → `completed` | `failed` | `cancelled`.

Open jobs are cancelled on **No-go** and **Back to pitch**.

### Stub HTTP (real, tested)

Grok Bot (cloud agent, routine, or skill) talks only to these endpoints. No model keys in Deepfold.

- `GET /jobs?status=queued&kind=draft_article`
- `POST /jobs/{id}/claim` `{ "worker": "grok-bot" }`
- `POST /jobs/{id}/complete` `{ "worker": "grok-bot", "spine_body": "..." }` (fields depend on kind)
- `GET /jobs/{id}`

Claim is exclusive (`409` if not `queued`). Complete from `queued` or `claimed` is allowed so a single worker step can finish a demo job. Failed completes send `error`.

The API applies the payload, writes `DraftVersion` / `MediaAsset` / grafs / social stubs, and an `AuditEvent`. That is the learning loop plus the CMS-bound copy. Deepfold never bills a token.

## Who spends the credits

```
Desk  --Go-->  Job queued
                  │
                  ▼
         Grok Bot claims the job
         (webhook, scheduled routine, or skill)
                  │
                  ▼
         Runs a skill with the bot's usage credits
                  │
                  ▼
         POST /jobs/{id}/complete
                  │
                  ▼
         Desk shows the article / plate / grafs
```

If the bot is not running, Drafting shows **Draft generating…** and a skeleton until a `draft_article` job completes and a spine exists. The Midlands demo pitch already has a seeded article: **Go** enqueues the three commission jobs and **completes them in-process** from that seed so the investor desk is not empty. That is a demo fulfillment, not an in-app LLM call. A pitch with an empty spine stays queued for a real worker.

## What must not be added

- `OPENAI_API_KEY`, `XAI_API_KEY`, or any vendor key on the API/desk for drafting or images
- Calling a chat-completions API from FastAPI or Next.js on the v1 path
- Auto-publish of `single_source`, `caution`, or `defamation_sensitive` copy
- Treating Conservative Post as the product name — it is one **title** under the publisher (`PUBLISHER_NAME`, default Newsworld)

Image policy is unchanged: editorial stills, not reconstructed incidents.

## Titles at thousands-scale

The outlet registry is the growth path (every UK town as a title, WordPress adapter per site). The desk must not render a checklist of the registry.

- `GET /outlets?q=&county=&region=&limit=` — typeahead, hard cap 50
- `GET /outlets/suggest?draft_id=` — small set from pitch `geography`
- `GET /outlets/packages` — e.g. Worcestershire — Redditch / Bromsgrove / Worcester
- Selected titles are chips; **Add title…** opens search

Packages are how a desk of thousands stays operable. Regional desks can come later as routing, not a second product.
