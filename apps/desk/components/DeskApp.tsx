"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  apiBase,
  getDraft,
  getPipeline,
  getSettings,
  listDrafts,
  listPackages,
  outletFacets,
  recordDecision,
} from "../lib/api";
import { openJobs } from "../lib/story";
import type {
  DeskSettings,
  DraftDetail,
  DraftListItem,
  Outlet,
  OutletPackage,
  PipelineStage,
  SocialPost,
} from "../lib/types";
import FiltersBar from "./FiltersBar";
import FocusTitles from "./FocusTitles";
import InfoRail from "./InfoRail";
import StoryCanvas from "./StoryCanvas";
import StoryList from "./StoryList";
import StoryRibbon from "./StoryRibbon";
import TitlePicker from "./TitlePicker";

type ReasonMode = "reject" | "request_changes" | "no_go" | null;
type View = "list" | "story";

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

function socialCopy(post: SocialPost) {
  return post.edited_body || post.body;
}

function actorLabel(settings: DeskSettings | null) {
  const raw = settings?.default_actor || "journalist";
  return raw.includes("@") ? raw.split("@")[0] : raw;
}

export default function DeskApp({ initialId }: { initialId?: string }) {
  const [view, setView] = useState<View>(initialId ? "story" : "list");
  const [stageFilter, setStageFilter] = useState("");
  const [platformFilter, setPlatformFilter] = useState("");
  const [countyFilter, setCountyFilter] = useState("");
  const [packageFilter, setPackageFilter] = useState("");
  const [stage, setStage] = useState("pitch");
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [queue, setQueue] = useState<DraftListItem[]>([]);
  const [packages, setPackages] = useState<OutletPackage[]>([]);
  const [counties, setCounties] = useState<string[]>([]);
  const [loaded, setLoaded] = useState(false);
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
  const [railOpen, setRailOpen] = useState(true);
  const spineRef = useRef("");
  spineRef.current = spine;

  const currentStage = stages.find((s) => s.id === stage);
  const generating = Boolean(draft && (draft.generating || (stage === "drafting" && !draft.draft_ready && !(spine || "").trim())));

  async function refreshList(focusId = focus?.id) {
    const [rows, pipe] = await Promise.all([
      listDrafts({
        stage: stageFilter || undefined,
        outletId: focusId,
        platform: platformFilter || undefined,
        packageId: packageFilter || undefined,
        county: countyFilter || undefined,
      }),
      getPipeline(focusId),
    ]);
    setQueue(rows);
    setStages(pipe.stages);
    setLoaded(true);
    return rows;
  }

  function applyDetail(detail: DraftDetail, { takeCopy }: { takeCopy: boolean }) {
    setDraft(detail);
    setStage(detail.pipeline_stage || "pitch");
    setSelected(Object.fromEntries(detail.targets.map((t) => [t.outlet.id, t.selected])));
    setGrafs(Object.fromEntries(detail.targets.map((t) => [t.outlet.id, t.local_graf])));
    setSocialEdits((prev) => {
      const next = { ...prev };
      for (const post of detail.social_posts) {
        if (next[post.id] === undefined) next[post.id] = socialCopy(post);
      }
      return next;
    });
    if (takeCopy || detail.generating || !spineRef.current.trim()) {
      setHeadline(detail.headline);
      setStandfirst(detail.standfirst);
      setSpine(detail.spine_body);
    }
  }

  async function openDraft(id: string, nextView: View = "story") {
    const detail = await getDraft(id);
    setExtras([]);
    applyDetail(detail, { takeCopy: true });
    setView(nextView);
    if (nextView === "story" && typeof window !== "undefined") {
      window.history.replaceState(null, "", `/drafts/${id}`);
    }
  }

  async function openStory(id: string) {
    setNotice(null);
    setError(null);
    try {
      await openDraft(id, "story");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function backToList() {
    setDraft(null);
    setView("list");
    setNotice(null);
    setError(null);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", "/");
    }
    void refreshList();
  }

  useEffect(() => {
    (async () => {
      try {
        const [deskSettings, packs, facets] = await Promise.all([
          getSettings(),
          listPackages(),
          outletFacets(),
        ]);
        setSettings(deskSettings);
        setPackages(packs);
        setCounties(facets.counties);
        if (initialId) await openDraft(initialId, "story");
      } catch (err) {
        setError(
          `Cannot reach the API at ${apiBase()}. Start Postgres/API with docker compose, or the SQLite fallback in the README. ${(err as Error).message}`,
        );
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!settings) return;
    void refreshList().catch((err) => setError((err as Error).message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stageFilter, platformFilter, countyFilter, packageFilter, focus?.id, settings]);

  useEffect(() => {
    if (view !== "story" || !draft) return;
    const waiting = draft.generating || openJobs(draft.jobs).length > 0;
    if (!waiting) return;
    const id = draft.id;
    const timer = window.setInterval(() => {
      void (async () => {
        try {
          const next = await getDraft(id);
          applyDetail(next, { takeCopy: false });
        } catch {
          /* keep the open document; next poll retries */
        }
      })();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [view, draft?.id, draft?.generating, draft?.jobs.map((job) => `${job.id}:${job.status}`).join("|")]);

  useEffect(() => {
    if (view !== "list") return;
    if (!queue.some((row) => row.worker_status)) return;
    const timer = window.setInterval(() => {
      void refreshList().catch(() => undefined);
    }, 4000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, queue.map((row) => row.worker_status).join("|")]);

  const selectedIds = useMemo(
    () => Object.entries(selected).filter(([, on]) => on).map(([id]) => id),
    [selected],
  );

  const showsBody = stage === "drafting" || stage === "checking" || stage === "publication";
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
      if (action === "go") setNotice("Commissioned. Jobs are queued for Grok Bot — this desk does not call a model.");
      if (action === "leave") setNotice("Left on the spike. This is not a No-go — unpark when you want it back.");
      if (action === "unleave") setNotice("Back on the spike.");
      if (action === "no_go") setNotice("No-go. The pitch is archived with your reason.");
      if (action === "request_rewrite") setNotice("Rewrite queued for Grok Bot.");
      if (action === "queue_featured_image") setNotice("Featured image queued for Grok Bot.");
      await refreshList();
      if (action === "no_go") {
        backToList();
        setNotice("No-go. The pitch is archived with your reason.");
      } else {
        setStage(followStage);
        applyDetail(next, { takeCopy: true });
        setView("story");
      }
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
  }

  async function addTitleToStory(item: DraftListItem, outlet: Outlet) {
    setBusy(true);
    setError(null);
    try {
      const ids = item.selected_outlet_ids.includes(outlet.id)
        ? item.selected_outlet_ids
        : [...item.selected_outlet_ids, outlet.id];
      await recordDecision(item.id, { action: "outlet_override", selected_outlet_ids: ids });
      await refreshList();
      if (draft?.id === item.id) await openDraft(item.id, view);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function copySocialPack() {
    if (!draft) return;
    const text = draft.social_posts
      .map((post) => `${post.platform === "x" ? "X" : "Facebook"}\n${socialEdits[post.id] || socialCopy(post)}`)
      .join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setNotice("Social pack copied.");
    } catch {
      setNotice("Could not copy the social pack.");
    }
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
  const featured = draft?.media.find((m) => m.role === "featured") || draft?.media[0];
  const listMode = view === "list";
  const imageJob = draft?.jobs.find((job) => job.kind === "featured_image");
  const imageQueued = imageJob?.status === "queued";
  const imageWorking = imageJob?.status === "claimed";
  const demoWorker = Boolean(settings?.demo_grok_worker || draft?.flags.demo_grok_worker);

  return (
    <div className={`desk ${listMode ? "list-mode" : `story-mode stage-${stage}`}${!listMode && railOpen && draft ? " has-rail" : ""}`}>
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

      {listMode ? (
        <FiltersBar
          stages={stages}
          stage={stageFilter}
          platform={platformFilter}
          county={countyFilter}
          packageId={packageFilter}
          counties={counties}
          packages={packages}
          onStage={(value) => {
            setStageFilter(value);
            setError(null);
          }}
          onPlatform={(value) => {
            setPlatformFilter(value);
            setError(null);
          }}
          onCounty={(value) => {
            setCountyFilter(value);
            setError(null);
          }}
          onPackage={(value) => {
            setPackageFilter(value);
            setError(null);
          }}
        />
      ) : (
        <nav className="crumb" aria-label="Stories">
          <button type="button" className="crumb-back" onClick={backToList}>
            Stories
          </button>
          <span aria-hidden="true">/</span>
          <span>{currentStage?.label || "Story"}</span>
        </nav>
      )}

      {error ? <div className="alert" role="alert">{error}</div> : null}

      {listMode ? (
        <StoryList
          rows={queue}
          stages={stages}
          stageFilter={stageFilter}
          loaded={loaded}
          busy={busy}
          onOpen={(id) => void openStory(id)}
          onAddTitle={(item, outlet) => void addTitleToStory(item, outlet)}
        />
      ) : draft ? (
        <>
          <StoryRibbon
            stage={stage}
            draft={draft}
            busy={busy}
            generating={generating}
            featured={featured}
            demoWorker={demoWorker}
            railOpen={railOpen}
            onToggleRail={() => setRailOpen((open) => !open)}
            onRun={(action, extra) => void run(action, extra)}
            onOpenReason={openReason}
            titlesPanel={
              <TitlePicker
                draftId={draft.id}
                stage={stage}
                targets={draft.targets}
                extras={extras}
                selected={selected}
                grafs={grafs}
                busy={busy}
                embedded
                onSelected={setSelected}
                onGrafs={setGrafs}
                onCatalog={rememberOutlet}
                onSave={() => run("outlet_override")}
              />
            }
            socialPanel={
              <div className="social-panel">
                {(draft.social_posts || []).length === 0 ? (
                  <p className="notes">No stubs yet. Use Publish → Send to social after a CMS draft.</p>
                ) : (
                  <>
                    <button type="button" className="btn quiet" onClick={() => void copySocialPack()}>
                      Copy pack
                    </button>
                    {draft.social_posts.map((post) => (
                      <div className="social" key={post.id}>
                        <p className="q-meta">
                          <span className="mark">{post.platform === "x" ? "x" : "facebook"}</span>
                          <span className="mark">{post.status}</span>
                        </p>
                        <textarea
                          className="social-input"
                          rows={4}
                          value={socialEdits[post.id] || ""}
                          onChange={(e) => setSocialEdits((prev) => ({ ...prev, [post.id]: e.target.value }))}
                        />
                        <div className="row">
                          <button
                            type="button"
                            className="btn"
                            disabled={busy}
                            onClick={() => run("social_approve", { social_post_id: post.id, social_copy: socialEdits[post.id] })}
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            className="btn"
                            disabled={busy}
                            onClick={() => run("social_edit", { social_post_id: post.id, social_copy: socialEdits[post.id] })}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="btn quiet"
                            disabled={busy}
                            onClick={() => run("social_hold", { social_post_id: post.id })}
                          >
                            Hold
                          </button>
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            }
          />
          <main className="well">
            <StoryCanvas
              draft={draft}
              stage={stage}
              headline={headline}
              standfirst={standfirst}
              spine={spine}
              generating={generating}
              notice={notice}
              featured={featured}
              imageQueued={Boolean(imageQueued)}
              imageWorking={Boolean(imageWorking)}
              selectedTitles={selectedOutlets.map((t) => t.outlet.name).join(" · ")}
              onHeadline={setHeadline}
              onStandfirst={setStandfirst}
              onSpine={setSpine}
            />
          </main>
          {railOpen ? <InfoRail draft={draft} stage={stage} /> : null}
        </>
      ) : (
        <main className="well">
          <div className="empty-well">
            <h2>{currentStage?.label || "Pipeline"}</h2>
            <p>{currentStage?.empty || "Select a story."}</p>
          </div>
        </main>
      )}

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
