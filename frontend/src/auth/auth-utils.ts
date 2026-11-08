import { z } from 'zod';
import type { ApiError } from '../api/client';

const challengeKey = 'evitrack-auth-challenge';

const challengeSchema = z.object({
  sentToMasked: z.string(),
  expiresAt: z.number(),
  resendAt: z.number(),
  next: z.string(),
});

export type AuthChallenge = z.infer<typeof challengeSchema>;

export function safeNextPath(value: string | null) {
  return value && value.startsWith('/') && !value.startsWith('//') ? value : '/dashboard';
}

export function storeAuthChallenge(challenge: AuthChallenge) {
  sessionStorage.setItem(challengeKey, JSON.stringify(challenge));
}

export function readAuthChallenge(): AuthChallenge | null {
  const value = sessionStorage.getItem(challengeKey);
  if (!value) return null;
  const result = challengeSchema.safeParse(JSON.parse(value));
  return result.success ? result.data : null;
}

export function clearAuthChallenge() {
  sessionStorage.removeItem(challengeKey);
}

export function isApiError(error: unknown): error is ApiError {
  return typeof error === 'object' && error !== null && 'status' in error && 'code' in error;
}

export function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, '0')}`;
}
