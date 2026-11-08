import { Menu, ShieldCheck, X } from 'lucide-react';
import { Suspense, useState } from 'react';
import { Link, Outlet } from 'react-router-dom';
import '../../styles/public.css';
import { buttonClass } from '../ui';

const sectionLinks = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#security', label: 'Security' },
];

export function Logo() {
  return (
    <Link to="/" className="inline-flex items-center gap-2 font-serif text-lg font-semibold text-text no-underline">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-navy-900 text-amber-500" aria-hidden="true">
        <ShieldCheck size={18} />
      </span>
      EviTrack
    </Link>
  );
}

export function PublicLayout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2 focus:shadow-soft">
        Skip to content
      </a>
      <header className="public-nav">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-6">
          <Logo />
          <nav aria-label="Primary" className="flex items-center gap-2">
            <ul
              id="site-menu"
              className={`${menuOpen ? 'absolute left-0 right-0 top-16 grid gap-1 border-b border-border bg-surface p-4 shadow-soft' : 'hidden'} md:static md:flex md:items-center md:gap-6 md:border-0 md:bg-transparent md:p-0 md:shadow-none`}
            >
              {sectionLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    onClick={() => setMenuOpen(false)}
                    className="block rounded-md px-3 py-3 text-sm font-medium text-text no-underline hover:underline md:py-1"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
              <li className="md:hidden">
                <Link to="/login" onClick={() => setMenuOpen(false)} className={buttonClass({ variant: 'secondary' })}>Sign in</Link>
              </li>
            </ul>
            <div className="hidden md:block">
              <Link to="/login" className={buttonClass({ variant: 'ghost', size: 'sm' })}>Sign in</Link>
            </div>
            <Link to="/register" className={buttonClass({ variant: 'accent', size: 'sm' })}>Request access</Link>
            <div className="md:hidden">
              <button
                type="button"
                className={buttonClass({ variant: 'ghost', size: 'sm' })}
                aria-expanded={menuOpen}
                aria-controls="site-menu"
                aria-label={menuOpen ? 'Close menu' : 'Open menu'}
                onClick={() => setMenuOpen((open) => !open)}
              >
                {menuOpen ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
              </button>
            </div>
          </nav>
        </div>
      </header>

      <main id="main" className="flex-1">
        <Suspense fallback={null}>
          <Outlet />
        </Suspense>
      </main>

      <footer className="border-t border-border bg-surface">
        <div className="mx-auto grid max-w-6xl gap-8 px-6 py-10 md:grid-cols-[2fr_1fr_1fr]">
          <div className="grid content-start gap-3">
            <Logo />
            <p className="max-w-sm text-sm text-muted">Digital evidence and case tracking for small law firms and police stations.</p>
            <p className="text-xs text-muted">This is a prototype. All data shown is dummy data; do not enter real personal information.</p>
          </div>
          <nav aria-label="Product links" className="grid content-start gap-2 text-sm">
            <span className="font-semibold text-text">Product</span>
            {sectionLinks.map((link) => <a key={link.href} href={link.href} className="text-muted no-underline hover:underline">{link.label}</a>)}
          </nav>
          <nav aria-label="Account links" className="grid content-start gap-2 text-sm">
            <span className="font-semibold text-text">Account</span>
            <Link to="/login" className="text-muted no-underline hover:underline">Sign in</Link>
            <Link to="/register" className="text-muted no-underline hover:underline">Request access</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
