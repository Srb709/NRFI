import { formatProbability, getLeanDisplay } from '@/lib/labels';
import { Game, Prediction } from '@/lib/types';
import ModelLabel from './ModelLabel';

export default function GameCard({ game, pred, source }: { game: Game; pred: Prediction; source: string }) {
  const fb = pred.feature_breakdown;
  return <div className="card space-y-2"><div className="flex justify-between"><h3 className="font-semibold">{game.game}</h3><ModelLabel label={pred.public_label} /></div><p className="text-sm text-zinc-400">{game.start_time} • {game.away_pitcher} vs {game.home_pitcher}</p><p className="text-sm">{getLeanDisplay(pred.lean)} • NRFI {formatProbability(pred.nrfi_probability)} • YRFI {formatProbability(pred.yrfi_probability)}</p><p className="text-xs text-zinc-500">{pred.board_status ?? 'Early board'} • Data quality: {pred.data_quality_score ?? 'n/a'}</p>{fb ? <p className="text-xs text-zinc-500">P:{fb.pitcher_safety_score} O:{fb.offense_danger_score} W:{fb.park_weather_score} C:{fb.certainty_score} R:{fb.recent_form_score}</p> : null}<ul className="text-sm text-zinc-300">{pred.reasons.map((r) => <li key={r}>• {r}</li>)}</ul><ul className="text-sm text-yellow-300">{pred.warnings.map((w) => <li key={w}>⚠ {w}</li>)}</ul><div className="flex justify-between text-xs text-zinc-500"><span>{game.status ?? 'Scheduled'}</span><span>{source}</span></div></div>;
}
