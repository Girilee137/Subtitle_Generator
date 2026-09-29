import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type UiState = {
  sidebarOpen: boolean
  darkMode: boolean
  serverProcessingConsent: boolean
  setSidebarOpen: (sidebarOpen: boolean) => void
  toggleTheme: () => void
  setServerProcessingConsent: (serverProcessingConsent: boolean) => void
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      darkMode: false,
      serverProcessingConsent: false,
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      toggleTheme: () => set((state) => ({ darkMode: !state.darkMode })),
      setServerProcessingConsent: (serverProcessingConsent) => set({ serverProcessingConsent }),
    }),
    { name: 'subtitle-platform-ui' },
  ),
)

