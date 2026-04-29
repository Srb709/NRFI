import { getLeanDisplay } from './labels';
import { Game, GeneratedContent, Prediction } from './types';

const BANNED_PHRASES = [
  'guaranteed winner',
  'lock',
  'max bet',
  'hammer',
  'mortgage',
  'free money',
  'can’t lose',
  'cant lose',
  'risk-free',
  'risk free',
  'sure thing'
];

export function sanitizeGeneratedContent(content: string): string {
  let sanitized = content;
  for (const phrase of BANNED_PHRASES) {
    const pattern = new RegExp(phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    sanitized = sanitized.replace(pattern, 'high-confidence angle');
  }
  return sanitized;
}

export function validateGeneratedContent(content: string): { safe: boolean; reason?: string } {
  const lower = content.toLowerCase();
  const match = BANNED_PHRASES.find((phrase) => lower.includes(phrase));
  if (match) {
    return { safe: false, reason: `Blocked phrase detected: ${match}` };
  }
  return { safe: true };
}

function finalizeBlock(block: string): string {
  const sanitized = sanitizeGeneratedContent(block);
  const safety = validateGeneratedContent(sanitized);
  if (safety.safe) return sanitized;
  return 'Content held for review due to guardrail policy. No guarantees. Just the board.';
}

export function generateContent(games: Game[], predictions: Prediction[]): GeneratedContent {
  const gameMap = new Map(games.map((g) => [g.game_id, g]));
  const withGame = predictions.map((p) => ({ prediction: p, game: gameMap.get(p.game_id) })).filter((x) => x.game);

  const cleanSetups = withGame.filter((x) => ['Lab Favorite', 'Clean First Frame', 'Quiet Inning Candidate'].includes(x.prediction.public_label));
  const yrfiSmoke = withGame.filter((x) => x.prediction.public_label === 'YRFI Smoke');
  const trapWatch = withGame.filter((x) => ['Trap Watch', 'Chaos Zone', 'Stay Away Spot', 'Pass'].includes(x.prediction.public_label));

  const boardLines = withGame.slice(0, 10).map(({ prediction, game }) => `• ${game!.game} — ${prediction.public_label} (${getLeanDisplay(prediction.lean)})`);
  const cleanLines = cleanSetups.slice(0, 4).map(({ prediction, game }) => `• ${game!.game}: clean first-inning setup, model lean ${prediction.lean}, notes: ${prediction.reasons[0] ?? 'Stable run environment.'}`);
  const smokeLines = yrfiSmoke.slice(0, 3).map(({ prediction, game }) => `• ${game!.game}: first-inning smoke with top-of-order danger. Watch ${prediction.warnings[0] ?? 'early traffic risk'}.`);
  const trapLines = trapWatch.slice(0, 4).map(({ prediction, game }) => `• ${game!.game}: ${prediction.public_label} due to ${prediction.warnings[0] ?? 'walk-risk flag'}.`);

  return {
    dailyBoard: finalizeBlock(`First Inning Lab — Daily Board\n${boardLines.join('\n')}\n\nModel-based baseball analysis only. No guarantees. Just the board.`),
    cleanSetupPost: finalizeBlock(`Clean Setup Watch\n${cleanLines.join('\n') || '• No clean first-inning setup cleared today.'}\n\nTrack lineups and weather before posting updates.`),
    yrfiSmokePost: finalizeBlock(`YRFI Smoke Watch\n${smokeLines.join('\n') || '• No elevated first-inning smoke flagged today.'}\n\nFocus on top-of-order danger and barrel-risk warning spots.`),
    trapWatchPost: finalizeBlock(`Trap Watch / Chaos Zone\n${trapLines.join('\n') || '• No trap-watch clusters on this board.'}\n\nRespect pass spots and avoid forcing volume.`),
    resultsRecapTemplate: finalizeBlock(`Results Recap Template\nDate: [YYYY-MM-DD]\nBoard size: [#]\nNRFI record: [W-L]\nYRFI record: [W-L]\nPass spots: [#]\nNotes: [lineup/news impact]\n\nEvery posted model lean stays in the tracker.`),
    discord: finalizeBlock(`Early Board (Discord Draft)\n${boardLines.slice(0, 6).join('\n')}\n\nThis is analysis for review only. No guarantees. Just the board.`)
  };
}
