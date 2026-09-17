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
