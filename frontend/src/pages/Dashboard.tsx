import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, Pause, Pencil, Play, Plus, RotateCcw, Search, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  useCreateProjectMutation,
  useDeleteProjectMutation,
  useProjectActionMutation,
  useProjectsQuery,
  useRenameProjectMutation,
  useSearchQuery,
  useSuggestQuery,
} from '@/hooks/useApi'
import type { ProcessingStatus, Project } from '@/types/api'

const statusClass: Record<ProcessingStatus, string> = {
  QUEUED: 'status queued',
  PROCESSING: 'status processing',
  COMPLETED: 'status completed',
  FAILED: 'status failed',
  PAUSED: 'status paused',
}

export function DashboardPage() {
  const [title, setTitle] = useState('')
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<Project | null>(null)
  const projects = useProjectsQuery()
  const createProject = useCreateProjectMutation()
  const renameProject = useRenameProjectMutation()
  const deleteProject = useDeleteProjectMutation()
  const pauseProject = useProjectActionMutation('pause')
  const resumeProject = useProjectActionMutation('resume')
  const retryProject = useProjectActionMutation('retry')
  const search = useSearchQuery(query)
  const suggest = useSuggestQuery(query)

  const visibleProjects = useMemo(() => projects.data?.items ?? [], [projects.data])

  function submit(event: FormEvent) {
    event.preventDefault()
    const nextTitle = title.trim()
    if (!nextTitle) {
      toast.error('Enter a project title first.')
      return
    }
    createProject.mutate(nextTitle, {
      onSuccess: () => {
        setTitle('')
        toast.success('Project created.')
      },
      onError: () => toast.error('Unable to create project. Please sign in again and retry.'),
    })
  }

  function rename(event: FormEvent) {
    event.preventDefault()
    if (!editing) return
    renameProject.mutate(
      { projectId: editing.project_id, title: editing.title },
      {
        onSuccess: () => setEditing(null),
      },
    )
  }

  return (
    <section className="dashboard">
      <div className="section-header">
        <div>
          <h1>Dashboard</h1>
          <p>{projects.data?.total ?? 0} projects</p>
        </div>
        <form className="create-project" onSubmit={submit}>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Project title"
            aria-label="Project title"
            required
          />
          <button type="submit" disabled={createProject.isPending}>
            <Plus size={16} />
            Create
          </button>
        </form>
      </div>

      <div className="search-row">
        <Search size={18} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search projects" />
      </div>

      {suggest.data && suggest.data.items.length > 0 && (
        <div className="suggestions">
          {suggest.data.items.map((item) => (
            <button key={item} type="button" onClick={() => setQuery(item)}>
              {item}
            </button>
          ))}
        </div>
      )}

      {search.data && (
        <div className="search-results">
          {search.data.items.map((item) => (
            <div key={`${item.project_id}-${item.segment_id ?? 'project'}`}>
              <strong>{item.title}</strong>
              {item.text && <span>{item.text}</span>}
            </div>
          ))}
        </div>
      )}

      <div className="project-table">
        <div className="project-row table-head">
          <span>Title</span>
          <span>Status</span>
          <span>Updated</span>
          <span>Actions</span>
        </div>
        {visibleProjects.map((project) => (
          <div className="project-row" key={project.project_id}>
            <Link className="project-title" to={`/projects/${project.project_id}`}>
              {project.title}
            </Link>
            <span className={statusClass[project.status]}>{project.status}</span>
            <span>{new Date(project.updated_at).toLocaleString()}</span>
            <ProjectActions
              project={project}
              onEdit={() => setEditing(project)}
              onPause={() => pauseProject.mutate(project.project_id)}
              onResume={() => resumeProject.mutate(project.project_id)}
              onRetry={() => retryProject.mutate(project.project_id)}
              onDelete={() => deleteProject.mutate(project.project_id)}
            />
          </div>
        ))}
        {visibleProjects.length === 0 && <div className="empty-state">No projects yet.</div>}
      </div>

      {editing && (
        <div className="modal-backdrop">
          <form className="modal" onSubmit={rename}>
            <h2>Rename project</h2>
            <input
              value={editing.title}
              onChange={(event) => setEditing({ ...editing, title: event.target.value })}
            />
            <div className="modal-actions">
              <button type="button" onClick={() => setEditing(null)}>
                Cancel
              </button>
              <button type="submit">
                <CheckCircle2 size={16} />
                Save
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  )
}

function ProjectActions({
  project,
  onEdit,
  onPause,
  onResume,
  onRetry,
  onDelete,
}: {
  project: Project
  onEdit: () => void
  onPause: () => void
  onResume: () => void
  onRetry: () => void
  onDelete: () => void
}) {
  return (
    <span className="row-actions">
      <button type="button" className="icon-button" onClick={onEdit} aria-label="Rename project">
        <Pencil size={16} />
      </button>
      {project.status === 'PROCESSING' && (
        <button type="button" className="icon-button" onClick={onPause} aria-label="Pause project">
          <Pause size={16} />
        </button>
      )}
      {project.status === 'PAUSED' && (
        <button type="button" className="icon-button" onClick={onResume} aria-label="Resume project">
          <Play size={16} />
        </button>
      )}
      {project.status === 'FAILED' && (
        <button type="button" className="icon-button" onClick={onRetry} aria-label="Retry project">
          <RotateCcw size={16} />
        </button>
      )}
      <button type="button" className="icon-button danger" onClick={onDelete} aria-label="Delete project">
        <Trash2 size={16} />
      </button>
    </span>
  )
}
