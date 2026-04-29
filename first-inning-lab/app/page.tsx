import Link from 'next/link';
import Shell from '@/components/Shell';

export default function Page() {
  return <Shell><section className="space-y-4"><h1 className="text-4xl font-semibold">The daily first-inning baseball lab.</h1><p className="text-zinc-300 max-w-3xl">NRFI/YRFI model boards, risk notes, public tracking, and copy-ready content. No guarantees. Just the board.</p><div className="flex gap-3"><Link href="/admin" className="card">Open Admin Dashboard</Link><Link href="/tracker" className="card">View Public Tracker</Link></div></section><section className="grid md:grid-cols-3 gap-4 mt-8"><div className="card"><h3>Model board</h3></div><div className="card"><h3>Risk notes</h3></div><div className="card"><h3>Public record</h3></div></section><section className="card mt-8 text-zinc-300">Free public X board now, private Discord early board later, pro dashboard later.</section><section className="card mt-4">This is baseball analysis, not betting advice. Track results, respect bankroll limits, and pass messy games.</section></Shell>;
}
