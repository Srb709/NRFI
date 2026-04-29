import { PublicResult } from '@/lib/types';

export default function TrackerTable({ rows }: { rows: PublicResult[] }) {
  return <div className="overflow-x-auto card"><table className="w-full text-sm"><thead className="text-zinc-400"><tr><th className="text-left py-2">date</th><th className="text-left">game</th><th className="text-left">label</th><th className="text-left">lean</th><th className="text-left">result</th><th className="text-left">W/L</th><th className="text-left">note</th></tr></thead><tbody>{rows.map((r, i) => <tr key={i} className="border-t border-zinc-800"><td className="py-2">{r.date}</td><td>{r.game}</td><td>{r.posted_label}</td><td>{r.model_lean}</td><td>{r.result}</td><td>{r.win_loss}</td><td>{r.note}</td></tr>)}</tbody></table></div>;
}
