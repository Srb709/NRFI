import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fallbackGames, fallbackPredictions, fallbackResults } from './demo-data';
import { Game, Prediction, PublicResult } from './types';

const dataDir = path.join(process.cwd(), 'data');

async function loadJsonFile<T>(fileName: string, fallback: T): Promise<T> {
  try {
    const filePath = path.join(dataDir, fileName);
    const raw = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(raw) as T;
  } catch (error) {
    if (typeof window === 'undefined') {
      console.error(`[local-store] Failed to load ${fileName}, using fallback demo data.`, error);
    }
    return fallback;
  }
}

export async function getGames(): Promise<Game[]> {
  return loadJsonFile<Game[]>('demo-games.json', fallbackGames);
}

export async function getPredictions(): Promise<Prediction[]> {
  return loadJsonFile<Prediction[]>('demo-predictions.json', fallbackPredictions);
}

export async function getResults(): Promise<PublicResult[]> {
  return loadJsonFile<PublicResult[]>('public-record.json', fallbackResults);
}
