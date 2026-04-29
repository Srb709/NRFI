import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fallbackGames, fallbackPredictions, fallbackResults } from './demo-data';
import { BoardMetadata, Game, LiveResult, Prediction, PublicResult } from './types';

const dataDir = path.join(process.cwd(), 'data');

const defaultMeta: BoardMetadata = {
  source: 'demo', generatedAt: null, boardStatus: 'DEMO_FALLBACK', isDemo: true, warnings: ['Live local board unavailable.'],
};

const VALID_LEANS: PublicResult['model_lean'][] = ['NRFI', 'YRFI', 'PASS'];
const VALID_RESULTS: PublicResult['result'][] = ['NRFI', 'YRFI', 'PENDING', 'UNKNOWN'];
const VALID_WIN_LOSS: PublicResult['win_loss'][] = ['W', 'L', 'PASS', 'PENDING', 'UNKNOWN'];

async function readJson<T>(fileName: string): Promise<T | null> {
  try { return JSON.parse(await fs.readFile(path.join(dataDir, fileName), 'utf-8')) as T; } catch { return null; }
}
const arr = <T>(v: unknown): T[] => Array.isArray(v) ? v as T[] : [];

let cacheMeta: BoardMetadata = defaultMeta;

function normalizeGame(game: Partial<Game> & Record<string, unknown>): Game {
  const awayTeam = (game.away_team as string) ?? 'Away';
  const homeTeam = (game.home_team as string) ?? 'Home';
  const awayProbable = (game.away_probable_pitcher as string) ?? 'TBD';
  const homeProbable = (game.home_probable_pitcher as string) ?? 'TBD';
  return {
    game_id: (game.game_id as string) ?? String(game.game_pk ?? ''),
    game: (game.game as string) ?? `${awayTeam} @ ${homeTeam}`,
    game_date: (game.game_date as string) ?? '',
    start_time: (game.start_time as string) ?? 'Time TBD',
    away_team: awayTeam,
    home_team: homeTeam,
    venue: game.venue as string | undefined,
    away_pitcher: (game.away_pitcher as string) ?? awayProbable,
    home_pitcher: (game.home_pitcher as string) ?? homeProbable,
    status: game.status as string | undefined,
  };
}

export async function getGames(): Promise<Game[]> {
  const board = await readJson<Record<string, unknown>>('live/today_board.json');
  if (board) {
    cacheMeta = { source:'live_local', generatedAt:(board.generated_at as string) ?? null, boardStatus:(board.board_status as string) ?? 'EARLY_BOARD', isDemo:false, warnings:arr<string>(board.warnings), summary:board.summary as BoardMetadata['summary'] };
    const games = arr<Record<string, unknown>>(board.games).map(normalizeGame);
    if (games.length) return games;
  }
  const games = await readJson<Array<Partial<Game> & Record<string, unknown>>>('live/today_games.json');
  if (games?.length) { cacheMeta = { ...cacheMeta, source:'live_local', isDemo:false, boardStatus: cacheMeta.boardStatus || 'EARLY_BOARD' }; return games.map(normalizeGame); }
  cacheMeta = defaultMeta;
  return (await readJson<Game[]>('demo-games.json')) ?? fallbackGames;
}

export async function getPredictions(): Promise<Prediction[]> {
  const board = await readJson<Record<string, unknown>>('live/today_board.json');
  if (board) {
    const predictions = arr<Prediction>(board.predictions);
    if (predictions.length) return predictions;
  }
  const preds = await readJson<Prediction[]>('live/today_predictions.json');
  if (preds?.length) return preds;
  return (await readJson<Prediction[]>('demo-predictions.json')) ?? fallbackPredictions;
}

function normalizeResult(row: LiveResult | PublicResult): PublicResult {
  const leanRaw = (row as LiveResult).lean ?? (row as PublicResult).model_lean;
  const resultRaw = (row as LiveResult).result ?? (row as PublicResult).result;
  const winLossRaw = (row as LiveResult).outcome ?? (row as PublicResult).win_loss;

  const lean: PublicResult['model_lean'] = VALID_LEANS.includes(leanRaw as PublicResult['model_lean']) ? (leanRaw as PublicResult['model_lean']) : 'PASS';
  const result: PublicResult['result'] = VALID_RESULTS.includes(resultRaw as PublicResult['result']) ? (resultRaw as PublicResult['result']) : 'UNKNOWN';
  const winLoss: PublicResult['win_loss'] = VALID_WIN_LOSS.includes(winLossRaw as PublicResult['win_loss']) ? (winLossRaw as PublicResult['win_loss']) : 'UNKNOWN';

  const awayRuns1st = (row as LiveResult).away_runs_1st;
  const homeRuns1st = (row as LiveResult).home_runs_1st;
  const firstInningNote = typeof awayRuns1st === 'number' && typeof homeRuns1st === 'number'
    ? `1st inning: ${awayRuns1st}-${homeRuns1st}`
    : undefined;

  return {
    date: (row as LiveResult).date ?? (row as PublicResult).date ?? new Date().toISOString().slice(0, 10),
    game: (row as LiveResult).game ?? (row as PublicResult).game ?? (row as LiveResult).game_id ?? 'Unknown game',
    posted_label: (row as PublicResult).posted_label ?? 'Model board',
    model_lean: lean,
    result,
    win_loss: winLoss,
    note: (row as PublicResult).note ?? firstInningNote,
  };
}

export async function getResults(): Promise<PublicResult[]> {
  const live = await readJson<LiveResult[]>('live/today_results.json');
  if (live?.length) return live.map(normalizeResult);

  const updatesRaw = await readJson<LiveResult[] | { date?: string; results?: LiveResult[] }>('live/public_record_updates.json');
  const updates = Array.isArray(updatesRaw) ? updatesRaw : arr<LiveResult>(updatesRaw?.results);
  if (updates.length) return updates.map(normalizeResult);

  const record = await readJson<PublicResult[]>('public-record.json');
  if (record?.length) return record.map(normalizeResult);
  return fallbackResults.map(normalizeResult);
}

export async function getBoardMetadata(): Promise<BoardMetadata> {
  await getGames();
  return cacheMeta;
}
