import { getResults } from '@/lib/local-store'; export async function GET(){ return Response.json(await getResults()); }
