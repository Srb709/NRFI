import demoGames from '@/data/demo-games.json';
import demoPredictions from '@/data/demo-predictions.json';
import publicRecord from '@/data/public-record.json';
import { Game, Prediction, PublicResult } from './types';

export const fallbackGames = demoGames as Game[];
export const fallbackPredictions = demoPredictions as Prediction[];
export const fallbackResults = publicRecord as PublicResult[];
