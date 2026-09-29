import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Languages, Scissors, Trash2, Wand2 } from 'lucide-react'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import { useParams } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { apiClient } from '@/api/client'
import { fileApi, subtitleApi } from '@/api/routes'
import type { ExportFormat, SubtitleSegment } from '@/types/api'

type PlayerHandle = ReturnType<typeof videojs>

export function EditorPage() {
  const { id } = useParams<{ id: string }>()
  const trackId = id ?? ''
  const queryClient = useQueryClient()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<PlayerHandle | null>(null)
  const [localMediaUrl, setLocalMediaUrl] = useState<string | null>(null)
  const [activeIdx, setActiveIdx] = useState(0)
  const [shiftOffset, setShiftOffset] = useState(0)
  const [exportFormat, setExportFormat] = useState<ExportFormat>('srt')
  const track = useQuery({ queryKey: ['track', trackId], queryFn: () => subtitleApi.track(trackId), enabled: !!trackId })
  const media = useQuery({
    queryKey: ['media-file', track.data?.file_id],
    queryFn: () => fileApi.get(track.data?.file_id ?? ''),
    enabled: Boolean(track.data?.file_id),
  })
  const segments = track.data?.segments ?? []
  const activeSegment = segments[activeIdx]
  const streamUrl = track.data && media.data?.is_stored !== false ? `${apiClient.defaults.baseURL}/files/${track.data.file_id}/stream` : undefined

  useEffect(() => {
    if (!videoRef.current || playerRef.current) return
    playerRef.current = videojs(videoRef.current, {
      controls: true,
      fluid: true,
      preload: 'auto',
    })
    return () => {
      playerRef.current?.dispose()
      playerRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!playerRef.current || !localMediaUrl) return
    playerRef.current.src({ src: localMediaUrl })
  }, [localMediaUrl])

  useEffect(() => {
    if (!playerRef.current || localMediaUrl || !streamUrl || media.data?.is_stored === false) return
    playerRef.current.src({ src: streamUrl })
  }, [localMediaUrl, media.data?.is_stored, streamUrl])

  useEffect(() => {
    const timer = window.setInterval(() => {
      const currentTime = playerRef.current?.currentTime() ?? 0
      const nextIdx = segments.findIndex((segment) => currentTime >= segment.start_time && currentTime <= segment.end_time)
      if (nextIdx >= 0) setActiveIdx(nextIdx)
    }, 250)
    return () => window.clearInterval(timer)
  }, [segments])

  const editSegment = useMutation({
    mutationFn: ({ segment, text }: { segment: SubtitleSegment; text: string }) =>
      subtitleApi.editSegment(segment.segment_id, { text }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const splitSegment = useMutation({
    mutationFn: (segment: SubtitleSegment) =>
      subtitleApi.splitSegment(segment.segment_id, {
        at_time: (segment.start_time + segment.end_time) / 2,
        at_char: Math.max(1, Math.floor(segment.text.length / 2)),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const mergeSegments = useMutation({
    mutationFn: (segment: SubtitleSegment) => {
      const next = segments[segment.idx + 1]
      if (!next) throw new Error('No next segment')
      return subtitleApi.mergeTrackSegments(trackId, { segment_a: segment.segment_id, segment_b: next.segment_id })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const shiftTrack = useMutation({
    mutationFn: () => subtitleApi.shiftTrack(trackId, { offset: shiftOffset }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const deleteSegment = useMutation({
    mutationFn: (segmentId: string) => subtitleApi.deleteSegment(segmentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const translate = useMutation({
    mutationFn: (target: string) => subtitleApi.translate(trackId, target),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const transliterate = useMutation({
    mutationFn: () => subtitleApi.transliterate(trackId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['track', trackId] }),
  })

  const overlayText = useMemo(() => activeSegment?.text ?? '', [activeSegment])

  function seek(segment: SubtitleSegment) {
    setActiveIdx(segment.idx)
    playerRef.current?.currentTime(segment.start_time)
  }

  function saveCurrent() {
    if (!activeSegment) return
    const input = document.querySelector<HTMLInputElement>(`[data-segment="${activeSegment.segment_id}"]`)
    if (input) editSegment.mutate({ segment: activeSegment, text: input.value })
  }

  function handleShortcut(event: KeyboardEvent<HTMLElement>) {
    if (event.ctrlKey && event.key === 'Enter') {
      event.preventDefault()
      saveCurrent()
    }
    if (event.altKey && event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIdx((idx) => Math.min(segments.length - 1, idx + 1))
    }
    if (event.altKey && event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIdx((idx) => Math.max(0, idx - 1))
    }
  }

  async function exportTrack() {
    const blob = await subtitleApi.exportBlob(trackId, exportFormat)
    const href = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = href
    anchor.download = `track-${trackId}.${exportFormat}`
    anchor.click()
    URL.revokeObjectURL(href)
  }

  if (track.isLoading) {
    return <section className="editor-page"><div className="empty-state"><h1>Loading subtitles...</h1><p>Fetching the selected subtitle track.</p></div></section>
  }

  if (track.isError) {
    return <section className="editor-page"><div className="empty-state"><h1>Unable to open subtitles</h1><p>{editorErrorMessage(track.error)}</p><button type="button" onClick={() => void track.refetch()}>Try again</button></div></section>
  }

  if (!track.data) {
    return <section className="editor-page"><div className="empty-state"><h1>Subtitle track not found</h1><p>Return to the project and select a generated track.</p></div></section>
  }

  return (
    <section className="editor-page" onKeyDown={handleShortcut}>
      <div className="section-header">
        <div>
          <h1>Editor</h1>
          <p>{track.data?.language} {track.data?.kind}</p>
        </div>
        <label className="local-file-picker">
          {media.data?.is_stored === false ? 'Attach local media' : 'Use local media'}
          <input type="file" accept="audio/*,video/*" onChange={(event) => {
            const file = event.target.files?.item(0)
            if (file) setLocalMediaUrl(URL.createObjectURL(file))
          }} />
        </label>
      </div>

      <div className="editor-grid">
        <div className="player-panel">
          {media.data?.is_stored === false && !localMediaUrl && (
            <div className="local-media-callout">
              This media was processed on your device. Attach the original local file to review playback here.
            </div>
          )}
          {media.data && (
            <span className={`mode-badge ${media.data.is_stored ? 'server' : 'browser'}`}>
              {media.data.is_stored ? 'Processed on server media' : 'Processed on your device'}
            </span>
          )}
          <div className="video-container">
            <video ref={videoRef} className="video-js vjs-default-skin" src={localMediaUrl ?? streamUrl} />
            <div className="subtitle-overlay">{overlayText}</div>
          </div>
          <div className="editor-tools">
            <button type="button" disabled={!activeSegment} onClick={() => activeSegment && splitSegment.mutate(activeSegment)}>
              <Scissors size={16} />
              Split
            </button>
            <button type="button" disabled={!activeSegment} onClick={() => activeSegment && mergeSegments.mutate(activeSegment)}>
              Merge next
            </button>
            <label>
              Shift
              <input type="number" step="0.1" value={shiftOffset} onChange={(event) => setShiftOffset(Number(event.target.value))} />
            </label>
            <button type="button" onClick={() => shiftTrack.mutate()}>Apply shift</button>
          </div>
          <div className="editor-tools">
            <button type="button" onClick={() => translate.mutate(track.data?.language === 'en' ? 'ta' : 'en')}>
              <Languages size={16} />
              Translate
            </button>
            <button type="button" disabled={track.data?.language !== 'ta'} onClick={() => transliterate.mutate()}>
              <Wand2 size={16} />
              Tanglish
            </button>
            <select value={exportFormat} onChange={(event) => setExportFormat(event.target.value as ExportFormat)}>
              <option value="srt">SRT</option>
              <option value="vtt">VTT</option>
              <option value="txt">TXT</option>
              <option value="html">HTML (opens in browser)</option>
            </select>
            <button type="button" onClick={exportTrack}>
              <Download size={16} />
              Export
            </button>
          </div>
        </div>

        <div className="segments-panel">
          {segments.map((segment) => (
            <div
              className={`segment-row ${segment.idx === activeIdx ? 'active' : ''} ${segment.confidence < 0.6 ? 'low-confidence' : ''}`}
              key={segment.segment_id}
              onClick={() => seek(segment)}
            >
              <span>{segment.idx + 1}</span>
              <input
                data-segment={segment.segment_id}
                defaultValue={segment.text}
                onBlur={(event) => editSegment.mutate({ segment, text: event.target.value })}
              />
              <small>{segment.start_time.toFixed(2)} - {segment.end_time.toFixed(2)}</small>
              <button type="button" className="icon-button danger" onClick={() => deleteSegment.mutate(segment.segment_id)}>
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function editorErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const response = error.response?.data as { detail?: string } | undefined
    return response?.detail ?? error.message
  }
  return error instanceof Error ? error.message : 'The subtitle track could not be loaded.'
}
