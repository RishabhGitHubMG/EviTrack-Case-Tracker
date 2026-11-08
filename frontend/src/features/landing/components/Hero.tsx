import { ArrowRight, FileVideo, Link2, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Pill, buttonClass } from '../../../components/ui';

export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="relative overflow-hidden bg-gradient-to-br from-navy-900 to-navy-700 text-white">
      <div aria-hidden="true" className="hero-grid absolute inset-0 opacity-70" />
      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-24">
        <div>
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-amber-500">Digital evidence and case tracking</p>
          <h1 id="hero-title" className="font-serif text-4xl font-semibold leading-tight sm:text-5xl lg:text-6xl">
            Every case. Every file. Every handover. Proven.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/80">
            One secure place for small law firms and police stations to manage cases, digital evidence, hearings and deadlines.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/login" className={buttonClass({ variant: 'accent', size: 'lg' })}>Sign in</Link>
            <a
              href="#how-it-works"
              className="inline-flex min-h-12 items-center gap-2 rounded-lg border border-white/30 px-[18px] py-2.5 font-semibold text-white no-underline transition hover:bg-white/10 motion-reduce:transition-none"
            >
              See how it works
              <ArrowRight size={16} aria-hidden="true" />
            </a>
          </div>
        </div>

        <div aria-hidden="true" className="relative">
          <div className="rounded-2xl border border-white/10 bg-surface p-5 text-text shadow-[0_24px_60px_rgba(0,0,0,0.35)] lg:-rotate-2">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-muted">EVT-2026-0001</p>
                <p className="font-serif text-lg font-semibold">Harbour Street robbery</p>
              </div>
              <Pill value="Under Investigation" />
            </div>
            <div className="mt-5 grid gap-3 rounded-xl border border-border p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="icon-tile"><FileVideo size={20} /></span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">CCTV_0412.mp4</p>
                    <p className="font-mono text-xs text-muted">SHA-256 9f2c4a1e…b71d03</p>
                  </div>
                </div>
                <Pill value="Verified" />
              </div>
              <div className="flex items-center gap-3 border-t border-border pt-3 text-sm">
                <span className="icon-tile icon-tile--success"><Link2 size={18} /></span>
                <p className="text-muted">Transferred to Forensics and accepted at 14:52</p>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 text-xs text-muted">
              <ShieldCheck size={14} />
              Every change is written to the audit trail
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
