export type SourceLink = {
  url: string;
  label: string;
  note?: string;
};

export type Outlet = {
  id: string;
  name: string;
  slug: string;
  town: string;
  county: string;
  region: string;
  cms_kind: string;
  cms_base_url: string;
  default_selected: boolean;
  active: boolean;
  localisation_brief: string;
};

export type OutletPackage = {
  id: string;
  name: string;
  slug: string;
  region: string;
  county: string;
  description: string;
  outlets: Outlet[];
};

export type Job = {
  id: string;
  draft_id: string;
  kind: string;
  status: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
  worker: string | null;
  error: string | null;
  claimed_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type MediaAsset = {
  id: string;
  role: string;
  caption: string;
  alt_text: string;
  credit: string;
  policy_tag: string;
  documentary_incident: boolean;
  placeholder_label: string;
  url?: string;
  prompt_version?: string;
};

export type SocialPost = {
  id: string;
  platform: string;
  body: string;
  edited_body: string | null;
  status: string;
};

export type PublishTarget = {
  id: string;
  outlet: Outlet;
  selected: boolean;
  local_headline: string;
  local_graf: string;
  cms_status: string;
  remote_post_id: string | null;
  last_error: string | null;
};

export type Decision = {
  id: string;
  actor: string;
  action: string;
  reason: string | null;
  diff: Record<string, unknown>;
  previous_status: string;
  new_status: string;
  created_at: string;
};

export type Confidence = {
  score: number;
  auto_draft_eligible: boolean;
  auto_publish_eligible: boolean;
  blocked_reasons: string[];
  notes: string[];
};

export type PlatformChip = {
  kind: "web" | "social" | string;
  label: string;
  outlet_id?: string | null;
  platform?: string | null;
};

export type DraftListItem = {
  id: string;
  headline: string;
  standfirst: string;
  slug: string;
  status: string;
  pipeline_stage: string | null;
  parked: boolean;
  verification_status: string;
  categories: string[];
  tags: string[];
  confidence_score: number;
  auto_draft_eligible: boolean;
  auto_publish_eligible: boolean;
  suggested_outlet_names: string[];
  platforms: PlatformChip[];
  user_need: string | null;
  selected_outlet_ids: string[];
  image_label: string | null;
  draft_ready: boolean;
  worker_status: string | null;
  worker_labels: string[];
  created_at: string;
  updated_at: string;
};

export type DraftVersion = {
  version_number: number;
  headline: string;
  created_by: string;
  created_at: string;
};

export type DraftDetail = DraftListItem & {
  byline: string;
  source_links: SourceLink[];
  geography: {
    regions?: string[];
    counties?: string[];
    towns?: string[];
  };
  spine_body: string;
  media: MediaAsset[];
  social_posts: SocialPost[];
  targets: PublishTarget[];
  decisions: Decision[];
  jobs: Job[];
  versions: DraftVersion[];
  confidence: Confidence;
  flags: {
    kill_switch: boolean;
    approve_and_publish_enabled: boolean;
    wp_live: boolean;
    demo_instant_fulfill?: boolean;
    demo_grok_worker?: boolean;
  };
  is_pitch: boolean;
  generating: boolean;
};

export type DeskSettings = {
  approve_and_publish_enabled: boolean;
  kill_switch: boolean;
  wp_live: boolean;
  default_actor: string;
  publisher_name: string;
  product: string;
  demo_instant_fulfill?: boolean;
  demo_grok_worker?: boolean;
};

export type PipelineStage = {
  id: string;
  label: string;
  hint: string;
  count: number;
  empty: string;
};

export type Pipeline = {
  stages: PipelineStage[];
};

export type DecisionPayload = {
  action: string;
  actor?: string;
  reason?: string;
  headline?: string;
  spine_body?: string;
  standfirst?: string;
  selected_outlet_ids?: string[];
  local_grafs?: Record<string, string>;
  social_post_id?: string;
  social_copy?: string;
};
