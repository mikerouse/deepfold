# Featured image brief (Saatchi plates)

Standing newsroom recipe for Deepfold `featured_image` jobs. **Do not invent policy.** The versioned prompt a worker must execute is:

[`apps/api/app/prompts/featured_image_v1.md`](../apps/api/app/prompts/featured_image_v1.md) — `brief_version`: **`featured_image_v1`**

Grok Bot (or another worker) generates the still. Deepfold **does not** hold OpenAI/xAI keys and **does not** call an image model from FastAPI or the desk. See [`architecture-ai-workers.md`](architecture-ai-workers.md).

When a journalist presses **Go**, the API enqueues `featured_image` with `brief_version`, `base_brief` (this recipe), `story_specific_scene`, `geography`, and `documentary_safe: true`. The worker claims the job, makes one landscape plate, and completes with `url`, `alt_text`, `caption`, and `prompt_version`. Deepfold stores a `MediaAsset` on the draft. Drafting and Checking show the plate; if the job is still queued they show **Image job queued…**

---

## 1. Photography recipe

Make **one** landscape featured still for a UK local-news article. Direct it as premium British **editorial and advertising photography** — **Saatchi rather than AI**.

- **Natural light only.** Overcast British daylight, late-afternoon sun, or civic dusk. No studio strobes, no beauty-dish skin, no neon.
- **Authentic UK.** Brick, limestone, wet tarmac, council stock, a high street, a shire civic facade, a dual carriageway, a suburban close. Not California, not a generic “city”, not a transatlantic suburb.
- **Landscape (16:9 or 3:2).** A magazine opener, not a portrait headshot, not a square social crop.
- **No text, no logos, no watermarks, no mastheads, no road signs with readable words, no newspaper nameplates.**
- **One strong idea.** One subject, one mood, one place-type. Do not illustrate every fact in the headline.
- **Avoid AI chrome.** No plastic skin, extra fingers, melted masonry, oversharpened HDR, cinematic teal-and-orange, lens-flare soup, stock-photo grins, floating type, or “unreal engine” gloss. Grain, atmosphere, and restraint beat polish.

The plate is a **mood still of civic fabric**, the sort of picture a good art director would buy from a photographer — not a reconstruction of news.

## 2. Append the story-specific scene

After the recipe, always append:

```
Story-specific scene: {story_specific_scene}
```

One to three sentences. Generic place-type and light. Never the incident, never a named person, never a specific real private address.

Deepfold fills `story_specific_scene` from headline / abstract / spine / geography (heuristic stub until a richer writer exists). The worker must not “improve” it into a documentary reconstruction.

## 3. Documentary safety

Never fabricate a photograph of a **specific real incident, crime, fire, crash, arrest, or identifiable person or private place** as if it were documentary evidence.

Use a **generic editorial plate**. Caption and alt must be honest: if the still is AI-generated, say so, and say it is not a photograph of the event.

`documentary_incident` stays **false** on worker plates. A real staff or agency photograph of an incident is a different path, captioned as such, and is not this job.

## 4. Output contract

The worker produces **image bytes** (hosted wherever the bot stores media) and POSTs a **URL** plus metadata:

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

Deepfold writes a `MediaAsset` (`role=featured`) linked to the draft. Fail the job rather than file a fake incident photo.
