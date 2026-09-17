"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBase, getDraft, getPipeline, getSettings, listDrafts, recordDecision } from "../lib/api";
import type {
  DeskSettings,
  DraftDetail,
  DraftListItem,
  Outlet,
  PipelineStage,
  SocialPost,
} from "../lib/types";
import FocusTitles from "./FocusTitles";
import TitlePicker from "./TitlePicker";

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

function mark(value: string, extra = "") {
  return <span className={`mark ${extra}`.trim()}>{value.replaceAll("_", " ")}</span>;
}

function socialCopy(post: SocialPost) {
  return post.edited_body || post.body;
}

function actorLabel(settings: DeskSettings | null) {
  const raw = settings?.default_actor || "journalist";
  return raw.includes("@") ? raw.split("@")[0] : raw;
}

function rowMarkers(item: DraftListItem, stage: string) {
  const marks: { text: string; tone?: string }[] = [];
  if (item.parked) marks.push({ text: "Left", tone: "left" });
  if (stage === "drafting" && !item.draft_ready) marks.push({ text: "Generating" });
  if (item.status === "changes_requested") marks.push({ text: "Changes", tone: "changes_requested" });
  if (item.status === "held") marks.push({ text: "Held", tone: "held" });
  if (stage !== "pitch" && item.verification_status !== "verified") {
    marks.push({
      text: item.verification_status.replaceAll("_", " "),
      tone: item.verification_status,
    });
  }
  const outlet = item.suggested_outlet_names[0];
  if (outlet && marks.length < 3) marks.push({ text: outlet });
  return marks.slice(0, 3);
}

export default function DeskApp({ initialId }: { initialId?: string }) {
  const [stage, setStage] = useState("pitch");
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [queue, setQueue] = useState<DraftListItem[]>([]);
  const [draft, setDraft] = useState<DraftDetail | null>(null);
  const [settings, setSettings] = useState<DeskSettings | null>(null);
  const [focus, setFocus] = useState<Outlet | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [headline, setHeadline] = useState("");
  const [standfirst, setStandfirst] = useState("");
  const [spine, setSpine] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [grafs, setGrafs] = useState<Record<string, string>>({});
  const [extras, setExtras] = useState<Outlet[]>([]);
  const [socialEdits, setSocialEdits] = useState<Record<string, string>>({});
  const [reasonMode, setReasonMode] = useState<ReasonMode>(null);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const currentStage = stages.find((s) => s.id === stage);
  const showRail = Boolean(draft) && stage !== "pitch";
  const generating = Boolean(draft && (draft.generating || (stage === "drafting" && !draft.draft_ready)));

  async function refresh(nextStage = stage, selectId?: string, focusId = focus?.id) {
    const [rows, pipe] = await Promise.all([listDrafts(nextStage, focusId), getPipeline(focusId)]);
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
    setExtras([]);
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
  const showsImage = (stage === "drafting" || stage === "checking") && !generating;
  const selectedOutlets = draft?.targets.filter((t) => t.selected) || [];
  const publisher = settings?.publisher_name || "Newsworld";

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
      if (showsBody && !generating) payload.spine_body = spine;
      const next = await recordDecision(draft.id, payload as Parameters<typeof recordDecision>[1]);
      const followStage = STAGE_AFTER_ACTION[action] || next.pipeline_stage || stage;
      if (action === "go") setNotice("Commissioned. The article is now in Drafting.");
      if (action === "leave") setNotice("Left on the spike. This is not a No-go — unpark when you want it back.");
      if (action === "unleave") setNotice("Back on the spike.");
      if (action === "no_go") setNotice("No-go. The pitch is archived with your reason.");
      await refresh(followStage, action === "no_go" ? undefined : next.id);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function openReason(mode: NonNullable<ReasonMode>) {
    setReason("");
    setReasonError(null);
    setError(null);
    setReasonMode(mode);
  }

  function submitReason() {
    if (!reasonMode) return;
    if (!reason.trim()) {
      setReasonError("A reason is required.");
      return;
    }
    const action = reasonMode;
    setReasonMode(null);
    setReasonError(null);
    const text = reason;
    setReason("");
    void run(action, { reason: text });
  }

  function rememberOutlet(outlet: Outlet) {
    setExtras((prev) => (prev.some((row) => row.id === outlet.id) ? prev : [...prev, outlet]));
  }

  async function changeFocus(outlet: Outlet | null) {
    setFocus(outlet);
    setNotice(null);
    setError(null);
    await refresh(stage, draft?.id, outlet?.id);
  }

  const reasonCopy = {
    no_go: {
      title: "No-go this pitch?",
      body: "No-go kills the idea and archives it with your reason. Leave on Pitch parks it on the spike instead — that is not a kill.",
      confirm: "No-go",
    },
    reject: {
      title: "Reject this draft",
      body: "A reason is required and is stored on the decision and audit log.",
      confirm: "Reject",
    },
    request_changes: {
      title: "Request changes",
      body: "A reason is required and is stored on the decision and audit log.",
      confirm: "Request changes",
    },
  } as const;

  const storyKicker = draft?.categories[0];
  const sensitive =
    draft && draft.verification_status !== "verified" && stage !== "pitch"
      ? draft.verification_status.replaceAll("_", " ")
      : null;
  const featured = draft?.media.find((m) => m.role === "featured") || draft?.media[0];

  return (
    <div className={`desk stage-${stage}${showRail ? " has-rail" : ""}`}>
      <header className="mast">
        <div className="mast-brand">
          <p className="kicker">{publisher}</p>
          <h1>Deepfold</h1>
        </div>
        <dl className="mast-meta">
          <FocusTitles focus={focus} onChange={(outlet) => void changeFocus(outlet)} />
          <div>
            <dt>Desk</dt>
            <dd>{actorLabel(settings)}</dd>
          </div>
          <div>
            <dt>Publish</dt>
            <dd>{settings?.approve_and_publish_enabled ? "On" : "Off"}</dd>
          </div>
          {settings?.kill_switch ? (
            <div className="hot">
              <dt>Kill switch</dt>
              <dd>On</dd>
            </div>
          ) : null}
        </dl>
      </header>

      <nav className="stages" aria-label="Pipeline stages">
        {stages.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`stage ${stage === item.id ? "active" : ""}`}
            aria-current={stage === item.id ? "page" : undefined}
            onClick={() => {
              setError(null);
              setNotice(null);
              void refresh(item.id);
            }}
          >
            <span className="stage-label">{item.label}</span>
            <span className={`stage-count${item.count === 0 ? " zero" : ""}`}>{item.count}</span>
          </button>
        ))}
      </nav>

      {error ? <div className="alert" role="alert">{error}</div> : null}

      <aside className="queue" aria-label="Stories in this stage">
        {queue.length === 0 ? (
          <p className="empty">{currentStage?.empty || "Nothing in this stage."}</p>
        ) : null}
        {queue.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`q-item ${draft?.id === item.id ? "active" : ""}`}
            onClick={() => {
              setNotice(null);
              void openDraft(item.id);
            }}
          >
            <h3>{item.headline}</h3>
            <p className="q-abstract">{item.standfirst}</p>
            <p className="q-meta">
              {rowMarkers(item, stage).map((row) =>
                row.tone ? (
                  <span className={`mark ${row.tone}`} key={row.text}>
                    {row.text}
                  </span>
                ) : (
                  <span key={row.text}>{row.text}</span>
                ),
              )}
            </p>
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
          <div className="well-inner">
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
                <textarea className="headline-input" value={headline} onChange={(e) => setHeadline(e.target.value)} rows={2} />
                <textarea className="standfirst-input" value={standfirst} onChange={(e) => setStandfirst(e.target.value)} rows={2} />
              </>
            )}
            {draft.parked ? <p className="byline">Left on the spike</p> : null}
            {notice ? <p className="quiet-banner">{notice}</p> : null}
            {showsBody && draft.tags.length > 0 && !generating ? (
              <p className="tag-line">{draft.tags.join(" · ")}</p>
            ) : null}
            {showsImage && featured ? (
              <figure className="well-plate">
                <div className="plate" title={featured.alt_text}>{featured.placeholder_label}</div>
                <figcaption className="caption">
                  {featured.caption} · {featured.credit}
                  {featured.documentary_incident ? " · Documentary (must be real)" : ""}
                </figcaption>
              </figure>
            ) : null}
            {generating ? (
              <div className="generating" aria-live="polite">
                <p className="quiet-banner">Draft generating… Grok Bot has the job. Credits sit on that side; this desk only stores the result.</p>
                <div className="skeleton-line" />
                <div className="skeleton-line" />
                <div className="skeleton-line short" />
                <div className="skeleton-line" />
                <div className="skeleton-line short" />
              </div>
            ) : null}
            {showsBody && !generating ? (
              <textarea className="body-input" value={spine} onChange={(e) => setSpine(e.target.value)} rows={16} />
            ) : null}
            <h2 className="section-label">Sources</h2>
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
                <h2 className="section-label">Suggested titles</h2>
                <p className="outlet-line">{selectedOutlets.map((t) => t.outlet.name).join(" · ") || "None selected"}</p>
              </>
            ) : null}
          </div>
        )}
      </main>

      {showRail ? (
        <aside className="rail">
          <section>
            <h2>Verification</h2>
            {mark(draft!.verification_status, draft!.verification_status)}
            <p className="notes">Single-source, caution and defamation-sensitive copy can never auto-publish.</p>
          </section>
          {stage === "checking" || stage === "drafting" ? (
            <section>
              <h2>Confidence</h2>
              <div className="meter" aria-hidden="true">
                <span style={{ width: `${Math.round(draft!.confidence.score * 100)}%` }} />
              </div>
              <p className="notes">
                {Math.round(draft!.confidence.score * 100)} · auto-draft{" "}
                {draft!.confidence.auto_draft_eligible ? "yes" : "no"} · auto-publish{" "}
                {draft!.confidence.auto_publish_eligible ? "yes" : "no"}
              </p>
            </section>
          ) : null}
          {showsOutlets ? (
            <TitlePicker
              draftId={draft!.id}
              stage={stage}
              targets={draft!.targets}
              extras={extras}
              selected={selected}
              grafs={grafs}
              busy={busy}
              onSelected={setSelected}
              onGrafs={setGrafs}
              onCatalog={rememberOutlet}
              onSave={() => run("outlet_override")}
            />
          ) : null}
          {showsSocial ? (
            <section>
              <h2>Social stubs</h2>
              {draft!.social_posts.map((s) => (
                <div className="social" key={s.id}>
                  <p className="q-meta">
                    {mark(s.platform === "x" ? "x" : "facebook")}
                    {mark(s.status)}
                  </p>
                  <textarea
                    className="social-input"
                    rows={4}
                    value={socialEdits[s.id] || ""}
                    onChange={(e) => setSocialEdits((prev) => ({ ...prev, [s.id]: e.target.value }))}
                  />
                  <div className="row">
                    <button type="button" className="btn" disabled={busy} onClick={() => run("social_approve", { social_post_id: s.id, social_copy: socialEdits[s.id] })}>Approve</button>
                    <button type="button" className="btn" disabled={busy} onClick={() => run("social_edit", { social_post_id: s.id, social_copy: socialEdits[s.id] })}>Edit</button>
                    <button type="button" className="btn quiet" disabled={busy} onClick={() => run("social_hold", { social_post_id: s.id })}>Hold</button>
                  </div>
                </div>
              ))}
            </section>
          ) : null}
          {stage === "checking" || stage === "drafting" ? (
            <section>
              <h2>Decisions</h2>
              {draft!.decisions.length === 0 ? <p className="notes">None yet.</p> : null}
              {draft!.decisions.slice(0, 6).map((d) => (
                <p className="notes" key={d.id}>
                  {d.action.replaceAll("_", " ")} · {d.actor}
                  {d.reason ? ` · ${d.reason}` : ""}
                </p>
              ))}
            </section>
          ) : null}
        </aside>
      ) : null}

      <footer className="actions" aria-label="Stage actions">
        {stage === "pitch" && draft ? (
          <>
            <button type="button" className="btn primary" disabled={busy} onClick={() => run("go")}>
              Go
            </button>
            {draft.parked ? (
              <button type="button" className="btn" disabled={busy} onClick={() => run("unleave")}>
                Unpark
              </button>
            ) : (
              <button type="button" className="btn quiet" disabled={busy} onClick={() => run("leave")}>
                Leave on Pitch
              </button>
            )}
            <button type="button" className="btn danger" disabled={busy} onClick={() => openReason("no_go")}>
              No-go
            </button>
            <span className="action-hint">Go commissions a draft. Leave parks. No-go kills, with a reason.</span>
          </>
        ) : null}
        {stage === "drafting" && draft ? (
          <>
            <button
              type="button"
              className="btn primary"
              disabled={busy || generating}
              onClick={() => run("send_to_checking")}
            >
              Send to checking
            </button>
            <button type="button" className="btn quiet" disabled={busy} onClick={() => run("return_to_pitch")}>
              Back to pitch
            </button>
            <button type="button" className="btn quiet" disabled={busy || generating} onClick={() => run("tweak")}>
              Save tweak
            </button>
          </>
        ) : null}
        {stage === "checking" && draft ? (
          <>
            <button type="button" className="btn primary" disabled={busy} onClick={() => run("approve_create_cms_drafts")}>
              Approve CMS draft
            </button>
            <button type="button" className="btn" disabled={busy} onClick={() => openReason("request_changes")}>
              Request changes
            </button>
            <button type="button" className="btn danger" disabled={busy} onClick={() => openReason("reject")}>
              Reject
            </button>
            <button type="button" className="btn quiet" disabled={busy} onClick={() => run("hold")}>
              Hold
            </button>
          </>
        ) : null}
        {stage === "publication" && draft ? (
          <>
            <button type="button" className="btn primary" disabled={busy} onClick={() => run("advance_to_social")}>
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
        <div
          className="modal-back"
          onClick={() => {
            setReasonMode(null);
            setReasonError(null);
          }}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="reason-title">
            <h3 id="reason-title">{reasonCopy[reasonMode].title}</h3>
            <p className="notes">{reasonCopy[reasonMode].body}</p>
            <textarea
              className="reason-input"
              rows={5}
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                if (reasonError) setReasonError(null);
              }}
              placeholder="Reason"
              aria-label="Reason"
            />
            {reasonError ? <p className="notes modal-error">{reasonError}</p> : null}
            <div className="row">
              <button
                type="button"
                className={`btn confirm ${reasonMode === "request_changes" ? "primary" : "danger"}`}
                onClick={submitReason}
              >
                {reasonCopy[reasonMode].confirm}
              </button>
              <button
                type="button"
                className="btn quiet"
                onClick={() => {
                  setReasonMode(null);
                  setReasonError(null);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
