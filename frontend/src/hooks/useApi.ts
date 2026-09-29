import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { authApi, projectApi, searchApi, userApi } from '@/api/routes'
import { useAuthStore } from '@/stores/authStore'

export const queryKeys = {
  me: ['me'] as const,
  quota: ['quota'] as const,
  projects: ['projects'] as const,
  search: (q: string) => ['search', q] as const,
  suggest: (q: string) => ['suggest', q] as const,
}

export function useLoginMutation() {
  const setSession = useAuthStore((state) => state.setSession)
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => setSession(data.access_token, data.refresh_token, data.user),
  })
}

export function useRegisterMutation() {
  const setSession = useAuthStore((state) => state.setSession)
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => setSession(data.access_token, data.refresh_token, data.user),
  })
}

export function useMeQuery() {
  const setUser = useAuthStore((state) => state.setUser)
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: userApi.me,
    enabled: Boolean(useAuthStore.getState().accessToken),
    retry: false,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
    meta: { onSuccessUser: setUser },
  })
}

export function useProjectsQuery() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => projectApi.list(),
  })
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: projectApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
  })
}

export function useRenameProjectMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, title }: { projectId: string; title: string }) =>
      projectApi.rename(projectId, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
  })
}

export function useDeleteProjectMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: projectApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
  })
}

export function useProjectActionMutation(action: 'pause' | 'resume' | 'retry') {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (projectId: string) => projectApi[action](projectId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.projects }),
  })
}

export function useSearchQuery(q: string) {
  return useQuery({
    queryKey: queryKeys.search(q),
    queryFn: () => searchApi.search(q),
    enabled: q.trim().length > 0,
  })
}

export function useSuggestQuery(q: string) {
  return useQuery({
    queryKey: queryKeys.suggest(q),
    queryFn: () => searchApi.suggest(q),
    enabled: q.trim().length > 0,
  })
}

