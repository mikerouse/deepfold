"use client";

import { useEffect, useRef, useState } from "react";
import { searchOutlets } from "../lib/api";
import { CAN_ADD_TITLES, VISIBLE_PLATFORMS } from "../lib/story";
import type { Outlet, PlatformChip } from "../lib/types";

type Props = {
  platforms: PlatformChip[];
  selectedIds: string[];
  stage?: string | null;
  busy?: boolean;
  onAdd?: (outlet: Outlet) => void;
};

export default function PlatformChips({ platforms, selectedIds, stage, busy, onAdd }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<Outlet[]>([]);
  const box = useRef<HTMLDivElement>(null);
  const selected = new Set(selectedIds);
  const visible = expanded ? platforms : platforms.slice(0, VISIBLE_PLATFORMS);
  const hidden = Math.max(0, platforms.length - VISIBLE_PLATFORMS);
  const canAdd = Boolean(onAdd) && CAN_ADD_TITLES.has(stage || "");

  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(() => {
      void (async () => {
        if (!query.trim()) {
          setHits([]);
          return;
        }
        const rows = await searchOutlets({ q: query, limit: 8 });
        setHits(rows.filter((row) => !selected.has(row.id)));
      })();
    }, 160);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, open, selected.size]);

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (box.current && !box.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="plats" onClick={(e) => e.stopPropagation()}>
      {visible.map((chip, index) => (
        <span className="plat" key={`${chip.kind}-${chip.label}-${index}`}>
          <span className="plat-kind">{chip.kind === "web" ? "Web" : "Social"}</span>
          <span className="plat-label">{chip.label}</span>
        </span>
      ))}
      {hidden > 0 && !expanded ? (
        <button
          type="button"
          className="plat-more"
          onClick={() => setExpanded(true)}
          aria-label={`Show ${hidden} more platforms`}
        >
          +{hidden}
        </button>
      ) : null}
      {expanded && hidden > 0 ? (
        <button type="button" className="plat-more" onClick={() => setExpanded(false)}>
          Less
        </button>
      ) : null}
      {canAdd ? (
        <div className="plat-add" ref={box}>
          <button
            type="button"
            className="plat-more"
            disabled={busy}
            onClick={() => setOpen((v) => !v)}
          >
            Add title
          </button>
          {open ? (
            <div className="title-pop plat-pop" role="listbox">
              <input
                autoFocus
                className="title-q"
                value={query}
                placeholder="Search titles"
                aria-label="Add a title"
                onChange={(e) => setQuery(e.target.value)}
              />
              {hits.length === 0 && query.trim() ? <p className="notes">No titles match.</p> : null}
              {!query.trim() ? <p className="notes">Type a town or title. Packages live in the story.</p> : null}
              {hits.map((outlet) => (
                <button
                  key={outlet.id}
                  type="button"
                  className="suggest-line"
                  onClick={() => {
                    onAdd?.(outlet);
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  {outlet.name}
                  <span>{[outlet.town, outlet.county || outlet.region].filter(Boolean).join(" · ")}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
