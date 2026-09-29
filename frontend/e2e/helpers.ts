import { expect, type APIRequestContext, type Page } from '@playwright/test'

export const apiBase = process.env.E2E_API_URL ?? 'http://localhost:8000/api/v1'

export type AuthSession = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  user: {
    user_id: string
    name: string
    email: string
    role: 'USER' | 'ADMIN'
    is_active: boolean
    storage_used: number
    server_processing_consent_at: string | null
    created_at: string
  }
}

export type ProjectRecord = {
  project_id: string
  title: string
  status: string
}

export type MediaRecord = {
  file_id: string
  project_id: string
  file_name: string
  file_type: string
  size_bytes: number
  duration_seconds: number | null
  is_stored: boolean
  created_at: string
}

export type TrackRecord = {
  track_id: string
  file_id: string
  language: string
  kind: string
}

export function uniqueEmail(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.round(Math.random() * 100_000)}@example.test`
}

export async function registerUser(request: APIRequestContext, email: string, password: string, name = 'E2E User') {
  const response = await request.post(`${apiBase}/auth/register`, {
    data: { name, email, password },
  })
  expect(response.ok()).toBeTruthy()
  return response.json() as Promise<AuthSession>
}

export async function loginUser(request: APIRequestContext, email: string, password: string) {
  const response = await request.post(`${apiBase}/auth/login`, {
    data: { email, password },
  })
  expect(response.ok()).toBeTruthy()
  return response.json() as Promise<AuthSession>
}

export async function createProject(request: APIRequestContext, token: string, title: string) {
  const response = await request.post(`${apiBase}/projects`, {
    headers: authHeaders(token),
    data: { title },
  })
  expect(response.ok()).toBeTruthy()
  return response.json() as Promise<ProjectRecord>
}

export async function createMetadataFile(request: APIRequestContext, token: string, projectId: string) {
  const response = await request.post(`${apiBase}/projects/${projectId}/files/metadata`, {
    headers: authHeaders(token),
    data: {
      file_name: 'local-only.wav',
      file_type: 'audio/wav',
      size_bytes: 32044,
      duration_seconds: 3,
    },
  })
  expect(response.ok()).toBeTruthy()
  return response.json() as Promise<MediaRecord>
}

export async function submitClientResult(request: APIRequestContext, token: string, fileId: string) {
  const response = await request.post(`${apiBase}/files/${fileId}/client-result`, {
    headers: authHeaders(token),
    data: {
      language: 'en',
      model: 'e2e-fixture',
      words: [
        { word: 'Browser', start: 0.1, end: 0.5, prob: 0.97 },
        { word: 'mode', start: 0.55, end: 0.9, prob: 0.95 },
        { word: 'works.', start: 1.0, end: 1.5, prob: 0.96 },
      ],
    },
  })
  expect(response.ok()).toBeTruthy()
  return response.json()
}

export async function getTracks(request: APIRequestContext, token: string, fileId: string) {
  const response = await request.get(`${apiBase}/files/${fileId}/tracks`, {
    headers: authHeaders(token),
  })
  expect(response.ok()).toBeTruthy()
  return response.json() as Promise<TrackRecord[]>
}

export async function installAuth(page: Page, session: AuthSession) {
  await page.addInitScript((payload) => {
    window.localStorage.setItem(
      'subtitle-platform-auth',
      JSON.stringify({
        state: {
          accessToken: payload.access_token,
          refreshToken: payload.refresh_token,
          user: payload.user,
        },
        version: 0,
      }),
    )
  }, session)
}

export function createWavBuffer(seconds = 2, sampleRate = 16_000) {
  const sampleCount = seconds * sampleRate
  const dataSize = sampleCount * 2
  const buffer = Buffer.alloc(44 + dataSize)
  buffer.write('RIFF', 0)
  buffer.writeUInt32LE(36 + dataSize, 4)
  buffer.write('WAVE', 8)
  buffer.write('fmt ', 12)
  buffer.writeUInt32LE(16, 16)
  buffer.writeUInt16LE(1, 20)
  buffer.writeUInt16LE(1, 22)
  buffer.writeUInt32LE(sampleRate, 24)
  buffer.writeUInt32LE(sampleRate * 2, 28)
  buffer.writeUInt16LE(2, 32)
  buffer.writeUInt16LE(16, 34)
  buffer.write('data', 36)
  buffer.writeUInt32LE(dataSize, 40)
  for (let idx = 0; idx < sampleCount; idx += 1) {
    const sample = Math.round(Math.sin((idx / sampleRate) * Math.PI * 2 * 440) * 8000)
    buffer.writeInt16LE(sample, 44 + idx * 2)
  }
  return buffer
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` }
}
