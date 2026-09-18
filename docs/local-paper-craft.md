# Local paper craft

Standing craft rules for Deepfold `draft_article` jobs when the primary title is a **local / Newsworld paper** — Redditch Standard, Bromsgrove Standard, Worcester Observer, and other town desks. The versioned prompt a worker must execute is:

[`apps/api/app/prompts/draft_article_local_v1.md`](../apps/api/app/prompts/draft_article_local_v1.md) — `brief_version`: **`draft_article_local_v1`**

Shared craft from Claire’s Sep 2026 house-style review. **The Conservative Post political line does not apply.** Keep each title’s local, independent news voice.

Grok Bot drafts; Deepfold **does not** hold vendor LLM keys. See [`architecture-ai-workers.md`](architecture-ai-workers.md). Conservative Post uses [`conservative-post-house-style.md`](conservative-post-house-style.md) instead.

When a journalist presses **Go** (or **Request rewrite**), the API enqueues `draft_article` with `brief_version`, `brief_path`, `base_brief` (this prompt), plus story context: `headline`, `slug`, `standfirst` / `abstract`, `spine` / `spine_body`, `geography`. The worker claims the job, writes local craft, and completes with `headline`, `standfirst`, and `spine_body`.

## Length (Mike, 18 Sep 2026)

Normal local news about **500–800 words**. Use good judgment: enough for a proper paper piece — not thin, not padded.

## Routing

- **Conservative Post / patriotic national** → [`conservative-post-house-style.md`](conservative-post-house-style.md) / `draft_article_conservative_post_v1`.
- **Redditch, Bromsgrove, Worcester, Nuneaton, Hinckley, and any other local** → this brief.
- **Unknown or no selected title** → this brief (local craft is the default).
