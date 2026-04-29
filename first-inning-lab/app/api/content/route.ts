import { NextResponse } from 'next/server';
import { generateContent } from '@/lib/content-generator';
import { getBoardMetadata, getGames, getPredictions } from '@/lib/local-store';
export async function GET() { const [games, preds, meta] = await Promise.all([getGames(), getPredictions(), getBoardMetadata()]); return NextResponse.json({ status: 'ok', ...meta, data: generateContent(games, preds) }); }
