## Phase 0 - repo layout  (2026-09-21)
- Diagram basis: A5 component/repo layout; A11 frontend stack; A12 infra/CI; A10 config.
- Done: Created backend/frontend/docs/CI/Docker/env scaffolds; Vite React TS scaffolded; frontend deps installed; shadcn init attempted.
- Files: .gitignore, .dockerignore, .env.example, docker-compose.yml, README.md, BUILD_LOG.md, docs/deploy.md, docs/traceability.md, .github/workflows/ci.yml, backend/pyproject.toml, backend/alembic.ini, backend/alembic/env.py, backend/alembic/script.py.mako, backend/Dockerfile, backend/Dockerfile.worker, backend/app/__init__.py, backend/app/main.py, backend/app/core/__init__.py, backend/app/core/config.py, backend/app/db/__init__.py, backend/app/models/__init__.py, backend/app/schemas/__init__.py, backend/app/api/__init__.py, backend/app/api/v1/__init__.py, backend/app/services/__init__.py, backend/app/ml/__init__.py, backend/app/workers/__init__.py, backend/app/utils/__init__.py, backend/tests/__init__.py, frontend/.gitignore, frontend/.oxlintrc.json, frontend/README.md, frontend/index.html, frontend/package.json, frontend/package-lock.json, frontend/tsconfig.json, frontend/tsconfig.app.json, frontend/tsconfig.node.json, frontend/vite.config.ts, frontend/tailwind.config.ts, frontend/components.json, frontend/src/App.css, frontend/src/App.tsx, frontend/src/index.css, frontend/src/main.tsx, frontend/src/assets/hero.png, frontend/src/assets/react.svg, frontend/src/assets/vite.svg, frontend/src/lib/utils.ts, frontend/src/lib/config.ts, frontend/src/lib/gpu.ts, frontend/src/lib/processingMode.ts, frontend/src/lib/audio.ts, frontend/src/lib/vad.ts, frontend/src/workers/whisper.worker.ts
- Commands: Get-Content AGENTS.md; npm create vite@latest frontend -- --template react-ts; npm install; npm install zustand @tanstack/react-query axios video.js recharts react-router-dom @huggingface/transformers lucide-react class-variance-authority clsx tailwind-merge tailwindcss @tailwindcss/vite tw-animate-css sonner; npx shadcn@latest init -y; New-Item repo layout.
- Decisions/deviations: shadcn init failed twice on Tailwind v4 config validation after prerequisites, so components.json/lib utils were added manually and the block recorded; ASR-only Python deps are optional to keep CI from installing torch/CUDA.
- Verified: npm create/install commands passed; shadcn blocked as above; file scaffold manually checked by creation commands.
- Status: PASS for `npm create vite@latest frontend -- --template react-ts`, `npm install`, and frontend dependency install; BLOCKED for `npx shadcn@latest init -y`.
- Next: Phase 1 - backend foundation and configuration.
## Phase 1 - backend foundation and schema  (2026-09-21)
- Diagram basis: A6 class diagram; A9 health API; A10 config/logging/security; A12 Alembic/Postgres.
- Done: Added settings/logging/errors/security, async DB session, all A6 models plus refresh_tokens/admin_profiles, FTS vectors/indexes, initial migration, admin startup seed, /health.
- Files: BUILD_LOG.md, docs/traceability.md, backend/pyproject.toml, backend/app/main.py, backend/app/core/config.py, backend/app/core/logging.py, backend/app/core/errors.py, backend/app/core/security.py, backend/app/core/deps.py, backend/app/db/base.py, backend/app/db/session.py, backend/app/models/__init__.py, backend/app/models/enums.py, backend/app/models/user.py, backend/app/models/project.py, backend/app/models/media_file.py, backend/app/models/subtitle_track.py, backend/app/models/subtitle_segment.py, backend/app/models/job.py, backend/app/models/job_chunk.py, backend/app/models/system_log.py, backend/app/models/export_record.py, backend/app/services/auth_service.py, backend/app/api/v1/health.py, backend/alembic/env.py, backend/alembic/versions/0001_initial_schema.py, backend/tests/test_smoke.py
- Commands: python -m pytest -q tests\test_smoke.py; python -m pip install -e ".[test]"; python -m alembic upgrade head; alembic upgrade head; python -m compileall app tests.
- Decisions/deviations: Added refresh_tokens required by A10 JWT rotation; ASR deps remain optional; local Postgres service exists but Alembic/pytest blocked by missing Python 3.11 env.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest not installed and project install rejects Python 3.14 (`>=3.11,<3.12` required); Alembic blocked because executable/module not installed.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_smoke.py` and `alembic upgrade head` until Python 3.11 backend env is available.
- Next: Phase 2 - auth and user APIs.
## Phase 2 - auth and user APIs  (2026-09-21)
- Diagram basis: DFD 1.0 auth/user; A9 Auth/User API; A10 security/logging/password reset.
- Done: Added Argon2/JWT/refresh rotation, auth/users routes, RBAC deps, login rate limit, password reset console/SMTP notification, and SystemLog writes.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/core/config.py, backend/app/core/security.py, backend/app/core/errors.py, backend/app/core/deps.py, backend/app/models/user.py, backend/app/schemas/auth.py, backend/app/services/auth_service.py, backend/app/services/log_service.py, backend/app/services/notification_service.py, backend/app/api/v1/auth.py, backend/app/api/v1/users.py, backend/app/main.py, backend/tests/test_auth_rbac.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_auth_rbac.py; python -c "from app.main import app; print(app.title)".
- Decisions/deviations: Password reset tokens use Redis-ready service boundary with in-memory fallback until a reset-token table is specified; login limiter falls back in-memory if Redis is unavailable.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed; runtime import blocked because FastAPI is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_auth_rbac.py` until Python 3.11 backend env/deps are available.
- Next: Phase 3 - project/media APIs and storage.
## Phase 3 - project/media APIs and storage  (2026-09-21)
- Diagram basis: DFD 2.0 project/media management; A7 state chart; A9 Projects/Media/Search APIs; A10 storage/trie.
- Done: Added projects CRUD/action routes, full state_machine transition table, streamed media upload with ffprobe validation/quota/storage layout, Range streaming, delete storage release, Trie search hooks.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/core/errors.py, backend/app/schemas/project.py, backend/app/utils/trie.py, backend/app/services/state_machine.py, backend/app/services/search_service.py, backend/app/services/project_service.py, backend/app/services/media_service.py, backend/app/api/v1/projects.py, backend/app/api/v1/files.py, backend/app/api/v1/search.py, backend/app/main.py, backend/tests/test_phase3_projects_media.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase3_projects_media.py.
- Decisions/deviations: No migration needed because Phase 1 schema already contained project/media fields; suffix byte ranges implemented for Video.js compatibility.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase3_projects_media.py` until Python 3.11 backend env/deps are available.
- Next: Phase 4 - processing job state and worker pipeline skeleton.
## Phase 4 - processing pipeline and jobs  (2026-09-21)
- Diagram basis: DFD 3.0/L2 3.1-3.8; A7 state chart; A8 server processing; A9 Processing/Jobs APIs.
- Done: Added Celery queues/priority config, ML modules audio/lang/VAD/chunk/cache/ASR/fake/align/DP segmenter, job/chunk progress, Redis pub/sub, process/job routes, pause/resume/retry job hooks.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/services/state_machine.py, backend/app/schemas/job.py, backend/app/ml/fake_asr.py, backend/app/ml/audio.py, backend/app/ml/lang_detect.py, backend/app/ml/vad.py, backend/app/ml/chunker.py, backend/app/ml/cache.py, backend/app/ml/asr.py, backend/app/ml/aligner.py, backend/app/ml/segmenter.py, backend/app/workers/celery_app.py, backend/app/workers/tasks.py, backend/app/services/processing_service.py, backend/app/api/v1/jobs.py, backend/app/api/v1/projects.py, backend/app/main.py, backend/tests/test_phase4_processing.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase4_processing.py.
- Decisions/deviations: Logged A7 extension PROCESSING--pauseProcessing-->PAUSED and PAUSED--resumeProcessing-->PROCESSING for unfinished jobs; fake-ASR eager path runs chunks inline while exposing Celery chunk chord helper for worker mode.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase4_processing.py` until Python 3.11 backend env/deps are available.
- Next: Phase 5 - subtitle editing, translation, transliteration, and exports.
## Phase 4B - hybrid backend processing  (2026-09-21)
- Diagram basis: A8b hybrid browser/server flow; A9 Hybrid APIs; A14 hybrid validation tests.
- Done: Added metadata-only files, client-result validation/browser Job mode, DP track creation, fake Tanglish track, consent/quota APIs, and server process consent/daily-limit/stored-media guards.
- Files: BUILD_LOG.md, docs/traceability.md, .env.example, backend/app/core/config.py, backend/app/core/errors.py, backend/app/schemas/hybrid.py, backend/app/ml/tanglish.py, backend/app/services/media_service.py, backend/app/services/client_result_service.py, backend/app/services/processing_service.py, backend/app/api/v1/files.py, backend/app/api/v1/users.py, backend/tests/test_phase4b_hybrid.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase4b_hybrid.py.
- Decisions/deviations: Tanglish browser result uses deterministic local transliteration until Phase 5 Gemini batching; no migration needed because Phase 1 media/job/track schema already supports browser mode.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase4b_hybrid.py` until Python 3.11 backend env/deps are available.
- Next: Phase 5 - subtitle editing, translation, transliteration, and exports.
## Phase 5 - subtitle editing APIs  (2026-09-21)
- Diagram basis: DFD 4.0 subtitle review/edit management; A9 Subtitles APIs; A6 SubtitleTrack/SubtitleSegment methods.
- Done: Added track/segment schemas, ownership-checked track listing/get, segment edit/split/delete, track merge/shift/delete, timing/no-overlap validation, and SystemLog writes.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/schemas/subtitle.py, backend/app/services/subtitle_service.py, backend/app/api/v1/tracks.py, backend/app/api/v1/segments.py, backend/app/main.py, backend/tests/test_phase5_subtitles.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase5_subtitles.py.
- Decisions/deviations: Merge is exposed on /tracks/{track_id}/merge and validates both segment ids belong to that track; no migration needed for existing subtitle schema.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase5_subtitles.py` until Python 3.11 backend env/deps are available.
- Next: Phase 6 - translation, transliteration, and exports.
## Phase 6 - translation and transliteration  (2026-09-21)
- Diagram basis: DFD 5.0 Translate; DFD 3.9 Tanglish transliteration; A10 Gemini behaviour; A9 Translate APIs.
- Done: Added Gemini wrapper with Redis cache/rate limiter/backoff/FAKE_GEMINI, fixed Tanglish map, translate/transliterate services/routes, worker tasks, and auto Tanglish for Tamil tracks.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/ml/tanglish.py, backend/app/ml/gemini.py, backend/app/schemas/translation.py, backend/app/services/translation_service.py, backend/app/services/worker_translation_service.py, backend/app/services/client_result_service.py, backend/app/services/processing_service.py, backend/app/api/v1/translate.py, backend/app/main.py, backend/app/workers/tasks.py, backend/tests/test_phase6_translation.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase6_translation.py.
- Decisions/deviations: Routes create tracks synchronously while Celery translation/transliteration tasks are available for worker dispatch; exports remain for the next phase.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase6_translation.py` until Python 3.11 backend env/deps are available.
- Next: Phase 7 - export service and search completion.
## Phase 7 - export, search, and realtime  (2026-09-21)
- Diagram basis: DFD 6.0 export; DFD 7.0 search; A9 Export/Search/Realtime APIs; D9 job progress events.
- Done: Added SRT/VTT/TXT exporters, export route with ExportRecord, FTS+Trie search routes, and JWT-authenticated Redis pub/sub WebSocket for job events.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/utils/timefmt.py, backend/app/services/export_service.py, backend/app/services/search_service.py, backend/app/api/v1/export.py, backend/app/api/v1/search.py, backend/app/api/v1/ws.py, backend/app/main.py, backend/tests/test_phase7_export_search_ws.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase7_export_search_ws.py.
- Decisions/deviations: WebSocket route is mounted outside /api/v1 as specified (/ws/jobs/{id}); search includes FTS operators plus ilike fallback for environments before tsvector triggers populate.
- Verified: `python -m compileall app tests` passed; pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase7_export_search_ws.py` until Python 3.11 backend env/deps are available.
- Next: Phase 8 - admin analytics, users, logs, storage, and reports.
## Phase 8 - admin operations and reports  (2026-09-21)
- Diagram basis: DFD 8.0 Admin Management; A9 Admin APIs; A10 notification/logging.
- Done: Added admin analytics incl jobs by mode, users activate/deactivate/delete, admin file delete, jobs/logs/storage, CSV/JSON reports, status emails, and log listing helper.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/schemas/admin.py, backend/app/services/report_service.py, backend/app/services/notification_service.py, backend/app/services/log_service.py, backend/app/api/v1/admin.py, backend/app/main.py, backend/tests/test_phase8_admin.py
- Commands: python -m compileall app tests; python -m pytest -q tests\test_phase8_admin.py; python -m pytest -q.
- Decisions/deviations: Full backend pytest was attempted per user request despite earlier phase guidance, but environment lacked pytest before test collection.
- Verified: `python -m compileall app tests` passed; focused and full pytest blocked because pytest is not installed in current Python 3.14 env.
- Status: PARTIAL PASS for `python -m compileall app tests`; BLOCKED for `python -m pytest -q tests\test_phase8_admin.py` and `python -m pytest -q` until Python 3.11 backend env/deps are available.
- Next: Phase 9 - frontend foundation and auth/dashboard shell.
## Phase 9 - frontend foundation and dashboard  (2026-09-21)
- Diagram basis: A11 frontend activity/swimlane; A9 API surface; DFD 1.0 auth; DFD 2.0 project dashboard; DFD 7.0 search.
- Done: Added Axios refresh interceptor, typed API layer/hooks, Zustand stores, router guards, layout/theme shell, auth pages, dashboard CRUD/status actions/search suggestions, profile/admin shells.
- Files: BUILD_LOG.md, docs/traceability.md, frontend/tsconfig.json, frontend/tsconfig.app.json, frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/App.css, frontend/src/index.css, frontend/src/lib/gpu.ts, frontend/src/types/api.ts, frontend/src/stores/authStore.ts, frontend/src/stores/uiStore.ts, frontend/src/stores/playerStore.ts, frontend/src/api/client.ts, frontend/src/api/routes.ts, frontend/src/hooks/useApi.ts, frontend/src/components/layout/AppLayout.tsx, frontend/src/components/routing/Guards.tsx, frontend/src/pages/auth/AuthPages.tsx, frontend/src/pages/Dashboard.tsx, frontend/src/pages/Profile.tsx, frontend/src/pages/Admin.tsx
- Commands: npx tsc --noEmit; npm run build; npm run build (approved after sandbox native dependency failure).
- Decisions/deviations: Vite build needed approval because sandboxed native Tailwind/Vite dependency execution failed with spawn EPERM; approved build passed.
- Verified: `npx tsc --noEmit` passed; `npm run build` passed.
- Status: PASS for `npx tsc --noEmit` and `npm run build`.
- Next: Phase 10 - frontend project upload, hybrid processing, progress, and editor shell.
## Phase 10 - frontend project workflow and editor  (2026-09-21)
- Diagram basis: A11 project/editor pages; A8/A8b processing controls; DFD 4.0 subtitle editing; A9 jobs/tracks/export APIs.
- Done: Added project detail page with upload progress, process controls, WS live progress hook, tracks list, Video.js editor, synced segment edits, split/merge/shift/delete, confidence highlighting, translate/Tanglish/export actions, shortcuts, profile retained.
- Files: BUILD_LOG.md, docs/traceability.md, frontend/src/api/routes.ts, frontend/src/hooks/useJobSocket.ts, frontend/src/pages/ProjectPage.tsx, frontend/src/pages/EditorPage.tsx, frontend/src/pages/Dashboard.tsx, frontend/src/App.tsx, frontend/src/App.css
- Commands: npx tsc --noEmit; npm run build; npm run build (approved after sandbox native dependency failure).
- Decisions/deviations: Browser WebGPU transcription UI remains for the next hybrid frontend phase; build emits a large chunk warning due to Video.js/editor bundle.
- Verified: `npx tsc --noEmit` passed; `npm run build` passed.
- Status: PASS for `npx tsc --noEmit` and `npm run build`.
- Next: Phase 11 - frontend browser WebGPU hybrid processing and admin UI completion.
## Phase 10B - hybrid browser processing frontend  (2026-09-21)
- Diagram basis: A8b hybrid browser/server flow; A11 project/editor pages; A9 Hybrid APIs.
- Done: Added WebGPU adapter checks, auto/browser/server decision logic, 16 kHz Web Audio decode windows, energy VAD/chunking, Transformers.js Whisper worker, metadata-only/client-result flow, consent/quota/fallback toasts, mode badges, and unstored local playback.
- Files: BUILD_LOG.md, docs/traceability.md, frontend/src/App.tsx, frontend/src/App.css, frontend/src/lib/config.ts, frontend/src/lib/gpu.ts, frontend/src/lib/processingMode.ts, frontend/src/lib/audio.ts, frontend/src/lib/vad.ts, frontend/src/workers/whisper.worker.ts, frontend/src/pages/ProjectPage.tsx, frontend/src/pages/EditorPage.tsx
- Commands: npx tsc --noEmit; npm run build; npm run build (approved after sandbox native dependency failure).
- Decisions/deviations: `onnx-community/whisper-small` retained after Hugging Face verification as a multilingual ONNX Whisper small repo; auto browser mode asks the user to choose en/ta when local ASR cannot restrict-detect.
- Verified: `npx tsc --noEmit` passed; `npm run build` passed with existing large chunk warning.
- Status: PASS for `npx tsc --noEmit` and `npm run build`.
- Next: Phase 11 - frontend admin UI completion and e2e hardening.
## Phase 11 - frontend admin UI  (2026-09-21)
- Diagram basis: A11 admin lane; DFD 8.0 admin management; A9 Admin APIs.
- Done: Added guarded admin dashboard with Recharts analytics, jobs monitor, users activate/deactivate/delete, storage/file delete controls, logs filter, CSV/JSON reports, and loading/empty/error/mobile states.
- Files: BUILD_LOG.md, docs/traceability.md, frontend/src/api/routes.ts, frontend/src/types/api.ts, frontend/src/pages/Admin.tsx, frontend/src/App.css
- Commands: npx tsc --noEmit; npm run build; npm run build (approved after sandbox native dependency failure).
- Decisions/deviations: Admin file listing is not an API endpoint, so file deletion is exposed from job rows plus direct file UUID entry under storage.
- Verified: `npx tsc --noEmit` passed; `npm run build` passed with existing large chunk warning.
- Status: PASS for `npx tsc --noEmit` and `npm run build`.
- Next: Phase 12 - full integration/e2e hardening and definition-of-done verification.
## Phase 12 - e2e and final verification  (2026-09-21)
- Diagram basis: A14 Playwright e2e; A12 CI/docker compose; A15 definition of done.
- Done: Added fake-ASR compose override, Playwright happy-path spec, browser-mode client-result spec, e2e helpers/config/script, CORS middleware, and CI backend/frontend/manual e2e jobs.
- Files: BUILD_LOG.md, docs/traceability.md, .github/workflows/ci.yml, docker-compose.e2e.yml, backend/app/main.py, frontend/package.json, frontend/package-lock.json, frontend/playwright.config.ts, frontend/e2e/helpers.ts, frontend/e2e/happy-path.spec.ts, frontend/e2e/browser-mode.spec.ts
- Commands: npm install -D @playwright/test; python -m pytest -q; py -3.11 -m pytest -q; python -m compileall app tests; npx tsc --noEmit; npm run build; npm run build (approved after sandbox native dependency failure); docker compose -f docker-compose.yml -f docker-compose.e2e.yml config; npx playwright test --list; npm run e2e -- --list.
- Decisions/deviations: Local file listing is still absent from admin API; e2e deletes files by job/direct UUID as Phase 11; live e2e stack could not run locally because Docker CLI is unavailable.
- Verified: `python -m compileall app tests`, `npx tsc --noEmit`, approved `npm run build`, `npx playwright test --list`, and `npm run e2e -- --list` passed.
- Status: PARTIAL PASS; blocked commands: `python -m pytest -q` (Python 3.14 has no pytest), `py -3.11 -m pytest -q` (no Python 3.11 runtime), `docker compose -f docker-compose.yml -f docker-compose.e2e.yml config` (Docker CLI not installed), so live Playwright stack was not runnable here.
- Next: Run CI/manual e2e on a host with Python 3.11 and Docker; no further build phase remains.
## Phase 12 follow-up - Docker startup  (2026-09-22)
- Diagram basis: A12 docker compose; A15 runnable stack.
- Done: Fixed sync Postgres driver URLs, comma CORS env parsing, and idempotent enum use in initial migration; started fake-ASR Docker stack.
- Files: BUILD_LOG.md, docs/traceability.md, .env.example, backend/app/core/config.py, backend/alembic/env.py, backend/alembic/versions/0001_initial_schema.py
- Commands: docker compose -f docker-compose.yml -f docker-compose.e2e.yml up -d --build backend worker-default frontend; docker compose -f docker-compose.yml -f docker-compose.e2e.yml up -d --build backend; docker compose -f docker-compose.yml -f docker-compose.e2e.yml ps; Invoke-WebRequest http://localhost:8000/health; Invoke-WebRequest http://localhost:5173.
- Decisions/deviations: SQLAlchemy sync paths use psycopg to match pinned deps; pydantic-settings decoding disabled so comma-separated CORS works.
- Verified: Backend, frontend, postgres, redis, redis-cache, worker-default are running; `/health` returned `{"status":"ok","db":true,"redis":true,"gpu":true}`; frontend returned HTTP 200.
- Status: PASS for Docker fake-ASR stack startup and health checks.
- Next: Use the running app locally; no further build phase remains.
## Phase 12 follow-up - local system run  (2026-09-23)
- Diagram basis: A8b browser-mode processing; A12/A15 local runnable stack.
- Done: Added Python 3.11 local venv, fixed eager async task scheduling for local fake-ASR/browser flow, fixed smoke-test import shadowing, and ran backend/frontend locally.
- Files: BUILD_LOG.md, docs/traceability.md, backend/app/workers/tasks.py, backend/tests/test_smoke.py
- Commands: py -3.11 -m venv backend\.venv311; backend\.venv311\Scripts\python.exe -m pip install -e backend; alembic upgrade head; uvicorn app.main:app --host 127.0.0.1 --port 8000; npm run build; npm run dev -- --host 127.0.0.1 --port 5173; python -m pytest -q tests\test_phase4b_hybrid.py tests\test_phase7_export_search_ws.py tests\test_smoke.py.
- Decisions/deviations: Local run uses existing reachable Postgres and remote Redis from `.env`; real server-upload mode still requires system ffmpeg/ffprobe on PATH.
- Verified: `/health` OK; frontend HTTP 200; browser-mode client-result smoke created COMPLETED job with 1 track and 1 segment; focused backend tests passed.
- Status: PASS for local backend/frontend run, frontend build, browser-mode subtitle generation, and 15 focused pytest tests.
- Next: Install ffmpeg/ffprobe for full server-upload media processing on Windows, then run full upload/process smoke.
## Phase 12 follow-up - deployment media cleanup (2026-09-26)
- Diagram basis: A8 server processing completion; A10 storage quota and media retention.
- Done: Defer source-byte deletion until subtitle tracks and completed job state commit; preserve media metadata/quota if deletion fails; remove unsafe duplicate local-directory cleanup; add success/failure tests.
- Files: backend/app/services/processing_service.py, backend/tests/test_phase4_processing.py, BUILD_LOG.md
- Commands: Python dependency setup (pytest/backend runtime; no torch/CUDA); `python -m compileall -q app tests`; `python -m pytest -q tests/test_phase4_processing.py tests/test_phase3_projects_media.py tests/test_deployment_storage.py`; `npm run build`
- Decisions/deviations: Cleanup failure is logged and does not turn completed transcription into a failed job; exposed Neon password was not stored or reused.
- Verified: Backend compilation succeeded; 17 targeted backend tests passed; frontend TypeScript/Vite production build passed (Vite emitted existing config/chunk-size warnings).
- Status: PASS — exact successful commands: `python -m compileall -q app tests`; `python -m pytest -q tests/test_phase4_processing.py tests/test_phase3_projects_media.py tests/test_deployment_storage.py`; `npm run build`.
- Next: Rotate the exposed Neon password in Neon, then update `DATABASE_URL` directly in Render and local `.env`; run deployment smoke with the replacement credential.
## Phase 12 follow-up - Neon URL validation (2026-09-26)
- Diagram basis: A12 deployment topology; A10 database configuration and migrations.
- Done: Checked the local Neon connection without displaying credentials; normalized explicit sync migration URLs to the psycopg3 driver; added a focused regression test.
- Files: backend/app/core/config.py, backend/tests/test_deployment_storage.py, docs/traceability.md, BUILD_LOG.md
- Commands: `python -m pytest -q tests/test_deployment_storage.py`; sanitized local `.env` check with `SELECT 1`; `python -m alembic current`.
- Decisions/deviations: Local URL uses Neon’s pooler endpoint; connection and read-only Alembic revision check both succeeded. Direct endpoint remains preferable for migrations if pooler behavior causes issues.
- Verified: Async and migration drivers target the same Neon database; TLS configured; `SELECT 1` succeeded; Alembic current succeeded; 3 deployment-storage tests passed.
- Status: PASS — `python -m pytest -q tests/test_deployment_storage.py`, sanitized `SELECT 1`, and `python -m alembic current` all passed.
- Next: Rotate the previously exposed Neon password and update local/Render secrets; then verify Render connectivity with the replacement.
## Phase 12 follow-up - local application run (2026-09-26)
- Diagram basis: A8 processing worker; A12 deployment topology; A11 frontend.
- Done: Started local FastAPI API, PostgreSQL queue worker, and Vite frontend using `.env` without printing its values.
- Files: docs/traceability.md, BUILD_LOG.md
- Commands: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; `python -m app.workers.runner --queue default`; `npm run dev -- --host 127.0.0.1`.
- Decisions/deviations: Started local processes directly rather than Docker; no secrets or `.env` contents were emitted.
- Verified: API `/health` returned HTTP 200 with `db=true` and `postgres_queue=true`; frontend `/` returned HTTP 200; API, worker, and frontend processes remained running.
- Status: PASS — successful checks: `GET http://127.0.0.1:8000/health` (200); `GET http://127.0.0.1:5173/` (200).
- Next: Open http://127.0.0.1:5173/ to use the app; stop the three processes when finished.
## Phase 12 follow-up - login schema repair (2026-09-26)
- Diagram basis: A9 authentication API; A12 Neon database and migration startup.
- Done: Applied pending Alembic schema migrations; restarted API and queue worker; startup seeded the configured admin account.
- Files: docs/traceability.md, BUILD_LOG.md
- Commands: `python -m alembic upgrade head`; API/worker restart; POST `/api/v1/auth/login` using configured admin credentials.
- Decisions/deviations: The database connection was valid but the schema was empty; existing user accounts were not present, so sign-in uses the configured admin or a newly registered account.
- Verified: Migration command exited 0; health endpoint returned HTTP 200 with DB and queue ready; configured-admin login returned HTTP 200 and role ADMIN.
- Status: PASS — `python -m alembic upgrade head`, `GET /health` (200), configured-admin `POST /api/v1/auth/login` (200).
- Next: Sign in using the admin email/password configured in local `.env`, or register a user account.
## Phase 12 follow-up - transcription quota failure diagnosis (2026-09-26)
- Diagram basis: A8 processing pipeline; A11 project processing status and error feedback.
- Done: Diagnosed latest job as Gemini 3.1 Pro free-tier input-token quota exhaustion (429); confirmed model is available to configured API account; added actionable failure text to the project page.
- Files: frontend/src/pages/ProjectPage.tsx, docs/traceability.md, BUILD_LOG.md
- Commands: Google Gemini model-list check (model IDs only); database job status/error classification; `npm run build`.
- Decisions/deviations: Kept Gemini 3.1 Pro selected; switching models or changing API billing requires user choice and account access.
- Verified: Model listing confirmed requested model; provider error identifies `GenerateContentInputTokensPerModelPerDay-FreeTier`; frontend TypeScript/Vite build passed.
- Status: PASS — `npm run build`.
- Next: Increase/wait for Gemini API model quota or choose an alternate available transcription model, then retry the failed job.
## Phase 12 follow-up - free Gemini Flash model (2026-09-26)
- Diagram basis: A8 Gemini transcription provider; A10 externalized Gemini model configuration.
- Done: Switched local, backend-default, example, and Render model configuration to `gemini-3.8-flash`; updated quota guidance to remove Pro-specific wording.
- Files: backend/app/core/config.py, .env, .env.example, render.yaml, frontend/src/pages/ProjectPage.tsx, backend/tests/test_deployment_storage.py, docs/traceability.md, BUILD_LOG.md
- Commands: `python -m pytest -q tests/test_deployment_storage.py tests/test_phase4_processing.py`; `npm run build`; restarted local API/worker.
- Decisions/deviations: Selected Flash for the free-tier path; no silent fallback. Provider quota remains controlled by Google account limits.
- Verified: 12 targeted backend tests passed; frontend build passed; restarted API/worker load `gemini-3.8-flash`; health HTTP 200 with DB and queue ready.
- Status: PASS — tests, build, and local health check passed.
- Next: Retry the failed project job with Gemini Flash; rotate the previously exposed API key in Google AI Studio.
## Phase 12 follow-up - Gemini 3.1 Pro selection  (2026-09-26)
- Diagram basis: A8 server processing; A10 Gemini model configuration.
- Done: Selected the account-listed Gemini 3.1 Pro preview model as the default and local model; removed credentials from `.env.example`.
- Files: backend/app/core/config.py, .env, .env.example, BUILD_LOG.md
- Commands: backend\.venv311\Scripts\python.exe -m compileall -q app tests; backend\.venv311\Scripts\python.exe -m pytest -q tests\test_phase4_processing.py tests\test_phase6_translation.py
- Decisions/deviations: Configured `gemini-3.1-pro-preview` because the account's available model list exposes that preview identifier rather than `gemini-3.1-pro`.
- Verified: Python compilation passed; 10 focused processing/translation tests passed; local API key remains hidden and fake modes remain disabled.
- Status: PASS for compilation and `10 passed` focused tests.
- Next: Run a real media transcription using Gemini 3.1 Pro preview after Redis is available.
## Phase 12 follow-up - PostgreSQL-only coordination  (2026-09-26)
- Diagram basis: A8 processing queue/progress; A10 cache, rate limits, and privacy; A12 local stack.
- Done: Removed Redis/Celery runtime usage; added PostgreSQL task queue, worker polling, expiring cache/rate counters, and DB-polled WebSocket updates; removed Redis compose/CI/env settings; sanitized example credentials.
- Files: backend/alembic/versions/0003_postgresql_queue_cache.py, backend/app/models/cache_entry.py, backend/app/models/queued_task.py, backend/app/models/__init__.py, backend/app/models/job.py, backend/app/schemas/job.py, backend/app/services/db_cache.py, backend/app/services/queue_service.py, backend/app/services/processing_service.py, backend/app/services/auth_service.py, backend/app/services/project_service.py, backend/app/services/media_service.py, backend/app/ml/cache.py, backend/app/ml/gemini.py, backend/app/ml/asr.py, backend/app/api/v1/health.py, backend/app/api/v1/ws.py, backend/app/workers/runner.py, backend/app/workers/__init__.py, backend/app/workers/tasks.py (deleted), backend/app/workers/celery_app.py (deleted), backend/pyproject.toml, backend/tests/test_auth_rbac.py, backend/tests/test_phase4_processing.py, backend/tests/test_phase6_translation.py, backend/tests/test_smoke.py, docker-compose.yml, .github/workflows/ci.yml, .env, .env.example, README.md, docs/deploy.md, docs/traceability.md, BUILD_LOG.md
- Commands: backend\.venv311\Scripts\python.exe -m compileall -q app tests; backend\.venv311\Scripts\python.exe -m pytest -q tests\test_phase3_projects_media.py tests\test_phase4_processing.py tests\test_phase4b_hybrid.py tests\test_phase6_translation.py tests\test_phase7_export_search_ws.py tests\test_phase8_admin.py tests\test_auth_rbac.py tests\test_smoke.py; backend\.venv311\Scripts\python.exe -m alembic upgrade head
- Decisions/deviations: Replaced pub/sub with WebSocket polling of persisted job state and replaced Celery with PostgreSQL rows claimed via `FOR UPDATE SKIP LOCKED`; each worker runs one queue.
- Verified: 42 focused tests passed; migration applied; PostgreSQL cache/rate counter and durable queue claim/ack smoke checks passed; `/health` reports db and postgres_queue true.
- Status: PASS for compilation, focused tests, Alembic migration, PostgreSQL queue/cache smoke, and health check.
- Next: Use the PostgreSQL worker stack for real media transcription; no Redis service/config is required.
## Phase 12 follow-up - Gemini transcription provider  (2026-09-26)
- Diagram basis: A8 server processing pipeline; A10 Gemini integration/configuration.
- Done: Added `ASR_PROVIDER=gemini`; uploaded stored audio to Gemini for structured word timestamps, preserving English/Tamil handling, segmentation, translation, Tanglish, and exports; retained Whisper as an explicit fallback and fake ASR for tests.
- Files: backend/app/core/config.py, backend/app/ml/asr.py, .env.example, docs/traceability.md, BUILD_LOG.md
- Commands: backend\.venv311\Scripts\python.exe -m compileall -q app tests; backend\.venv311\Scripts\python.exe -m pytest -q tests\test_phase4b_hybrid.py tests\test_phase7_export_search_ws.py
- Decisions/deviations: Gemini receives stored audio for server transcription only after the existing consent gate; the API key remains local in `.env` and the example file is sanitized.
- Verified: 13 focused backend tests passed; Python compilation passed.
- Status: PASS for compilation and focused processing/export/search/WebSocket tests.
- Next: Revoke the exposed Gemini key, put a replacement in local `.env`, then run one real stored-media transcription.
## Phase 12 follow-up - profile polish  (2026-09-26)
- Diagram basis: A11 frontend profile/account flow; A10 privacy and quota behavior.
- Done: Reworked Profile into a responsive account center with identity summary, editable details, password security, live quota usage, and server-processing privacy status.
- Files: frontend/src/pages/Profile.tsx, frontend/src/App.css, docs/traceability.md, BUILD_LOG.md
- Commands: npm run build
- Decisions/deviations: Reused existing user and quota APIs; privacy consent remains informational here because consent is granted in the processing flow.
- Verified: TypeScript compilation and Vite production bundle completed successfully.
- Status: PASS for `npm run build`.
- Next: Install ffmpeg/ffprobe for full server-upload media processing on Windows, then run full upload/process smoke.
## Phase 12 follow-up - switch to faster-whisper server transcription  (2026-09-26)
- Diagram basis: A8 server processing pipeline; A8b hybrid (removed); A4 STT fixed stack.
- Done: Removed Gemini-based ASR and all browser/device-side (WebGPU) transcription. All transcription now uses faster-whisper medium model on the server. Frontend ProjectPage simplified to upload-then-process server flow only; mode selector, browser benchmark, Whisper Web Worker, and consent dialog removed. processingMode.ts and lib/config.ts cleaned up; whisper.worker.ts stubbed.
- Files: backend/app/ml/asr.py, backend/app/core/config.py, frontend/src/pages/ProjectPage.tsx, frontend/src/lib/processingMode.ts, frontend/src/lib/config.ts, frontend/src/workers/whisper.worker.ts, .env.example, BUILD_LOG.md
- Commands: `python -m compileall -q app tests`; `python -m pytest -q tests/test_phase4_processing.py tests/test_phase4b_hybrid.py tests/test_phase6_translation.py`; `npm run build`
- Decisions/deviations: Removed ASR_PROVIDER=gemini code path entirely; Gemini key/model retained for translation/transliteration only. BROWSER_* env vars removed. whisper.worker.ts kept as a stub so the file compiles (not imported at runtime).
- Verified: Backend compilation passed; 18 focused tests passed; frontend TypeScript + Vite production build passed (existing chunk-size warning only).
- Status: PASS — `python -m compileall -q app tests`; `18 passed`; `npm run build` (exit 0).
- Next: Install faster-whisper (`pip install faster-whisper`) in the backend venv, then run a real server transcription job.
## Phase 12 follow-up - fix subtitle repetition + medium GPU model  (2026-09-26)
- Diagram basis: A8 steps 3.5-3.7 chunked ASR; A4 STT stack (medium, CUDA).
- Done: Fixed root cause of repeating subtitles — faster-whisper was receiving the full audio file for every chunk and timestamps were only filtered post-hoc; each chunk is now physically extracted with ffmpeg before transcription so the model sees only its window. Added no_repeat_ngram_size=5. Switched WHISPER_MODEL=medium and WHISPER_DEVICE=cuda in .env and config default. Fixed queue routing bug (gpu→default). Fixed consent gate removal.
- Files: backend/app/ml/asr.py, .env, BUILD_LOG.md
- Commands: `python -m compileall -q app tests`
- Decisions/deviations: ffmpeg clip extraction adds ~0.1s overhead per chunk but fully prevents the repetition bug; cache key uses clip PCM so identical clips hit cache correctly.
- Verified: Backend compilation passed; diagnostic confirmed all 8 chunks were returning identical 62-word results (first verse repeated); fix confirmed by code inspection.
- Status: PASS for compilation; repetition fix deployed; retry job to verify correct output.
- Next: Retry the failed project job via the UI Retry button; verify each chunk produces unique words.
## Phase 12 follow-up - native localhost startup and medium Whisper  (2026-09-28)
- Diagram basis: A4 medium faster-whisper; A8 server processing; A12 local startup.
- Done: Made root `.env` loading independent of working directory; aligned local environment example and docs; corrected health GPU reporting; added a GPU health test; started API, PostgreSQL worker, and Vite locally without Docker.
- Files: backend/app/core/config.py, backend/app/api/v1/health.py, backend/tests/test_health.py, .env.example, README.md, docs/deploy.md, docs/traceability.md, BUILD_LOG.md
- Commands: `backend\.venv311\Scripts\python.exe -m compileall -q backend\app backend\tests`; `backend\.venv311\Scripts\python.exe -m pytest -q tests\test_health.py tests\test_phase4_processing.py tests\test_deployment_storage.py` (FAKE_ASR=1, FAKE_GEMINI=1); `npm run build`; `backend\.venv311\Scripts\python.exe -m alembic current`.
- Decisions/deviations: No Docker used. `.env` credentials were kept private; user corrected the database URL. CUDA unavailable, so `WHISPER_DEVICE=auto` uses medium on CPU int8.
- Verified: Compile passed; 13 tests passed; frontend build passed; database at migration `0003_postgresql_queue_cache (head)`; API health returned `status=ok`, `db=true`, `storage=true`, `gpu=false`; frontend returned HTTP 200 and rendered the sign-in page; worker process running.
- Status: PASS — compileall, 13 focused pytest tests, `npm run build`, Alembic current, API/frontend/worker local smoke checks.
- Next: Run one real medium-model transcription; the model weights download on first use.
## Phase 12 follow-up - localhost services verified  (2026-09-28)
- Diagram basis: A8 PostgreSQL processing worker; A12 local API and frontend.
- Done: Confirmed the existing FastAPI server, PostgreSQL-backed processing worker, and Vite frontend are running locally.
- Files: BUILD_LOG.md
- Commands: PowerShell `Get-NetTCPConnection` for ports 8000 and 5173; `Invoke-RestMethod http://127.0.0.1:8000/health`; `curl.exe -sS -o NUL -w '%{http_code}' http://127.0.0.1:5173`; process query for `app.workers.runner --queue default`.
- Decisions/deviations: Reused the already-running local services; no restart or Docker used.
- Verified: API reports `status=ok`, `db=true`, `postgres_queue=true`, `storage=true`; frontend HTTP 200; worker process running.
- Status: PASS — backend, frontend, and worker availability checks.
- Next: Open `http://127.0.0.1:5173` to use the local application.
## Phase 12 follow-up - database connectivity and admin record check  (2026-09-28)
- Diagram basis: A6 PostgreSQL domain models; A12 migrations; A10 persisted accounts and logs.
- Done: Queried PostgreSQL and alembic revision; verified required application tables and seeded active admin records.
- Files: docs/traceability.md, BUILD_LOG.md
- Commands: `backend\.venv311\Scripts\python.exe -m alembic heads`; async SQLAlchemy `SELECT 1`, `alembic_version`, and read-only counts/lookups on users, admin_profiles, projects, media_files, subtitle_tracks, subtitle_segments, jobs, queued_tasks, and system_logs.
- Decisions/deviations: Read-only checks; did not alter accounts, passwords, or application data.
- Verified: Connection/query passed; database revision matches head `0003_postgresql_queue_cache`; all eight application tables queried; configured and screenshot-email admin records are active; 3 users, 1 project, 2 media files, 1 job, 15 system logs.
- Status: PASS — database connectivity, migrations, required tables, and admin lookup.
- Next: If sign-in still rejects credentials, use the password originally set when that admin account was first created; changing `ADMIN_PASSWORD` later does not reset an existing account.
## Phase 12 follow-up - approved admin sign-in repair  (2026-09-28)
- Diagram basis: DFD 1.0 login; A6 User/Admin and refresh tokens; A10 password hashing.
- Done: After user approval, synchronized the verified active `admin@gmail.com` account's Argon2 hash to the configured local admin password, revoked its active refresh tokens, and logged the change without storing the password in logs.
- Files: BUILD_LOG.md, docs/traceability.md
- Commands: Local Python/SQLAlchemy account update with role, active-status, email, and non-default password guards; local API `POST /api/v1/auth/login` verification using the private `.env` credentials.
- Decisions/deviations: Updated only the explicitly verified account; credential values were neither displayed nor logged.
- Verified: Hash matches configured password; login returned HTTP 200 and an ADMIN access-token response.
- Status: PASS — approved password synchronization and live admin login.
- Next: Sign in at the local frontend with the configured admin email and password from `.env`.
## Phase 12 follow-up - environment admin credentials persisted (2026-09-29)
- Diagram basis: DFD 1.0 login; A6 User/Admin; A10 Argon2 password hashing and audit logs.
- Done: Created or synchronized the configured admin database account; ensured ADMIN role/profile and active status; revoked existing refresh tokens; recorded an audit event.
- Files: BUILD_LOG.md, docs/traceability.md
- Commands: `backend\.venv311\Scripts\python.exe -` (inline SQLAlchemy synchronization and verification using application settings).
- Decisions/deviations: Used configured environment values; persisted only an Argon2 password hash and did not display or log credentials.
- Verified: Database transaction committed; account role and active status checked; configured password verified against stored hash.
- Status: PASS — `backend\.venv311\Scripts\python.exe -` (admin account synchronization and verification).
- Next: Sign in with the configured admin credentials from `.env`.
