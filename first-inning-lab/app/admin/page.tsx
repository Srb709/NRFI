import ContentBlock from '@/components/ContentBlock';
import GameCard from '@/components/GameCard';
import Shell from '@/components/Shell';
import StatCard from '@/components/StatCard';
import { generateContent } from '@/lib/content-generator';
import { getBoardMetadata, getGames, getPredictions } from '@/lib/local-store';

export default async function Page() {
  const [games, preds, meta] = await Promise.all([getGames(), getPredictions(), getBoardMetadata()]);
  const content = generateContent(games, preds);
  return <Shell><h1 className="text-3xl font-semibold mb-4">Admin Dashboard</h1>
    <div className="card mb-6"><p className="text-xs text-zinc-400">{meta.isDemo ? 'DEMO MODE' : 'LIVE LOCAL BOARD'}</p><p className="text-sm text-zinc-300">Source: {meta.source} • Generated: {meta.generatedAt ?? 'n/a'} • Board: {meta.boardStatus}</p><p className="text-xs text-zinc-500 mt-2">Early board may use probable pitchers and incomplete lineups. Final board should be refreshed after lineups post.</p></div>
    <div className="grid md:grid-cols-4 gap-4 mb-6"><StatCard title="Games" value={meta.summary?.games ?? games.length} /><StatCard title="NRFI leans" value={meta.summary?.nrfi_leans ?? preds.filter((p) => p.lean === 'NRFI').length} /><StatCard title="YRFI leans" value={meta.summary?.yrfi_leans ?? preds.filter((p) => p.lean === 'YRFI').length} /><StatCard title="Pass discipline" value={meta.summary?.passes ?? preds.filter((p) => p.lean === 'PASS').length} /></div>
    <div className="grid md:grid-cols-2 gap-4 mb-6"><StatCard title="Low confidence" value={meta.summary?.low_confidence ?? 0} /><StatCard title="Data quality" value={meta.summary?.average_data_quality ?? 'n/a'} /></div>
    <h2 className="text-xl mb-3">Model board</h2><div className="grid md:grid-cols-2 gap-4">{games.map((g) => { const p = preds.find((x) => x.game_id === g.game_id); return p ? <GameCard key={g.game_id} game={g} pred={p} source={meta.source} /> : null; })}</div>
    <h2 className="text-xl mt-8 mb-3">Content Studio</h2><div className="grid md:grid-cols-2 gap-4"><ContentBlock title="Daily board post" content={content.dailyBoard} /><ContentBlock title="Clean setup post" content={content.cleanSetupPost} /><ContentBlock title="YRFI smoke post" content={content.yrfiSmokePost} /><ContentBlock title="Trap watch post" content={content.trapWatchPost} /><ContentBlock title="Results recap template" content={content.resultsRecapTemplate} /><ContentBlock title="Discord early board post" content={content.discord} /></div></Shell>;
}
