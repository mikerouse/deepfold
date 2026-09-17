"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import type { DraftDetail, MediaAsset } from "../lib/types";

type ReasonMode = "reject" | "request_changes" | "no_go";
type MenuId = "story" | "draft" | "image" | "titles" | "publish" | "social" | null;

type Props = {
  stage: string;
  draft: DraftDetail;
  busy: boolean;
  generating: boolean;
  featured?: MediaAsset;
  demoWorker: boolean;
  railOpen: boolean;
  titlesPanel: ReactNode;
  socialPanel: ReactNode;
  onToggleRail: () => void;
  onRun: (action: string, extra?: Record<string, unknown>) => void;
  onOpenReason: (mode: ReasonMode) => void;
};

type Item = {
  id: string;
  label: string;
  action?: string;
  reason?: ReasonMode;
  disabled?: boolean;
  danger?: boolean;
  hint?: string;
};

function Menu({
  id,
  label,
  open,
  wide,
  onToggle,
  children,
}: {
  id: MenuId;
  label: string;
  open: boolean;
  wide?: boolean;
  onToggle: (id: MenuId) => void;
  children: ReactNode;
}) {
  return (
    <div className="ribbon-menu">
      <button
        type="button"
        className="ribbon-menu-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => onToggle(open ? null : id)}
      >
        {label}
      </button>
      {open ? (
        <div className={`ribbon-drop${wide ? " wide" : ""}`} role="menu">
          {children}
        </div>
      ) : null}
    </div>
  );
}

function MenuItems({
  items,
  busy,
  onRun,
  onOpenReason,
  onDone,
}: {
  items: Item[];
  busy: boolean;
  onRun: (action: string) => void;
  onOpenReason: (mode: ReasonMode) => void;
  onDone: () => void;
}) {
  if (items.length === 0) {
    return <p className="ribbon-empty">Nothing in this menu at this stage.</p>;
  }
  return (
    <>
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          role="menuitem"
          className={`ribbon-item${item.danger ? " danger" : ""}`}
          disabled={busy || item.disabled}
          onClick={() => {
            if (item.reason) {
              onOpenReason(item.reason);
              onDone();
              return;
            }
            if (item.action) {
              onRun(item.action);
              onDone();
            }
          }}
        >
          <span>{item.label}</span>
          {item.hint ? <small>{item.hint}</small> : null}
        </button>
      ))}
    </>
  );
}

export default function StoryRibbon({
  stage,
  draft,
  busy,
  generating,
  featured,
  demoWorker,
  railOpen,
  titlesPanel,
  socialPanel,
  onToggleRail,
  onRun,
  onOpenReason,
}: Props) {
  const [menu, setMenu] = useState<MenuId>(null);
  const bar = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (bar.current && !bar.current.contains(event.target as Node)) setMenu(null);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setMenu(null);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const storyItems: Item[] = [];
  if (stage === "pitch") {
    storyItems.push({ id: "go", label: "Go", action: "go", hint: "Queue draft, image and title jobs for Grok Bot" });
    if (draft.parked) {
      storyItems.push({ id: "unleave", label: "Unpark", action: "unleave" });
    } else {
      storyItems.push({ id: "leave", label: "Leave on Pitch", action: "leave", hint: "Park on the spike — not a kill" });
    }
    storyItems.push({ id: "no_go", label: "No-go…", reason: "no_go", danger: true, hint: "Archive with a reason" });
  } else {
        storyItems.push({
          id: "return",
          label: "Back to pitch",
          action: "return_to_pitch",
          disabled: stage !== "drafting" && stage !== "checking",
        });
  }

  const draftItems: Item[] = [];
  if (stage === "drafting" || stage === "checking") {
    draftItems.push({
      id: "rewrite",
      label: "Request rewrite",
      action: "request_rewrite",
      hint: "Queue another draft_article job",
    });
    draftItems.push({ id: "tweak", label: "Save copy", action: "tweak", disabled: generating });
  }

  const publishItems: Item[] = [];
  if (stage === "drafting") {
    publishItems.push({
      id: "check",
      label: "Send to checking",
      action: "send_to_checking",
      disabled: generating || !draft.draft_ready,
    });
  }
  if (stage === "checking") {
    publishItems.push({ id: "cms", label: "Create WordPress drafts", action: "approve_create_cms_drafts" });
    publishItems.push({ id: "changes", label: "Request changes…", reason: "request_changes" });
    publishItems.push({ id: "reject", label: "Reject…", reason: "reject", danger: true });
    publishItems.push({ id: "hold", label: "Hold", action: "hold" });
  }
  if (stage === "publication") {
    publishItems.push({ id: "social", label: "Send to social", action: "advance_to_social" });
  }

  const status = (draft.worker_labels && draft.worker_labels.length > 0
    ? draft.worker_labels.join(" · ")
    : null) || (generating ? "Queued for drafting" : null);

  let primary: { label: string; action: string; disabled?: boolean; danger?: boolean } | null = null;
  if (stage === "pitch") primary = { label: "Go", action: "go" };
  if (stage === "drafting") {
    primary = { label: "Send to checking", action: "send_to_checking", disabled: generating || !draft.draft_ready };
  }
  if (stage === "checking") primary = { label: "Create WP drafts", action: "approve_create_cms_drafts" };
  if (stage === "publication") primary = { label: "Send to social", action: "advance_to_social" };

  const versions = draft.versions || [];
  const imageJob = (draft.jobs || []).find((job) => job.kind === "featured_image");
  const imageOpen = imageJob && (imageJob.status === "queued" || imageJob.status === "claimed");

  return (
    <div className="ribbon" ref={bar} role="menubar" aria-label="Story">
      <Menu id="story" label="Story" open={menu === "story"} onToggle={setMenu}>
        <MenuItems items={storyItems} busy={busy} onRun={onRun} onOpenReason={onOpenReason} onDone={() => setMenu(null)} />
      </Menu>
      <Menu id="draft" label="Draft" open={menu === "draft"} onToggle={setMenu}>
        <MenuItems items={draftItems} busy={busy} onRun={onRun} onOpenReason={onOpenReason} onDone={() => setMenu(null)} />
        {versions.length > 0 ? (
          <div className="ribbon-history">
            <p>Versions</p>
            {versions.slice(0, 8).map((version) => (
              <p key={`${version.version_number}-${version.created_at}`}>
                v{version.version_number} · {version.created_by.split("@")[0]} ·{" "}
                {new Date(version.created_at).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}
              </p>
            ))}
          </div>
        ) : (
          <p className="ribbon-empty">No versions yet — they appear when Grok Bot files a spine.</p>
        )}
      </Menu>
      <Menu id="image" label="Image" open={menu === "image"} onToggle={setMenu}>
        <button
          type="button"
          role="menuitem"
          className="ribbon-item"
          disabled={busy || Boolean(imageOpen) || stage === "pitch"}
          onClick={() => {
            onRun("queue_featured_image");
            setMenu(null);
          }}
        >
          <span>Queue featured plate</span>
          <small>featured_image job for Grok Bot</small>
        </button>
        {featured ? (
          <div className="ribbon-history">
            <p>Caption</p>
            <p>{featured.caption || "—"}</p>
            <p>Alt · {featured.alt_text || "—"}</p>
            <p>{featured.credit}</p>
            {featured.prompt_version ? <p>Brief {featured.prompt_version}</p> : null}
          </div>
        ) : (
          <p className="ribbon-empty">
            {imageOpen ? "Plate job is open. The still appears here when a MediaAsset is filed." : "No featured plate yet."}
          </p>
        )}
      </Menu>
      <Menu id="titles" label="Titles" open={menu === "titles"} wide onToggle={setMenu}>
        <div className="ribbon-panel">{titlesPanel}</div>
      </Menu>
      <Menu id="publish" label="Publish" open={menu === "publish"} onToggle={setMenu}>
        <MenuItems items={publishItems} busy={busy} onRun={onRun} onOpenReason={onOpenReason} onDone={() => setMenu(null)} />
      </Menu>
      <Menu id="social" label="Social" open={menu === "social"} wide onToggle={setMenu}>
        <div className="ribbon-panel">
          {stage === "social" || (draft.social_posts || []).length > 0 ? (
            socialPanel
          ) : (
            <p className="ribbon-empty">Social stubs appear after Send to social. Connectors are not wired yet.</p>
          )}
        </div>
      </Menu>

      <div className="ribbon-end">
        {status ? (
          <p className="ribbon-status" aria-live="polite">
            {status}
            {demoWorker ? <span className="ribbon-demo"> · Simulating Grok Bot</span> : null}
          </p>
        ) : demoWorker ? (
          <p className="ribbon-status">
            <span className="ribbon-demo">Simulating Grok Bot</span>
          </p>
        ) : null}
        {primary ? (
          <button
            type="button"
            className="btn primary ribbon-primary"
            disabled={busy || primary.disabled}
            onClick={() => onRun(primary!.action)}
          >
            {primary.label}
          </button>
        ) : null}
        <button type="button" className={`ribbon-info${railOpen ? " on" : ""}`} onClick={onToggleRail}>
          Info
        </button>
      </div>
    </div>
  );
}
