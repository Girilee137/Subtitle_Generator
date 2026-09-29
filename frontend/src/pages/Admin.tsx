import { useMemo, useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { Activity, Download, HardDrive, RefreshCcw, Shield, Trash2, Users } from 'lucide-react'
import { toast } from 'sonner'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { adminApi } from '@/api/routes'
import type { AdminJob, AdminLog, AdminUser, StorageSummary } from '@/types/api'

type AdminTab = 'dashboard' | 'jobs' | 'users' | 'storage' | 'logs' | 'reports'

type ChartPoint = {
  name: string
  value: number
}

const tabs: { id: AdminTab; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'jobs', label: 'Jobs' },
  { id: 'users', label: 'Users' },
  { id: 'storage', label: 'Storage' },
  { id: 'logs', label: 'Logs' },
  { id: 'reports', label: 'Reports' },
]

const chartColors = ['#1f6feb', '#0f766e', '#a16207', '#b91c1c', '#6d28d9', '#475569']

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard')
  const [logLevel, setLogLevel] = useState('')
  const [manualFileId, setManualFileId] = useState('')
  const queryClient = useQueryClient()
  const analytics = useQuery({ queryKey: ['admin', 'analytics'], queryFn: adminApi.analytics })
  const jobs = useQuery({ queryKey: ['admin', 'jobs'], queryFn: adminApi.jobs })
  const usersQuery = useQuery({ queryKey: ['admin', 'users'], queryFn: adminApi.users })
  const storage = useQuery({ queryKey: ['admin', 'storage'], queryFn: adminApi.storage })
  const logs = useQuery({ queryKey: ['admin', 'logs', logLevel], queryFn: () => adminApi.logs(logLevel || undefined) })

  const toggleUser = useMutation({
    mutationFn: ({ userId, active }: { userId: string; active: boolean }) =>
      active ? adminApi.deactivateUser(userId) : adminApi.activateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      toast.success('User status updated.')
    },
    onError: () => toast.error('Unable to update user status.'),
  })

  const deleteUser = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'analytics'] })
      toast.success('User deleted.')
    },
    onError: () => toast.error('Unable to delete user.'),
  })

  const deleteFile = useMutation({
    mutationFn: adminApi.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'storage'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'jobs'] })
      setManualFileId('')
      toast.success('File deleted.')
    },
    onError: () => toast.error('Unable to delete file.'),
  })

  const report = useMutation({
    mutationFn: adminApi.reportBlob,
    onSuccess: (blob, format) => {
      const href = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = href
      anchor.download = `admin-report.${format}`
      anchor.click()
      URL.revokeObjectURL(href)
    },
    onError: () => toast.error('Unable to export report.'),
  })

  const projectStatusData = useMemo(
    () => toChartData(analytics.data?.projects_by_status ?? {}),
    [analytics.data?.projects_by_status],
  )
  const jobsByModeData = useMemo(() => toChartData(analytics.data?.jobs_by_mode ?? {}), [analytics.data?.jobs_by_mode])
  const jobsByDayData = useMemo(() => toChartData(analytics.data?.jobs_by_day ?? {}).sort((a, b) => a.name.localeCompare(b.name)), [analytics.data?.jobs_by_day])

  return (
    <section className="admin-page">
      <div className="section-header">
        <div>
          <h1>Admin</h1>
          <p>Operations, storage, users, reports</p>
        </div>
        <button type="button" className="secondary-action" onClick={() => refreshAdmin(queryClient)}>
          <RefreshCcw size={16} />
          Refresh
        </button>
      </div>

      <div className="admin-tabs" role="tablist" aria-label="Admin sections">
        {tabs.map((tab) => (
          <button key={tab.id} type="button" className={activeTab === tab.id ? 'active' : ''} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'dashboard' && (
        <DashboardPanel
          isLoading={analytics.isLoading}
          isError={analytics.isError}
          users={analytics.data?.users ?? 0}
          activeUsers={analytics.data?.active_users ?? 0}
          serverJobs={analytics.data?.jobs_by_mode.SERVER ?? 0}
          browserJobs={analytics.data?.jobs_by_mode.BROWSER ?? 0}
          storageUsed={analytics.data?.storage_used ?? 0}
          averageSeconds={analytics.data?.avg_processing_seconds ?? null}
          projectStatusData={projectStatusData}
          jobsByModeData={jobsByModeData}
          jobsByDayData={jobsByDayData}
        />
      )}
      {activeTab === 'jobs' && <JobsPanel jobs={jobs.data ?? []} isLoading={jobs.isLoading} isError={jobs.isError} onDeleteFile={(fileId) => deleteFile.mutate(fileId)} />}
      {activeTab === 'users' && (
        <UsersPanel
          users={usersQuery.data ?? []}
          isLoading={usersQuery.isLoading}
          isError={usersQuery.isError}
          onToggle={(user) => toggleUser.mutate({ userId: user.user_id, active: user.is_active })}
          onDelete={(userId) => deleteUser.mutate(userId)}
        />
      )}
      {activeTab === 'storage' && (
        <StoragePanel
          storage={storage.data}
          isLoading={storage.isLoading}
          isError={storage.isError}
          fileId={manualFileId}
          onFileIdChange={setManualFileId}
          onDeleteFile={() => manualFileId.trim() && deleteFile.mutate(manualFileId.trim())}
        />
      )}
      {activeTab === 'logs' && <LogsPanel logs={logs.data ?? []} isLoading={logs.isLoading} isError={logs.isError} level={logLevel} onLevelChange={setLogLevel} />}
      {activeTab === 'reports' && <ReportsPanel isPending={report.isPending} onExport={(format) => report.mutate(format)} />}
    </section>
  )
}

function DashboardPanel({
  isLoading,
  isError,
  users,
  activeUsers,
  serverJobs,
  browserJobs,
  storageUsed,
  averageSeconds,
  projectStatusData,
  jobsByModeData,
  jobsByDayData,
}: {
  isLoading: boolean
  isError: boolean
  users: number
  activeUsers: number
  serverJobs: number
  browserJobs: number
  storageUsed: number
  averageSeconds: number | null
  projectStatusData: ChartPoint[]
  jobsByModeData: ChartPoint[]
  jobsByDayData: ChartPoint[]
}) {
  if (isLoading) return <LoadingState label="Loading analytics" />
  if (isError) return <ErrorState label="Analytics unavailable" />

  return (
    <>
      <div className="metrics admin-metrics">
        <Metric icon={<Users size={18} />} value={users} label="Users" />
        <Metric icon={<Shield size={18} />} value={activeUsers} label="Active" />
        <Metric icon={<Activity size={18} />} value={serverJobs} label="Server jobs" />
        <Metric icon={<HardDrive size={18} />} value={browserJobs} label="Device jobs" />
      </div>
      <div className="admin-chart-grid">
        <ChartPanel title="Projects by status" empty={projectStatusData.length === 0}>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={projectStatusData} dataKey="value" nameKey="name" outerRadius={92} label>
                {projectStatusData.map((entry, index) => (
                  <Cell key={entry.name} fill={chartColors[index % chartColors.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Jobs by mode" empty={jobsByModeData.length === 0}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={jobsByModeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Jobs by day" empty={jobsByDayData.length === 0}>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={jobsByDayData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#1f6feb" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartPanel>
        <div className="admin-panel summary-panel">
          <h2>Processing</h2>
          <strong>{averageSeconds === null ? 'n/a' : `${Math.round(averageSeconds)}s`}</strong>
          <span>Average processing time</span>
          <strong>{formatBytes(storageUsed)}</strong>
          <span>Total storage used</span>
        </div>
      </div>
    </>
  )
}

function JobsPanel({ jobs, isLoading, isError, onDeleteFile }: { jobs: AdminJob[]; isLoading: boolean; isError: boolean; onDeleteFile: (fileId: string) => void }) {
  if (isLoading) return <LoadingState label="Loading jobs" />
  if (isError) return <ErrorState label="Jobs unavailable" />
  if (jobs.length === 0) return <EmptyState label="No jobs yet" />

  return (
    <div className="admin-panel table-panel">
      <div className="admin-table jobs-table">
        <div className="admin-row admin-row-head">
          <span>Status</span>
          <span>Mode</span>
          <span>Stage</span>
          <span>Progress</span>
          <span>File</span>
          <span>Action</span>
        </div>
        {jobs.map((job) => (
          <div className="admin-row" key={job.job_id}>
            <span className={`status ${job.status.toLowerCase()}`}>{job.status}</span>
            <span className={`mode-badge ${job.mode === 'BROWSER' ? 'browser' : 'server'}`}>{job.mode}</span>
            <span>{job.stage ?? 'waiting'}</span>
            <span>{Math.round(job.progress)}% ({job.chunks_done}/{job.chunks_total})</span>
            <code>{shortId(job.file_id)}</code>
            <button type="button" className="icon-button danger" onClick={() => onDeleteFile(job.file_id)} aria-label="Delete file">
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function UsersPanel({
  users,
  isLoading,
  isError,
  onToggle,
  onDelete,
}: {
  users: AdminUser[]
  isLoading: boolean
  isError: boolean
  onToggle: (user: AdminUser) => void
  onDelete: (userId: string) => void
}) {
  if (isLoading) return <LoadingState label="Loading users" />
  if (isError) return <ErrorState label="Users unavailable" />
  if (users.length === 0) return <EmptyState label="No users found" />

  return (
    <div className="admin-panel table-panel">
      <div className="admin-table users-table">
        <div className="admin-row admin-row-head">
          <span>User</span>
          <span>Role</span>
          <span>Status</span>
          <span>Storage</span>
          <span>Actions</span>
        </div>
        {users.map((user) => (
          <div className="admin-row" key={user.user_id}>
            <span>
              <strong>{user.name}</strong>
              <small>{user.email}</small>
            </span>
            <span>{user.role}</span>
            <span className={`status ${user.is_active ? 'completed' : 'paused'}`}>{user.is_active ? 'ACTIVE' : 'INACTIVE'}</span>
            <span>{formatBytes(user.storage_used)}</span>
            <span className="row-actions">
              <button type="button" className="secondary-action compact" onClick={() => onToggle(user)}>
                {user.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button type="button" className="icon-button danger" onClick={() => onDelete(user.user_id)} aria-label="Delete user">
                <Trash2 size={14} />
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function StoragePanel({
  storage,
  isLoading,
  isError,
  fileId,
  onFileIdChange,
  onDeleteFile,
}: {
  storage: StorageSummary | undefined
  isLoading: boolean
  isError: boolean
  fileId: string
  onFileIdChange: (fileId: string) => void
  onDeleteFile: () => void
}) {
  if (isLoading) return <LoadingState label="Loading storage" />
  if (isError) return <ErrorState label="Storage unavailable" />

  return (
    <div className="admin-chart-grid">
      <div className="admin-panel summary-panel">
        <h2>Storage</h2>
        <strong>{formatBytes(storage?.storage_used ?? 0)}</strong>
        <span>Used by stored media</span>
        <strong>{storage?.stored_files_count ?? 0}/{storage?.files_count ?? 0}</strong>
        <span>Stored files / all files</span>
      </div>
      <div className="admin-panel">
        <h2>Delete file</h2>
        <div className="admin-inline-form">
          <input value={fileId} onChange={(event) => onFileIdChange(event.target.value)} placeholder="File UUID" />
          <button type="button" className="danger-action" disabled={!fileId.trim()} onClick={onDeleteFile}>
            <Trash2 size={16} />
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

function LogsPanel({
  logs,
  isLoading,
  isError,
  level,
  onLevelChange,
}: {
  logs: AdminLog[]
  isLoading: boolean
  isError: boolean
  level: string
  onLevelChange: (level: string) => void
}) {
  return (
    <div className="admin-panel table-panel">
      <div className="admin-toolbar">
        <label>
          Level
          <select value={level} onChange={(event) => onLevelChange(event.target.value)}>
            <option value="">All</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </label>
      </div>
      {isLoading && <LoadingState label="Loading logs" />}
      {isError && <ErrorState label="Logs unavailable" />}
      {!isLoading && !isError && logs.length === 0 && <EmptyState label="No logs match this filter" />}
      {!isLoading && !isError && logs.length > 0 && (
        <div className="admin-table logs-table">
          <div className="admin-row admin-row-head">
            <span>Time</span>
            <span>Level</span>
            <span>Action</span>
            <span>Detail</span>
          </div>
          {logs.map((log) => (
            <div className="admin-row" key={log.id}>
              <span>{formatDate(log.ts)}</span>
              <span>{log.level}</span>
              <span>{log.action}</span>
              <code>{JSON.stringify(log.detail)}</code>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ReportsPanel({ isPending, onExport }: { isPending: boolean; onExport: (format: 'csv' | 'json') => void }) {
  return (
    <div className="admin-panel reports-panel">
      <h2>Reports</h2>
      <div className="report-actions">
        <button type="button" disabled={isPending} onClick={() => onExport('csv')}>
          <Download size={16} />
          CSV
        </button>
        <button type="button" disabled={isPending} onClick={() => onExport('json')}>
          <Download size={16} />
          JSON
        </button>
      </div>
    </div>
  )
}

function ChartPanel({ title, empty, children }: { title: string; empty: boolean; children: ReactNode }) {
  return (
    <div className="admin-panel chart-panel">
      <h2>{title}</h2>
      {empty ? <EmptyState label="No data yet" /> : children}
    </div>
  )
}

function Metric({ icon, value, label }: { icon: ReactNode; value: number; label: string }) {
  return (
    <div>
      {icon}
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  )
}

function LoadingState({ label }: { label: string }) {
  return <div className="state-panel loading-state">{label}...</div>
}

function ErrorState({ label }: { label: string }) {
  return <div className="state-panel error-state">{label}</div>
}

function EmptyState({ label }: { label: string }) {
  return <div className="state-panel empty-state">{label}</div>
}

function toChartData(record: Record<string, number>): ChartPoint[] {
  return Object.entries(record).map(([name, value]) => ({ name, value }))
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let size = value / 1024
  let idx = 0
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024
    idx += 1
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[idx]}`
}

function shortId(value: string) {
  return value.slice(0, 8)
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}

function refreshAdmin(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: ['admin'] })
}
