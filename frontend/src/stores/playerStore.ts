import { create } from 'zustand'

type PlayerState = {
  currentTime: number
  activeSegmentIdx: number | null
  setCurrentTime: (currentTime: number) => void
  setActiveSegmentIdx: (activeSegmentIdx: number | null) => void
}

export const usePlayerStore = create<PlayerState>((set) => ({
  currentTime: 0,
  activeSegmentIdx: null,
  setCurrentTime: (currentTime) => set({ currentTime }),
  setActiveSegmentIdx: (activeSegmentIdx) => set({ activeSegmentIdx }),
}))

