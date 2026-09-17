"use client";

import { useEffect, useRef, useState } from "react";
import { searchOutlets } from "../lib/api";
import type { Outlet } from "../lib/types";

type Props = {
  focus: Outlet | null;
  onChange: (outlet: Outlet | null) => void;
};

export default function FocusTitles({ focus, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<Outlet[]>([]);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(() => {
      void (async () => {
        const rows = await searchOutlets({ q: query, limit: 8 });
        setHits(rows);
      })();
    }, 160);
    return () => clearTimeout(handle);
  }, [query, open]);

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (box.current && !box.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="focus-titles" ref={box}>
      <dt>Titles</dt>
      <dd>
        <button type="button" className="focus-btn" onClick={() => setOpen((v) => !v)}>
          {focus ? focus.name : "All titles"}
        </button>
        {focus ? (
          <button type="button" className="chip-x" aria-label="Show all titles" onClick={() => onChange(null)}>
            ×
          </button>
        ) : null}
      </dd>
      {open ? (
        <div className="title-pop focus-pop">
          <input
            autoFocus
            id="focus-title-search"
            name="focus-title-search"
            className="title-q"
            value={query}
            placeholder="Focus a title"
            aria-label="Focus a title"
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="button"
            className="suggest-line"
            onClick={() => {
              onChange(null);
              setOpen(false);
              setQuery("");
            }}
          >
            All titles
            <span>Publisher-wide spike</span>
          </button>
          {hits.map((outlet) => (
            <button
              key={outlet.id}
              type="button"
              className="suggest-line"
              onClick={() => {
                onChange(outlet);
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
  );
}
