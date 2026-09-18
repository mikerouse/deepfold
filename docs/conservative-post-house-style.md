# Conservative Post house style

Standing editorial brief for Deepfold `draft_article` jobs when the primary title is **Conservative Post** (patriotic national). **Do not dilute.** The versioned prompt a worker must execute is:

[`apps/api/app/prompts/draft_article_conservative_post_v1.md`](../apps/api/app/prompts/draft_article_conservative_post_v1.md) — `brief_version`: **`draft_article_conservative_post_v1`**

Claire’s Sep 2026 master prompt. Grok Bot (or another worker) drafts the article. Deepfold **does not** hold OpenAI/xAI keys and **does not** call a chat model from FastAPI or the desk. See [`architecture-ai-workers.md`](architecture-ai-workers.md).

Local titles (Redditch Standard, Bromsgrove Standard, Worcester Observer, and other Newsworld locals) use [`local-paper-craft.md`](local-paper-craft.md) — shared craft, **without** the CP political line.

When a journalist presses **Go** (or **Request rewrite**), the API enqueues `draft_article` with `brief_version`, `brief_path`, `base_brief` (this prompt), plus story context: `headline`, `slug`, `standfirst` / `abstract`, `spine` / `spine_body`, `geography`. The worker claims the job, writes to this house style, and completes with `headline`, `standfirst`, and `spine_body`. Deepfold stores the spine and a version.

## Routing

- **Conservative Post / patriotic national** (seeded slug `conservative-post`, or a National-region patriotic title) → this brief, even if local titles are also selected (the spine is the national piece; locals get grafs from `localize_outlets`).
- **Locals and unknown titles** → [`local-paper-craft.md`](local-paper-craft.md) / `draft_article_local_v1`. If no outlet is selected, default to local craft.
