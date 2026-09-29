import type { AxiosProgressEvent } from 'axios'
import type {
  AdminAnalytics,
  AdminJob,
  AdminLog,
  AdminUser,
  ExportFormat,
  Job,
  MediaFile,
  MessageResponse,
  Project,
  ProjectList,
  Quota,
  SearchResult,
  StorageSummary,
  SubtitleTrack,
  TokenPair,
  TrackWithSegments,
  User,
} from '@/types/api'
import { apiClient } from './client'

export const authApi = {
  register: (payload: { name: string; email: string; password: string }) =>
    apiClient.post<TokenPair>('/auth/register', payload).then((res) => res.data),
  login: (payload: { email: string; password: string }) =>
    apiClient.post<TokenPair>('/auth/login', payload).then((res) => res.data),
  forgotPassword: (email: string) =>
    apiClient.post<MessageResponse>('/auth/password/forgot', { email }).then((res) => res.data),
  resetPassword: (payload: { token: string; password: string }) =>
    apiClient.post<MessageResponse>('/auth/password/reset', payload).then((res) => res.data),
}

export const userApi = {
  me: () => apiClient.get<User>('/users/me').then((res) => res.data),
  updateMe: (payload: { name?: string; password?: string }) =>
    apiClient.patch<User>('/users/me', payload).then((res) => res.data),
  consentServerProcessing: () =>
    apiClient.post<MessageResponse>('/users/me/consent/server-processing').then((res) => res.data),
  quota: () => apiClient.get<Quota>('/users/me/quota').then((res) => res.data),
}

export const projectApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiClient.get<ProjectList>('/projects', { params }).then((res) => res.data),
  create: (title: string) => apiClient.post<Project>('/projects', { title }).then((res) => res.data),
  get: (projectId: string) => apiClient.get<Project>(`/projects/${projectId}`).then((res) => res.data),
  rename: (projectId: string, title: string) =>
    apiClient.patch<Project>(`/projects/${projectId}`, { title }).then((res) => res.data),
  delete: (projectId: string) => apiClient.delete(`/projects/${projectId}`),
  pause: (projectId: string) => apiClient.post<Job>(`/projects/${projectId}/pause`).then((res) => res.data),
  resume: (projectId: string) => apiClient.post<Job>(`/projects/${projectId}/resume`).then((res) => res.data),
  retry: (projectId: string) => apiClient.post<Job>(`/projects/${projectId}/retry`).then((res) => res.data),
  job: (projectId: string) => apiClient.get<Job>(`/projects/${projectId}/job`).then((res) => res.data),
}

export const fileApi = {
  upload: (projectId: string, file: File) => {
    const data = new FormData()
    data.append('file', file)
    return apiClient
      .post<MediaFile>(`/projects/${projectId}/files`, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((res) => res.data)
  },
  uploadWithProgress: (projectId: string, file: File, onProgress: (percent: number) => void) => {
    const data = new FormData()
    data.append('file', file)
    return apiClient
      .post<MediaFile>(`/projects/${projectId}/files`, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event: AxiosProgressEvent) => {
          if (event.total) onProgress(Math.round((event.loaded / event.total) * 100))
        },
      })
      .then((res) => res.data)
  },
  metadata: (projectId: string, payload: Omit<MediaFile, 'file_id' | 'project_id' | 'created_at' | 'is_stored'>) =>
    apiClient.post<MediaFile>(`/projects/${projectId}/files/metadata`, payload).then((res) => res.data),
  list: (projectId: string) => apiClient.get<MediaFile[]>(`/projects/${projectId}/files`).then((res) => res.data),
  get: (fileId: string) => apiClient.get<MediaFile>(`/files/${fileId}`).then((res) => res.data),
  delete: (fileId: string) => apiClient.delete(`/files/${fileId}`),
  process: (fileId: string, payload: { language: string; priority: number }) =>
    apiClient.post<{ job_id: string }>(`/files/${fileId}/process`, payload).then((res) => res.data),
  clientResult: (fileId: string, payload: { language: string; model: string; words: unknown[] }) =>
    apiClient.post<Job>(`/files/${fileId}/client-result`, payload).then((res) => res.data),
}

export const subtitleApi = {
  fileTracks: (fileId: string) => apiClient.get<SubtitleTrack[]>(`/files/${fileId}/tracks`).then((res) => res.data),
  track: (trackId: string) => apiClient.get<TrackWithSegments>(`/tracks/${trackId}`).then((res) => res.data),
  editSegment: (segmentId: string, payload: { text?: string; start_time?: number; end_time?: number }) =>
    apiClient.patch(`/segments/${segmentId}`, payload).then((res) => res.data),
  splitSegment: (segmentId: string, payload: { at_time: number; at_char: number }) =>
    apiClient.post(`/segments/${segmentId}/split`, payload).then((res) => res.data),
  mergeTrackSegments: (trackId: string, payload: { segment_a: string; segment_b: string }) =>
    apiClient.post<TrackWithSegments>(`/tracks/${trackId}/merge`, payload).then((res) => res.data),
  shiftTrack: (trackId: string, payload: { offset: number; from_idx?: number }) =>
    apiClient.post<TrackWithSegments>(`/tracks/${trackId}/shift`, payload).then((res) => res.data),
  deleteSegment: (segmentId: string) => apiClient.delete(`/segments/${segmentId}`),
  deleteTrack: (trackId: string) => apiClient.delete(`/tracks/${trackId}`),
  translate: (trackId: string, target_language: string) =>
    apiClient.post<TrackWithSegments>(`/tracks/${trackId}/translate`, { target_language }).then((res) => res.data),
  transliterate: (trackId: string) =>
    apiClient.post<TrackWithSegments>(`/tracks/${trackId}/transliterate`).then((res) => res.data),
  exportUrl: (trackId: string, format: ExportFormat) =>
    `${apiClient.defaults.baseURL}/tracks/${trackId}/export?format=${format}`,
  exportBlob: (trackId: string, format: ExportFormat) =>
    apiClient
      .get<Blob>(`/tracks/${trackId}/export`, { params: { format }, responseType: 'blob' })
      .then((res) => res.data),
}

export const searchApi = {
  search: (q: string) => apiClient.get<{ items: SearchResult[] }>('/search', { params: { q } }).then((res) => res.data),
  suggest: (q: string) => apiClient.get<{ items: string[] }>('/search/suggest', { params: { q } }).then((res) => res.data),
}

export const adminApi = {
  analytics: () => apiClient.get<AdminAnalytics>('/admin/analytics').then((res) => res.data),
  users: () => apiClient.get<AdminUser[]>('/admin/users').then((res) => res.data),
  activateUser: (userId: string) => apiClient.patch<AdminUser>(`/admin/users/${userId}/activate`).then((res) => res.data),
  deactivateUser: (userId: string) => apiClient.patch<AdminUser>(`/admin/users/${userId}/deactivate`).then((res) => res.data),
  deleteUser: (userId: string) => apiClient.delete(`/admin/users/${userId}`),
  deleteFile: (fileId: string) => apiClient.delete(`/admin/files/${fileId}`),
  jobs: () => apiClient.get<AdminJob[]>('/admin/jobs').then((res) => res.data),
  logs: (level?: string) => apiClient.get<AdminLog[]>('/admin/logs', { params: { level } }).then((res) => res.data),
  storage: () => apiClient.get<StorageSummary>('/admin/storage').then((res) => res.data),
  reportUrl: (format: 'csv' | 'json') => `${apiClient.defaults.baseURL}/admin/reports/export?format=${format}`,
  reportBlob: (format: 'csv' | 'json') =>
    apiClient
      .get<Blob>('/admin/reports/export', { params: { format }, responseType: 'blob' })
      .then((res) => res.data),
}
