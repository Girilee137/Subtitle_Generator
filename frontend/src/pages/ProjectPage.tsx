import { useEffect, useMemo, useState, type ChangeEvent, type DragEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { CheckCircle2, FileVideo, Loader2, UploadCloud } from 'lucide-react'
import { toast } from 'sonner'
import { fileApi, projectApi, subtitleApi, userApi } from '@/api/routes'
import { useJobSocket } from '@/hooks/useJobSocket'
import type { Job, MediaFile } from '@/types/api'

const languageOptions = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'ta', label: 'Tamil' },
  { value: 'en', label: 'English' },
]

export function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const projectId = id ?? ''
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [activeFile, setActiveFile] = useState<MediaFile | null>(null)
  const [language, setLanguage] = useState('auto')
  const [priority, setPriority] = useState(5)
  const [job, setJob] = useState<Job | null>(null)
  const project = useQuery({ queryKey: ['project', projectId], queryFn: () => projectApi.get(projectId), enabled: !!projectId })
  const files = useQuery({ queryKey: ['files', projectId], queryFn: () => fileApi.list(projectId), enabled: !!projectId })
  const latestJob = useQuery({
    queryKey: ['project-job', projectId],
    queryFn: () => projectApi.job(projectId),
    enabled: !!projectId,
    retry: false,
  })
  const quota = useQuery({ queryKey: ['quota'], queryFn: userApi.quota })
  const trackFileId = job?.file_id ?? activeFile?.file_id ?? latestJob.data?.file_id
  const tracks = useQuery({
    queryKey: ['file-tracks', trackFileId],
    queryFn: () => subtitleApi.fileTracks(trackFileId ?? ''),
    enabled: Boolean(trackFileId),
  })
  const refetchTracks = tracks.refetch
  const live = useJobSocket(job?.job_id ?? null)

  const latestProgress = live.event?.progress ?? job?.progress ?? 0
  const latestStage = live.event?.stage ?? job?.stage ?? null
  const latestStatus = live.event?.status ?? job?.status ?? project.data?.status
  const processingError = live.event?.error ?? job?.error ?? latestJob.data?.error
  const serverJobsLeft = quota.data ? Math.max(0, quota.data.server_jobs_limit - quota.data.server_jobs_used) : null

  useEffect(() => {
    if (live.event?.status !== 'COMPLETED') return
    void queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    void queryClient.invalidateQueries({ queryKey: ['files', projectId] })
    void queryClient.invalidateQueries({ queryKey: ['project-job', projectId] })
    if (trackFileId) void refetchTracks()
  }, [live.event?.status, projectId, queryClient, refetchTracks, trackFileId])

  const uploadFile = useMutation({
    mutationFn: async (file: File) => {
      setUploadProgress(0)
      return fileApi.uploadWithProgress(projectId, file, setUploadProgress)
    },
    onSuccess: (media) => {
      setActiveFile(media)
      queryClient.invalidateQueries({ queryKey: ['files', projectId] })
      toast.success('Media uploaded to server.')
    },
    onError: (error) => toast.error(errorMessage(error)),
  })

  const process = useMutation({
    mutationFn: async () => {
      const media = await ensureUploadedFile()
      const accepted = await fileApi.process(media.file_id, { language, priority })
      return projectApi.job(projectId).catch(() => makePendingServerJob(accepted.job_id, media, priority))
    },
    onSuccess: (nextJob) => {
      setJob(nextJob)
      queryClient.invalidateQueries({ queryKey: ['quota'] })
      queryClient.invalidateQueries({ queryKey: ['file-tracks', activeFile?.file_id] })
      toast.success('Server transcription job queued.')
    },
    onError: (error) => toast.error(errorMessage(error)),
  })

  const fileList = useMemo(() => files.data ?? [], [files.data])

  function chooseFile(file: File | null) {
    if (!file) return
    setSelectedFile(file)
    setActiveFile(null)
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    chooseFile(event.dataTransfer.files.item(0))
  }

  function onFileInput(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.item(0) ?? null)
  }

  async function ensureUploadedFile() {
    if (activeFile?.is_stored) return activeFile
    if (!selectedFile) throw new Error('Choose an audio or video file first.')
    const uploaded = await fileApi.uploadWithProgress(projectId, selectedFile, setUploadProgress)
    setActiveFile(uploaded)
    queryClient.invalidateQueries({ queryKey: ['files', projectId] })
    return uploaded
  }

  return (
    <section className="project-page">
      <div className="section-header">
        <div>
          <h1>{project.data?.title ?? 'Project'}</h1>
          <p>{latestStatus ?? 'QUEUED'}</p>
        </div>
        {serverJobsLeft !== null && <span className="quota-pill">{serverJobsLeft} server jobs left today</span>}
      </div>

      <div className="project-grid">
        <div className="dropzone" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
          <UploadCloud size={30} />
          <strong>{selectedFile?.name ?? 'Drop audio or video here'}</strong>
          <input type="file" accept="audio/*,video/*" onChange={onFileInput} />
          <button
            type="button"
            disabled={!selectedFile || uploadFile.isPending}
            onClick={() => selectedFile && uploadFile.mutate(selectedFile)}
          >
            {uploadFile.isPending ? <Loader2 size={16} /> : <UploadCloud size={16} />}
            Upload to server
          </button>
          {uploadProgress > 0 && <progress value={uploadProgress} max={100} />}
        </div>

        <div className="process-panel">
          <label>
            File
            <select value={activeFile?.file_id ?? ''} onChange={(event) => setActiveFile(fileList.find((item) => item.file_id === event.target.value) ?? null)}>
              <option value="">Select uploaded file</option>
              {fileList.filter((f) => f.is_stored).map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.file_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Language
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              {languageOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Priority
            <input type="number" min={0} max={9} value={priority} onChange={(event) => setPriority(Number(event.target.value))} />
          </label>
          <button type="button" disabled={process.isPending || uploadFile.isPending} onClick={() => process.mutate()}>
            {process.isPending ? <Loader2 size={16} /> : <CheckCircle2 size={16} />}
            Generate subtitles
          </button>
        </div>
      </div>

      <div className="progress-panel">
        <span>Progress {Math.round(latestProgress)}%</span>
        <progress value={latestProgress} max={100} />
        <span>
          {latestStage ?? 'waiting'} {live.connected ? 'live' : ''}
        </span>
        {latestStatus === 'FAILED' && (
          <p className="form-error" role="alert">
            Subtitle generation failed: {processingFailureMessage(processingError)}
          </p>
        )}
        {job && <span className="mode-badge server">Processed on server</span>}
      </div>

      <div className="track-list">
        <h2>Tracks</h2>
        {tracks.data?.map((track) => (
          <Link key={track.track_id} to={`/tracks/${track.track_id}`} className="track-item">
            <FileVideo size={18} />
            <span>{track.language}</span>
            <strong>{track.kind}</strong>
          </Link>
        ))}
      </div>
    </section>
  )
}

function makePendingServerJob(jobId: string, media: MediaFile, priority: number): Job {
  return {
    job_id: jobId,
    project_id: media.project_id,
    file_id: media.file_id,
    mode: 'SERVER',
    status: 'PROCESSING',
    stage: 'extract',
    progress: 0,
    priority,
    chunks_total: 0,
    chunks_done: 0,
    error: null,
    celery_root_id: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
}

function errorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const code = (error.response?.data as { code?: string; detail?: string } | undefined)?.code
    if (code === 'DAILY_LIMIT') return 'Daily server processing limit reached. Try again tomorrow.'
    return (error.response?.data as { detail?: string } | undefined)?.detail ?? error.message
  }
  return error instanceof Error ? error.message : 'Something went wrong.'
}

function processingFailureMessage(error: string | null | undefined) {
  if (!error) return 'The worker could not complete this job. Check the worker logs and retry.'
  return error.length > 400 ? `${error.slice(0, 400)}…` : error
}
