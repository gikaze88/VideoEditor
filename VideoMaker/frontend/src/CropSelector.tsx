/**
 * Sélecteur de crop visuel et interactif.
 * - Extrait une frame de la vidéo dans le navigateur via <canvas>
 * - Affiche la frame avec un rectangle draggable (zone à GARDER)
 * - Les zones supprimées sont assombries
 * - 8 poignées de redimensionnement + déplacement au centre
 * - Calcule et expose les valeurs px (top/bottom/left/right à couper)
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { RotateCcw, Loader } from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface CropRect {
  x: number // px depuis bord gauche de l'image affichée
  y: number // px depuis bord haut
  w: number
  h: number
}

type HandleId = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'move'

export interface CropValues {
  top: number
  bottom: number
  left: number
  right: number
}

interface DragState {
  handle: HandleId
  startX: number
  startY: number
  startRect: CropRect
}

interface Props {
  file: File
  onChange: (values: CropValues) => void
}

// ─── Constantes ───────────────────────────────────────────────────────────────

const MIN_SIZE = 40    // taille minimale du crop en px affichés
const HANDLE_SIZE = 12 // taille des poignées en px

const CURSOR_MAP: Record<HandleId, string> = {
  nw: 'nw-resize', n: 'n-resize', ne: 'ne-resize',
  e: 'e-resize',
  se: 'se-resize', s: 's-resize', sw: 'sw-resize',
  w: 'w-resize',
  move: 'move',
}

// ─── Utilitaires ─────────────────────────────────────────────────────────────

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v))
}

async function extractFrame(file: File, timeSec = 2): Promise<{ dataUrl: string; width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    const url = URL.createObjectURL(file)
    video.preload = 'metadata'
    video.muted = true
    video.src = url

    const cleanup = () => URL.revokeObjectURL(url)

    video.addEventListener('loadedmetadata', () => {
      // Aller à 10% de la durée ou 2s, selon ce qui est plus court
      video.currentTime = Math.min(timeSec, video.duration * 0.1)
    })

    video.addEventListener('seeked', () => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        const ctx = canvas.getContext('2d')!
        ctx.drawImage(video, 0, 0)
        cleanup()
        resolve({
          dataUrl: canvas.toDataURL('image/jpeg', 0.85),
          width: video.videoWidth,
          height: video.videoHeight,
        })
      } catch (e) {
        cleanup()
        reject(e)
      }
    })

    video.addEventListener('error', () => {
      cleanup()
      reject(new Error('Impossible de lire la vidéo'))
    })
  })
}

// ─── Composant principal ──────────────────────────────────────────────────────

export default function CropSelector({ file, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [frame, setFrame]           = useState<{ dataUrl: string; width: number; height: number } | null>(null)
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState<string | null>(null)
  const [displaySize, setDisplaySize] = useState({ w: 0, h: 0 })
  const [rect, setRect]             = useState<CropRect>({ x: 0, y: 0, w: 0, h: 0 })
  const dragRef = useRef<DragState | null>(null)

  // Extraire la frame quand le fichier change
  useEffect(() => {
    setLoading(true)
    setError(null)
    extractFrame(file)
      .then(f => {
        setFrame(f)
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
      })
  }, [file])

  // Mesurer le conteneur et calculer la taille d'affichage
  useLayoutEffect(() => {
    if (!frame || !containerRef.current) return
    const el = containerRef.current
    const updateSize = () => {
      const dw = el.clientWidth
      const dh = Math.round(dw * (frame.height / frame.width))
      setDisplaySize({ w: dw, h: dh })
      // Initialiser le rect au maximum (tout garder)
      setRect({ x: 0, y: 0, w: dw, h: dh })
    }
    updateSize()
    const ro = new ResizeObserver(updateSize)
    ro.observe(el)
    return () => ro.disconnect()
  }, [frame])

  // Notifier le parent quand le rect change
  useEffect(() => {
    if (!frame || !displaySize.w) return
    const scaleX = frame.width  / displaySize.w
    const scaleY = frame.height / displaySize.h
    const values: CropValues = {
      top:    Math.round(rect.y * scaleY),
      bottom: Math.round((displaySize.h - rect.y - rect.h) * scaleY),
      left:   Math.round(rect.x * scaleX),
      right:  Math.round((displaySize.w - rect.x - rect.w) * scaleX),
    }
    onChange(values)
  }, [rect, frame, displaySize, onChange])

  // ─── Drag handlers ──────────────────────────────────────────────────────────

  const startDrag = useCallback((handle: HandleId, e: React.PointerEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragRef.current = {
      handle,
      startX: e.clientX,
      startY: e.clientY,
      startRect: { ...rect },
    }
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }, [rect])

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    const drag = dragRef.current
    if (!drag) return
    const { w: dw, h: dh } = displaySize
    const dx = e.clientX - drag.startX
    const dy = e.clientY - drag.startY
    const { x: sx, y: sy, w: sw, h: sh } = drag.startRect
    let { x, y, w, h } = drag.startRect

    switch (drag.handle) {
      case 'move':
        x = clamp(sx + dx, 0, dw - sw)
        y = clamp(sy + dy, 0, dh - sh)
        break
      case 'nw':
        x = clamp(sx + dx, 0, sx + sw - MIN_SIZE)
        y = clamp(sy + dy, 0, sy + sh - MIN_SIZE)
        w = sw - (x - sx)
        h = sh - (y - sy)
        break
      case 'n':
        y = clamp(sy + dy, 0, sy + sh - MIN_SIZE)
        h = sh - (y - sy)
        break
      case 'ne':
        y = clamp(sy + dy, 0, sy + sh - MIN_SIZE)
        w = clamp(sw + dx, MIN_SIZE, dw - sx)
        h = sh - (y - sy)
        break
      case 'e':
        w = clamp(sw + dx, MIN_SIZE, dw - sx)
        break
      case 'se':
        w = clamp(sw + dx, MIN_SIZE, dw - sx)
        h = clamp(sh + dy, MIN_SIZE, dh - sy)
        break
      case 's':
        h = clamp(sh + dy, MIN_SIZE, dh - sy)
        break
      case 'sw':
        x = clamp(sx + dx, 0, sx + sw - MIN_SIZE)
        w = sw - (x - sx)
        h = clamp(sh + dy, MIN_SIZE, dh - sy)
        break
      case 'w':
        x = clamp(sx + dx, 0, sx + sw - MIN_SIZE)
        w = sw - (x - sx)
        break
    }
    setRect({ x, y, w, h })
  }, [displaySize])

  const onPointerUp = useCallback(() => {
    dragRef.current = null
  }, [])

  // ─── Reset ──────────────────────────────────────────────────────────────────

  const reset = () => {
    setRect({ x: 0, y: 0, w: displaySize.w, h: displaySize.h })
  }

  // ─── Calcul des valeurs affichées ────────────────────────────────────────────

  const cropValues: CropValues = frame && displaySize.w ? {
    top:    Math.round(rect.y * (frame.height / displaySize.h)),
    bottom: Math.round((displaySize.h - rect.y - rect.h) * (frame.height / displaySize.h)),
    left:   Math.round(rect.x * (frame.width  / displaySize.w)),
    right:  Math.round((displaySize.w - rect.x - rect.w) * (frame.width  / displaySize.w)),
  } : { top: 0, bottom: 0, left: 0, right: 0 }

  const keptW = frame ? frame.width  - cropValues.left - cropValues.right  : 0
  const keptH = frame ? frame.height - cropValues.top  - cropValues.bottom : 0

  // ─── Poignées de resize ──────────────────────────────────────────────────────

  const handles: Array<{ id: HandleId; style: React.CSSProperties }> = [
    { id: 'nw', style: { left: rect.x,               top: rect.y } },
    { id: 'n',  style: { left: rect.x + rect.w / 2,  top: rect.y } },
    { id: 'ne', style: { left: rect.x + rect.w,       top: rect.y } },
    { id: 'e',  style: { left: rect.x + rect.w,       top: rect.y + rect.h / 2 } },
    { id: 'se', style: { left: rect.x + rect.w,       top: rect.y + rect.h } },
    { id: 's',  style: { left: rect.x + rect.w / 2,  top: rect.y + rect.h } },
    { id: 'sw', style: { left: rect.x,               top: rect.y + rect.h } },
    { id: 'w',  style: { left: rect.x,               top: rect.y + rect.h / 2 } },
  ]

  // ─── Rendu ───────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 bg-gray-800 rounded-xl text-gray-400 gap-2">
        <Loader size={18} className="animate-spin" />
        Extraction de la frame...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-48 bg-gray-800 rounded-xl text-red-400 text-sm">
        {error}
      </div>
    )
  }

  if (!frame) return null

  return (
    <div className="space-y-3">
      {/* Éditeur visuel */}
      <div
        ref={containerRef}
        className="relative w-full select-none rounded-xl overflow-hidden cursor-crosshair"
        style={{ height: displaySize.h || 'auto', background: '#000' }}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        {displaySize.w > 0 && (
          <>
            {/* Image de fond */}
            <img
              src={frame.dataUrl}
              alt="preview"
              className="absolute inset-0 w-full h-full object-fill pointer-events-none"
              draggable={false}
            />

            {/* Overlays sombres (zones supprimées) */}
            {/* Haut */}
            {rect.y > 0 && (
              <div
                className="absolute bg-black/60"
                style={{ left: 0, top: 0, width: '100%', height: rect.y }}
              />
            )}
            {/* Bas */}
            {rect.y + rect.h < displaySize.h && (
              <div
                className="absolute bg-black/60"
                style={{ left: 0, top: rect.y + rect.h, width: '100%', height: displaySize.h - rect.y - rect.h }}
              />
            )}
            {/* Gauche */}
            {rect.x > 0 && (
              <div
                className="absolute bg-black/60"
                style={{ left: 0, top: rect.y, width: rect.x, height: rect.h }}
              />
            )}
            {/* Droite */}
            {rect.x + rect.w < displaySize.w && (
              <div
                className="absolute bg-black/60"
                style={{ left: rect.x + rect.w, top: rect.y, width: displaySize.w - rect.x - rect.w, height: rect.h }}
              />
            )}

            {/* Bordure de la zone gardée */}
            <div
              className="absolute border-2 border-white/80"
              style={{ left: rect.x, top: rect.y, width: rect.w, height: rect.h }}
            >
              {/* Zone de déplacement (centre) */}
              <div
                className="absolute inset-0"
                style={{ cursor: CURSOR_MAP.move }}
                onPointerDown={e => startDrag('move', e)}
              />

              {/* Règle des tiers (guide visuel) */}
              <div className="absolute inset-0 pointer-events-none">
                {[1/3, 2/3].map(v => (
                  <div key={v} className="absolute w-full border-t border-white/20" style={{ top: `${v * 100}%` }} />
                ))}
                {[1/3, 2/3].map(v => (
                  <div key={v} className="absolute h-full border-l border-white/20" style={{ left: `${v * 100}%` }} />
                ))}
              </div>
            </div>

            {/* Poignées de resize */}
            {handles.map(h => (
              <div
                key={h.id}
                className="absolute bg-white border-2 border-gray-700 rounded-sm shadow-lg z-10"
                style={{
                  width: HANDLE_SIZE,
                  height: HANDLE_SIZE,
                  left: h.style.left as number - HANDLE_SIZE / 2,
                  top: h.style.top as number - HANDLE_SIZE / 2,
                  cursor: CURSOR_MAP[h.id],
                }}
                onPointerDown={e => startDrag(h.id, e)}
              />
            ))}
          </>
        )}
      </div>

      {/* Barre d'infos + reset */}
      <div className="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-2.5">
        <div className="flex gap-4 text-xs font-mono">
          <span className="text-gray-400">
            Zone gardée: <span className="text-white font-semibold">{keptW} × {keptH}</span> px
          </span>
          <span className="text-gray-500">|</span>
          <span className="text-red-400">
            ↑{cropValues.top} ↓{cropValues.bottom} ←{cropValues.left} →{cropValues.right}
          </span>
        </div>
        <button
          type="button"
          onClick={reset}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
        >
          <RotateCcw size={12} />
          Reset
        </button>
      </div>

      {/* Labels directionnel autour de l'image pour guider */}
      <div className="grid grid-cols-3 gap-1 text-center text-xs text-gray-500">
        <div />
        <div className="flex justify-center gap-2">
          <span>↑ Haut supprimé:</span>
          <span className="text-white font-mono">{cropValues.top}px</span>
        </div>
        <div />
        <div className="flex justify-end items-center gap-1">
          <span>←</span>
          <span className="text-white font-mono">{cropValues.left}px</span>
        </div>
        <div className="text-gray-600">[ zone gardée ]</div>
        <div className="flex justify-start items-center gap-1">
          <span className="text-white font-mono">{cropValues.right}px</span>
          <span>→</span>
        </div>
        <div />
        <div className="flex justify-center gap-2">
          <span>↓ Bas supprimé:</span>
          <span className="text-white font-mono">{cropValues.bottom}px</span>
        </div>
        <div />
      </div>
    </div>
  )
}
