// Server-only processing mode. Browser/device-side transcription has been removed.
// All transcription runs on the server using faster-whisper (medium model).
export type ProcessingMode = 'server'
export type RuntimeProcessingMode = 'server'

export type ProcessingDecision = {
  mode: RuntimeProcessingMode
  reason: string
  needsConsent: false
  slowWasmWarning: false
}

/** Always returns server mode. */
export function decideProcessingMode(): ProcessingDecision {
  return {
    mode: 'server',
    reason: 'Server transcription using faster-whisper medium model.',
    needsConsent: false,
    slowWasmWarning: false,
  }
}
