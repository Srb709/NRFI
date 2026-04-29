import { getPredictions } from '@/lib/local-store'; export async function GET(){ return Response.json(await getPredictions()); }
