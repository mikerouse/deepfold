"use client";

import type { DraftDetail, Job } from "../lib/types";

function mark(value: string, extra = "") {
  return <span className={`mark ${extra}`.trim()}>{value.replaceAll("_", " ")}</span>;
}

function jobLine(job: Job) {
  const short = job.id.slice(0, 8);
  const label =
    job.kind === "draft_article" && typeof job.payload?.house_style_label === "string"
      ? job.payload.house_style_label.trim()
      : "";
  const style = label ? ` · ${label}` : "";
  return `${job.kind.replaceAll("_", " ")} · ${job.status} · ${short}${style}`;
}

type Props = {
  draft: DraftDetail;
  stage: string;
};

export default function InfoRail({ draft, stage }: Props) {
  const geo = draft.geography || {};
  const places = [
    ...(geo.regions || []),
    ...(geo.counties || []),
    ...(geo.towns || []),
  ];
  const jobs = draft.jobs || [];

  return (
    <aside className="rail" aria-label="Story information">
      <section>
        <h2>Sources</h2>
        {draft.source_links.length === 0 ? <p className="notes">None filed.</p> : null}
        <ul className="sources">
          {draft.source_links.map((source) => (
            <li key={source.url}>
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.label}
              </a>
              {source.note ? ` — ${source.note}` : ""}
            </li>
          ))}
        </ul>
      </section>

      {stage !== "pitch" ? (
        <section>
          <h2>Verification</h2>
          {mark(draft.verification_status, draft.verification_status)}
          <p className="notes">Single-source, caution and defamation-sensitive copy can never auto-publish.</p>
        </section>
      ) : null}

      {stage === "checking" || stage === "drafting" ? (
        <section>
          <h2>Confidence</h2>
          <div className="meter" aria-hidden="true">
            <span style={{ width: `${Math.round(draft.confidence.score * 100)}%` }} />
          </div>
          <p className="notes">
            {Math.round(draft.confidence.score * 100)} · auto-draft{" "}
            {draft.confidence.auto_draft_eligible ? "yes" : "no"} · auto-publish{" "}
            {draft.confidence.auto_publish_eligible ? "yes" : "no"}
          </p>
        </section>
      ) : null}

      <section>
        <h2>Geography</h2>
        {places.length === 0 ? <p className="notes">No geography on this pitch.</p> : null}
        <p className="notes">{places.join(" · ")}</p>
      </section>

      {jobs.length > 0 ? (
        <section>
          <h2>Jobs</h2>
          {jobs.map((job) => (
            <p className="notes job-id" key={job.id} title={job.id}>
              {jobLine(job)}
              {job.worker ? ` · ${job.worker}` : ""}
            </p>
          ))}
        </section>
      ) : null}

      {draft.decisions.length > 0 ? (
        <section>
          <h2>Audit</h2>
          {draft.decisions.slice(0, 8).map((decision) => (
            <p className="notes" key={decision.id}>
              {decision.action.replaceAll("_", " ")} · {decision.actor}
              {decision.reason ? ` · ${decision.reason}` : ""}
            </p>
          ))}
        </section>
      ) : (
        <section>
          <h2>Audit</h2>
          <p className="notes">No decisions yet.</p>
        </section>
      )}
    </aside>
  );
}
