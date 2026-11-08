import { QueryClient } from '@tanstack/react-query';

export const queryKeys = {
  all: ['evitrack'] as const,
  session: () => [...queryKeys.all, 'session'] as const,
  cases: () => [...queryKeys.all, 'cases'] as const,
  case: (id: number | string) => [...queryKeys.cases(), id] as const,
  evidence: () => [...queryKeys.all, 'evidence'] as const,
  notifications: () => [...queryKeys.all, 'notifications'] as const,
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: true },
    mutations: { retry: 0 },
  },
});
