import Link from 'next/link';

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <header className="mb-8 border-b border-zinc-800 pb-4 flex items-center justify-between">
          <p className="font-semibold tracking-wide text-amber-300">First Inning Lab</p>
          <nav className="flex gap-4 text-sm text-zinc-300">
            <Link href="/">Home</Link><Link href="/admin">Admin</Link><Link href="/tracker">Tracker</Link>
          </nav>
        </header>
        {children}
      </div>
    </main>
  );
}
