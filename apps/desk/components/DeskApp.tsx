"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBase, getDraft, getPipeline, getSettings, listDrafts, recordDecision } from "../lib/api";
import type {
  DeskSettings,
  DraftDetail,
  DraftListItem,
  PipelineStage,
  SocialPost,
} from "../lib/types";

type ReasonMode = "reject" | "request_changes" | "no_go" | null;

const STAGE_AFTER_ACTION: Record<string, string> = {
  go: "drafting",
  send_to_checking: "checking",
  approve_create_cms_drafts: "publication",
  advance_to_social: "social",
  return_to_pitch: "pitch",
  no_go: "pitch",
  leave: "pitch",
  unleave: "pitch",
  hold: "checking",
  request_changes: "checking",
};

function pill(value: string, extra = "") {
  return <span className={`pill ${value} ${extra}`.trim()}>{value.replaceAll("_", " ")}</span>;
}

function socialCopy(post: SocialPost) {
  return post.edited_body || post.body;
}

function statusLabel(item: DraftListItem) {
  if (item.parked) return "Left";
  if (item.status === "changes_requested") return "Changes";
  if (item.status === "held") return "Held";
  if (item.status === "approved_cms_draft") return "CMS draft";
  if (item.pipeline_stage) return item.pipeline_stage;
  return item.status;
}

export default function DeskApp({ initialId }: { initialId?: string }) {
  const [stage, setStage] = useState("pitch");
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [queue, setQueue] = useState<DraftListItem[]>([]);
  const [draft, setDraft] = useState<DraftDetail | null>(null);
  const [settings, setSettings] = useState<DeskSettings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [headline, setHeadline] = useState("");
  const [standfirst, setStandfirst] = useState("");
  const [spine, setSpine] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [grafs, setGrafs] = useState<Record<string, string>>({});
  const [socialEdits, setSocialEdits] = useState<Record<string, string>>({});
  const [reasonMode, setReasonMode] = useState<ReasonMode>(null);
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  const currentStage = stages.find((s) => s.id === stage);

  async function refresh(nextStage = stage, selectId?: string) {
    const [rows, pipe] = await Promise.all([listDrafts(nextStage), getPipeline()]);
    setQueue(rows);
    setStages(pipe.stages);
    setStage(nextStage);
    const preferred = selectId || (draft && nextStage === stage ? draft.id : undefined);
    const id = (preferred && rows.some((r) => r.id === preferred) && preferred) || rows[0]?.id || initialId;
    if (id && rows.some((r) => r.id === id)) {
      await openDraft(id);
    } else {
      setDraft(null);
    }
  }

  async function openDraft(id: string) {
    const detail = await getDraft(id);
    setDraft(detail);
    setHeadline(detail.headline);
    setStandfirst(detail.standfirst);
    setSpine(detail.spine_body);
    setSelected(Object.fromEntries(detail.targets.map((t) => [t.outlet.id, t.selected])));
    setGrafs(Object.fromEntries(detail.targets.map((t) => [t.outlet.id, t.local_graf])));
    setSocialEdits(Object.fromEntries(detail.social_posts.map((s) => [s.id, socialCopy(s)])));
  }

  useEffect(() => {
    (async () => {
      try {
        const deskSettings = await getSettings();
        setSettings(deskSettings);
        await refresh("pitch", initialId);
      } catch (err) {
        setError(
          `Cannot reach the API at ${apiBase()}. Start Postgres/API with docker compose, or the SQLite fallback in the README. ${(err as Error).message}`,
        );
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedIds = useMemo(
    () => Object.entries(selected).filter(([, on]) => on).map(([id]) => id),
    [selected],
  );

  const showsBody = stage === "drafting" || stage === "checking" || stage === "publication";
  const showsOutlets = stage === "drafting" || stage === "checking" || stage === "publication";
  const showsSocial = stage === "social";
  const showsImage = stage === "drafting" || stage === "checking";

  async function run(action: string, extra?: Record<string, unknown>) {
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        action,
        headline,
        standfirst,
        selected_outlet_ids: selectedIds,
        local_grafs: grafs,
        ...extra,
      };
      if (showsBody) payload.spine_body = spine;
      const next = await recordDecision(draft.id, payload as Parameters<typeof recordDecision>[1]);
      const followStage = STAGE_AFTER_ACTION[action] || next.pipeline_stage || stage;
      if (action === "go") setNotice("Commissioned. The article, image plate, tags and outlets are now in Drafting.");
      if (action === "leave") setNotice("Left on the spike. This is not a No-go — unpark whenever you want it back.");
      if (action === "unleave") setNotice("Back on the spike.");
      if (action === "no_go") setNotice("No-go. The pitch is archived with your reason.");
      await refresh(followStage, action === "no_go" ? undefined : next.id);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function submitReason() {
    if (!reasonMode) return;
    if (!reason.trim()) {
      setError("A reason is required.");
      return;
    }
    const action = reasonMode;
    setReasonMode(null);
    const text = reason;
    setReason("");
    void run(action, { reason: text });
  }

  const reasonCopy = {
    no_go: {
      title: "No-go this pitch?",
      body: "No-go kills the idea and archives it with your reason. Leave parks it on the spike instead — that is not a kill.",
      confirm: "No-go",
    },
    reject: {
      title: "Reject this draft",
      body: "A reason is required and is stored on the decision + audit log.",
      confirm: "Reject",
    },
    request_changes: {
      title: "Request changes",
      body: "A reason is required and is stored on the decision + audit log.",
      confirm: "Request changes",
    },
  } as const;

  return (
    <div className={`desk stage-${stage}`}>
      <header className="mast">
        <div className="mast-brand">
          <div className="kicker">Conservative Post · UK local news</div>
          <h1>Deepfold Approvals Desk</h1>
          <p className="mast-line">Editorial pipeline — pitch first, draft only after Go.</p>
        </div>
        <div className="mast-meta">
          <div>
            Actor
            <strong>{settings?.default_actor || "journalist"}</strong>
          </div>
          <div>
            Publish
            <strong>{settings?.approve_and_publish_enabled ? "ON" : "off"}</strong>
          </div>
        </div>
      </header>

      <nav className="stages" aria-label="Pipeline stages">
        {stages.map((item) => (
          <button
            key={item.id}
            className={`stage ${stage === item.id ? "active" : ""}`}
            onClick={() => {
              setError(null);
              setNotice(null);
              void refresh(item.id);
            }}
          >
            <span className="stage-label">{item.label}</span>
            <span className="stage-count">{item.count}</span>
            <span className="stage-hint">{item.hint}</span>
          </button>
        ))}
      </nav>

      <div className="flags">
        <span className={settings?.kill_switch ? "hot" : ""}>
          Kill switch {settings?.kill_switch ? "ON" : "off"}
        </span>
        <span>Approve &amp; publish {settings?.approve_and_publish_enabled ? "ON" : "OFF (default)"}</span>
        <span>WP {settings?.wp_live ? "live" : "draft-only / dry-run"}</span>
        <span>Never auto-publish single-source, caution, or defamation-sensitive</span>
      </div>

      {error ? <div className="error" style={{ gridColumn: "1 / -1" }}>{error}</div> : null}

      <aside className="queue">
        <h2>{currentStage?.label || "Spike"}</h2>
        {queue.length === 0 ? (
          <p className="empty">{currentStage?.empty || "Nothing in this stage."}</p>
        ) : null}
        {queue.map((item) => (
          <button
            key={item.id}
            className={`q-item ${draft?.id === item.id ? "active" : ""}`}
            onClick={() => {
              setNotice(null);
              void openDraft(item.id);
            }}
          >
            {item.image_label ? (
              <div className="q-thumb" title={item.image_label}>
                {item.image_label}
              </div>
            ) : (
              <div className="q-thumb pitch">{item.parked ? "Left" : "Pitch"}</div>
            )}
            <div>
              <div className="town">{item.suggested_outlet_names[0] || item.categories[0]}</div>
              <h3>{item.headline}</h3>
              <div className="q-meta">
                {pill(statusLabel(item), item.parked ? "left" : item.status)}
                {stage !== "pitch" ? pill(item.verification_status) : null}
                {item.suggested_outlet_names.slice(0, 3).map((name) => (
                  <span className="chip" key={name}>{name}</span>
                ))}
              </div>
            </div>
          </button>
        ))}
      </aside>

      <main className="well">
        {!draft ? (
          <div className="empty-well">
            <h2>{currentStage?.label || "Pipeline"}</h2>
            <p>{currentStage?.empty || "Select a story."}</p>
          </div>
        ) : (
          <>
            <div className="byline">
              {stage === "pitch" ? "Pitch · abstract only" : draft.byline} · {draft.slug}
              {draft.parked ? " · Left on the spike" : ""}
            </div>
            {stage === "pitch" ? (
              <>
                <h2 className="headline-display">{headline}</h2>
                <p className="abstract-display">{standfirst}</p>
              </>
            ) : (
              <>
                <textarea className="headline-input" value={headline} onChange={(e) => setHeadline(e.target.value)} rows={2} />
                <textarea className="standfirst-input" value={standfirst} onChange={(e) => setStandfirst(e.target.value)} rows={2} />
              </>
            )}
            <div className="q-meta">
              {draft.categories.map((c) => (
                <span className="pill" key={c}>{c}</span>
              ))}
              {stage !== "pitch"
                ? draft.tags.map((t) => (
                    <span className="pill" key={t}>{t}</span>
                  ))
                : draft.suggested_outlet_names.map((name) => (
                    <span className="chip" key={name}>{name}</span>
                  ))}
            </div>
            {notice ? <div className="banner quiet-banner">{notice}</div> : null}
            {showsBody ? (
              <textarea className="body-input" value={spine} onChange={(e) => setSpine(e.target.value)} />
            ) : (
              <p className="pitch-note">
                This is not a draft. Go commissions the article, image plate, tags and outlets. Leave parks it.
                No-go kills it, with a reason.
              </p>
            )}
            <h2 className="section-label">{stage === "pitch" ? "Sources" : "Source links"}</h2>
            <ul className="sources">
              {draft.source_links.map((s) => (
                <li key={s.url}>
                  <a href={s.url} target="_blank" rel="noreferrer">{s.label}</a>
                  {s.note ? ` — ${s.note}` : ""}
                </li>
              ))}
            </ul>
            {stage === "pitch" ? (
              <>
                <h2 className="section-label">Suggested outlets</h2>
                <div className="q-meta">
                  {draft.targets.filter((t) => t.selected).map((t) => (
                    <span className="chip" key={t.id}>{t.outlet.name}</span>
                  ))}
                </div>
              </>
            ) : null}
          </>
        )}
      </main>

      <aside className="rail">
        {draft && stage === "pitch" ? (
          <div className="panel">
            <h2>Pitch</h2>
            <p className="notes">
              Headline, abstract, sources and suggested outlets only. Nothing is written yet — that starts after
              Go.
            </p>
            <p className="notes">
              <strong>Go</strong> commissions a draft. <strong>Leave</strong> parks this idea. <strong>No-go</strong>{" "}
              archives it.
            </p>
          </div>
        ) : null}
        {draft && stage !== "pitch" ? (
          <>
            <div className="panel">
              <h2>Verification</h2>
              {pill(draft.verification_status)}
              <p className="notes">
                Single-source, caution and defamation-sensitive copy can never auto-publish.
              </p>
            </div>
            {stage === "checking" || stage === "drafting" ? (
              <div className="panel">
                <h2>Confidence</h2>
                <div className="meter">
                  <span style={{ width: `${Math.round(draft.confidence.score * 100)}%` }} />
                </div>
                <div className="notes">
                  {Math.round(draft.confidence.score * 100)} · auto-draft{" "}
                  {draft.confidence.auto_draft_eligible ? "yes" : "no"} · auto-publish{" "}
                  {draft.confidence.auto_publish_eligible ? "yes" : "no"}
                </div>
              </div>
            ) : null}
            {showsImage ? (
              <div className="panel">
                <h2>Featured image</h2>
                {draft.media.map((m) => (
                  <figure key={m.id}>
                    <div className="plate" title={m.alt_text}>{m.placeholder_label}</div>
                    <figcaption className="caption">
                      {m.caption} · {m.credit}
                      {m.documentary_incident ? " · DOCUMENTARY (must be real)" : " · not a fake incident photo"}
                    </figcaption>
                  </figure>
                ))}
              </div>
            ) : null}
            {showsOutlets ? (
              <div className="panel">
                <h2>{stage === "publication" ? "CMS targets" : "Target outlets"}</h2>
                {draft.targets.map((t) => (
                  <label className="outlet" key={t.id}>
                    <header>
                      <input
                        type="checkbox"
                        checked={!!selected[t.outlet.id]}
                        onChange={(e) => setSelected((prev) => ({ ...prev, [t.outlet.id]: e.target.checked }))}
                      />
                      <strong>{t.outlet.name}</strong>
                      <span className="pill">{t.outlet.town}</span>
                    </header>
                    {stage === "publication" ? (
                      <div className="notes">
                        CMS {t.cms_status}
                        {t.remote_post_id ? ` · ${t.remote_post_id}` : ""}
                        {t.last_error ? ` · ${t.last_error}` : ""}
                      </div>
                    ) : (
                      <>
                        <div className="brief">{t.outlet.localisation_brief}</div>
                        <textarea
                          className="graf-input"
                          rows={4}
                          value={grafs[t.outlet.id] || ""}
                          onChange={(e) => setGrafs((prev) => ({ ...prev, [t.outlet.id]: e.target.value }))}
                        />
                      </>
                    )}
                  </label>
                ))}
                {stage === "drafting" || stage === "checking" ? (
                  <button className="btn quiet" disabled={busy} onClick={() => run("outlet_override")}>
                    Save outlet override
                  </button>
                ) : null}
              </div>
            ) : null}
            {showsSocial ? (
              <div className="panel">
                <h2>Social stubs</h2>
                {draft.social_posts.map((s) => (
                  <div className="social" key={s.id}>
                    <div className="q-meta">
                      {pill(s.platform === "x" ? "x" : "facebook")}
                      {pill(s.status)}
                    </div>
                    <textarea
                      className="social-input"
                      rows={4}
                      value={socialEdits[s.id] || ""}
                      onChange={(e) => setSocialEdits((prev) => ({ ...prev, [s.id]: e.target.value }))}
                    />
                    <div className="row">
                      <button className="btn" disabled={busy} onClick={() => run("social_approve", { social_post_id: s.id, social_copy: socialEdits[s.id] })}>Approve</button>
                      <button className="btn" disabled={busy} onClick={() => run("social_edit", { social_post_id: s.id, social_copy: socialEdits[s.id] })}>Edit</button>
                      <button className="btn" disabled={busy} onClick={() => run("social_hold", { social_post_id: s.id })}>Hold</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
            {stage === "checking" || stage === "drafting" ? (
              <div className="panel">
                <h2>Decisions</h2>
                {draft.decisions.length === 0 ? <p className="notes">None yet — the learning loop starts here.</p> : null}
                {draft.decisions.slice(0, 6).map((d) => (
                  <p className="notes" key={d.id}>
                    {d.action.replaceAll("_", " ")} · {d.actor}
                    {d.reason ? ` · ${d.reason}` : ""}
                  </p>
                ))}
              </div>
            ) : null}
          </>
        ) : null}
      </aside>

      <footer className="actions">
        {stage === "pitch" && draft ? (
          <>
            <button className="btn primary" disabled={busy} onClick={() => run("go")}>
              Go
            </button>
            {draft.parked ? (
              <button className="btn" disabled={busy} onClick={() => run("unleave")}>
                Unpark
              </button>
            ) : (
              <button className="btn quiet" disabled={busy} onClick={() => run("leave")}>
                Leave
              </button>
            )}
            <button className="btn danger" disabled={busy} onClick={() => setReasonMode("no_go")}>
              No-go
            </button>
            <span className="action-hint">Go commissions a draft. Leave parks. No-go kills, with a reason.</span>
          </>
        ) : null}
        {stage === "drafting" && draft ? (
          <>
            <button className="btn primary" disabled={busy} onClick={() => run("send_to_checking")}>
              Send to checking
            </button>
            <button className="btn quiet" disabled={busy} onClick={() => run("return_to_pitch")}>
              Back to pitch
            </button>
            <button className="btn quiet" disabled={busy} onClick={() => run("tweak")}>
              Save tweak
            </button>
          </>
        ) : null}
        {stage === "checking" && draft ? (
          <>
            <button className="btn primary" disabled={busy} onClick={() => run("approve_create_cms_drafts")}>
              Approve CMS draft
            </button>
            <button className="btn" disabled={busy} onClick={() => setReasonMode("request_changes")}>
              Request changes
            </button>
            <button className="btn danger" disabled={busy} onClick={() => setReasonMode("reject")}>
              Reject
            </button>
            <button className="btn" disabled={busy} onClick={() => run("hold")}>
              Hold
            </button>
          </>
        ) : null}
        {stage === "publication" && draft ? (
          <>
            <button className="btn primary" disabled={busy} onClick={() => run("advance_to_social")}>
              Send to social
            </button>
            <span className="action-hint">WordPress stays draft-only unless Approve &amp; publish is flagged on.</span>
          </>
        ) : null}
        {stage === "social" && draft ? (
          <span className="action-hint">Approve, edit or hold each stub. Connectors are not wired yet.</span>
        ) : null}
        {!draft ? <span className="action-hint">{currentStage?.empty}</span> : null}
      </footer>

      {reasonMode ? (
        <div className="modal-back" onClick={() => setReasonMode(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{reasonCopy[reasonMode].title}</h3>
            <p className="notes">{reasonCopy[reasonMode].body}</p>
            <textarea className="reason-input" rows={5} value={reason} onChange={(e) => setReason(e.target.value)} />
            <div className="row" style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <button className={`btn ${reasonMode === "request_changes" ? "primary" : "danger"}`} onClick={submitReason}>
                {reasonCopy[reasonMode].confirm}
              </button>
              <button className="btn quiet" onClick={() => setReasonMode(null)}>Cancel</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
