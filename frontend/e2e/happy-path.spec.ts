import { expect, test } from '@playwright/test'
import { createWavBuffer, uniqueEmail } from './helpers'

test('registers, processes with fake ASR, edits, exports, and admin sees analytics', async ({ page }) => {
  const email = uniqueEmail('happy')
  const password = 'Passw0rd!234'
  const projectTitle = `Happy path ${Date.now()}`

  await page.goto('/register')
  await page.getByPlaceholder('Name').fill('Happy User')
  await page.getByPlaceholder('Email').fill(email)
  await page.getByPlaceholder('Password').fill(password)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()

  await page.getByPlaceholder('Project title').fill(projectTitle)
  await page.getByRole('button', { name: /Create/ }).click()
  await page.getByRole('link', { name: projectTitle }).click()
  await expect(page.getByRole('heading', { name: projectTitle })).toBeVisible()

  await page.locator('input[type="file"]').setInputFiles({
    name: 'sample.wav',
    mimeType: 'audio/wav',
    buffer: createWavBuffer(),
  })
  await page.getByLabel('Also save media on server').check()
  await page.getByRole('button', { name: 'Upload' }).click()
  await expect(page.getByText(/Server-ready/)).toBeVisible()

  await page.getByLabel('Language').selectOption('en')
  await page.getByLabel('Processing mode').selectOption('server')
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: /Generate subtitles/ }).click()
  await expect(page.getByText('Processed on server')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.track-item').first()).toBeVisible({ timeout: 30_000 })

  await page.locator('.track-item').first().click()
  await expect(page.getByRole('heading', { name: 'Editor' })).toBeVisible()
  const firstSegment = page.locator('.segment-row input').first()
  await expect(firstSegment).toBeVisible()
  await firstSegment.fill('Edited subtitle line')
  await firstSegment.blur()

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: /Export/ }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toContain('.srt')

  await page.getByRole('button', { name: 'Sign out' }).click()
  await page.goto('/login')
  await page.getByPlaceholder('Email').fill('admin@example.local')
  await page.getByPlaceholder('Password').fill('change-me-admin')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await page.getByRole('link', { name: 'Admin' }).click()
  await expect(page.getByRole('heading', { name: 'Admin' })).toBeVisible()
  await expect(page.getByText('Server jobs')).toBeVisible()
})
