export type Role = 'USER' | 'ADMIN'
export type ProcessingStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'PAUSED'
export type JobMode = 'SERVER' | 'BROWSER'
export type JobStage =
  | 'extract'
  | 'detect_lang'
  | 'vad'
  | 'chunk'
  | 'schedule'
  | 'asr'
  | 'align'
  | 'segment'
  | 'tanglish'
  | 'done'
export type TrackKind = 'ORIGINAL' | 'TRANSLATION' | 'TRANSLITERATION'
export type ExportFormat = 'srt' | 'vtt' | 'txt' | 'html'

export type User = {
  user_id: string
  name: string
  email: string
  role: Role
  is_active: boolean
  storage_used: number
  server_processing_consent_at: string | null
  created_at: string
}

export type TokenPair = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  user: User
}

export type Project = {
  project_id: string
  owner_id: string
  title: string
  status: ProcessingStatus
  created_at: string
  updated_at: string
}

export type ProjectList = {
  items: Project[]
  total: number
}

export type MediaFile = {
  file_id: string
  project_id: string
  file_name: string
  file_type: string
  size_bytes: number
  duration_seconds: number | null
  is_stored: boolean
  created_at: string
}

export type Job = {
  job_id: string
  project_id: string
  file_id: string
  mode: JobMode
  status: ProcessingStatus
  stage: JobStage | null
  progress: number
  priority: number
  chunks_total: number
  chunks_done: number
  error: string | null
  celery_root_id: string | null
  created_at: string
  updated_at: string
}

export type SubtitleSegment = {
  segment_id: string
  track_id: string
  idx: number
  start_time: number
  end_time: number
  text: string
  confidence: number
  created_at: string
  updated_at: string
}

export type SubtitleTrack = {
  track_id: string
  file_id: string
  language: string
  source_language: string | null
  is_translated: boolean
  kind: TrackKind
  created_at: string
  updated_at: string
}

export type TrackWithSegments = SubtitleTrack & {
  segments: SubtitleSegment[]
}

export type AdminAnalytics = {
  users: number
  active_users: number
  projects_by_status: Record<string, number>
  storage_used: number
  jobs_by_mode: Record<string, number>
  jobs_by_day: Record<string, number>
  avg_processing_seconds: number | null
}

export type AdminUser = {
  user_id: string
  name: string
  email: string
  role: Role
  is_active: boolean
  storage_used: number
  created_at: string
}

export type AdminJob = {
  job_id: string
  project_id: string
  file_id: string
  mode: JobMode
  status: ProcessingStatus
  stage: JobStage | null
  progress: number
  chunks_done: number
  chunks_total: number
  error: string | null
  created_at: string
}

export type AdminLog = {
  id: string
  ts: string
  level: string
  actor_id: string | null
  action: string
  detail: Record<string, unknown>
}

export type StorageSummary = {
  storage_used: number
  files_count: number
  stored_files_count: number
}

export type SearchResult = {
  project_id: string
  title: string
  segment_id: string | null
  text: string | null
}

export type Quota = {
  server_jobs_used: number
  server_jobs_limit: number
  storage_used: number
  storage_quota: number
}

export type MessageResponse = {
  detail: string
}
