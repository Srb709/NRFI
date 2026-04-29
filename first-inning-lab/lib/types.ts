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
  nrfi_probability: number;
  yrfi_probability: number;
  lean: Lean;
  public_label: string;
  confidence_tier?: ConfidenceTier;
  reasons: string[];
  warnings: string[];
  created_at?: string;
};

export type PublicResult = {
  date: string;
  game: string;
  posted_label: string;
  model_lean: Lean;
  result: 'NRFI' | 'YRFI';
  win_loss: 'W' | 'L' | 'PUSH' | 'PASS';
  note?: string;
};

export type GeneratedContent = {
  dailyBoard: string;
  cleanSetupPost: string;
  yrfiSmokePost: string;
  trapWatchPost: string;
  resultsRecapTemplate: string;
  discord: string;
};
