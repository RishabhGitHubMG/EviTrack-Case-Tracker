import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { components } from '../api/schema.gen';
import { api } from '../api/client';
import { clearAuthChallenge } from './auth-utils';

export type User = components['schemas']['User'];

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<User>;
  signOut: () => Promise<void>;
  expireSession: () => void;
  can: (permission: string) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const currentUser = await api<User>('/auth/me/');
    setUser(currentUser);
    setLoading(false);
    return currentUser;
  }, []);

  useEffect(() => {
    let active = true;
    api<User>('/auth/me/')
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch((error: unknown) => {
        if (active && !(typeof error === 'object' && error !== null && 'status' in error && error.status === 401)) {
          setUser(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const expireSession = useCallback(() => {
    setUser(null);
    clearAuthChallenge();
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api<void>('/auth/logout/', { method: 'POST' });
    } finally {
      expireSession();
    }
  }, [expireSession]);

  const value = useMemo(() => ({
    user,
    loading,
    refreshUser,
    signOut,
    expireSession,
    can: (permission: string) => Boolean(user?.permissions.includes(permission)),
  }), [user, loading, refreshUser, signOut, expireSession]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useSession() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useSession must be used within AuthProvider');
  return context;
}
