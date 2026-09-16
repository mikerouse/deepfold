"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBase, getDraft, getSettings, listDrafts, recordDecision } from "../lib/api";
import type { DeskSettings, DraftDetail, DraftListItem, SocialPost } from "../lib/types";

type ReasonMode = "reject" | "request_changes" | null;

function pill(value: string) {
  return <span className={`pill ${value}`}>{value.replaceAll("_", " ")}</span>;
}

function socialCopy(post: SocialPost) {
  return post.edited_body || post.body;
}

export default function DeskApp({ initialId }: { initialId?: string }) {
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

  async function loadQueue(selectId?: string) {
    const rows = await listDrafts();
    setQueue(rows);
    const id = selectId || draft?.id || initialId || rows[0]?.id;
    if (id) await openDraft(id);
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
        const [deskSettings] = await Promise.all([getSettings(), loadQueue()]);
        setSettings(deskSettings);
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

  async function run(action: string, extra?: Record<string, unknown>) {
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      const next = await recordDecision(draft.id, {
        action,
        headline,
        standfirst,
        spine_body: spine,
        selected_outlet_ids: selectedIds,
        local_grafs: grafs,
        ...extra,
      });
      setDraft(next);
      await loadQueue(next.id);
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

  return (
    <div className="desk">
      <header className="mast">
        <div className="mast-brand">
          <div className="kicker">Conservative Post · UK local news</div>
          <h1>Deepfold Approvals Desk</h1>
        </div>
        <div className="mast-meta">
          <div>
            Spike
            <strong>{queue.filter((d) => d.status === "awaiting_review").length} awaiting</strong>
          </div>
          <div>
            Actor
            <strong>{settings?.default_actor || "journalist"}</strong>
          </div>
        </div>
      </header>

      <div className="flags">
        <span className={settings?.kill_switch ? "hot" : ""}>
          Kill switch {settings?.kill_switch ? "ON" : "off"}
        </span>
        <span>Approve &amp; publish {settings?.approve_and_publish_enabled ? "ON" : "OFF (default)"}</span>
        <span>WP live {settings?.wp_live ? "on" : "dry-run"}</span>
        <span>Connectors later · social is modelled only</span>
      </div>

      {error ? <div className="error" style={{ gridColumn: "1 / -1" }}>{error}</div> : null}

      <aside className="queue">
        <h2>Copy spike</h2>
        {queue.map((item) => (
          <button
            key={item.id}
            className={`q-item ${draft?.id === item.id ? "active" : ""}`}
            onClick={() => openDraft(item.id)}
          >
            <div className="town">{item.suggested_outlet_names[0] || item.categories[0]}</div>
            <h3>{item.headline}</h3>
            <div className="q-meta">
              {pill(item.status)}
              {pill(item.verification_status)}
              <span className="pill">{Math.round(item.confidence_score * 100)}%</span>
            </div>
          </button>
        ))}
      </aside>

      <main className="well">
        {!draft ? (
          <div className="banner">No draft selected. Seed the API if the spike is empty.</div>
        ) : (
          <>
            <div className="byline">{draft.byline} · {draft.slug}</div>
            <textarea className="headline-input" value={headline} onChange={(e) => setHeadline(e.target.value)} rows={2} />
            <textarea className="standfirst-input" value={standfirst} onChange={(e) => setStandfirst(e.target.value)} rows={2} />
            <div className="q-meta">
              {draft.categories.map((c) => (
                <span className="pill" key={c}>{c}</span>
              ))}
              {draft.tags.map((t) => (
                <span className="pill" key={t}>{t}</span>
              ))}
            </div>
            <textarea className="body-input" value={spine} onChange={(e) => setSpine(e.target.value)} />
            <h2 className="section-label">Source links</h2>
            <ul className="sources">
              {draft.source_links.map((s) => (
                <li key={s.url}>
                  <a href={s.url} target="_blank" rel="noreferrer">{s.label}</a>
                  {s.note ? ` — ${s.note}` : ""}
                </li>
              ))}
            </ul>
          </>
        )}
      </main>

      <aside className="rail">
        {draft ? (
          <>
            <div className="panel">
              <h2>Verification</h2>
              {pill(draft.verification_status)}
              <p className="notes">
                Single-source, caution and defamation-sensitive copy can never auto-publish.
              </p>
            </div>
            <div className="panel">
              <h2>Confidence stub</h2>
              <div className="meter">
                <span style={{ width: `${Math.round(draft.confidence.score * 100)}%` }} />
              </div>
              <div>{Math.round(draft.confidence.score * 100)} · auto-draft {draft.confidence.auto_draft_eligible ? "yes" : "no"} · auto-publish {draft.confidence.auto_publish_eligible ? "yes" : "no"}</div>
              {draft.confidence.notes.map((n) => (
                <p className="notes" key={n}>{n}</p>
              ))}
            </div>
            <div className="panel">
              <h2>Featured image</h2>
              {draft.media.map((m) => (
                <figure key={m.id}>
                  <div className="plate" title={m.alt_text}>{m.placeholder_label}</div>
                  <figcaption className="caption">
                    {m.caption} · {m.credit} · policy {m.policy_tag.replaceAll("_", " ")}
                    {m.documentary_incident ? " · DOCUMENTARY (must be real)" : " · not a fake incident photo"}
                  </figcaption>
                </figure>
              ))}
            </div>
            <div className="panel">
              <h2>Target outlets</h2>
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
                  <div className="brief">{t.outlet.localisation_brief}</div>
                  <textarea
                    className="graf-input"
                    rows={4}
                    value={grafs[t.outlet.id] || ""}
                    onChange={(e) => setGrafs((prev) => ({ ...prev, [t.outlet.id]: e.target.value }))}
                  />
                  <div className="notes">CMS {t.cms_status}{t.remote_post_id ? ` · ${t.remote_post_id}` : ""}</div>
                </label>
              ))}
              <button className="btn quiet" disabled={busy} onClick={() => run("outlet_override")}>
                Save outlet override
              </button>
            </div>
            <div className="panel">
              <h2>Social packs</h2>
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
            <div className="panel">
              <h2>Decisions</h2>
              {draft.decisions.length === 0 ? <p className="notes">None yet — the learning loop starts here.</p> : null}
              {draft.decisions.map((d) => (
                <p className="notes" key={d.id}>
                  {d.action.replaceAll("_", " ")} · {d.actor}
                  {d.reason ? ` · ${d.reason}` : ""}
                </p>
              ))}
            </div>
          </>
        ) : null}
      </aside>

      <footer className="actions">
        <button className="btn primary" disabled={busy || !draft} onClick={() => run("approve_create_cms_drafts")}>
          Approve &amp; create CMS drafts
        </button>
        <button
          className="btn"
          disabled={busy || !draft || !settings?.approve_and_publish_enabled || settings.kill_switch}
          title="Feature-flagged off by default"
          onClick={() => run("approve_publish")}
        >
          Approve &amp; publish
        </button>
        <button className="btn" disabled={busy || !draft} onClick={() => setReasonMode("request_changes")}>
          Request changes
        </button>
        <button className="btn danger" disabled={busy || !draft} onClick={() => setReasonMode("reject")}>
          Reject
        </button>
        <button className="btn" disabled={busy || !draft} onClick={() => run("hold")}>
          Hold
        </button>
        <button className="btn quiet" disabled={busy || !draft} onClick={() => run("tweak")}>
          Save tweak
        </button>
      </footer>

      {reasonMode ? (
        <div className="modal-back" onClick={() => setReasonMode(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{reasonMode === "reject" ? "Reject this draft" : "Request changes"}</h3>
            <p className="notes">A reason is required and is stored on the decision + audit log.</p>
            <textarea className="reason-input" rows={5} value={reason} onChange={(e) => setReason(e.target.value)} />
            <div className="row" style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <button className="btn danger" onClick={submitReason}>Record</button>
              <button className="btn quiet" onClick={() => setReasonMode(null)}>Cancel</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
