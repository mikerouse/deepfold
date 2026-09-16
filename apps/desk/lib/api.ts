import type { DecisionPayload, DeskSettings, DraftDetail, DraftListItem } from "./types";

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

export function listDrafts() {
  return request<DraftListItem[]>("/drafts");
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
