import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fallbackGames, fallbackPredictions, fallbackResults } from './demo-data';
import { BoardMetadata, Game, LiveResult, Prediction, PublicResult } from './types';

const dataDir = path.join(process.cwd(), 'data');

const defaultMeta: BoardMetadata = {
  source: 'demo', generatedAt: null, boardStatus: 'DEMO_FALLBACK', isDemo: true, warnings: ['Live local board unavailable.'],
};

async function readJson<T>(fileName: string): Promise<T | null> {
  try { return JSON.parse(await fs.readFile(path.join(dataDir, fileName), 'utf-8')) as T; } catch { return null; }
}
const arr = <T>(v: unknown): T[] => Array.isArray(v) ? v as T[] : [];

let cacheMeta: BoardMetadata = defaultMeta;

export async function getGames(): Promise<Game[]> {
  const board = await readJson<Record<string, unknown>>('live/today_board.json');
  if (board) {
    cacheMeta = { source:'live_local', generatedAt:(board.generated_at as string) ?? null, boardStatus:(board.board_status as string) ?? 'EARLY_BOARD', isDemo:false, warnings:arr<string>(board.warnings), summary:board.summary as BoardMetadata['summary'] };
    const games = arr<Game>(board.games);
    if (games.length) return games;
  }
  const games = await readJson<Game[]>('live/today_games.json');
  if (games?.length) { cacheMeta = { ...cacheMeta, source:'live_local', isDemo:false, boardStatus: cacheMeta.boardStatus || 'EARLY_BOARD' }; return games; }
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
  const lean = (row as LiveResult).lean ?? (row as PublicResult).model_lean ?? 'PASS';
  const result = (row as LiveResult).result ?? (row as PublicResult).result ?? 'UNKNOWN';
  const winLoss = (row as LiveResult).outcome ?? (row as PublicResult).win_loss ?? 'UNKNOWN';
  return {
    date: (row as LiveResult).date ?? (row as PublicResult).date ?? new Date().toISOString().slice(0,10),
    game: (row as LiveResult).game ?? (row as PublicResult).game ?? (row as LiveResult).game_id ?? 'Unknown game',
    posted_label: (row as PublicResult).posted_label ?? 'Model board',
    model_lean: lean,
    result,
    win_loss: winLoss,
    note: (row as PublicResult).note,
  };
}

export async function getResults(): Promise<PublicResult[]> {
  const live = await readJson<LiveResult[]>('live/today_results.json');
  if (live?.length) return live.map(normalizeResult);
  const updates = await readJson<LiveResult[]>('live/public_record_updates.json');
  if (updates?.length) return updates.map(normalizeResult);
  const record = await readJson<PublicResult[]>('public-record.json');
  if (record?.length) return record.map(normalizeResult);
  return fallbackResults.map(normalizeResult);
}

export async function getBoardMetadata(): Promise<BoardMetadata> {
  await getGames();
  return cacheMeta;
}
