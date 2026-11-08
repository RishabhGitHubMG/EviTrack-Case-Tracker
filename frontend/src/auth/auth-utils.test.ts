import { describe, expect, it } from 'vitest';
import { formatDuration, isApiError, safeNextPath } from './auth-utils';

describe('auth route utilities', () => {
  it('allows only same-origin next paths', () => {
    expect(safeNextPath('/cases?status=open')).toBe('/cases?status=open');
    expect(safeNextPath('//attacker.example')).toBe('/dashboard');
    expect(safeNextPath('https://attacker.example')).toBe('/dashboard');
    expect(safeNextPath(null)).toBe('/dashboard');
  });

  it('recognizes normalized API errors and formats countdowns', () => {
    expect(isApiError({ status: 400, code: 'validation_error' })).toBe(true);
    expect(isApiError(new Error('failure'))).toBe(false);
    expect(formatDuration(629)).toBe('10:29');
    expect(formatDuration(9)).toBe('0:09');
  });
});
