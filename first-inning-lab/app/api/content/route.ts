import { NextResponse } from 'next/server';
import { generateContent } from '@/lib/content-generator';
import { getGames, getPredictions } from '@/lib/local-store';

export async function GET() {
  try {
    const data = generateContent(await getGames(), await getPredictions());
    return NextResponse.json({ status: 'ok', source: 'demo', generatedAt: new Date().toISOString(), data });
  } catch (error) {
    return NextResponse.json({ status: 'error', message: 'Failed to generate content', error: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 });
  }
}
