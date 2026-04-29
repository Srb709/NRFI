import Shell from '@/components/Shell';
import StatCard from '@/components/StatCard';
import TrackerTable from '@/components/TrackerTable';
import { getResults } from '@/lib/local-store';

export default async function Page() {
  const rows = await getResults();
  const wins = rows.filter((r) => r.win_loss === 'W').length;
  const losses = rows.filter((r) => r.win_loss === 'L').length;
  const tracked = rows.length;
  const winRate = tracked ? `${Math.round((wins / tracked) * 100)}%` : '0%';
  const nrfiRec = rows.filter((r) => r.model_lean === 'NRFI' && ['W', 'L'].includes(r.win_loss));
  const yrfiRec = rows.filter((r) => r.model_lean === 'YRFI' && ['W', 'L'].includes(r.win_loss));
  return <Shell><h1 className="text-3xl font-semibold">Public record</h1><p className="text-zinc-400 mt-2">Every posted model lean should be trackable. No deleted misses.</p><div className="grid md:grid-cols-6 gap-4 my-6"><StatCard title="Total tracked" value={tracked} /><StatCard title="Wins" value={wins} /><StatCard title="Losses" value={losses} /><StatCard title="Win rate" value={winRate} /><StatCard title="NRFI record" value={`${nrfiRec.filter(r=>r.win_loss==='W').length}-${nrfiRec.filter(r=>r.win_loss==='L').length}`} /><StatCard title="YRFI record" value={`${yrfiRec.filter(r=>r.win_loss==='W').length}-${yrfiRec.filter(r=>r.win_loss==='L').length}`} /></div><TrackerTable rows={rows} /><p className="mt-4 text-sm text-zinc-500">Demo tracker data is placeholder data until live tracking is connected.</p></Shell>;
}
