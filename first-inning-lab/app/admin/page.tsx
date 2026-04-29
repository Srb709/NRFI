import ContentBlock from '@/components/ContentBlock';
import GameCard from '@/components/GameCard';
import Shell from '@/components/Shell';
import StatCard from '@/components/StatCard';
import { generateContent } from '@/lib/content-generator';
import { getGames, getPredictions } from '@/lib/local-store';

export default async function Page() {
  const games = await getGames();
  const preds = await getPredictions();
  const content = generateContent(games, preds);
  const nrfi = preds.filter((p) => p.lean === 'NRFI').length;
  const yrfi = preds.filter((p) => p.public_label === 'YRFI Smoke').length;
  const passChaos = preds.filter((p) => ['PASS', 'Chaos Zone'].includes(p.lean) || p.public_label === 'Chaos Zone').length;

  return <Shell><h1 className="text-3xl font-semibold mb-4">Admin Dashboard</h1><div className="grid md:grid-cols-4 gap-4 mb-6"><StatCard title="Games today" value={games.length} /><StatCard title="NRFI leans" value={nrfi} /><StatCard title="YRFI smoke" value={yrfi} /><StatCard title="Pass/chaos games" value={passChaos} /></div><h2 className="text-xl mb-3">Today's Board</h2><div className="grid md:grid-cols-2 gap-4">{games.map((g) => { const p = preds.find((x) => x.game_id === g.game_id); return p ? <GameCard key={g.game_id} game={g} pred={p} /> : null; })}</div><h2 className="text-xl mt-8 mb-3">Content Studio</h2><div className="grid md:grid-cols-2 gap-4"><ContentBlock title="Daily board post" content={content.dailyBoard} /><ContentBlock title="Clean setup post" content={content.cleanSetupPost} /><ContentBlock title="YRFI smoke post" content={content.yrfiSmokePost} /><ContentBlock title="Trap watch post" content={content.trapWatchPost} /><ContentBlock title="Results recap template" content={content.resultsRecapTemplate} /><ContentBlock title="Discord early board post" content={content.discord} /></div><p className="mt-6 text-sm text-zinc-400">This dashboard generates copy for review only. It does not auto-post or place bets.</p></Shell>;
}
