import { getLabelTone } from '@/lib/labels';

export default function ModelLabel({ label }: { label: string }) {
  const tone = getLabelTone(label);
  const cls = tone === 'positive' ? 'border-amber-500/50 text-amber-200' : tone === 'danger' ? 'border-red-500/40 text-red-300' : tone === 'warning' ? 'border-yellow-500/40 text-yellow-300' : 'border-zinc-600 text-zinc-300';
  return <span className={`text-xs px-2 py-1 rounded border ${cls}`}>{label}</span>;
}
