export type Lean = 'NRFI' | 'YRFI' | 'PASS';

export type ConfidenceTier = 'A' | 'B' | 'C' | 'PASS';

export type Game = {
  game_id: string;
  game: string;
  game_date: string;
  start_time: string;
  away_team: string;
  home_team: string;
  venue?: string;
  away_pitcher?: string;
  home_pitcher?: string;
  status?: string;
};

export type Prediction = {
  game_id: string;
  model_version?: string;
  nrfi_probability: number | null;
  yrfi_probability: number | null;
  probability_available?: boolean;
  model_status?: string;
  probability_quality?: string;
  missing_data?: string[];
  feature_status?: Record<string, boolean>;
  lean: Lean;
  public_label: string;
  confidence_tier?: ConfidenceTier;
  reasons: string[];
  warnings: string[];
  created_at?: string;
  board_status?: string;
  data_quality_score?: number;
  feature_breakdown?: {
    pitcher_safety_score?: number;
    offense_danger_score?: number;
    park_weather_score?: number;
    certainty_score?: number;
    recent_form_score?: number;
  };
};

export type PublicResult = {
  date: string;
  game: string;
  posted_label: string;
  model_lean: Lean;
  result: 'NRFI' | 'YRFI' | 'PENDING' | 'UNKNOWN';
  win_loss: 'W' | 'L' | 'PUSH' | 'PASS' | 'PENDING' | 'UNKNOWN';
  note?: string;
};

export type LiveResult = {
  game_id?: string;
  game?: string;
  lean?: Lean;
  outcome?: 'W' | 'L' | 'PASS' | 'PENDING' | 'UNKNOWN';
  result?: 'NRFI' | 'YRFI' | 'PENDING' | 'UNKNOWN';
  away_runs_1st?: number | null;
  home_runs_1st?: number | null;
  total_runs_1st?: number | null;
  date?: string;
};

export type BoardMetadata = {
  source: 'live_local' | 'demo';
  resultsSource?: 'live' | 'public_record' | 'empty' | 'demo';
  generatedAt: string | null;
  boardStatus: string;
  isDemo: boolean;
  warnings: string[];
  summary?: {
    games?: number;
    nrfi_leans?: number;
    yrfi_leans?: number;
    passes?: number;
    low_confidence?: number;
    average_data_quality?: number | null;
  };
};

export type GeneratedContent = {
  dailyBoard: string;
  cleanSetupPost: string;
  yrfiSmokePost: string;
  trapWatchPost: string;
  resultsRecapTemplate: string;
  discord: string;
};
