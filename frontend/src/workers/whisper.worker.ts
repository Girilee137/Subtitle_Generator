/**
 * whisper.worker.ts — stub only.
 *
 * Browser-side WebGPU transcription has been removed. All transcription now
 * runs server-side via faster-whisper (medium model). This file is kept so
 * existing imports do not break during the transition; it is not used at runtime.
 */

self.onmessage = () => {
  self.postMessage({ type: 'error', message: 'Browser transcription is disabled. Use server mode.' })
}
