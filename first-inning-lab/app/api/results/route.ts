import { NextResponse } from 'next/server';
import { getBoardMetadata, getResults } from '@/lib/local-store';
export async function GET() { const [data, meta] = await Promise.all([getResults(), getBoardMetadata()]); return NextResponse.json({ status: 'ok', ...meta, data }); }
