import { NextResponse } from 'next/server';
import { getGames, getPredictions, getResults } from '@/lib/local-store';

export async function GET() {
  try {
    const generatedAt = new Date().toISOString();
    let data: unknown = [];
    if ('games' === 'games') data = await getGames();
    if ('games' === 'predictions') data = await getPredictions();
    if ('games' === 'results') data = await getResults();
    return NextResponse.json({ status: 'ok', source: 'demo', generatedAt, data });
  } catch (error) {
    return NextResponse.json({ status: 'error', message: 'Failed to load demo data', error: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 });
  }
}
