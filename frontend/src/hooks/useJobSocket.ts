import { useEffect, useState } from 'react'
import { apiClient } from '@/api/client'
import { API_URL } from '@/lib/config'
import { useAuthStore } from '@/stores/authStore'
import type { Job, JobStage, ProcessingStatus } from '@/types/api'

export type JobEvent = {
  job_id: string
  status: ProcessingStatus
  stage: JobStage | null
  progress: number
  chunks_done: number
  chunks_total: number
  error?: string | null
}

export function useJobSocket(jobId: string | null) {
  const token = useAuthStore((state) => state.accessToken)
  const [event, setEvent] = useState<JobEvent | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!jobId || !token) return
    const wsBase = API_URL.replace(/^http/, 'ws')
    const socket = new WebSocket(`${wsBase}/ws/jobs/${jobId}?token=${encodeURIComponent(token)}`)
    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = (message) => setEvent(JSON.parse(message.data) as JobEvent)

    const refreshStatus = async () => {
      try {
        const response = await apiClient.get<Job>(`/jobs/${jobId}`)
        const current = response.data
        setEvent({
          job_id: current.job_id,
          status: current.status,
          stage: current.stage,
          progress: current.progress,
          chunks_done: current.chunks_done,
          chunks_total: current.chunks_total,
          error: current.error,
        })
      } catch {
        // WebSocket events remain the primary live path when polling is unavailable.
      }
    }

    void refreshStatus()
    const timer = window.setInterval(refreshStatus, 1000)
    return () => {
      window.clearInterval(timer)
      socket.close()
    }
  }, [jobId, token])

  return { event, connected }
}

