export type SpeechInterval = {
  start: number
  end: number
}

export type BrowserAudioChunk = {
  start: number
  end: number
  samples: Float32Array
}

const FRAME_SECONDS = 0.03
const MERGE_GAP_SECONDS = 0.5
const MAX_CHUNK_SECONDS = 30
const PADDING_SECONDS = 0.3

export function detectSpeech(samples: Float32Array, sampleRate: number): SpeechInterval[] {
  const frameLength = Math.max(1, Math.floor(FRAME_SECONDS * sampleRate))
  const energies: number[] = []
  for (let offset = 0; offset < samples.length; offset += frameLength) {
    let sum = 0
    const end = Math.min(offset + frameLength, samples.length)
    for (let idx = offset; idx < end; idx += 1) sum += samples[idx] * samples[idx]
    energies.push(Math.sqrt(sum / Math.max(1, end - offset)))
  }

  const sorted = [...energies].sort((a, b) => a - b)
  const median = sorted[Math.floor(sorted.length / 2)] ?? 0
  const high = sorted[Math.floor(sorted.length * 0.9)] ?? median
  const threshold = Math.max(0.008, median + (high - median) * 0.25)
  const raw: SpeechInterval[] = []
  let activeStart: number | null = null

  energies.forEach((energy, frameIdx) => {
    if (energy >= threshold && activeStart === null) activeStart = frameIdx * FRAME_SECONDS
    if ((energy < threshold || frameIdx === energies.length - 1) && activeStart !== null) {
      const frameEnd = energy < threshold ? frameIdx * FRAME_SECONDS : (frameIdx + 1) * FRAME_SECONDS
      if (frameEnd - activeStart >= 0.12) raw.push({ start: activeStart, end: frameEnd })
      activeStart = null
    }
  })

  return mergeIntervals(raw)
}

export function chunkSpeech(samples: Float32Array, sampleRate: number, windowStartSeconds = 0): BrowserAudioChunk[] {
  const intervals = detectSpeech(samples, sampleRate)
  if (intervals.length === 0) {
    return [{ start: windowStartSeconds, end: windowStartSeconds + samples.length / sampleRate, samples }]
  }

  return intervals.flatMap((interval) => {
    const paddedStart = Math.max(0, interval.start - PADDING_SECONDS)
    const paddedEnd = Math.min(samples.length / sampleRate, interval.end + PADDING_SECONDS)
    const chunks: BrowserAudioChunk[] = []
    for (let start = paddedStart; start < paddedEnd; start += MAX_CHUNK_SECONDS) {
      const end = Math.min(start + MAX_CHUNK_SECONDS, paddedEnd)
      const startSample = Math.floor(start * sampleRate)
      const endSample = Math.min(samples.length, Math.ceil(end * sampleRate))
      chunks.push({
        start: windowStartSeconds + start,
        end: windowStartSeconds + end,
        samples: samples.slice(startSample, endSample),
      })
    }
    return chunks
  })
}

function mergeIntervals(intervals: SpeechInterval[]) {
  const merged: SpeechInterval[] = []
  intervals.forEach((interval) => {
    const previous = merged.at(-1)
    if (previous && interval.start - previous.end < MERGE_GAP_SECONDS) {
      previous.end = interval.end
    } else {
      merged.push({ ...interval })
    }
  })
  return merged
}
