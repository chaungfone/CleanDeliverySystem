import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { apiFetch, getToken, setToken } from './api';
import type { LoginResult, OtpRequestResult, UserInfo } from './types';

interface AuthContextValue {
  user: UserInfo | null;
  loading: boolean;
  login: (phone: string) => Promise<OtpRequestResult>;
  verifyOtp: (phone: string, otp: string) => Promise<LoginResult>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const ADMIN_ROLES = ['ADMIN', 'BRANCH_MANAGER'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await apiFetch<UserInfo>('/auth/me');
        if (!cancelled) {
          if (ADMIN_ROLES.includes(me.role)) {
            setUser(me);
          } else {
            setToken(null);
          }
        }
      } catch {
        setToken(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function login(phone: string): Promise<OtpRequestResult> {
    return apiFetch<OtpRequestResult>('/auth/request-otp', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phone }),
    });
  }

  async function verifyOtp(phone: string, otp: string): Promise<LoginResult> {
    let result: LoginResult;
    try {
      result = await apiFetch<LoginResult>('/auth/verify-otp', {
        method: 'POST',
        body: JSON.stringify({ phone_number: phone, otp }),
      });
    } catch (err) {
      throw err;
    }
    setToken(result.access_token);
    try {
      const me = await apiFetch<UserInfo>('/auth/me');
      if (!ADMIN_ROLES.includes(me.role)) {
        setToken(null);
        throw new Error('This account does not have admin access.');
      }
      setUser(me);
    } catch (err) {
      setToken(null);
      throw err;
    }
    return result;
  }

  function logout() {
    setToken(null);
    setUser(null);
    apiFetch('/auth/logout', { method: 'POST' }).catch(() => {
      // Cookie cleanup is best-effort; local access token is already cleared.
    });
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, verifyOtp, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export interface DecodedAuthUser {
  sub: string | null;
  role: string | null;
  exp: number | null;
  iat: number | null;
  aud: string | null;
  raw: Record<string, unknown> | null;
}

export function decodeJwtPayload(token: string | null | undefined): DecodedAuthUser | null {
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64Payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64Payload + '='.repeat((4 - (base64Payload.length % 4)) % 4);
    const decoded = atob(padded);
    const obj = JSON.parse(decoded) as Record<string, unknown>;
    return {
      sub: typeof obj.sub === 'string' ? obj.sub : null,
      role: typeof obj.role === 'string' ? obj.role : null,
      exp: typeof obj.exp === 'number' ? obj.exp : null,
      iat: typeof obj.iat === 'number' ? obj.iat : null,
      aud: typeof obj.aud === 'string' ? obj.aud : null,
      raw: obj,
    };
  } catch {
    return null;
  }
}

export function getAuthUser(): DecodedAuthUser | null {
  return decodeJwtPayload(getToken());
}
