import { formatProbability, getLeanDisplay } from '@/lib/labels';
import { Game, Prediction } from '@/lib/types';
import ModelLabel from './ModelLabel';

export default function GameCard({ game, pred }: { game: Game; pred: Prediction }) {
  return <div className="card space-y-2"><div className="flex justify-between"><h3 className="font-semibold">{game.game}</h3><ModelLabel label={pred.public_label} /></div><p className="text-sm text-zinc-400">{game.start_time} • {game.away_pitcher} vs {game.home_pitcher}</p><p className="text-sm">{getLeanDisplay(pred.lean)} • NRFI {formatProbability(pred.nrfi_probability)} • YRFI {formatProbability(pred.yrfi_probability)}</p><ul className="text-sm text-zinc-300">{pred.reasons.map((r) => <li key={r}>• {r}</li>)}</ul><ul className="text-sm text-yellow-300">{pred.warnings.map((w) => <li key={w}>⚠ {w}</li>)}</ul><div className="flex justify-between text-xs text-zinc-500"><span>{game.status ?? 'Demo scheduled'}</span><span>Demo data</span></div></div>;
}
