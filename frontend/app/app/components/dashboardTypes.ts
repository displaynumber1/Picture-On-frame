export type AutopostDashboardItem = {
  id: number;
  video_name: string;
  status: string;
  title?: string | null;
  hook_text?: string | null;
  cta_text?: string | null;
  hashtags?: string | null;
  score?: number | null;
  score_reasons?: string[] | null;
  next_check_at?: string | null;
  scheduled_at?: string | null;
  status_note?: string | null;
  title_source?: string | null;
  hook_source?: string | null;
  cta_source?: string | null;
  hashtags_source?: string | null;
  credit_used?: number | null;
  score_details?: {
    feedback_delta?: number;
    feedback_summary?: string;
    feedback_reasons?: string[];
  } | null;
};

export type AdminAutopostLog = {
  id: number;
  user_id: string;
  video_name?: string;
  status: string;
  score?: number | null;
  created_at?: string;
  views?: number | null;
  likes?: number | null;
  comments?: number | null;
  shares?: number | null;
};

export type AutopostFeedbackWeights = {
  user_id: string;
  learning_strength: number;
  weights: {
    hook?: Record<string, number>;
    cta?: Record<string, number>;
    hashtag?: Record<string, number>;
  };
  global_weights?: {
    hook?: Record<string, number>;
    cta?: Record<string, number>;
    hashtag?: Record<string, number>;
  };
};

export type AdminSubscriptionInfo = {
  user_id: string;
  subscribed: boolean;
  trial_upload_remaining: number;
};

export type AdminAuditLog = {
  id: number;
  actor_user_id: string;
  actor_email?: string;
  action: string;
  target_user_id?: string | null;
  details?: Record<string, any> | null;
  created_at?: string;
};

export type AdminMidtransStatus = {
  midtrans_is_production: boolean;
  server_key_configured: boolean;
  client_key_configured: boolean;
  packages: Record<string, { price: number; coins: number }>;
};

export type MetricsUploadResult = {
  status: 'idle' | 'success' | 'error';
  message: string | null;
};

export type TrendsPreview = {
  total: number;
  rows: Array<{
    category: string | null;
    hashtag: string | null;
    weight: number | null;
  }>;
};

export type EngagementTemplates = {
  hooks: string[];
  ctas: string[];
  captions: string[];
  hashtags: string[];
};

export type AutopostInsights = {
  fatigue_alerts: Array<{ type: string; text: string }>;
  trend_decay: { status: string; delta: number };
  retention_summary: { dropoff_second: number | null; avg_retention: number[] };
  best_times: Array<{ hour: number; engagement_rate: number }>;
  recommendations: string[];
};
