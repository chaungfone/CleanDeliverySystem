export const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1';

const TOKEN_KEY = 'cd_dashboard_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// Refresh token is held server-side in an HttpOnly cookie (set by POST /auth/refresh-cookie).
// It is never written to localStorage/JS, so an XSS payload cannot exfiltrate it.
let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh-cookie`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!res.ok) return false;
      const data = await res.json().catch(() => null);
      if (data?.access_token) {
        setToken(data.access_token);
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface ApiOptions extends RequestInit {
  timeoutMs?: number;
}

const DEFAULT_TIMEOUT_MS = 90000;

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  return requestWithRetry<T>(path, options, false);
}

async function requestWithRetry<T>(
  path: string,
  options: ApiOptions,
  retried: boolean,
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const fullUrl = `${API_BASE_URL}${path}`;
    const res = await fetch(fullUrl, {
      ...fetchOptions,
      headers,
      credentials: 'include',
      signal: controller.signal,
    });

    if (res.status === 401 && !retried) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return requestWithRetry<T>(path, options, true);
      }
    }

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        if (body?.error?.message) {
          detail = body.error.message;
        } else if (body?.detail) {
          detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        }
      } catch {
      }
      throw new ApiError(res.status, detail);
    }

    if (res.status === 204) {
      return undefined as T;
    }

    const contentType = res.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      return (await res.json()) as T;
    }
    if (contentType.includes('text/html')) {
      // The host's SPA fallback served the dashboard HTML for an API route
      // (e.g. the backend function is missing/broken on the deploy). The body
      // is not JSON, so surface a clear error instead of returning garbage
      // that later fails with "x.map is not a function".
      throw new ApiError(
        502,
        'The API returned an HTML page instead of JSON. Check that the backend is deployed and reachable.',
      );
    }
    return (await res.text()) as unknown as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(0, `Request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    if (err instanceof Error) {
      throw new ApiError(0, err.message || 'Network error');
    }
    throw new ApiError(0, String(err));
  } finally {
    clearTimeout(timer);
  }
}

export async function downloadFile(path: string, filename: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default API_BASE_URL;

