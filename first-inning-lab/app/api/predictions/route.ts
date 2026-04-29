import { NextResponse } from 'next/server';
import { getBoardMetadata, getPredictions } from '@/lib/local-store';
export async function GET() { const [data, meta] = await Promise.all([getPredictions(), getBoardMetadata()]); return NextResponse.json({ status: 'ok', ...meta, data }); }
