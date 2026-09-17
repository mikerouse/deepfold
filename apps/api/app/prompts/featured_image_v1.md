# Featured image brief — `featured_image_v1`

Standing recipe for Deepfold `featured_image` jobs. Grok Bot executes this file; do not invent policy. Deepfold does not call an image model and does not hold vendor API keys. The worker spends the credits, then `POST /jobs/{id}/complete` with the result.

Version: **featured_image_v1**
Path: `apps/api/app/prompts/featured_image_v1.md`

---

## 1. Photography recipe (the plate)

Make **one** landscape featured still for a UK local-news article. Direct it as premium British **editorial and advertising photography** — **Saatchi rather than AI**.

- **Natural light only.** Overcast British daylight, late-afternoon sun, or civic dusk. No studio strobes, no beauty-dish skin, no neon.
- **Authentic UK.** Brick, limestone, wet tarmac, council stock, a high street, a shire civic facade, a dual carriageway, a suburban close. Not California, not a generic “city”, not a transatlantic suburb.
- **Landscape (16:9 or 3:2).** A magazine opener, not a portrait headshot, not a square social crop.
- **No text, no logos, no watermarks, no mastheads, no road signs with readable words, no newspaper nameplates.**
- **One strong idea.** One subject, one mood, one place-type. Do not illustrate every fact in the headline.
- **Avoid AI chrome.** No plastic skin, extra fingers, melted masonry, oversharpened HDR, cinematic teal-and-orange, lens-flare soup, stock-photo grins, floating type, or “unreal engine” gloss. Grain, atmosphere, and restraint beat polish.

The plate is a **mood still of civic fabric**, the sort of picture a good art director would buy from a photographer — not a reconstruction of news.

---

## 2. Append the story-specific scene

After the recipe above, always append exactly:

```
Story-specific scene: {story_specific_scene}
```

`story_specific_scene` is 1–3 sentences on the job payload. It names a **generic** place-type and light, not the incident. Do not expand it into a documentary reconstruction. Do not add named people, a crime scene, a fire, or a specific real address.

---

## 3. Documentary safety (non-negotiable)

Never fabricate a photograph of a **specific real incident, crime, fire, crash, arrest, or identifiable person or private place** as if it were documentary evidence.

| Unsafe (do not generate) | Safe (do this instead) |
| --- | --- |
| The burgled house, the estate, CCTV, police tape, a suspect | A generic suburban street in daylight; no incident |
| The crash, the queue of a named smash, wreckage | A generic UK carriageway; empty of incident |
| The fire, flames on a named building | Civic fabric or a skyline; no blaze |
| The cabinet member, the builder, the meeting in progress | An empty chamber, a civic exterior, lights on, nobody there |
| A named school, hospital ward, or private home as “the scene” | A generic civic or street still that could be anywhere in that county |

If the story is crime, accident, fire, or allegation: **generic editorial plate + honest caption/alt**. The picture must not be usable as fake evidence.

`documentary_safe` on the job is **true**. Keep it true. Do not set `documentary_incident` on an AI plate.

---

## 4. Output contract (worker → Deepfold)

Generate the still **outside** Deepfold. Then complete the job. Deepfold stores a `MediaAsset` on the draft; it does not bill a token.

`POST /jobs/{id}/complete`

```json
{
  "worker": "grok-bot",
  "url": "https://… or a durable image URL",
  "alt_text": "Plain description of what the still actually shows",
  "caption": "Honest caption. If AI-generated, say it is a generic/editorial illustration, not a photograph of the event.",
  "prompt_version": "featured_image_v1",
  "placeholder_label": "Short plate title, e.g. County civic building — dusk exterior",
  "credit": "Desk stock / editorial illustration"
}
```

| Field | Required | Rule |
| --- | --- | --- |
| `url` (or `image_url`) | yes | Public URL of the landscape still (bytes hosted by the worker, not by Deepfold). |
| `alt_text` | yes | Describe the **picture**, not the news. No “photo of the burglary”. |
| `caption` | yes | If the still is AI-generated, the caption **must** say it is generic/editorial, not documentary. |
| `prompt_version` | yes | `featured_image_v1` (this file). |
| `placeholder_label` | optional | Short label for desks that have no bitmap yet. |
| `credit` | optional | Default `Desk stock / editorial illustration`. |
| `error` | on failure | If you cannot make a safe plate, fail the job; do not post a fake incident photo. |

Do not POST model API keys. Do not ask Deepfold to call an image model.

---

## Payload the desk already put on the job

Read `GET /jobs/{id}` (or the claim response). For `kind=featured_image` you will find:

- `brief_version` — `featured_image_v1`
- `base_brief` — this recipe
- `story_specific_scene` — 1–3 sentences to append
- `geography` — regions / counties / towns from the pitch
- `documentary_safe` — `true`
- `headline`, `slug`, `standfirst`

Concatenate `base_brief` + a blank line + `Story-specific scene: ` + `story_specific_scene`. That is the full prompt. Do not add a second style guide.
