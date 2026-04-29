'use client';

import { useState } from 'react';

export default function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  async function onCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  }
  return <button onClick={onCopy} className="px-3 py-1 rounded border border-zinc-700 text-xs">{copied ? 'Copied' : 'Copy'}</button>;
}
