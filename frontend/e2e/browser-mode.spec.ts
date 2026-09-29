import { expect, test } from '@playwright/test'
import {
  createMetadataFile,
  createProject,
  getTracks,
  installAuth,
  registerUser,
  submitClientResult,
  uniqueEmail,
} from './helpers'

test('browser mode posts client result and prompts for local playback media', async ({ page, request }) => {
  const session = await registerUser(request, uniqueEmail('browser'), 'Passw0rd!234', 'Browser User')
  const project = await createProject(request, session.access_token, `Browser mode ${Date.now()}`)
  const media = await createMetadataFile(request, session.access_token, project.project_id)
  await submitClientResult(request, session.access_token, media.file_id)
  const tracks = await getTracks(request, session.access_token, media.file_id)
  const original = tracks.find((track) => track.kind === 'ORIGINAL')
  expect(original).toBeTruthy()

  await installAuth(page, session)
  await page.goto(`/tracks/${original?.track_id}`)
  await expect(page.getByText('This media was processed on your device. Attach the original local file to review playback here.')).toBeVisible()
  await expect(page.getByText('Processed on your device')).toBeVisible()
  await expect(page.getByText('Browser mode works.')).toBeVisible()
})
