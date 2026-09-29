A1. Mission
Build the complete, runnable Privacy-First AI Multilingual Subtitle Generation
& Management Platform: users upload audio/video, the system transcribes
locally (GPU faster-whisper), segments subtitles with a DP algorithm,
optionally translates (English 
⇄
 Tamil) and transliterates Tamil→Tanglish
(Tamil in Roman letters) via Gemini, lets users edit against a video player,
exports SRT/VTT/TXT, searches past projects; admins manage users, storage,
logs, analytics. Source of truth = the UML/DFD diagrams summarized in A5
A9. No placeholders, no TODO stubs, no fake implementations except the
test-only 
FAKE_ASR=1
 engine. Hybrid processing (A8b): transcription runs on
the visitor's own GPU in the browser (WebGPU) when a real GPU exists and is
fast enough; otherwise the file is uploaded (after explicit consent) and
processed by the server GPU worker.
Supported languages (fixed): Tamil (
ta ) and English (
en ) only. Constant
SUPPORTED_LANGUAGES = ["en","ta"]
 in 
core/config.py 
. Auto-detect
compares only 
en
 vs 
ta
 probabilities from faster-whisper 
detect_language
(pick the higher; reject others with 422). Translation directions: 
en→ta
 and
ta→en 
. Code-mixed Tamil-English speech (Tanglish audio): transcribe with
ta 
; keep English words as spoken. UI language selector shows: Auto-detect,
Tamil, English.
A2. Credit rules (mandatory — obey every run)
Never run any git command (no 
git init/add/commit/tag 
, no 
.git
folder). The user will run the project locally first and push to GitHub
manually later.
Work one phase per run. Stop after the BUILD_LOG entry. Never start the
next phase.
Do not print file contents in chat. Final chat message ≤ 8 lines: phase, files
changed count, tests result, next phase.
Do not re-read files you just wrote. Read only files you must edit. No
repo-wide exploration after Phase 0; use 
BUILD_LOG.md
 as memory.
Use scaffolding CLIs (
npm create vite 
, 
alembic init 
, 
npx
shadcn@latest init/add 
) instead of hand-writing boilerplate.
Write files in batches (many files per step). Prefer complete files over
many small edits.
Run only the tests relevant to the phase (
pytest -q path 
, 
noEmit 
, 
tsc --
vite build
 at frontend phases end). Never run the full suite
except Phase 12.
Never install torch/CUDA in CI or tests; tests run with 
FAKE_ASR=1 
,
FAKE_GEMINI=1 
.
No long explanations, no summaries of the spec, no re-planning. If a
diagram is ambiguous, apply the rule in A6/A13 and log it in one line.
If a command fails twice with the same error, log it in BUILD_LOG under
"Blocked" and move on to what is unblocked.
A3. Build-history protocol (how each step is recorded)
After every phase, do all of these:
1. Append to 
BUILD_LOG.md
 (≤ 12 lines per phase) using exactly this
template:
## Phase N — <title>  (<YYYY-MM-DD>)- Diagram basis: <which diagram/process ids drove this phase>- Done: <bullets, what was built>- Files: <every path created/changed this phase>- Commands: <install/migrate/test commands run>- Decisions/deviations: <any ambiguity resolved, any change from 
diagram + why>- Verified: <test names / results / manual check>- Status: <PASS/FAIL + exact commands that passed>- Next: <next phase>
2. No git. Instead of commits, the 
Files:
 line in each BUILD_LOG entry
must list every path created/changed in that phase, and 
Status:
 must
record the exact test/build commands that passed. This is the build
history. Create a 
.gitignore
 and 
.dockerignore
 in Phase 0
(node_modules, .venv, pycache, .env, storage/, models/, pgdata/, dist/,
*.wav) so the later manual push is clean, but never run git yourself.
3. Maintain 
docs/traceability.md 
: table 
Diagram element → code path
DFD 3.8 Segment Subtitles (DP) →
(e.g., 
backend/app/ml/segmenter.py 
). Append rows each phase.
4. Never rewrite earlier BUILD_LOG entries.
A4. Fixed tech stack (do not substitute)
Layer
Tech
Frontend
UI
React + Vite + TypeScript
Tailwind CSS + shadcn/ui
State
API calls
Zustand
TanStack Query + Axios
Video player
Charts
Video.js
Recharts
Backend
DB / ORM /
migrations
Python 3.11 + FastAPI (async)
PostgreSQL 16 / SQLAlchemy 2.x / Alembic
Layer
Tech
Auth
Queue /
worker
JWT (access+refresh) + Argon2 (
argon2-cffi 
)
Redis + Celery
Storage
Audio
Local filesystem (
STORAGE_ROOT 
)
FFmpeg
VAD
STT (server)
Silero VAD (
silero-vad
 pip package, torch)
STT (browser,
hybrid)
Translation
faster-whisper (CUDA float16; CPU int8 fallback)
@huggingface/transformers
 Whisper on WebGPU
inside a Web Worker (only addition to the fixed stack)
Gemini API free tier (
google-genai 
)
Search
Realtime
PostgreSQL FTS (tsvector + GIN) + in-memory Trie
WebSocket (FastAPI) + Redis pub/sub
Testing
Container
Pytest (+ httpx, pytest-asyncio) + Playwright
Docker + docker-compose
CI/hosting
GitHub Actions, Vercel Hobby (frontend), Cloudflare
Tunnel (backend)
A5. Architecture (from Component Diagram)
Component diagram shows microservices; build a modular monolith with
identical boundaries (cost ₹0, one deploy). One FastAPI app, one router +
service module per component:
auth_service, project_service, media_service, processing_service,
subtitle_service, notification_service, export_service, report_service
(analytics), logging_service 
. API Gateway responsibilities (routing, request
validation, auth filter) = FastAPI routers + pydantic +
Depends(get_current_user)
 / 
Depends(require_admin) 
. Processing runs in
Celery worker(s). External: Whisper (local), Gemini API, optional SMTP (if
SMTP_HOST
 unset, log emails to console).
Repo layout:
subtitle-platform/
AGENTS.md  BUILD_LOG.md  README.md  docker-compose.yml  
.env.example  .github/workflows/ci.yml
docs/traceability.md  docs/deploy.md
backend/
pyproject.toml  alembic.ini  alembic/  Dockerfile  
Dockerfile.worker
app/
main.py
core/ (config.py, security.py, logging.py, deps.py, 
errors.py)
db/ (base.py, session.py)
models/ (user.py, project.py, media_file.py, 
subtitle_track.py, subtitle_segment.py, job.py, job_chunk.py, 
system_log.py, export_record.py)
schemas/ (one pydantic module per model group)
api/v1/ (auth.py, users.py, projects.py, files.py, jobs.py, 
tracks.py, segments.py, export.py, search.py, admin.py, ws.py, 
health.py)
services/ (auth_service.py, project_service.py, 
media_service.py, subtitle_service.py, export_service.py, 
search_service.py, notification_service.py, report_service.py, 
log_service.py, client_result_service.py, state_machine.py)
ml/ (audio.py, lang_detect.py, vad.py, chunker.py, asr.py, 
cache.py, aligner.py, segmenter.py, gemini.py, tanglish.py, 
fake_asr.py)
workers/ (celery_app.py, tasks.py)
utils/ (trie.py, timefmt.py)
tests/
frontend/  (Vite TS app, 
src/{api,components,pages,stores,hooks,lib,workers,types}, e2e/; 
lib/{config,gpu,processingMode,audio,vad}.ts, 
workers/whisper.worker.ts)
A6. Domain model (from Class Diagram; UUID PKs,
created_at /
updated_at timestamptz)
User: user_id, name, email (unique, citext-like lowercase), password_hash
(Argon2), role 
Role{USER,ADMIN} 
, is_active, storage_used (bigint bytes),
server_processing_consent_at (nullable timestamptz), created_at.
Methods → service functions: register, login→token, reset_password,
update_profile, upload_file.
Admin = User with role ADMIN + 
permissions: text[]
 (table
admin_profiles 
: admin_id=user_id FK, permissions). Admin actions:
activate/deactivate/delete user, delete file, view logs, view analytics,
export report.
Project: project_id, owner_id→User (1..* owns), title, status
ProcessingStatus{QUEUED,PROCESSING,COMPLETED,FAILED,PAUSED} 
,
created_at, updated_at, 
deleted_at
 (soft delete = state "Deleted"),
search_vector
 tsvector (title) with GIN index.
MediaFile: file_id, project_id (Project 1..* contains), file_name, file_type
(mime), size_bytes, duration_seconds, 
is_stored
 (bool; false = browser
mode, media never uploaded), storage_path (nullable), audio_path
(nullable). 
validate_type()
 (extension+magic bytes via ffprobe; allowed:
mp3, wav, m4a, aac, ogg, flac, mp4, mkv, mov, webm; max size
MAX_UPLOAD_MB
 default 500), 
extract_audio()
 (ffmpeg → 16 kHz mono
wav).
SubtitleTrack: track_id, file_id, language, source_language, is_translated
(bool), 
kind{ORIGINAL,TRANSLATION,TRANSLITERATION}
 (extension for
Tanglish). Methods: merge(a,b), split(seg), export_as(format),
translate(lang).
SubtitleSegment: segment_id, track_id, idx, start_time (float s), end_time,
text, confidence (0–1). Methods: edit(new_text), shift_timing(offset).
Constraint 
end_time > start_time 
; unique (track_id, idx).
Job (D9 Job Status/Progress DB): job_id, project_id, file_id, 
mode
{SERVER,BROWSER} 
, status (same enum), stage
(
e
xtract|detect_lang|vad|chunk|schedule|asr|align|segment|tanglish|done 
),
progress (0–100), priority (0–9, lower = sooner), chunks_total,
chunks_done, error, celery_root_id, timestamps.
JobChunk: job_id, idx, start_s, end_s, status, result JSONB (words with
start/end/prob), needed so pause/resume/retry skip finished chunks.
SystemLog (D8): id, ts, level, actor_id nullable, action, detail JSONB.
ExportRecord: id, track_id, user_id, format, created_at (this is the
"Exported" state; project status stays COMPLETED).
A7. State machine (from State Chart) — implement in
services/state_machine.py
Single source of truth; every status change goes through
transition(project, event) 
; illegal → HTTP 409.
| From | Event | To | Entry action |
|---|---|---|---|
| (start) | createProject | QUEUED | wait in queue |
| QUEUED | startProcessing | PROCESSING | run pipeline |
| PROCESSING | processingCompleted | COMPLETED | available for
view/edit/export |
| PROCESSING | failProcessing | FAILED | log error |
| PROCESSING | resumeProcessing (self-loop) | PROCESSING | re-dispatch
unfinished chunks |
| COMPLETED | pauseProcessing | PAUSED | processing on hold |
| PAUSED | resumeProcessing | COMPLETED | — |
| COMPLETED | exportSubtitles | COMPLETED | write ExportRecord
(Exported) |
| FAILED | retryProcessing | QUEUED | re-enqueue |
| FAILED, PAUSED, (any non-processing) | deleteProject | DELETED (soft:
deleted_at 
, files + storage_used released) | resources released |
Documented extensions (log in BUILD_LOG Phase 4): 
PROCESSING --
pauseProcessing--> PAUSED
 and 
PAUSED --resumeProcessing--> PROCESSING
when the job is unfinished (needed for real pause). Diagram edge "Failed →
New labeled pauseProcessing" is treated as a labeling error; only
retryProcessing
 is implemented for FAILED.
A8. Processing pipeline (from Sequence 4.x, DFD L1
3.0, DFD L2 3.1–3.9)
POST /files/{id}/process
 → validates, sets Project QUEUED→PROCESSING
(
u
pdateStatus(PROCESSING) 
), creates Job, dispatches Celery chain, returns
202 {job_id} 
. Steps (each updates Job.stage/progress and publishes to
Redis channel 
job:{job_id} 
):
1. 3.1 Extract audio: 
ffmpeg -i in -vn -ac 1 -ar 16000 -f wav out.wav 
;
store 
audio_path 
, 
duration_seconds
 (ffprobe).
2. 3.2 Detect language: if request language = 
auto 
, faster-whisper
detect_language
 on first 30 s; else use given.
3. 3.3 VAD: Silero VAD → speech intervals.
4. 3.4 Intelligent chunking: merge intervals with gaps < 0.5 s; cut chunks ≤
30 s at longest internal silence; 0.3 s overlap-free padding; persist
JobChunk rows.
5. 3.5 Schedule (priority queue): enqueue one Celery task per chunk on
queue 
gpu
 with 
priority
 = f(media duration) (shorter files first; admin
boosted allowed). Celery Redis config 
broker_transport_options=
{"priority_steps": list(range(10)), "queue_order_strategy":
"priority"} 
. Worker 
process.-c 1
 for GPU queue, model loaded once per
6. 3.6 Whisper inference: faster-whisper 
word_timestamps=True 
,
vad_filter=False
 (VAD already done), 
beam_size=5 
,
condition_on_previous_text=False
 (prevents Tamil repetition loops),
language
 forced to detected/selected 
ta
 or 
en
. Device auto: CUDA
float16 → else CPU int8. LRU cache (D6): Redis db 1, 
maxmemory-policy allkeys-lru 
; key 
maxmemory 256mb 
,
asr:{sha256(chunk_pcm)}:{model}:
{lang} 
; hit → skip inference. Save words into JobChunk.result; update
progress = chunks_done/chunks_total × 85.
7. 3.7 Word-level alignment: after all chunks done (Celery chord callback),
offset word times by chunk start, sort, fix overlaps (clamp 
start ≥
prev.end 
), drop empty tokens; compute per-word probability.
8. 3.8 DP segmentation (
segments. 
ml/segmenter.py 
): input word list → subtitle
dp[i]
 = min cost to segment first i words; transition 
over window ≤ 30 words. Hard constraints: chars ≤ 
j→i
MAX_CHARS
 (en 84 =
2×42; ta 64 = 2×32), duration ≤ 7 s → cost ∞. Character count uses
grapheme clusters (
regex.findall(r'\X', text) 
, add 
regex
dependency) so Tamil combining vowel signs are not over-counted. Cost
= (len_chars − target)²/target (target en 37, ta 28) + 3 if duration < 1.0 s +
0.5 per segment + break penalty: −2 if break follows 
. ? !
 (Tamil uses
the same marks) or gap ≥ 0.35 s, +2 if breaking mid-phrase (gap < 0.05 s
and no punctuation). Backtrack to segments; text = joined words;
confidence = mean word prob; start/end from first/last word. Pure
function, fully unit-tested.
9. Create SubtitleTrack (
createTrack(mediaFileId, language) 
, kind
ORIGINAL) + SubtitleSegments (
split & createSegments(trackId) 
),
bulk insert.
10. 3.9 Tanglish transliteration: if track language = 
ta 
, call Gemini to
transliterate Tamil script → Roman-letter Tamil (Tanglish, e.g. 
→ 
va
வணக்கம்
nakkam 
; English words already in Latin stay unchanged) in batches
of 40 segments; create second track (
language="ta-Latn" 
, kind
TRANSLITERATION, is_translated=True, source_language="ta") with
identical timings. With 
FAKE_GEMINI=1
 use a deterministic fake (simple
per-character Tamil→Latin map).
11. Set Project COMPLETED (
updateStatus(COMPLETED) 
), Job done 100 %,
publish final event, 
notification_service.send_status_email
 (if SMTP
set), write SystemLog.
On exception: Project FAILED, Job.error, log, publish 
failed 
. Retry via
POST /projects/{id}/retry 
. Pause: set Redis flag 
job:{id}:paused 
;
chunk tasks check it and exit early (retry later); resume clears flag and re
dispatches only chunks with status != DONE.
A8b. Hybrid processing (browser GPU first, server
fallback)
Modes: 
auto
 (default) | 
browser
 | 
lib/processingMode.ts 
:
1. Explicit 
browser 
/
server 
. Frontend decision logic in
server
 selection wins. 
browser
 without a real GPU
shows a slow-WASM warning dialog and proceeds only on confirm.
2. 
a
uto 
: 
navigator.gpu
 exists AND 
await
navigator.gpu.requestAdapter()
 is non-null AND
!adapter.isFallbackAdapter
 → after model load, run a 10 s benchmark
transcription in the worker; real-time factor = wall time / 10 s; if ≤
BROWSER_MAX_RTF
 (default 0.5, in 
lib/config.ts 
) → browser mode, else
server mode. No real GPU → server mode. 
auto
 never runs WASM CPU.
3. Server fallback needs consent: first time show dialog "No suitable GPU on
your device — your file will be uploaded and processed on our server".
Accept → 
POST /users/me/consent/server-processing
 (sets
server_processing_consent_at 
); also remember in 
uiStore 
. Without
consent 
/process
 returns 403 
{code:"CONSENT_REQUIRED"} 
.
POST /projects/{id}/files/metadata
Browser-mode flow (DFD 3.1–3.6 on client, 3.7–3.9 on server):
a. 
{file_name,file_type,size_bytes,duration_seconds}
 → MediaFile with
is_stored=false 
, 
storage_path=null 
; nothing uploaded, quota untouched.
Optional checkbox "Also save media on the server" (default off) uses the
normal upload (
is_stored=true 
).
b. 
workers/whisper.worker.ts
 loads Whisper via
@huggingface/transformers
 (
pipeline('automatic-speech-recognition',
BROWSER_WHISPER_MODEL, {device:'webgpu'}) 
, cached by the browser).
Default model id in 
of at least 
lib/config.ts 
; it must be a multilingual ONNX Whisper
small
 size (Tamil needs it). Verify the id exists on the Hugging
Face hub; if not, use the nearest multilingual ONNX Whisper variant and log it.
c. Decode with Web Audio (
OfflineAudioContext 
, 16 kHz mono Float32);
decode long media in ≤ 10-minute windows to bound memory.
d. 
lib/vad.ts 
: energy-based VAD (30 ms frames, adaptive threshold) +
chunking ≤ 30 s at silences, same rules as A8 step 4.
e. Transcribe each chunk with 
return_timestamps:'word' 
, language
'tamil'|'english' 
. If selection is Auto and worker cannot detect language
restricted to en/ta, ask the user to pick and log it.
f. 
POST /files/{id}/client-result
words:[{word,start,end,prob?}]} 
.
{language:"en"|"ta", model:string,
services/client_result_service.py 
): ownership check; project
Backend (
must be QUEUED (or FAILED after retry); create Job 
mode=BROWSER 
; validate
— language in 
SUPPORTED_LANGUAGES 
, 
CLIENT_RESULT_MAX_WORDS 
, every 
len(words) ≤
start<end 
, starts non-decreasing, 
duration_seconds + 1 
, word ≤ 64 chars, strip control characters, 
end ≤
prob
defaults 0.9; then state machine QUEUED→PROCESSING, run aligner cleanup
+ DP segmenter (A8 step 8) + create track/segments + Tanglish task if 
ta 
, →
COMPLETED, publish 
job:{id}
 event, SystemLog. Skips audio extraction,
VAD and Whisper.
Server mode: unchanged (A8). 
POST /files/{id}/process
 additionally
requires 
is_stored=true 
, consent, and the daily limit 
SERVER_JOBS_PER_DAY
(default 5 per user; count Jobs with 
mode=SERVER
 since UTC midnight; admins
exempt) else 429 
{code:"DAILY_LIMIT"} 
. 
GET /users/me/quota
 →
{server_jobs_used, server_jobs_limit, storage_used, storage_quota} 
.
Editor playback with unstored media: prompt the user to pick their local file
and play it via 
URL.createObjectURL 
; it is never uploaded. Job/project
badges: "Processed on your device" / "Processed on server".
Privacy: in browser mode audio never leaves the device; only text and
timestamps are sent (and Gemini receives text only, as before).
A9. API (prefix 
/api/v1 , JSON, pydantic v2, OpenAPI on)
Auth/User (DFD 1.0): 
POST /auth/register 
, 
POST /auth/login 
, 
/auth/refresh 
, 
POST
POST /auth/password/forgot 
, 
POST /auth/password/reset 
,
GET|PATCH /users/me 
.
Projects (2.0): 
POST|GET /projects
 (GET paginated, filter status),
GET|PATCH|DELETE /projects/{id} 
, 
POST
/projects/{id}/pause|resume|retry 
.
Media (2.0): 
POST /projects/{id}/files
 (multipart, streamed to disk in 1 MB
chunks, quota check, 
validate_type 
), 
GET /projects/{id}/files 
, 
/files/{id}/stream
 (HTTP Range support for Video.js), 
/files/{id} 
.
Processing (3.0): 
POST /files/{id}/process
 body 
priority?:0-9}
 → 202; 
GET /jobs/{id} 
; 
Subtitles (4.0): 
GET /files/{id}/tracks 
, 
GET
DELETE
{language:"auto"|iso,
GET /projects/{id}/job 
.
GET /tracks/{id}
 (track +
segments), 
PATCH /segments/{id}
 (text/start/end), 
POST
/segments/{id}/split {at_time, at_char}
, 
POST /tracks/{id}/shift
{offset, from_idx?}
 (shiftTiming), 
POST /tracks/{id}/merge {segment_a,
segment_b}
, 
DELETE /segments/{id}
, 
DELETE /tracks/{id}
.
Translate (5.0): 
POST /tracks/{id}/translate {target_language:
"en"|"ta"}
 (must differ from source) → new track (kind TRANSLATION); POST /tracks/{id}/transliterate
.
Export (6.0): 
GET /tracks/{id}/export?format=srt|vtt|txt
(StreamingResponse, 
Content-Disposition
), writes ExportRecord.
Search (7.0): 
GET /search?q=
 (FTS 
websearch_to_tsquery
 over project titles
+ segment text via 
to_tsvector
 GIN on segments), 
GET /search/suggest?
q=
 (Trie prefix, ≤ 8 results).
Admin (8.0, 
require_admin
): 
GET /admin/analytics
 (users, projects by
status, storage, jobs/day, avg processing time, GPU/job metrics), 
GET
/admin/users
, 
PATCH /admin/users/{id}/activate|deactivate
, 
DELETE
/admin/users/{id}
, 
DELETE /admin/files/{id}
, 
GET /admin/jobs
, 
GET
/admin/logs?level=&limit=
, 
GET /admin/storage
, 
GET
/admin/reports/export?format=csv|json
.
Realtime: 
WS /ws/jobs/{job_id}?token=<jwt>
 → JSON events {job_id,status,stage,progress,chunks_done,chunks_total,error?}
.
Health: 
GET /health
 (db, redis, gpu flag).
Hybrid (A8b): 
POST /projects/{id}/files/metadata
, 
POST
/files/{id}/client-result
, 
POST /users/me/consent/server-processing
, GET /users/me/quota
.
Rules: ownership checks on every project/file/track/segment route (403 for
others; admins bypass read only through 
/admin/*
). Uniform error body {detail, code}
.
A10. Cross-cutting behaviour
Translation (5.0): 
ml/gemini.py
 wraps 
google-genai
; model from GEMINI_MODEL
 env (default 
gemini-2.5-flash
); batches of 40 segments
as JSON in/out with strict schema; exponential backoff on 429/5xx (max
5); global rate limiter (
GEMINI_RPM
 env, default 10) via Redis token
bucket; cache per 
sha256(text|src|tgt)
 in Redis db 1 (LRU). Only text
ever leaves the machine; never audio.
Trie (
utils/trie.py
): insert/delete/prefix-search; per-user tries kept in a
process-local dict, lazily built from project titles, updated on project
create/rename/delete; unit tested.
Exporters (
export_service.py
): SRT (
HH:MM:SS,mmm
), VTT (
WEBVTT
, HH:MM:SS.mmm
), TXT (one segment per line). Round-trip tested.
Storage:
STORAGE_ROOT/{user_id}/{project_id}/{file_id}/original.ext
 and
audio.wav 
; update 
users.storage_used 
; quota 
USER_QUOTA_MB
 default
5000; delete removes files and decrements.
Logging: structured JSON logs + 
SystemLog
 rows for auth events,
uploads, process start/finish/fail, exports, admin actions.
Security/Privacy: Argon2 hashing; JWT access 15 min / refresh 7 days
(refresh rotation, stored hashed in 
refresh_tokens 
); login rate-limit via
Redis (5/min/IP+email); CORS allowlist from 
CORS_ORIGINS 
; sanitize
filenames (uuid on disk); no third-party analytics; media stays on the
user's device in browser mode and is uploaded only to your own server
when the user chooses or consents to server processing; translation is
opt-in per action; account/project deletion physically deletes files.
Config: all via 
pydantic-settings 
; ship 
.env.example
 with every
DATABASE_URL, REDIS_URL, CELERY_BROKER_URL,
variable: 
CACHE_REDIS_URL, JWT_SECRET, STORAGE_ROOT, MAX_UPLOAD_MB,
USER_QUOTA_MB, WHISPER_MODEL(default medium; large-v3 if VRAM ≥ 8
GB; 
small
only for quick English dev tests — small is weak for
Tamil), WHISPER_DEVICE(auto), GEMINI_API_KEY, GEMINI_MODEL,
GEMINI_RPM, SMTP_*, CORS_ORIGINS, FAKE_ASR, FAKE_GEMINI,
SERVER_JOBS_PER_DAY(default 5), CLIENT_RESULT_MAX_WORDS(default
200000), ADMIN_EMAIL, ADMIN_PASSWORD 
; frontend 
(seed admin on startup if absent).
.env 
: 
VITE_API_URL
A11. Frontend (from Activity/Swimlane diagram: User
+ Admin lanes)
Stack per A4. Vite proxy 
/api
 and 
/ws
 to backend in dev; 
VITE_API_URL
 in
prod. Axios instance with Bearer token + 401 → refresh-once interceptor.
TanStack Query for all server state; Zustand only for: 
authStore
 (tokens/user,
persisted), 
uiStore
 (sidebar, theme), 
playerStore
 (current time, active
segment idx). shadcn/ui components: button, input, card, dialog, dropdown
menu, table, tabs, badge, progress, toast(sonner), select, skeleton, form,
textarea, tooltip.
Pages/routes (React Router, lazy-loaded):
/login 
, 
/register 
, 
/forgot-password 
, 
/reset-password
 —
Register/Login → Credentials valid? (inline errors).
/ 
Dashboard: project cards/table, status badges (5 statuses), create
project dialog, search bar with Trie suggestions (debounced 200 ms) +
FTS results, pause/resume/retry/delete actions per state machine (disable
illegal actions).
/projects/:id 
Project: dropzone upload (progress bar via Axios
onUploadProgress 
, client-side type/size check = "File valid?"), language
select (Auto-detect / Tamil / English only), priority, processing mode
selector "Auto (recommended) / My device / Server" (A8b), "Generate
subtitles" button, live progress (WS hook with auto-reconnect: stage
stepper + %), tracks list.
/tracks/:id 
Editor ("Review → Satisfied? → Edit"): Video.js player (audio
files show waveform-less audio UI; if 
is_stored=false 
, ask the user to
pick their local file and play it via blob URL, never uploaded), synced
segment list (active row highlight, click to seek, low-confidence < 0.6
highlighted amber), inline text edit (save on blur, PATCH), start/end time
inputs, split at cursor, merge with next, delete, shift timing (global offset
dialog), live subtitle overlay via Video.js text track built from segments,
keyboard shortcuts (Space play, Ctrl+Enter save, Alt+↑/↓ move
selection), Translate dialog (English
⇄
Tamil only) and Tanglish button
(only when track language is Tamil), Export dialog (SRT/VTT/TXT → blob
download).
/profile 
: update name/password, storage-used bar.
/admin
 (route guard role=ADMIN): tabs — Dashboard (Recharts: projects
by status pie, jobs/day line, storage bar, avg processing time), Jobs
monitor (table + live status), Users (activate/deactivate/delete),
Storage/Files (delete file), Logs (level filter), Reports (CSV/JSON export).
Loading skeletons, empty states, error toasts, responsive (mobile-first),
dark mode toggle. 
tsc --noEmit
 and 
vite build
 must pass with zero
errors.
A12. Infra
docker-compose.yml 
: 
postgres:16 
, 
redis:7
 (cache instance --
maxmemory 256mb --maxmemory-policy allkeys-lru
 as second service
redis-cache 
), 
backend
 (uvicorn, runs 
alembic upgrade head
 on start),
worker-gpu
 (Celery -Q gpu -c 1 
,
deploy.resources.reservations.devices
 nvidia GPU, base image
nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 
, installs ffmpeg +
torch cu121 + faster-whisper), 
worker-default
 (
image), 
frontend
 (dev only). Volumes: -Q default -c 2 
, CPU
pgdata 
, 
storage 
, 
models
 (HF
cache).
docs/deploy.md 
: (a) local docker run, (b) Cloudflare Tunnel (
cloudflared
tunnel --url http://localhost:8000
 and named-tunnel config, set
backend 
CORS_ORIGINS
 to Vercel URL), (c) Vercel Hobby (root 
build 
npm run build 
, env 
VITE_API_URL 
, 
frontend 
,
vercel.json
 SPA rewrite), (d)
WebSocket via tunnel (
wss:// 
).
CI (
.github/workflows/ci.yml 
): backend 
pytest
 (services
postgres+redis, 
FAKE_ASR=1 FAKE_GEMINI=1 
), frontend 
workflow_dispatch 
).
npm ci && npm
run build && npx tsc --noEmit 
. Playwright e2e is a separate manual job
(
A13. Ambiguity rules
Component diagram (microservices) → modular monolith. Enum has 5
statuses → "Deleted" = soft delete flag, "Exported" = ExportRecord. Sequence
steps 4.x are synchronous in the diagram but async in reality → API returns
202 and worker performs 4.1–4.6 in order. Diagram mentions Hinglish; here it
is replaced by Tanglish for Tamil. Any other ambiguity: choose the simplest
option that satisfies the diagram, log one line under "Decisions/deviations".
A14. Testing (Pytest + Playwright)
Backend unit: state machine (all legal + illegal transitions), segmenter DP
(constraints, punctuation preference, determinism, Tamil grapheme counting
with combining vowel signs), fake_asr returning both an English and a Tamil
sample transcript, Tanglish fake transliteration, trie, exporters (SRT/VTT/TXT
round-trip), aligner (offset/overlap), security (argon2, JWT expiry/refresh
rotation). Hybrid: client-result validation (non-monotonic times, oversized
payload, end beyond duration, wrong owner → 4xx), consent-required 403,
daily-limit 429, metadata-only file flow, Job mode recorded. Integration (httpx
AsyncClient + test DB): register→login→create project→upload tiny
wav→process (
FAKE_ASR=1 
, Celery
task_always_eager=True 
)→tracks→edit/shift/merge/split→export→search→admin
analytics→RBAC 403s→delete releases storage. Playwright e2e (one spec,
e2e/happy-path.spec.ts 
): register → create project → upload fixture → wait
COMPLETED → edit a segment → export SRT download assertion → admin
login sees analytics.
A15. Definition of done
docker compose up
 brings the system up; migrations apply; seeded admin
can log in; full happy path works with real faster-whisper on GPU and with
FAKE_ASR=1
; hybrid works: WebGPU browser transcription when a real GPU is
present and fast enough, consented server fallback otherwise; all pytest pass; vite build
 passes; Playwright happy path passes; README has setup (5
steps max), env table, architecture diagram (mermaid), and links to docs/traceability.md
 and 
BUILD_LOG.md
