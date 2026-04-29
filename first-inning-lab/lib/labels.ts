import { Lean, Prediction } from './types';

export const APPROVED_PUBLIC_LABELS = [
  'Lab Favorite',
  'Clean First Frame',
  'Quiet Inning Candidate',
  'Slight Lean',
  'Trap Watch',
  'Chaos Zone',
  'YRFI Smoke',
  'Stay Away Spot',
  'Pass'
] as const;

export function getPublicLabel(prediction: Prediction): string {
  const { nrfi_probability, yrfi_probability, warnings } = prediction;
  const warningCount = warnings.length;

  if (prediction.lean === 'PASS') return 'Pass';
  if (nrfi_probability >= 0.64 && warningCount <= 1) return 'Lab Favorite';
  if (nrfi_probability >= 0.60) return 'Clean First Frame';
  if (nrfi_probability >= 0.56) return 'Quiet Inning Candidate';
  if (nrfi_probability >= 0.52) return 'Slight Lean';
  if (yrfi_probability >= 0.61) return 'YRFI Smoke';
  if (yrfi_probability >= 0.56) return warningCount >= 2 ? 'Chaos Zone' : 'Trap Watch';
  return warningCount >= 2 ? 'Stay Away Spot' : 'Pass';
}

export function getLabelTone(label: string): 'positive' | 'warning' | 'neutral' | 'danger' {
  if (['Lab Favorite', 'Clean First Frame'].includes(label)) return 'positive';
  if (['YRFI Smoke', 'Chaos Zone'].includes(label)) return 'danger';
  if (['Trap Watch', 'Stay Away Spot'].includes(label)) return 'warning';
  return 'neutral';
}

export function getLeanDisplay(lean: Lean): string {
  if (lean === 'NRFI') return 'NRFI model lean';
  if (lean === 'YRFI') return 'YRFI model lean';
  return 'Pass spot';
}

export function formatProbability(value: number): string {
  return `${Math.round(value * 100)}%`;
}
