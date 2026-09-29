import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types/api'

type AuthState = {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setSession: (accessToken: string, refreshToken: string, user: User) => void
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
      setSession: (accessToken, refreshToken, user) => set({ accessToken, refreshToken, user }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setUser: (user) => set({ user }),
      clearSession: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'subtitle-platform-auth' },
  ),
)

