/**
 * Éditeur de clips vidéo
 * Workflow : Upload source → Player + Timeline → Marquer IN/OUT → Extraire / Merger → Créer vidéo
 */
import {
  useEffect, useRef, useState,
} from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload, Play, Pause, SkipBack, SkipForward,
  Scissors, Trash2, ChevronRight, Merge, Zap,
  AlertCircle, Loader,
} from 'lucide-react'
import { createBatchExtractJob, type SourceInfo, type ClipMark } from '../api'
import {
  getEditorState, setEditorState, resetEditorState,
  type StoredClip,
} from '../editorStore'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmt(s: number): string {
  if (!isFinite(s) || s < 0) s = 0
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = Math.floor(s % 60)
  const ds = Math.floor((s % 1) * 10)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}.${ds}`
  return `${m}:${String(sec).padStart(2, '0')}.${ds}`
}

const SPEEDS = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, 4]

// ─── Upload zone ──────────────────────────────────────────────────────────────

function UploadZone({ onUploaded }: { onUploaded: (info: SourceInfo) => void }) {
  const [dragging,  setDragging]  = useState(false)
  const [progress,  setProgress]  = useState<number | null>(null)
  const [error,     setError]     = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleFile(file: File) {
    setError(null)
    setProgress(0)
    try {
      const info = await uploadSourceXHR(file, setProgress)
      onUploaded(info)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erreur upload')
      setProgress(null)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-2">Éditeur de clips</h1>
        <p className="text-gray-400">Chargez une vidéo, marquez des segments, extrayez et créez</p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => progress === null && inputRef.current?.click()}
        className={`w-full max-w-lg border-2 border-dashed rounded-2xl p-6 sm:p-10 md:p-12 text-center cursor-pointer transition-all ${
          dragging
            ? 'border-violet-400 bg-violet-500/10'
            : 'border-gray-600 bg-gray-900 hover:border-violet-500 hover:bg-gray-800'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="video/*,.mkv,.avi,.mov"
          className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />
        {progress === null ? (
          <>
            <Upload size={40} className="mx-auto text-violet-400 mb-4" />
            <p className="text-white font-medium text-lg">Glisser-déposer ou cliquer</p>
            <p className="text-gray-500 text-sm mt-1">MP4, MKV, AVI, MOV, WebM…</p>
          </>
        ) : (
          <>
            <Loader size={36} className="mx-auto text-violet-400 mb-4 animate-spin" />
            <p className="text-white font-medium">Upload en cours… {progress}%</p>
            <div className="mt-4 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-violet-500 transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
    </div>
  )
}

// ─── Timeline ─────────────────────────────────────────────────────────────────

const CLIP_COLORS = [
  'bg-violet-500/60',
  'bg-blue-500/60',
  'bg-emerald-500/60',
  'bg-amber-500/60',
  'bg-pink-500/60',
  'bg-cyan-500/60',
]
const CLIP_BORDERS = [
  'border-violet-400',
  'border-blue-400',
  'border-emerald-400',
  'border-amber-400',
  'border-pink-400',
  'border-cyan-400',
]

interface TimelineProps {
  duration: number
  currentTime: number
  clips: (ClipMark & { id: string })[]
  pendingStart: number | null
  onSeek: (t: number) => void
}

function Timeline({ duration, currentTime, clips, pendingStart, onSeek }: TimelineProps) {
  const ref = useRef<HTMLDivElement>(null)

  function pct(t: number) {
    return duration > 0 ? `${Math.min(100, (t / duration) * 100)}%` : '0%'
  }

  function handleClick(e: React.MouseEvent) {
    if (!ref.current || duration <= 0) return
    const rect = ref.current.getBoundingClientRect()
    const ratio = (e.clientX - rect.left) / rect.width
    onSeek(Math.max(0, Math.min(duration, ratio * duration)))
  }

  // Drag to seek
  function handleMouseDown(e: React.MouseEvent) {
    const el = ref.current
    if (!el || duration <= 0) return
    e.preventDefault()
    function move(ev: MouseEvent) {
      const rect = el!.getBoundingClientRect()
      const ratio = (ev.clientX - rect.left) / rect.width
      onSeek(Math.max(0, Math.min(duration, ratio * duration)))
    }
    function up() {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', up)
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
  }

  return (
    <div className="space-y-1">
      {/* Timestamps */}
      <div className="flex justify-between text-xs text-gray-600 font-mono px-0.5">
        <span>{fmt(0)}</span>
        <span>{fmt(duration / 4)}</span>
        <span>{fmt(duration / 2)}</span>
        <span>{fmt((duration * 3) / 4)}</span>
        <span>{fmt(duration)}</span>
      </div>

      {/* Timeline bar */}
      <div
        ref={ref}
        className="relative h-10 bg-gray-800 rounded-lg cursor-pointer select-none"
        onClick={handleClick}
        onMouseDown={handleMouseDown}
      >
        {/* Played zone */}
        <div
          className="absolute top-0 left-0 h-full bg-gray-700 rounded-lg"
          style={{ width: pct(currentTime) }}
        />

        {/* Clip segments */}
        {clips.map((clip, i) => (
          <div
            key={clip.id}
            className={`absolute top-1 h-8 rounded border ${CLIP_COLORS[i % CLIP_COLORS.length]} ${CLIP_BORDERS[i % CLIP_BORDERS.length]}`}
            style={{
              left:  pct(clip.start),
              width: pct(clip.end - clip.start),
            }}
            title={`Clip ${i + 1}: ${fmt(clip.start)} → ${fmt(clip.end)}`}
          />
        ))}

        {/* Pending IN marker */}
        {pendingStart !== null && (
          <div
            className="absolute top-0 h-full w-0.5 bg-green-400 shadow-[0_0_6px_#4ade80]"
            style={{ left: pct(pendingStart) }}
          >
            <span className="absolute -top-4 -translate-x-1/2 text-green-400 text-[10px] font-mono whitespace-nowrap">
              IN {fmt(pendingStart)}
            </span>
          </div>
        )}

        {/* Current time cursor */}
        <div
          className="absolute top-0 h-full w-0.5 bg-white shadow-[0_0_4px_white] pointer-events-none"
          style={{ left: pct(currentTime) }}
        />
      </div>
    </div>
  )
}

// ─── Main Editor ──────────────────────────────────────────────────────────────

export default function Editor() {
  const navigate = useNavigate()

  // Restaurer le state depuis le store persistant (survit à la navigation)
  const saved = getEditorState()

  // Source
  const [source,      setSourceState] = useState<SourceInfo | null>(saved.source)

  // Player state
  const videoRef      = useRef<HTMLVideoElement>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration,    setDuration]    = useState(0)
  const [playing,     setPlaying]     = useState(false)
  const [speed,       setSpeed]       = useState(1)
  const [videoReady,  setVideoReady]  = useState(false)

  // Clip marking
  const [pendingStart, setPendingStartState] = useState<number | null>(saved.pendingStart)
  const [clips, setClipsState]              = useState<StoredClip[]>(saved.clips)

  // Submission
  const [submitting, setSubmitting] = useState(false)
  const [submitErr,  setSubmitErr]  = useState<string | null>(null)

  // Wrappers qui écrivent aussi dans le store
  function setSource(s: SourceInfo | null) {
    setSourceState(s)
    setEditorState({ source: s })
  }
  function setClips(fn: (prev: StoredClip[]) => StoredClip[]) {
    setClipsState(prev => {
      const next = fn(prev)
      setEditorState({ clips: next })
      return next
    })
  }
  function setPendingStart(t: number | null) {
    setPendingStartState(t)
    setEditorState({ pendingStart: t })
  }

  // Sauvegarder la position vidéo en continu
  const saveTimeRef = useRef<ReturnType<typeof setInterval> | null>(null)
  useEffect(() => {
    saveTimeRef.current = setInterval(() => {
      if (videoRef.current) setEditorState({ lastTime: videoRef.current.currentTime })
    }, 2000)
    return () => { if (saveTimeRef.current) clearInterval(saveTimeRef.current) }
  }, [])

  // ── Video event listeners ──────────────────────────────────────────────────
  useEffect(() => {
    const video = videoRef.current
    if (!video || !source) return

    const onTime     = () => setCurrentTime(video.currentTime)
    const onMeta     = () => {
      setDuration(video.duration)
      setVideoReady(true)
      // Restaurer la position sauvegardée
      const saved = getEditorState()
      if (saved.lastTime > 0 && saved.lastTime < video.duration) {
        video.currentTime = saved.lastTime
      }
    }
    const onPlay     = () => setPlaying(true)
    const onPause    = () => setPlaying(false)
    const onEnded    = () => setPlaying(false)

    video.addEventListener('timeupdate',     onTime)
    video.addEventListener('loadedmetadata', onMeta)
    video.addEventListener('play',           onPlay)
    video.addEventListener('pause',          onPause)
    video.addEventListener('ended',          onEnded)
    return () => {
      video.removeEventListener('timeupdate',     onTime)
      video.removeEventListener('loadedmetadata', onMeta)
      video.removeEventListener('play',           onPlay)
      video.removeEventListener('pause',          onPause)
      video.removeEventListener('ended',          onEnded)
    }
  }, [source])

  // ── Controls ──────────────────────────────────────────────────────────────
  function togglePlay() {
    const v = videoRef.current
    if (!v) return
    playing ? v.pause() : v.play()
  }

  function seek(t: number) {
    const v = videoRef.current
    if (!v) return
    v.currentTime = Math.max(0, Math.min(duration, t))
  }

  function changeSpeed(s: number) {
    setSpeed(s)
    if (videoRef.current) videoRef.current.playbackRate = s
  }

  // ── Keyboard shortcuts ────────────────────────────────────────────────────
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!source || (e.target as HTMLElement).tagName === 'INPUT') return
      if (e.code === 'Space')       { e.preventDefault(); togglePlay() }
      if (e.code === 'ArrowLeft')   seek(currentTime - (e.shiftKey ? 5 : 1))
      if (e.code === 'ArrowRight')  seek(currentTime + (e.shiftKey ? 5 : 1))
      if (e.code === 'KeyI')        markIn()
      if (e.code === 'KeyO')        markOut()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  // ── Clip marking ──────────────────────────────────────────────────────────
  function markIn() {
    setPendingStart(currentTime)
  }

  function markOut() {
    if (pendingStart === null) return
    const start = pendingStart
    const end   = currentTime
    if (end <= start) {
      setPendingStart(null)
      return
    }
    setClips(prev => [
      ...prev,
      { id: crypto.randomUUID(), start, end },
    ])
    setPendingStart(null)
  }

  function removeClip(id: string) {
    setClips(prev => prev.filter(c => c.id !== id))
  }

  function jumpToClip(clip: ClipMark) {
    seek(clip.start)
    videoRef.current?.pause()
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  async function submitBatch(merge: boolean) {
    if (!source || clips.length === 0) return
    setSubmitting(true)
    setSubmitErr(null)
    try {
      const sorted = [...clips].sort((a, b) => a.start - b.start)
      const job = await createBatchExtractJob({
        source_id: source.source_id,
        clips:     sorted.map(({ start, end }) => ({ start, end })),
        merge,
        title:     `${sorted.length} clip${sorted.length > 1 ? 's' : ''} — ${source.filename}`,
      })
      navigate(`/jobs/${job.id}`)
    } catch (e: unknown) {
      setSubmitErr(e instanceof Error ? e.message : 'Erreur')
      setSubmitting(false)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  if (!source) {
    return <UploadZone onUploaded={setSource} />
  }

  const canMark    = videoReady && duration > 0
  const canSubmit  = clips.length > 0 && !submitting
  const totalClipDuration = clips.reduce((acc, c) => acc + (c.end - c.start), 0)

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Éditeur de clips</h1>
          <p className="text-gray-500 text-sm mt-0.5 truncate max-w-[260px] sm:max-w-none">{source.filename}</p>
        </div>
        <button
          type="button"
          onClick={() => { resetEditorState(); setSourceState(null); setClipsState([]); setPendingStartState(null) }}
          className="self-start sm:self-auto text-xs text-gray-500 hover:text-gray-300 border border-gray-700 hover:border-gray-500 px-3 py-2 rounded-lg transition-colors"
        >
          Changer de vidéo
        </button>
      </div>

      {/* Main layout: video left, clips right */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-4">

        {/* ── Left: Player ──────────────────────────────────────── */}
        <div className="space-y-3">

          {/* Video */}
          <div className="relative bg-black rounded-2xl overflow-hidden aspect-video">
            <video
              ref={videoRef}
              src={`/api/sources/${source.source_id}/stream`}
              className="w-full h-full object-contain"
              preload="metadata"
              onClick={togglePlay}
            />
            {!videoReady && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                <Loader size={32} className="text-violet-400 animate-spin" />
              </div>
            )}
            {/* Play overlay */}
            {!playing && videoReady && (
              <div
                className="absolute inset-0 flex items-center justify-center cursor-pointer"
                onClick={togglePlay}
              >
                <div className="bg-black/50 rounded-full p-4">
                  <Play size={32} className="text-white" fill="white" />
                </div>
              </div>
            )}
          </div>

          {/* Controls row */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 bg-gray-900 rounded-2xl px-4 py-3">
            {/* Seek -10s */}
            <button
              type="button"
              onClick={() => seek(currentTime - 10)}
              className="text-gray-400 hover:text-white transition-colors"
              title="Reculer 10s (←)"
            >
              <SkipBack size={18} />
            </button>

            {/* Play/Pause */}
            <button
              type="button"
              onClick={togglePlay}
              disabled={!videoReady}
              className="bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white rounded-full w-9 h-9 flex items-center justify-center transition-colors"
              title="Play/Pause (Espace)"
            >
              {playing ? <Pause size={16} fill="white" /> : <Play size={16} fill="white" />}
            </button>

            {/* Seek +10s */}
            <button
              type="button"
              onClick={() => seek(currentTime + 10)}
              className="text-gray-400 hover:text-white transition-colors"
              title="Avancer 10s (→)"
            >
              <SkipForward size={18} />
            </button>

            {/* Time */}
            <span className="font-mono text-sm text-gray-300 tabular-nums">
              {fmt(currentTime)}
              <span className="text-gray-600"> / </span>
              {fmt(duration)}
            </span>

            {/* Speed */}
            <div className="ml-auto flex flex-wrap items-center gap-1">
              {SPEEDS.map(s => (
                <button
                  key={s}
                  type="button"
                  onClick={() => changeSpeed(s)}
                  className={`text-xs px-2 py-1 rounded-md transition-colors ${
                    speed === s
                      ? 'bg-violet-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-gray-900 rounded-2xl px-4 py-4 space-y-3">
            <Timeline
              duration={duration}
              currentTime={currentTime}
              clips={clips}
              pendingStart={pendingStart}
              onSeek={seek}
            />

            {/* Mark IN / OUT */}
            <div className="flex gap-2 mt-1">
              <button
                type="button"
                disabled={!canMark}
                onClick={markIn}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium border transition-all ${
                  pendingStart !== null
                    ? 'bg-green-500/10 border-green-500 text-green-400'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-green-500 hover:text-green-400 disabled:opacity-40'
                }`}
                title="Marquer le début du clip (I)"
              >
                <Scissors size={15} />
                {pendingStart !== null
                  ? `IN marqué — ${fmt(pendingStart)}`
                  : 'Marquer début (I)'}
              </button>

              <button
                type="button"
                disabled={!canMark || pendingStart === null || currentTime <= (pendingStart ?? 0)}
                onClick={markOut}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium border bg-gray-800 border-gray-700 text-gray-300 hover:border-violet-500 hover:text-violet-300 disabled:opacity-40 transition-all"
                title="Marquer la fin du clip (O)"
              >
                <Scissors size={15} className="scale-x-[-1]" />
                Marquer fin (O)
              </button>
            </div>

            {/* Keyboard shortcuts hint */}
            <p className="text-[11px] text-gray-600 text-center">
              Espace = play/pause · ← → = ±1s · Shift+←→ = ±5s · I = IN · O = OUT
            </p>
          </div>
        </div>

        {/* ── Right: Clip list ──────────────────────────────────── */}
        <div className="space-y-3">
          <div className="bg-gray-900 rounded-2xl p-4 space-y-3 min-h-[200px]">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-white text-sm">
                Clips marqués
                {clips.length > 0 && (
                  <span className="ml-2 bg-violet-600 text-white text-xs rounded-full px-2 py-0.5">
                    {clips.length}
                  </span>
                )}
              </h2>
              {clips.length > 0 && (
                <span className="text-xs text-gray-500 font-mono">
                  Total: {fmt(totalClipDuration)}
                </span>
              )}
            </div>

            {clips.length === 0 ? (
              <div className="text-center text-gray-600 py-8">
                <Scissors size={28} className="mx-auto mb-2 opacity-40" />
                <p className="text-sm">Aucun clip marqué</p>
                <p className="text-xs mt-1">Utilisez IN / OUT pour délimiter des segments</p>
              </div>
            ) : (
              <div className="space-y-2">
                {clips.map((clip, i) => (
                  <div
                    key={clip.id}
                    className={`flex items-center gap-2 p-2.5 rounded-xl border ${CLIP_BORDERS[i % CLIP_BORDERS.length]} bg-gray-800/50`}
                  >
                    {/* Color dot */}
                    <div className={`w-2 h-2 rounded-full shrink-0 ${CLIP_COLORS[i % CLIP_COLORS.length].replace('/60', '')}`} />

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-mono text-white">
                        {fmt(clip.start)} → {fmt(clip.end)}
                      </p>
                      <p className="text-xs text-gray-500">
                        durée: {fmt(clip.end - clip.start)}
                      </p>
                    </div>

                    {/* Actions */}
                    <button
                      type="button"
                      onClick={() => jumpToClip(clip)}
                      className="text-gray-500 hover:text-violet-400 transition-colors"
                      title="Aller à ce clip"
                    >
                      <ChevronRight size={15} />
                    </button>
                    <button
                      type="button"
                      onClick={() => removeClip(clip.id)}
                      className="text-gray-600 hover:text-red-400 transition-colors"
                      title="Supprimer ce clip"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="space-y-2">
            {submitErr && (
              <div className="flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 text-sm">
                <AlertCircle size={14} />
                {submitErr}
              </div>
            )}

            {/* Extraire séparément (merge=false) — un fichier par clip */}
            <button
              type="button"
              disabled={!canSubmit}
              onClick={() => submitBatch(false)}
              className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-violet-500 text-white py-3 rounded-xl font-medium text-sm transition-all disabled:opacity-40"
            >
              {submitting ? <Loader size={16} className="animate-spin" /> : <Scissors size={16} />}
              Extraire les clips séparément
              {clips.length > 0 && <span className="text-gray-400">({clips.length})</span>}
            </button>

            {/* Merger en une vidéo (merge=true) */}
            <button
              type="button"
              disabled={!canSubmit}
              onClick={() => submitBatch(true)}
              className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 text-white py-3 rounded-xl font-medium text-sm transition-colors disabled:opacity-40"
            >
              {submitting ? <Loader size={16} className="animate-spin" /> : <Merge size={16} />}
              Merger en une vidéo
            </button>

            {/* Suite logique si 1 clip ou merged */}
            {clips.length > 0 && (
              <p className="text-xs text-gray-600 text-center leading-relaxed">
                <Zap size={10} className="inline mr-1 text-violet-500" />
                Après l'extraction, utilisez "Job précédent" dans Podcast, Wave ou Portrait
              </p>
            )}
          </div>

          {/* Source info */}
          <div className="bg-gray-900/50 rounded-xl p-3 space-y-1">
            <p className="text-xs text-gray-600 font-medium uppercase tracking-wider">Source</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs font-mono">
              <span className="text-gray-500">Durée</span>
              <span className="text-gray-300">{fmt(source.duration)}</span>
              {source.width > 0 && <>
                <span className="text-gray-500">Résolution</span>
                <span className="text-gray-300">{source.width}×{source.height}</span>
              </>}
              {source.fps > 0 && <>
                <span className="text-gray-500">FPS</span>
                <span className="text-gray-300">{source.fps}</span>
              </>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── XHR Upload with progress ─────────────────────────────────────────────────

function uploadSourceXHR(file: File, onProgress: (pct: number) => void): Promise<SourceInfo> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const fd  = new FormData()
    fd.append('file', file)

    xhr.upload.addEventListener('progress', e => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
    })
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        try { resolve(JSON.parse(xhr.responseText)) }
        catch { reject(new Error('Réponse invalide du serveur')) }
      } else {
        reject(new Error(`Upload échoué (${xhr.status}): ${xhr.responseText}`))
      }
    })
    xhr.addEventListener('error', () => reject(new Error('Erreur réseau lors de l\'upload')))
    xhr.open('POST', '/api/sources/upload')
    xhr.send(fd)
  })
}
