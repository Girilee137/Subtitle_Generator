export type DecodedAudioWindow = {
  startSeconds: number
  samples: Float32Array
  sampleRate: number
}

const TARGET_SAMPLE_RATE = 16_000
const MAX_WINDOW_SECONDS = 600

export async function decodeAudioWindows(file: File, maxWindowSeconds = MAX_WINDOW_SECONDS): Promise<DecodedAudioWindow[]> {
  const AudioCtor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AudioCtor) throw new Error('Web Audio is not available in this browser.')

  const context = new AudioCtor()
  try {
    const decoded = await context.decodeAudioData(await file.arrayBuffer())
    const mono = mixToMono(decoded)
    const resampled = resampleLinear(mono, decoded.sampleRate, TARGET_SAMPLE_RATE)
    const windowLength = Math.max(TARGET_SAMPLE_RATE, Math.floor(maxWindowSeconds * TARGET_SAMPLE_RATE))
    const windows: DecodedAudioWindow[] = []

    for (let offset = 0; offset < resampled.length; offset += windowLength) {
      windows.push({
        startSeconds: offset / TARGET_SAMPLE_RATE,
        samples: resampled.slice(offset, Math.min(offset + windowLength, resampled.length)),
        sampleRate: TARGET_SAMPLE_RATE,
      })
    }

    return windows
  } finally {
    void context.close()
  }
}

export async function readMediaDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const element = document.createElement(file.type.startsWith('audio/') ? 'audio' : 'video')
    const url = URL.createObjectURL(file)
    element.preload = 'metadata'
    element.onloadedmetadata = () => {
      const duration = Number.isFinite(element.duration) ? element.duration : null
      URL.revokeObjectURL(url)
      resolve(duration)
    }
    element.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(null)
    }
    element.src = url
  })
}

function mixToMono(buffer: AudioBuffer) {
  const mono = new Float32Array(buffer.length)
  for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) {
    const data = buffer.getChannelData(channel)
    for (let idx = 0; idx < data.length; idx += 1) mono[idx] += data[idx] / buffer.numberOfChannels
  }
  return mono
}

function resampleLinear(samples: Float32Array, fromRate: number, toRate: number) {
  if (fromRate === toRate) return samples
  const ratio = fromRate / toRate
  const next = new Float32Array(Math.ceil(samples.length / ratio))
  for (let idx = 0; idx < next.length; idx += 1) {
    const source = idx * ratio
    const left = Math.floor(source)
    const right = Math.min(samples.length - 1, left + 1)
    const mix = source - left
    next[idx] = samples[left] * (1 - mix) + samples[right] * mix
  }
  return next
}
