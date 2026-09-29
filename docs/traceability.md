| Diagram element | Code path |
| --- | --- |
| Component diagram: API Gateway / modular monolith | backend/app/main.py; backend/app/api/v1/ |
| Component diagram: Auth Service | backend/app/services/auth_service.py; backend/app/api/v1/auth.py |
| Component diagram: Project Service | backend/app/services/project_service.py; backend/app/api/v1/projects.py |
| Component diagram: Media Service | backend/app/services/media_service.py; backend/app/api/v1/files.py |
| Component diagram: Processing Service | backend/app/services/processing_service.py; backend/app/workers/ |
| Component diagram: Subtitle Service | backend/app/services/subtitle_service.py; backend/app/api/v1/tracks.py; backend/app/api/v1/segments.py |
| Component diagram: Export Service | backend/app/services/export_service.py; backend/app/api/v1/export.py |
| Component diagram: Report Service | backend/app/services/report_service.py; backend/app/api/v1/admin.py |
| Component diagram: Logging Service | backend/app/services/log_service.py; backend/app/models/system_log.py |
| DFD 3.8 Segment Subtitles (DP) | backend/app/ml/segmenter.py |
| Hybrid browser processing | frontend/src/lib/processingMode.ts; frontend/src/workers/whisper.worker.ts; backend/app/services/client_result_service.py |
| Class Diagram: User/Admin/RefreshToken | backend/app/models/user.py |
| Class Diagram: Project/MediaFile | backend/app/models/project.py; backend/app/models/media_file.py |
| Class Diagram: SubtitleTrack/SubtitleSegment | backend/app/models/subtitle_track.py; backend/app/models/subtitle_segment.py |
| Class Diagram: Job/JobChunk | backend/app/models/job.py; backend/app/models/job_chunk.py |
| Class Diagram: SystemLog/ExportRecord | backend/app/models/system_log.py; backend/app/models/export_record.py |
| API Health | backend/app/api/v1/health.py; backend/app/main.py |
| Admin seed on startup | backend/app/services/auth_service.py; backend/app/main.py |
| Database session and migrations | backend/app/db/session.py; backend/app/db/base.py; backend/alembic/versions/0001_initial_schema.py |
| DFD 1.0 Register/Login/Refresh | backend/app/api/v1/auth.py; backend/app/services/auth_service.py; backend/app/core/security.py |
| DFD 1.0 Password reset | backend/app/api/v1/auth.py; backend/app/services/notification_service.py |
| Auth filter / RBAC deps | backend/app/core/deps.py |
| User profile APIs | backend/app/api/v1/users.py; backend/app/schemas/auth.py |
| SystemLog auth/user events | backend/app/services/log_service.py; backend/app/services/auth_service.py; backend/app/api/v1/users.py |
| DFD 2.0 Project CRUD | backend/app/api/v1/projects.py; backend/app/services/project_service.py |
| State Chart project transitions | backend/app/services/state_machine.py |
| DFD 2.0 Media upload/validation/storage | backend/app/api/v1/files.py; backend/app/services/media_service.py |
| Media stream with HTTP Range | backend/app/api/v1/files.py |
| Trie project suggestions | backend/app/utils/trie.py; backend/app/services/search_service.py; backend/app/api/v1/search.py |
| DFD 3.0 Process Media | backend/app/api/v1/jobs.py; backend/app/services/processing_service.py; backend/app/workers/runner.py |
| DFD 3.1 Extract Audio | backend/app/ml/audio.py |
| DFD 3.2 Detect Language | backend/app/ml/lang_detect.py |
| DFD 3.3 Voice Activity Detection | backend/app/ml/vad.py |
| DFD 3.4 Intelligent Chunking | backend/app/ml/chunker.py |
| DFD 3.5 Priority Scheduling | backend/app/models/queued_task.py; backend/app/services/queue_service.py; backend/app/workers/runner.py |
| DFD 3.6 Whisper Inference and Cache | backend/app/ml/asr.py; backend/app/ml/cache.py; backend/app/ml/fake_asr.py |
| DFD 3.7 Word Alignment | backend/app/ml/aligner.py |
| DFD 3.8 Segment Subtitles DP | backend/app/ml/segmenter.py |
| Job progress and WebSocket updates | backend/app/services/processing_service.py; backend/app/api/v1/ws.py |
| A8b metadata-only media | backend/app/api/v1/files.py; backend/app/services/media_service.py |
| A8b browser client-result processing | backend/app/api/v1/files.py; backend/app/services/client_result_service.py |
| A8b server consent/quota gates | backend/app/api/v1/users.py; backend/app/services/processing_service.py |
| A8b Tanglish browser result track | backend/app/ml/tanglish.py; backend/app/services/client_result_service.py |
| DFD 4.0 Subtitle track retrieval | backend/app/api/v1/tracks.py; backend/app/services/subtitle_service.py |
| DFD 4.0 Segment edit/split/merge/delete | backend/app/api/v1/segments.py; backend/app/api/v1/tracks.py; backend/app/services/subtitle_service.py |
| DFD 4.0 Shift timing validation | backend/app/api/v1/tracks.py; backend/app/services/subtitle_service.py |
| DFD 5.0 Translate subtitles | backend/app/api/v1/translate.py; backend/app/services/translation_service.py; backend/app/ml/gemini.py |
| DFD 3.9 Tanglish transliteration | backend/app/api/v1/translate.py; backend/app/ml/tanglish.py; backend/app/services/translation_service.py |
| Translation worker tasks | backend/app/workers/tasks.py; backend/app/services/worker_translation_service.py |
| Auto Tanglish for Tamil output | backend/app/services/processing_service.py; backend/app/services/client_result_service.py |
| DFD 6.0 Export subtitles | backend/app/api/v1/export.py; backend/app/services/export_service.py; backend/app/models/export_record.py |
| DFD 7.0 Search projects/segments | backend/app/api/v1/search.py; backend/app/services/search_service.py |
| Realtime job progress WebSocket | backend/app/api/v1/ws.py; backend/app/services/processing_service.py |
| DFD 8.0 Admin analytics/users/jobs/logs/storage/reports | backend/app/api/v1/admin.py; backend/app/services/report_service.py |
| Admin notifications and logs | backend/app/services/notification_service.py; backend/app/services/log_service.py |
| Frontend API client and refresh interceptor | frontend/src/api/client.ts; frontend/src/api/routes.ts |
| Frontend auth state and route guards | frontend/src/stores/authStore.ts; frontend/src/components/routing/Guards.tsx |
| Frontend dashboard project CRUD/search | frontend/src/pages/Dashboard.tsx; frontend/src/hooks/useApi.ts |
| Frontend layout/theme shell | frontend/src/components/layout/AppLayout.tsx; frontend/src/stores/uiStore.ts; frontend/src/App.css |
| Frontend project upload/process/progress | frontend/src/pages/ProjectPage.tsx; frontend/src/hooks/useJobSocket.ts; frontend/src/api/routes.ts |
| Frontend editor segment workflow | frontend/src/pages/EditorPage.tsx; frontend/src/api/routes.ts |
| Frontend Video.js playback/editor | frontend/src/pages/EditorPage.tsx |
| A8b frontend processing decision | frontend/src/lib/gpu.ts; frontend/src/lib/processingMode.ts; frontend/src/pages/ProjectPage.tsx |
| A8b browser audio decode/VAD/chunking | frontend/src/lib/audio.ts; frontend/src/lib/vad.ts |
| A8b browser Whisper WebGPU worker | frontend/src/workers/whisper.worker.ts; frontend/src/lib/config.ts |
| A8b device/server consent and quota UI | frontend/src/pages/ProjectPage.tsx; frontend/src/stores/uiStore.ts |
| A8b unstored media editor playback | frontend/src/pages/EditorPage.tsx |
| Frontend guarded admin dashboard | frontend/src/pages/Admin.tsx; frontend/src/components/routing/Guards.tsx |
| Frontend admin jobs/users/storage/logs/reports | frontend/src/pages/Admin.tsx; frontend/src/api/routes.ts; frontend/src/types/api.ts |
| A14 Playwright happy path | frontend/e2e/happy-path.spec.ts; frontend/playwright.config.ts |
| A14 browser-mode metadata/client-result e2e | frontend/e2e/browser-mode.spec.ts; frontend/e2e/helpers.ts |
| Fake-ASR e2e stack and CI | docker-compose.e2e.yml; .github/workflows/ci.yml |
| Frontend/backend CORS integration | backend/app/main.py; frontend/src/api/client.ts |
| A12 Docker startup sync DB/CORS config | backend/alembic/env.py; backend/app/core/config.py; .env.example |
| Local fake-ASR eager task execution | backend/app/workers/tasks.py |
| A11 Profile/account management UI | frontend/src/pages/Profile.tsx; frontend/src/App.css |
| Gemini audio/video transcription | backend/app/ml/asr.py; backend/app/core/config.py; .env.example |
| PostgreSQL queue, cache, and coordination | backend/app/models/queued_task.py; backend/app/models/cache_entry.py; backend/app/services/queue_service.py; backend/app/services/db_cache.py; backend/app/workers/runner.py |
| Render API/worker, Neon PostgreSQL, Vercel SPA, and R2 media persistence | render.yaml; frontend/vercel.json; backend/app/core/config.py; backend/app/services/object_storage.py; docs/deploy.md |
| Automatic source media cleanup after transcription | backend/app/services/processing_service.py; backend/app/services/object_storage.py |
| Neon runtime and Alembic database URL validation | backend/app/core/config.py; backend/alembic/env.py; backend/tests/test_deployment_storage.py |
| Local API, PostgreSQL worker, and frontend launch validation | backend/app/main.py; backend/app/workers/runner.py; frontend/package.json |
| Database schema migrations and admin sign-in bootstrap | backend/alembic/; backend/app/main.py; backend/app/services/auth_service.py; backend/app/api/v1/auth.py |
| Processing failure status and Gemini API quota explanation | frontend/src/pages/ProjectPage.tsx; backend/app/services/processing_service.py; backend/app/ml/asr.py |
| Free-tier Gemini Flash transcription model configuration | backend/app/core/config.py; .env.example; render.yaml; frontend/src/pages/ProjectPage.tsx |
| Native localhost startup and medium faster-whisper device fallback | README.md; backend/app/core/config.py; .env.example |
| Local PostgreSQL migration and application-table verification | backend/app/db/session.py; backend/alembic/versions/0003_postgresql_queue_cache.py; backend/app/models/ |
| Approved local admin password synchronization and login verification | backend/app/core/security.py; backend/app/models/user.py; backend/app/models/system_log.py; backend/app/api/v1/auth.py |
| Environment-configured admin account persistence and Argon2 verification | backend/app/core/config.py; backend/app/core/security.py; backend/app/models/user.py; backend/app/models/system_log.py |
