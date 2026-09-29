# Production deployment

Production topology: Vercel hosts the Vite frontend, Render runs the FastAPI API and a separate PostgreSQL queue worker, Neon provides PostgreSQL, and Cloudflare R2 stores uploaded media. The app deletes original media after successful transcription but retains project history and editable subtitle tracks.

## 1. Create external services

1. Create a Neon PostgreSQL project and database. Copy its direct (non-pooler) connection URL with SSL enabled; the app runs Alembic migrations at API startup. Set that value as `DATABASE_URL` in the Render environment group.
2. Create a private Cloudflare R2 bucket. Create an R2 API token with object read/write/delete permissions scoped to that bucket. Record the S3 endpoint (`https://<account-id>.r2.cloudflarestorage.com`), bucket name, access key ID, and secret access key.
3. Create a Google AI Studio API key for Gemini and keep it only in Render's secret environment settings.

## 2. Deploy backend and worker to Render

Connect the repository to Render and use the repository's `render.yaml` Blueprint. It creates:

- `subtitle-platform-api`: Docker web service; runs database migrations on startup and serves `/health`.
- `subtitle-platform-worker`: Docker background worker; claims durable tasks from the PostgreSQL queue.

In the shared `subtitle-platform-production` environment group, fill in `DATABASE_URL`, `GEMINI_API_KEY`, `R2_ENDPOINT_URL`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `ADMIN_EMAIL`, and a strong `ADMIN_PASSWORD`. Set `CORS_ORIGINS` to the exact Vercel production origin, e.g. `https://your-project.vercel.app` (comma-separate any additional trusted origins). The Blueprint generates `JWT_SECRET`; never check secrets into the repository.

Keep `STORAGE_BACKEND=r2`, `ASR_PROVIDER=gemini`, `FAKE_ASR=0`, and `FAKE_GEMINI=0` in production. Both Render services must use the same Neon database and R2 credentials. R2 is required because Render's service filesystems are not shared or durable across the API and worker.

After deployment, verify `https://<api-service>.onrender.com/health` reports `status=ok`, `db=true`, `postgres_queue=true`, and `storage=true`. The worker should remain running without restarting.

## 3. Deploy frontend to Vercel

Import the repository into Vercel and set the project root to `frontend`. Use `npm run build` and `dist` as the output directory. Add `VITE_API_URL=https://<api-service>.onrender.com` to the Vercel production environment and redeploy. `frontend/vercel.json` provides client-side route fallback.

The Vercel origin must exactly match an entry in Render's `CORS_ORIGINS`. The frontend uses the same API origin for REST and job WebSocket connections.

## 4. Persistence, privacy, and cost notes

- Neon stores users, projects, subtitle tracks, job history, task queue, and cache; it does not store audio/video bytes.
- Originals upload to the private R2 bucket. On successful server transcription the original media object is deleted; project/file metadata and subtitle history remain. If deletion fails, the error is recorded for administrators and the file metadata remains stored.
- Browser-mode processing keeps audio on the device. Server processing uploads audio to your Render API/R2 and sends audio to Gemini; make this clear to users and configure consent accordingly.
- Render background workers and persistent Neon/R2 use may require paid plans. This configuration does not depend on Docker running on your own computer, but Render builds the services from the included Dockerfiles.
- For local Windows development without Docker, follow the native PostgreSQL, Python worker, FastAPI, and Vite steps in the repository [README](../README.md). Use a local PostgreSQL instance on port 5432 and keep `STORAGE_BACKEND=local`; set `WHISPER_MODEL=medium` and `WHISPER_DEVICE=auto` in `.env`.

## Health and WebSockets

Use HTTPS for the API and WSS for `/ws/jobs/{job_id}`. Render's HTTPS origin is used by both. No Redis service is needed.
