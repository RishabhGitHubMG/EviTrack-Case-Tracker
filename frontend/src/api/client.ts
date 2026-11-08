export type ApiError = {
  status: number;
  code: string;
  message: string;
  fields?: Record<string, string[]> | null;
  retryAfter?: number | null;
};

const apiBase = import.meta.env.VITE_API_BASE ?? '/api/v1';
const unsafeMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function cookie(name: string): string | undefined {
  return document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase();
  const headers = new Headers(init.headers);
  if (unsafeMethods.has(method)) {
    const token = cookie('csrftoken');
    if (token) headers.set('X-CSRFToken', decodeURIComponent(token));
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    method,
    headers,
    credentials: 'include',
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const error: ApiError = {
      status: response.status,
      code: body.code ?? 'server_error',
      message: body.message ?? 'The request could not be completed.',
      fields: body.fields,
      retryAfter: body.retry_after,
    };
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent('evitrack:unauthorized'));
    }
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
