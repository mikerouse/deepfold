"use client";

import { groupByStage, stageMarks } from "../lib/story";
import type { DraftListItem, Outlet, PipelineStage } from "../lib/types";
import PlatformChips from "./PlatformChips";

type Props = {
  rows: DraftListItem[];
  stages: PipelineStage[];
  stageFilter: string;
  loaded: boolean;
  busy: boolean;
  onOpen: (id: string) => void;
  onAddTitle: (item: DraftListItem, outlet: Outlet) => void;
};

export default function StoryList({ rows, stages, stageFilter, loaded, busy, onOpen, onAddTitle }: Props) {
  const groups = groupByStage(rows, stages, stageFilter);
  const empty = loaded && rows.length === 0;

  return (
    <div className="stories" aria-label="Stories by stage">
      {!loaded ? <p className="group-empty">Loading the spike…</p> : null}
      {empty ? (
        <p className="empty-well">
          <span className="kicker">Stories</span>
          <br />
          Nothing matches these filters. Clear county or package to see the spike.
        </p>
      ) : null}
      {loaded && !empty
        ? groups.map((group) => (
        <section className="story-group" key={group.id} aria-labelledby={`stage-${group.id}`}>
          <header className="story-group-head">
            <h2 id={`stage-${group.id}`}>
              {group.label}
              <span>{group.items.length}</span>
            </h2>
          </header>
          {group.items.length === 0 ? (
            <p className="group-empty">{group.empty}</p>
          ) : (
            <>
              <div className="story-head" aria-hidden="true">
                <span>Description</span>
                <span>Need</span>
                <span>Titles / platforms</span>
                <span>Stage</span>
              </div>
              {group.items.map((item) => {
                const marks = stageMarks(item);
                return (
                  <div
                    key={item.id}
                    className="story-row"
                    role="link"
                    tabIndex={0}
                    onClick={() => onOpen(item.id)}
                    onKeyDown={(event) => {
                      if (event.key !== "Enter" && event.key !== " ") return;
                      if ((event.target as HTMLElement).closest("button, input, select, a")) return;
                      event.preventDefault();
                      onOpen(item.id);
                    }}
                  >
                    <div className="story-desc">
                      <h3>{item.headline}</h3>
                      <p>{item.standfirst}</p>
                    </div>
                    <div className="story-need">{item.user_need || "—"}</div>
                    <PlatformChips
                      platforms={item.platforms || []}
                      selectedIds={item.selected_outlet_ids || []}
                      stage={item.pipeline_stage}
                      busy={busy}
                      onAdd={(outlet) => onAddTitle(item, outlet)}
                    />
                    <div className="story-stage">
                      <span className="story-stage-name">{group.label}</span>
                      {marks.map((mark) => (
                        <span className={`mark ${mark.tone || ""}`.trim()} key={mark.text}>
                          {mark.text}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </section>
      ))
        : null}
    </div>
  );
}
