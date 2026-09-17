"use client";

import { useEffect, useRef, useState } from "react";
import { outletFacets, searchOutlets, suggestOutlets } from "../lib/api";
import type { Outlet, OutletPackage, PublishTarget } from "../lib/types";

type Props = {
  draftId: string;
  stage: string;
  targets: PublishTarget[];
  extras: Outlet[];
  selected: Record<string, boolean>;
  grafs: Record<string, string>;
  busy: boolean;
  onSelected: (next: Record<string, boolean>) => void;
  onGrafs: (next: Record<string, string>) => void;
  onCatalog: (outlet: Outlet) => void;
  onSave: () => void;
};

export default function TitlePicker({
  draftId,
  stage,
  targets,
  extras,
  selected,
  grafs,
  busy,
  onSelected,
  onGrafs,
  onCatalog,
  onSave,
}: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [hits, setHits] = useState<Outlet[]>([]);
  const [suggested, setSuggested] = useState<Outlet[]>([]);
  const [packages, setPackages] = useState<OutletPackage[]>([]);
  const [county, setCounty] = useState("");
  const [counties, setCounties] = useState<string[]>([]);
  const box = useRef<HTMLDivElement>(null);

  const selectedIds = new Set(Object.entries(selected).filter(([, on]) => on).map(([id]) => id));
  const byId = new Map<string, Outlet>();
  for (const t of targets) byId.set(t.outlet.id, t.outlet);
  for (const extra of extras) byId.set(extra.id, extra);
  const selectedOutlets = [...selectedIds].map((id) => byId.get(id)).filter((row): row is Outlet => Boolean(row));

  useEffect(() => {
    void (async () => {
      try {
        const [suggest, facets] = await Promise.all([suggestOutlets(draftId), outletFacets()]);
        setSuggested(suggest.outlets);
        setPackages(suggest.packages);
        setCounties(facets.counties);
      } catch {
        setSuggested([]);
      }
    })();
  }, [draftId]);

  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(() => {
      void (async () => {
        const rows = await searchOutlets({ q: query, county: county || undefined, limit: 8 });
        setHits(rows.filter((row) => !selectedIds.has(row.id)));
      })();
    }, 160);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, county, open, draftId, selectedIds.size]);

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (box.current && !box.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  function addOutlet(outlet: Outlet) {
    onCatalog(outlet);
    onSelected({ ...selected, [outlet.id]: true });
    if (!grafs[outlet.id]) {
      onGrafs({ ...grafs, [outlet.id]: "" });
    }
    setQuery("");
    setOpen(false);
  }

  function addPackage(pack: OutletPackage) {
    const nextSel = { ...selected };
    const nextGrafs = { ...grafs };
    for (const outlet of pack.outlets) {
      onCatalog(outlet);
      nextSel[outlet.id] = true;
      if (!nextGrafs[outlet.id]) nextGrafs[outlet.id] = "";
    }
    onSelected(nextSel);
    onGrafs(nextGrafs);
  }

  function remove(id: string) {
    onSelected({ ...selected, [id]: false });
  }

  const publication = stage === "publication";

  return (
    <section>
      <h2>{publication ? "CMS titles" : "Titles"}</h2>
      <div className="chips">
        {selectedOutlets.map((outlet) => (
          <span className="chip" key={outlet.id}>
            {outlet.name}
            <button type="button" className="chip-x" aria-label={`Remove ${outlet.name}`} onClick={() => remove(outlet.id)}>
              ×
            </button>
          </span>
        ))}
      </div>

      {suggested.length > 0 ? (
        <div className="suggest-block">
          <p className="notes">Suggested from the pitch geography</p>
          {suggested.map((outlet) => (
            <button
              key={outlet.id}
              type="button"
              className="suggest-line"
              disabled={busy || selectedIds.has(outlet.id)}
              onClick={() => addOutlet(outlet)}
            >
              {outlet.name}
              <span>{[outlet.town, outlet.county].filter(Boolean).join(", ")}</span>
            </button>
          ))}
        </div>
      ) : null}

      {packages.length > 0 ? (
        <div className="suggest-block">
          <p className="notes">Packages</p>
          {packages.map((pack) => (
            <button key={pack.id} type="button" className="suggest-line" disabled={busy} onClick={() => addPackage(pack)}>
              {pack.name}
              <span>Add {pack.outlets.length}</span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="title-search" ref={box}>
        <button type="button" className="add-title" onClick={() => setOpen(true)}>
          Add title…
        </button>
        {open ? (
          <div className="title-pop" role="listbox">
            <input
              autoFocus
              className="title-q"
              value={query}
              placeholder="Search titles"
              aria-label="Search titles"
              onChange={(e) => setQuery(e.target.value)}
            />
            {counties.length > 0 ? (
              <select className="title-filter" value={county} onChange={(e) => setCounty(e.target.value)} aria-label="County">
                <option value="">All counties</option>
                {counties.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            ) : null}
            {hits.length === 0 ? <p className="notes">No titles match.</p> : null}
            {hits.map((outlet) => (
              <button key={outlet.id} type="button" className="suggest-line" onClick={() => addOutlet(outlet)}>
                {outlet.name}
                <span>{[outlet.town, outlet.county || outlet.region].filter(Boolean).join(" · ")}</span>
              </button>
            ))}
          </div>
        ) : null}
      </div>

      {!publication
        ? selectedOutlets.map((outlet) => (
            <label className="outlet" key={outlet.id}>
              <header>
                <strong>{outlet.name}</strong>
              </header>
              <div className="brief">{outlet.localisation_brief}</div>
              <textarea
                className="graf-input"
                rows={3}
                value={grafs[outlet.id] || ""}
                onChange={(e) => onGrafs({ ...grafs, [outlet.id]: e.target.value })}
              />
            </label>
          ))
        : selectedOutlets.map((outlet) => {
            const t = targets.find((row) => row.outlet.id === outlet.id);
            return (
              <p className="notes" key={outlet.id}>
                {outlet.name} · CMS {t?.cms_status || "pending"}
                {t?.remote_post_id ? ` · ${t.remote_post_id}` : ""}
                {t?.last_error ? ` · ${t.last_error}` : ""}
              </p>
            );
          })}

      {stage === "drafting" || stage === "checking" ? (
        <button type="button" className="btn quiet" disabled={busy} onClick={onSave}>
          Save titles
        </button>
      ) : null}
    </section>
  );
}
