"use client";

import type { OutletPackage, PipelineStage } from "../lib/types";

type Props = {
  stages: PipelineStage[];
  stage: string;
  platform: string;
  county: string;
  packageId: string;
  counties: string[];
  packages: OutletPackage[];
  onStage: (value: string) => void;
  onPlatform: (value: string) => void;
  onCounty: (value: string) => void;
  onPackage: (value: string) => void;
};

export default function FiltersBar({
  stages,
  stage,
  platform,
  county,
  packageId,
  counties,
  packages,
  onStage,
  onPlatform,
  onCounty,
  onPackage,
}: Props) {
  const total = stages.reduce((sum, item) => sum + item.count, 0);
  return (
    <div className="filters" aria-label="Story filters">
      <div className="filter-cluster" role="tablist" aria-label="Stage">
        <span className="filter-kicker">Stage</span>
        <button
          type="button"
          className={`stage ${stage === "" ? "active" : ""}`}
          aria-current={stage === "" ? "page" : undefined}
          onClick={() => onStage("")}
        >
          <span className="stage-label">All</span>
          <span className={`stage-count${total === 0 ? " zero" : ""}`}>{total}</span>
        </button>
        {stages.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`stage ${stage === item.id ? "active" : ""}`}
            aria-current={stage === item.id ? "page" : undefined}
            onClick={() => onStage(item.id)}
          >
            <span className="stage-label">{item.label}</span>
            <span className={`stage-count${item.count === 0 ? " zero" : ""}`}>{item.count}</span>
          </button>
        ))}
      </div>
      <div className="filter-cluster" aria-label="Platform type">
        <span className="filter-kicker">Platform</span>
        {[
          { id: "", label: "All" },
          { id: "web", label: "Web" },
          { id: "social", label: "Social" },
        ].map((item) => (
          <button
            key={item.id || "all-platforms"}
            type="button"
            className={`stage ${platform === item.id ? "active" : ""}`}
            onClick={() => onPlatform(item.id)}
          >
            <span className="stage-label">{item.label}</span>
          </button>
        ))}
      </div>
      <label className="filter-field">
        <span>County</span>
        <select
          id="filter-county"
          name="filter-county"
          value={county}
          onChange={(e) => onCounty(e.target.value)}
          aria-label="County"
        >
          <option value="">All counties</option>
          {counties.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>
      <label className="filter-field">
        <span>Package</span>
        <select
          id="filter-package"
          name="filter-package"
          value={packageId}
          onChange={(e) => onPackage(e.target.value)}
          aria-label="Package"
        >
          <option value="">All packages</option>
          {packages.map((pack) => (
            <option key={pack.id} value={pack.id}>
              {pack.county || pack.name}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
