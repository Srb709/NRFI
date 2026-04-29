import { formatProbability, getLeanDisplay } from '@/lib/labels';
import { Game, Prediction } from '@/lib/types';
import ModelLabel from './ModelLabel';

const formatPct = (v?: number) => typeof v === 'number' ? `${Math.round(v * 100)}%` : 'n/a';
const formatNum = (v?: number) => typeof v === 'number' ? (v <= 1 ? `${Math.round(v * 100)}%` : v.toFixed(2)) : 'n/a';

export default function GameCard({ game, pred, source }: { game: Game; pred: Prediction; source: string }) {
  const fb = pred.feature_breakdown;
  const matchup = game.game || `${game.away_team || 'Away'} @ ${game.home_team || 'Home'}`;
  const startTime = game.start_time || 'Time TBD';
  const awayPitcher = game.away_pitcher || 'TBD';
  const homePitcher = game.home_pitcher || 'TBD';
  const reasons = pred.reasons ?? [];
  const warnings = pred.warnings ?? [];

  return <div className="card space-y-2"><div className="flex justify-between"><h3 className="font-semibold">{matchup}</h3><ModelLabel label={pred.public_label} /></div><p className="text-sm text-zinc-400">{startTime} • {awayPitcher} vs {homePitcher}</p><p className="text-sm">{getLeanDisplay(pred.lean)} • NRFI {formatProbability(pred.nrfi_probability)} • YRFI {formatProbability(pred.yrfi_probability)}</p><p className="text-xs text-zinc-500">{pred.board_status ?? 'Early board'} • Data quality: {formatPct(pred.data_quality_score)}</p>{fb ? <p className="text-xs text-zinc-500">P:{formatNum(fb.pitcher_safety_score)} O:{formatNum(fb.offense_danger_score)} W:{formatNum(fb.park_weather_score)} C:{formatNum(fb.certainty_score)} R:{formatNum(fb.recent_form_score)}</p> : null}<ul className="text-sm text-zinc-300">{reasons.map((r) => <li key={r}>• {r}</li>)}</ul><ul className="text-sm text-yellow-300">{warnings.map((w) => <li key={w}>⚠ {w}</li>)}</ul><div className="flex justify-between text-xs text-zinc-500"><span>{game.status ?? 'Scheduled'}</span><span>{source}</span></div></div>;
}
