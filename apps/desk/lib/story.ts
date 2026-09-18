import type { DraftListItem, Job, PipelineStage } from "./types";

export const VISIBLE_PLATFORMS = 3;

export const CAN_ADD_TITLES = new Set(["pitch", "drafting", "checking", "publication"]);

export function groupByStage(rows: DraftListItem[], stages: PipelineStage[], stageFilter: string) {
  const groups = stages.map((stage) => ({
    ...stage,
    items: rows.filter((row) => row.pipeline_stage === stage.id),
  }));
  if (stageFilter) return groups.filter((group) => group.id === stageFilter);
  return groups;
}

export function openJobs(jobs: Job[] | undefined) {
  return (jobs || []).filter((job) => job.status === "queued" || job.status === "claimed");
}

export function houseStyleNote(jobs: Job[] | undefined): string | null {
  const job = openJobs(jobs).find((row) => row.kind === "draft_article");
  if (!job) return null;
  const payload = job.payload || {};
  const label = typeof payload.house_style_label === "string" ? payload.house_style_label.trim() : "";
  if (label) return `House style: ${label}`;
  const version = typeof payload.brief_version === "string" ? payload.brief_version : "";
  if (version === "draft_article_conservative_post_v1") return "House style: Conservative Post v1";
  if (version === "draft_article_local_v1") return "House style: Local craft v1";
  return null;
}

export function stageMarks(item: DraftListItem) {
  const stage = item.pipeline_stage || "";
  const marks: { text: string; tone?: string }[] = [];
  if (item.parked) marks.push({ text: "Left", tone: "left" });
  if (item.worker_status) marks.push({ text: item.worker_status, tone: "worker" });
  if (item.status === "changes_requested") marks.push({ text: "Changes", tone: "changes_requested" });
  if (item.status === "held") marks.push({ text: "Held", tone: "held" });
  if (stage && stage !== "pitch" && item.verification_status !== "verified") {
    marks.push({
      text: item.verification_status.replaceAll("_", " "),
      tone: item.verification_status,
    });
  }
  return marks.slice(0, 2);
}
