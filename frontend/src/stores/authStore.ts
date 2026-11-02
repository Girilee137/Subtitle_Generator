import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types/api'

type AuthState = {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  demoMode: boolean
  setSession: (accessToken: string, refreshToken: string, user: User) => void
  setDemoSession: (user: User) => void
  setAccessToken: (accessToken: string) => void
  setUser: (user: User) => void
  clearSession: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      demoMode: false,
      setSession: (accessToken, refreshToken, user) =>
        set({ accessToken, refreshToken, user, demoMode: false }),
      setDemoSession: (user) =>
        set({ accessToken: null, refreshToken: null, user, demoMode: true }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setUser: (user) => set({ user }),
      clearSession: () => set({ accessToken: null, refreshToken: null, user: null, demoMode: false }),
    }),
    { name: 'subtitle-platform-auth' },
  ),
)
