import Shell from '@/components/Shell';
import StatCard from '@/components/StatCard';
import TrackerTable from '@/components/TrackerTable';
import { getBoardMetadata, getResults } from '@/lib/local-store';

export default async function Page() {
  const [rows, meta] = await Promise.all([getResults(), getBoardMetadata()]);
  const wins = rows.filter((r) => r.win_loss === 'W').length;
  const losses = rows.filter((r) => r.win_loss === 'L').length;
  const passes = rows.filter((r) => r.win_loss === 'PASS').length;
  const pending = rows.filter((r) => r.win_loss === 'PENDING').length;
  const unknown = rows.filter((r) => r.win_loss === 'UNKNOWN').length;
  const tracked = rows.length;
  const graded = wins + losses;
  const winRate = graded ? `${Math.round((wins / graded) * 100)}%` : '0%';
  const subtitle = meta.resultsSource === 'live'
    ? 'LIVE LOCAL RESULTS'
    : meta.resultsSource === 'public_record'
      ? 'PUBLIC/HISTORICAL RECORD'
      : meta.resultsSource === 'demo'
        ? 'DEMO TRACKER'
        : 'AWAITING GRADED RESULTS';

  return <Shell><h1 className="text-3xl font-semibold">Public record</h1><p className="text-zinc-400 mt-2">{subtitle}</p><div className="grid md:grid-cols-7 gap-4 my-6"><StatCard title="Total tracked" value={tracked} /><StatCard title="Wins" value={wins} /><StatCard title="Losses" value={losses} /><StatCard title="Passes" value={passes} /><StatCard title="Pending" value={pending} /><StatCard title="Unknown" value={unknown} /><StatCard title="Win rate" value={winRate} /></div>{meta.resultsSource === 'empty' ? <p className="text-zinc-300">No graded results yet. Results will appear after games are graded.</p> : <TrackerTable rows={rows} />}</Shell>;
}
