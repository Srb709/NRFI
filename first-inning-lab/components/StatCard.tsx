export default function StatCard({ title, value }: { title: string; value: string | number }) {
  return <div className="card"><p className="text-xs text-zinc-400 uppercase tracking-wide">{title}</p><p className="text-2xl mt-1">{value}</p></div>;
}
