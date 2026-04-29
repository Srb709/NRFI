import { NextResponse } from 'next/server';
import { getBoardMetadata, getGames } from '@/lib/local-store';
export async function GET() { const [data, meta] = await Promise.all([getGames(), getBoardMetadata()]); return NextResponse.json({ status: 'ok', ...meta, data }); }
