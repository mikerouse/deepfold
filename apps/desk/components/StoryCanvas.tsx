"use client";

import { houseStyleNote } from "../lib/story";
import type { DraftDetail, MediaAsset } from "../lib/types";

type Props = {
  draft: DraftDetail;
  stage: string;
  headline: string;
  standfirst: string;
  spine: string;
  generating: boolean;
  notice: string | null;
  featured?: MediaAsset;
  imageQueued: boolean;
  imageWorking: boolean;
  selectedTitles: string;
  onHeadline: (value: string) => void;
  onStandfirst: (value: string) => void;
  onSpine: (value: string) => void;
};

export default function StoryCanvas({
  draft,
  stage,
  headline,
  standfirst,
  spine,
  generating,
  notice,
  featured,
  imageQueued,
  imageWorking,
  selectedTitles,
  onHeadline,
  onStandfirst,
  onSpine,
}: Props) {
  const storyKicker = draft.categories[0];
  const houseStyle = houseStyleNote(draft.jobs);
  const sensitive =
    draft.verification_status !== "verified" && stage !== "pitch"
      ? draft.verification_status.replaceAll("_", " ")
      : null;
  const showsBody = stage === "drafting" || stage === "checking" || stage === "publication";
  const showsImage = stage === "drafting" || stage === "checking" || stage === "publication";
  const status = draft.worker_labels?.[0];

  return (
    <div className="well-inner document">
      {storyKicker || sensitive ? (
        <p className="kicker-story">
          {storyKicker}
          {sensitive ? (
            <>
              {storyKicker ? " · " : null}
              <span className="sensitive">{sensitive}</span>
            </>
          ) : null}
        </p>
      ) : null}
      {stage === "pitch" ? (
        <>
          <h2 className="headline-display">{headline}</h2>
          <p className="abstract-display">{standfirst}</p>
        </>
      ) : (
        <>
          <textarea
            className="headline-input"
            value={headline}
            onChange={(e) => onHeadline(e.target.value)}
            rows={2}
            aria-label="Headline"
          />
          <textarea
            className="standfirst-input"
            value={standfirst}
            onChange={(e) => onStandfirst(e.target.value)}
            rows={2}
            aria-label="Standfirst"
          />
        </>
      )}
      {draft.parked ? <p className="byline">Left on the spike</p> : null}
      {notice ? <p className="quiet-banner">{notice}</p> : null}
      {houseStyle ? <p className="quiet-banner">{houseStyle}</p> : null}
      {showsBody && draft.tags.length > 0 && !generating ? <p className="tag-line">{draft.tags.join(" · ")}</p> : null}

      {showsImage && featured?.url ? (
        <figure className="well-plate">
          <div className="plate">
            <img src={featured.url} alt={featured.alt_text || featured.placeholder_label} />
          </div>
          <figcaption className="caption">
            {featured.caption} · {featured.credit}
            {featured.documentary_incident ? " · Documentary (must be real)" : ""}
          </figcaption>
        </figure>
      ) : null}
      {showsImage && featured && !featured.url ? (
        <figure className="well-plate">
          <div className="plate">
            <span className="plate-label">{featured.placeholder_label}</span>
          </div>
          <figcaption className="caption">
            {featured.caption} · {featured.credit}
          </figcaption>
        </figure>
      ) : null}
      {showsImage && !featured && (imageQueued || imageWorking) ? (
        <figure className="well-plate">
          <div className="plate plate-queued" aria-live="polite">
            {imageWorking ? "Generating image…" : "Queued for image"}
          </div>
          <figcaption className="caption">Grok Bot holds the featured-image brief. This desk only stores the plate.</figcaption>
        </figure>
      ) : null}

      {generating ? (
        <div className="generating" aria-live="polite">
          <p className="quiet-banner">
            {status === "Drafting…"
              ? "Drafting… Grok Bot has claimed the job. Credits sit on that side; this desk only stores the result."
              : "Queued for drafting. Grok Bot will claim the job. Credits sit on that side; this desk only stores the result."}
          </p>
          <div className="skeleton-line" />
          <div className="skeleton-line" />
          <div className="skeleton-line short" />
          <div className="skeleton-line" />
          <div className="skeleton-line short" />
        </div>
      ) : null}

      {showsBody && !generating ? (
        <textarea
          className="body-input"
          value={spine}
          onChange={(e) => onSpine(e.target.value)}
          rows={16}
          aria-label="Article body"
        />
      ) : null}

      {stage === "pitch" ? (
        <>
          <h2 className="section-label">Suggested titles</h2>
          <p className="outlet-line">{selectedTitles || "None selected"}</p>
        </>
      ) : null}
    </div>
  );
}
