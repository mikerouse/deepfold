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
| `draft_article` | **Go** / rewrite | `Draft.spine_body` + `DraftVersion` (standing house-style brief embedded) |
| `featured_image` | **Go** | `MediaAsset` (Saatchi-style plate; never a fake incident photo) |
| `localize_outlets` | **Go** | `PublishTarget.local_graf` per selected title |
| `social_stubs` | Send to social | `SocialPost` bodies |

Statuses: `queued` → `claimed` → `completed` | `failed` | `cancelled`.

Open jobs are cancelled on **No-go** and **Back to pitch**.

### Draft article (`draft_article`)

Standing house style (do not invent a second prompt): Claire’s Sep 2026 Conservative Post master editorial, and shared local craft without CP politics.

| Brief | When | Prompt |
| --- | --- | --- |
| `draft_article_conservative_post_v1` | Primary title is Conservative Post / patriotic national | [`docs/conservative-post-house-style.md`](conservative-post-house-style.md) / [`apps/api/app/prompts/draft_article_conservative_post_v1.md`](../apps/api/app/prompts/draft_article_conservative_post_v1.md) |
| `draft_article_local_v1` | Redditch Standard, Bromsgrove Standard, Worcester Observer, other locals, or unknown | [`docs/local-paper-craft.md`](local-paper-craft.md) / [`apps/api/app/prompts/draft_article_local_v1.md`](../apps/api/app/prompts/draft_article_local_v1.md) |

**Routing.** If Conservative Post (seeded slug `conservative-post`, or a National-region patriotic title) is among the selected titles, the spine uses the CP brief even when local titles are also selected — locals still get grafs from `localize_outlets`. Otherwise the first selected outlet is the primary. If nothing is selected or the title is unknown, **default to local craft** (no CP politics).

On **Go** and **Request rewrite** the API enqueues this kind with a complete payload so a Grok Bot skill can draft without a second style guide:

| Field | Meaning |
| --- | --- |
| `brief_version` | `draft_article_conservative_post_v1` or `draft_article_local_v1` |
| `brief_path` | repo path of the prompt file |
| `base_brief` | full text of that file |
| `house_style_label` | `Conservative Post v1` or `Local craft v1` (desk may show this) |
| `headline`, `slug`, `standfirst`, `abstract` | story context (`abstract` is the pitch standfirst) |
| `spine` / `spine_body` | existing copy if any (rewrites start from this) |
| `geography` | pitch regions / counties / towns |
| `source_links`, `categories`, `tags`, `verification_status` | commission extras |
| `primary_outlet` | `{name, slug, region}` of the title the spine is for, or `null` |

The worker follows `base_brief` as the complete house style, writes **one article** outside Deepfold, and completes:

```http
POST /jobs/{id}/complete
```

```json
{
  "worker": "grok-bot",
  "headline": "Punchy factual headline, 8–14 words",
  "standfirst": "The news in one or two sentences",
  "spine_body": "Full article in British English"
}
```

Deepfold stores the spine and a `DraftVersion`. Workers must follow the embedded house style. Do not add vendor LLM keys to the API. Fail the job rather than invent facts.

The desk shows **Queued for drafting** until a worker claims the article job (**Drafting…**), then the spine. A quiet **House style: Conservative Post v1** / **Local craft v1** note may appear while that job is open.

### Featured image (`featured_image`)

Standing recipe (do not invent policy): [`docs/featured-image-brief.md`](featured-image-brief.md) and the versioned prompt [`apps/api/app/prompts/featured_image_v1.md`](../apps/api/app/prompts/featured_image_v1.md) (`brief_version`: `featured_image_v1`).

On **Go** the API enqueues this kind with a complete payload so a Grok Bot skill can run without a second style guide:

| Field | Meaning |
| --- | --- |
| `brief_version` | `featured_image_v1` |
| `brief_path` | repo path of the prompt file |
| `base_brief` | full text of that file |
| `story_specific_scene` | 1–3 sentences from headline / abstract / spine / geography (heuristic stub) |
| `geography` | pitch regions / counties / towns |
| `documentary_safe` | always `true` |
| `headline`, `slug`, `standfirst` | story context |

The worker concatenates `base_brief` + `Story-specific scene: {story_specific_scene}`, generates **one landscape still** outside Deepfold, and completes:

```http
POST /jobs/{id}/complete
```

```json
{
  "worker": "grok-bot",
  "url": "https://…",
  "alt_text": "What the still actually shows",
  "caption": "Generic editorial still; AI-generated illustration, not a photograph of the event.",
  "prompt_version": "featured_image_v1",
  "placeholder_label": "County civic building — dusk exterior",
  "credit": "Desk stock / editorial illustration"
}
```

Deepfold stores a `MediaAsset` (`role=featured`) on the draft: `url`, alt, caption, `prompt_version`. AI plates are never `documentary_incident`. Fail the job rather than file a fake crime / fire / crash / named-person photo.

The Midlands demo pitch already has a seeded plate URL and article spine in the database. **Go does not complete those jobs in-process** unless `DEMO_INSTANT_FULFILL=true`. Default (investor path): enqueue `draft_article`, `featured_image`, and `localize_outlets` and leave them `queued` for Grok Bot. The desk shows **Queued for drafting** until a worker claims the article job (**Drafting…**), then the spine. Same for the plate: **Queued for image** / **Generating image…** / still shown when a `MediaAsset` exists.

`DEMO_INSTANT_FULFILL` is a demo shortcut, not an in-app image-model or LLM call. Leave it off unless you need the old “body appears on Go” behaviour.

### Stub HTTP (real, tested)

Grok Bot (cloud agent, routine, or skill) talks only to these endpoints. No model keys in Deepfold.

- `GET /jobs?status=queued&kind=draft_article`
- `GET /jobs?status=queued&kind=featured_image`
- `POST /jobs/{id}/claim` `{ "worker": "grok-bot" }`
- `POST /jobs/{id}/complete` `{ "worker": "grok-bot", "spine_body": "..." }` (fields depend on kind; `draft_article` must follow the embedded `base_brief` house style; featured image: `url`, `alt_text`, `caption`, `prompt_version`)
- `GET /jobs/{id}`
- `POST /jobs/demo-tick` — optional localhost stand-in, only when `DEMO_GROK_WORKER` is on

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

If the bot is not running, Drafting shows **Queued for drafting** (job `queued`) then **Drafting…** (job `claimed`) and a skeleton until a `draft_article` job completes and a spine is visible. A pitch with an empty spine stays queued for a real worker. Seeded copy in the database is not revealed until that job completes (unless `DEMO_INSTANT_FULFILL=true`).

### Optional localhost demo worker

Set `DEMO_GROK_WORKER=1` (or `true`) to simulate Grok Bot **without vendor API keys**. A background loop, or `POST /jobs/demo-tick`, claims the oldest queued job as worker `demo-grok-bot`, waits ~3s (`DEMO_GROK_WORKER_DELAY_SECONDS`), and completes it with seed/stub content. The desk can poll and show Queued → Drafting → body. This is labelled in `/settings` (`demo_grok_worker`) and on the story toolbar. It is **not** an LLM call.

Default for both flags is **off**. Grok Bot remains the real credit spender.

## What must not be added

- `OPENAI_API_KEY`, `XAI_API_KEY`, or any vendor key on the API/desk for drafting or images
- Calling a chat-completions API from FastAPI or Next.js on the v1 path
- Auto-publish of `single_source`, `caution`, or `defamation_sensitive` copy
- Treating Conservative Post as the product name — it is one **title** under the publisher (`PUBLISHER_NAME`, default Newsworld)

Image policy is unchanged: editorial stills, not reconstructed incidents. The standing recipe is [`docs/featured-image-brief.md`](featured-image-brief.md) / `featured_image_v1`. Drafting house style is [`conservative-post-house-style.md`](conservative-post-house-style.md) or [`local-paper-craft.md`](local-paper-craft.md) as routed on the job.

## Titles at thousands-scale

The outlet registry is the growth path (every UK town as a title, WordPress adapter per site). The desk must not render a checklist of the registry.

- `GET /outlets?q=&county=&region=&limit=` — typeahead, hard cap 50
- `GET /outlets/suggest?draft_id=` — small set from pitch `geography`
- `GET /outlets/packages` — e.g. Worcestershire — Redditch / Bromsgrove / Worcester
- Selected titles are chips; **Add title…** opens search

Packages are how a desk of thousands stays operable. Regional desks can come later as routing, not a second product.
