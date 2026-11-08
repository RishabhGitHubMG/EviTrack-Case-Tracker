import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './client';

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = 'csrftoken=; Max-Age=0; Path=/';
});

describe('api auth requests', () => {
  it('normalizes attempt counts and includes session credentials', async () => {
    document.cookie = 'csrftoken=test-token; Path=/';
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ code: 'validation_error', message: 'Invalid credentials.', attempts_left: 3 }), { status: 400 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(api('/auth/login/', { method: 'POST', body: JSON.stringify({ email: 'user@example.test', password: 'bad', remember_me: false }) }))
      .rejects.toMatchObject({ status: 400, code: 'validation_error', message: 'Invalid credentials.', attemptsLeft: 3 });

    const [, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request.credentials).toBe('include');
    expect(new Headers(request.headers).get('X-CSRFToken')).toBe('test-token');
  });

  it('loads a CSRF cookie before the first unsafe request', async () => {
    const fetchMock = vi.fn<typeof fetch>(async (input) => {
      if (String(input).endsWith('/auth/csrf/')) {
        document.cookie = 'csrftoken=fresh-token; Path=/';
        return new Response(JSON.stringify({ status: 'ok' }), { status: 200 });
      }
      return new Response(null, { status: 204 });
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(api('/auth/logout/', { method: 'POST' })).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [, request] = fetchMock.mock.calls[1] as [RequestInfo | URL, RequestInit];
    expect(new Headers(request.headers).get('X-CSRFToken')).toBe('fresh-token');
  });

  it('dispatches unauthorized when the session has expired', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ code: 'not_authenticated', message: 'Sign in required.' }), { status: 401 }));
    vi.stubGlobal('fetch', fetchMock);
    const unauthorized = vi.fn();
    window.addEventListener('evitrack:unauthorized', unauthorized);

    await expect(api('/auth/me/')).rejects.toMatchObject({ status: 401, code: 'not_authenticated' });
    expect(unauthorized).toHaveBeenCalledOnce();
    window.removeEventListener('evitrack:unauthorized', unauthorized);
  });
});
