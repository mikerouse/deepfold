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
  region: string;
  cms_kind: string;
  cms_base_url: string;
  default_selected: boolean;
  active: boolean;
  localisation_brief: string;
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
  image_label: string | null;
  created_at: string;
  updated_at: string;
};

export type DraftDetail = DraftListItem & {
  byline: string;
  source_links: SourceLink[];
  spine_body: string;
  media: MediaAsset[];
  social_posts: SocialPost[];
  targets: PublishTarget[];
  decisions: Decision[];
  confidence: Confidence;
  flags: {
    kill_switch: boolean;
    approve_and_publish_enabled: boolean;
    wp_live: boolean;
  };
  is_pitch: boolean;
};

export type DeskSettings = {
  approve_and_publish_enabled: boolean;
  kill_switch: boolean;
  wp_live: boolean;
  default_actor: string;
  product: string;
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
