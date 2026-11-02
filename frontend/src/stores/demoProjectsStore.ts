import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Project } from '@/types/api'

type DemoProjectsState = {
  projects: Project[]
  createProject: (title: string) => void
  renameProject: (projectId: string, title: string) => void
  deleteProject: (projectId: string) => void
}

function createSampleProjects(): Project[] {
  const now = Date.now()
  const samples = [
    { title: 'Tamil interview — sample', status: 'COMPLETED' as const, ageInDays: 1 },
    { title: 'Product walkthrough — sample', status: 'PROCESSING' as const, ageInDays: 3 },
    { title: 'English lecture — sample', status: 'QUEUED' as const, ageInDays: 6 },
  ]

  return samples.map(({ title, status, ageInDays }, index) => {
    const updatedAt = new Date(now - ageInDays * 86_400_000).toISOString()
    return {
      project_id: `demo-project-${index + 1}`,
      owner_id: 'local-demo-user',
      title,
      status,
      created_at: updatedAt,
      updated_at: updatedAt,
    }
  })
}

export const useDemoProjectsStore = create<DemoProjectsState>()(
  persist(
    (set) => ({
      projects: createSampleProjects(),
      createProject: (title) =>
        set((state) => {
          const now = new Date().toISOString()
          return {
            projects: [
              {
                project_id: `demo-project-${crypto.randomUUID()}`,
                owner_id: 'local-demo-user',
                title,
                status: 'QUEUED',
                created_at: now,
                updated_at: now,
              },
              ...state.projects,
            ],
          }
        }),
      renameProject: (projectId, title) =>
        set((state) => ({
          projects: state.projects.map((project) =>
            project.project_id === projectId
              ? { ...project, title, updated_at: new Date().toISOString() }
              : project,
          ),
        })),
      deleteProject: (projectId) =>
        set((state) => ({
          projects: state.projects.filter((project) => project.project_id !== projectId),
        })),
    }),
    { name: 'subtitle-platform-demo-projects' },
  ),
)
