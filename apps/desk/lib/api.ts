import type {
  DecisionPayload,
  DeskSettings,
  DraftDetail,
  DraftListItem,
  Outlet,
  OutletPackage,
  Pipeline,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function apiBase() {
  return API_BASE;
}

function withOutlet(path: string, outletId?: string | null) {
  if (!outletId) return path;
  const join = path.includes("?") ? "&" : "?";
  return `${path}${join}outlet_id=${encodeURIComponent(outletId)}`;
}

export function listDrafts(opts?: {
  stage?: string;
  outletId?: string | null;
  platform?: string;
  packageId?: string;
  county?: string;
}) {
  const query = new URLSearchParams();
  if (opts?.stage) query.set("stage", opts.stage);
  if (opts?.platform) query.set("platform", opts.platform);
  if (opts?.packageId) query.set("package_id", opts.packageId);
  if (opts?.county) query.set("county", opts.county);
  const suffix = query.toString() ? `?${query}` : "";
  return request<DraftListItem[]>(withOutlet(`/drafts${suffix}`, opts?.outletId));
}

export function getPipeline(outletId?: string | null) {
  return request<Pipeline>(withOutlet("/pipeline", outletId));
}

export function getDraft(id: string) {
  return request<DraftDetail>(`/drafts/${id}`);
}

export function recordDecision(id: string, payload: DecisionPayload) {
  return request<DraftDetail>(`/drafts/${id}/decisions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSettings() {
  return request<DeskSettings>("/settings");
}

export function searchOutlets(params: { q?: string; region?: string; county?: string; limit?: number }) {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.region) query.set("region", params.region);
  if (params.county) query.set("county", params.county);
  if (params.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query}` : "";
  return request<Outlet[]>(`/outlets${suffix}`);
}

export function listPackages() {
  return request<OutletPackage[]>("/outlets/packages");
}

export function outletFacets() {
  return request<{ regions: string[]; counties: string[] }>("/outlets/facets");
}

export function suggestOutlets(draftId: string) {
  return request<{ outlets: Outlet[]; packages: OutletPackage[] }>(
    `/outlets/suggest?draft_id=${encodeURIComponent(draftId)}`,
  );
}
