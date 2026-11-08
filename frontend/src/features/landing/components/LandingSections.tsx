import {
  ArrowRightLeft,
  Archive,
  BarChart3,
  CalendarClock,
  Check,
  CircleX,
  FolderKanban,
  KeyRound,
  Link2,
  ScrollText,
  ShieldCheck,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { buttonClass } from '../../../components/ui';
import { Reveal } from './Reveal';

const trustItems: Array<{ icon: LucideIcon; label: string }> = [
  { icon: ShieldCheck, label: 'SHA-256 integrity' },
  { icon: Link2, label: 'Chain of custody' },
  { icon: KeyRound, label: 'Role-based access' },
  { icon: ScrollText, label: 'Immutable audit trail' },
];

export function TrustStrip() {
  return (
    <section aria-label="Trust highlights" className="border-b border-border bg-surface">
      <ul className="mx-auto grid max-w-6xl gap-4 px-6 py-6 sm:grid-cols-2 lg:grid-cols-4">
        {trustItems.map(({ icon: Icon, label }) => (
          <li key={label} className="flex items-center gap-3 text-sm font-semibold text-text">
            <span className="icon-tile"><Icon size={20} aria-hidden="true" /></span>
            {label}
          </li>
        ))}
      </ul>
    </section>
  );
}

const todayItems = [
  'Paper registers and handwritten logs',
  'Evidence copied onto pen drives and chat groups',
  'Hearing dates kept in personal diaries',
  'Hearings missed and deadlines forgotten',
];

const withEvitrackItems = [
  'Central case records for every team',
  'Evidence hashed the moment it is uploaded',
  'Automatic reminders before every hearing',
];

export function ProblemSolution() {
  return (
    <section aria-labelledby="problem-title" className="mx-auto max-w-6xl px-6 py-20">
      <Reveal>
        <h2 id="problem-title" className="font-serif text-3xl font-semibold text-text sm:text-4xl">Stop running cases from scattered files</h2>
      </Reveal>
      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <Reveal>
          <div className="h-full rounded-card border border-border bg-surface p-6 shadow-soft">
            <h3 className="font-serif text-xl font-semibold text-text">Today</h3>
            <ul className="mt-5 grid gap-4">
              {todayItems.map((item) => (
                <li key={item} className="flex gap-3 text-muted">
                  <CircleX size={20} className="mt-0.5 shrink-0 text-danger" aria-hidden="true" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="h-full rounded-card border border-border bg-surface p-6 shadow-soft">
            <h3 className="font-serif text-xl font-semibold text-text">With EviTrack</h3>
            <ul className="mt-5 grid gap-4">
              {withEvitrackItems.map((item) => (
                <li key={item} className="flex gap-3 text-text">
                  <Check size={20} className="mt-0.5 shrink-0 text-success" aria-hidden="true" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

const features: Array<{ icon: LucideIcon; title: string; description: string }> = [
  { icon: FolderKanban, title: 'Case management', description: 'Cases, parties, assignments and status in one record, visible only to the people assigned to it.' },
  { icon: Archive, title: 'Evidence vault', description: 'Each uploaded file is fingerprinted with SHA-256 and kept outside the public web root.' },
  { icon: ArrowRightLeft, title: 'Chain of custody', description: 'A hand-over is a request the receiver must accept, and every step is recorded.' },
  { icon: CalendarClock, title: 'Hearings and reminders', description: 'Schedule hearings and tasks, with reminders sent ahead of each date.' },
  { icon: BarChart3, title: 'Reports and dashboard', description: 'See open cases, upcoming hearings and integrity alerts at a glance, and export PDF reports.' },
  { icon: ScrollText, title: 'Audit and security', description: 'A hash-chained audit trail, one-time email codes and lockout after repeated failed sign-ins.' },
];

export function FeaturesGrid() {
  return (
    <section id="features" aria-labelledby="features-title" className="public-section border-t border-border bg-bg">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Features</p>
          <h2 id="features-title" className="mt-2 font-serif text-3xl font-semibold text-text sm:text-4xl">Everything a case file needs</h2>
        </Reveal>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, description }, index) => (
            <Reveal key={title} delay={index * 80}>
              <article className="h-full rounded-card border border-border bg-surface p-6 shadow-soft transition duration-200 hover:-translate-y-1 hover:shadow-[var(--shadow-lift)] motion-reduce:transition-none motion-reduce:hover:translate-y-0">
                <span className="icon-tile"><Icon size={20} aria-hidden="true" /></span>
                <h3 className="mt-4 text-base font-semibold text-text">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{description}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

const steps = [
  { title: 'Upload and hash', description: 'Each file is fingerprinted with SHA-256 the moment it arrives.' },
  { title: 'Transfer with a handshake', description: 'The sender requests a transfer and the receiver accepts or rejects it.' },
  { title: 'Verify on demand', description: 'Re-hash any file at any time and compare it with the stored fingerprint.' },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" aria-labelledby="how-title" className="public-section border-t border-border bg-surface">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">How it works</p>
          <h2 id="how-title" className="mt-2 font-serif text-3xl font-semibold text-text sm:text-4xl">Three steps from upload to proof</h2>
        </Reveal>
        <div className="mt-12 grid gap-10 md:grid-cols-[1fr_auto] md:items-center">
          <div className="relative">
            <span aria-hidden="true" className="absolute left-5 top-5 hidden h-px w-[calc(100%-2.5rem)] bg-border md:block" />
            <ol className="relative grid gap-10 md:grid-cols-3 md:gap-6">
              {steps.map((step, index) => (
                <li key={step.title} className="list-none">
                  <Reveal delay={index * 120} className="grid gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-full bg-navy-900 font-semibold text-white">{index + 1}</span>
                    <h3 className="text-base font-semibold text-text">{step.title}</h3>
                    <p className="text-sm leading-relaxed text-muted">{step.description}</p>
                  </Reveal>
                </li>
              ))}
            </ol>
          </div>
          <Reveal delay={360}>
            <div role="img" aria-label="Integrity status changes from Verified to Modified after a file is altered" className="grid gap-3 rounded-card border border-border bg-bg p-5">
              <p aria-hidden="true" className="text-xs font-semibold uppercase tracking-widest text-muted">Integrity check</p>
              <div aria-hidden="true" className="verdict-stage">
                <span className="verdict verdict--verified"><ShieldCheck size={16} />Verified</span>
                <span className="verdict verdict--modified"><TriangleAlert size={16} />Modified</span>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

const securityItems = [
  'Email one-time code on every sign-in',
  'Account lockout after repeated failed attempts',
  'Role-based access to each case',
  'Immutable audit log with hash chaining',
  'Evidence files stored outside the web root',
];

export function SecurityBand() {
  return (
    <section id="security" aria-labelledby="security-title" className="public-section bg-navy-900 text-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-2 lg:items-center">
        <Reveal>
          <p className="text-xs font-semibold uppercase tracking-widest text-amber-500">Security</p>
          <h2 id="security-title" className="mt-2 font-serif text-3xl font-semibold sm:text-4xl">Built for evidence that has to hold up</h2>
          <p className="mt-4 max-w-lg leading-relaxed text-white/80">Access, sign-in and records are controlled on the server, so every rule applies no matter which screen someone uses.</p>
        </Reveal>
        <Reveal delay={120}>
          <ul className="grid gap-4 rounded-card border border-white/10 bg-white/5 p-6">
            {securityItems.map((item) => (
              <li key={item} className="flex items-center gap-3">
                <Check size={18} className="shrink-0 text-amber-500" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}

export function FinalCta() {
  return (
    <section aria-labelledby="cta-title" className="bg-bg">
      <Reveal>
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-6 py-16 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 id="cta-title" className="font-serif text-3xl font-semibold text-text">Ready to stop losing evidence?</h2>
            <p className="mt-2 text-muted">Access is granted by approval only. Request access and an administrator will review it.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/login" className={buttonClass({ variant: 'accent', size: 'lg' })}>Sign in</Link>
            <Link to="/register" className={buttonClass({ variant: 'secondary', size: 'lg' })}>Request access</Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
