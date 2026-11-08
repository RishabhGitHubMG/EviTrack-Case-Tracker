import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { 900: 'var(--navy-900)', 700: 'var(--navy-700)' },
        amber: { 500: 'var(--amber-500)', 600: 'var(--amber-600)' },
        surface: 'var(--surface)',
        bg: 'var(--bg)',
        border: 'var(--border)',
        text: 'var(--text)',
        muted: 'var(--muted)',
        success: 'var(--success)',
        danger: 'var(--danger)',
        warning: 'var(--warning)',
        info: 'var(--info)',
        primary: 'var(--navy-900)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['"Source Serif 4 Variable"', '"Source Serif 4"', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: { card: '12px' },
      boxShadow: { soft: '0 1px 3px rgba(20,33,61,.08)' },
    },
  },
  plugins: [],
} satisfies Config;
