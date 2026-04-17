import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Upload, Play, Plus, X, Youtube, ChevronDown, ChevronUp } from 'lucide-react'
import {
  createJob, fetchConfig, type AppConfig,
  getYoutubeAuthStatus, getYoutubePlaylists, fetchYoutubeMeta,
  type YoutubePlaylist, type YoutubeCategory, type YoutubeLanguage,
} from '../api'
import CropSelector, { type CropValues } from '../CropSelector'
import JobPicker from '../JobPicker'

// ─── Composants utilitaires ──────────────────────────────────────────────────

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-gray-300 mb-1">{children}</label>
}

function Required() {
  return <span className="text-red-400 ml-0.5">*</span>
}

function Select({
  name, value, onChange, children,
}: { name: string; value: string; onChange: (v: string) => void; children: React.ReactNode }) {
  return (
    <select
      name={name}
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
    >
      {children}
    </select>
  )
}

function Input({
  name, placeholder, value, onChange, type = 'text',
}: { name: string; placeholder?: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <input
      name={name}
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
    />
  )
}

function FileInput({
  name, label, accept, multiple = false, onPicked,
}: { name: string; label: string; accept?: string; multiple?: boolean; onPicked?: (has: boolean) => void }) {
  const ref = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<string[]>([])

  return (
    <div>
      <input
        ref={ref}
        type="file"
        name={name}
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={e => {
          const picked = Array.from(e.target.files ?? []).map(f => f.name)
          setFiles(picked)
          onPicked?.(picked.length > 0)
        }}
      />
      <button
        type="button"
        onClick={() => ref.current?.click()}
        className={`flex items-center gap-2 w-full border border-dashed rounded-lg px-3 py-3 text-sm transition-colors ${
          files.length > 0
            ? 'bg-gray-800 border-violet-500 text-gray-200'
            : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-violet-500 hover:text-gray-200'
        }`}
      >
        <Upload size={15} />
        {files.length > 0 ? files.join(', ') : label}
      </button>
    </div>
  )
}

function Checkbox({
  name, label, checked, onChange,
}: { name: string; label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-300">
      <input
        type="checkbox"
        name={name}
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        className="accent-violet-500 w-4 h-4"
      />
      {label}
    </label>
  )
}

// ─── Previews disposition ─────────────────────────────────────────────────────

/**
 * Miniature du canvas portrait 1080×1920.
 * Montre la zone logo (haut), la zone disponible (bas) et la mini-vidéo
 * à la taille et position calculées.
 */
function PortraitPreview({ size, posX, posY }: { size: string; posX: string; posY: string }) {
  // Constantes identiques au backend portrait.py
  const CANVAS_W    = 1080
  const CANVAS_H    = 1920
  const LOGO_H      = 960
  const MAX_MINI_H  = 760
  const MAX_VIDEO_W = 680
  const BORDER_W    = 3
  const EDGE_MARGIN = 20

  const previewH = 280
  const previewW = Math.round(previewH * CANVAS_W / CANVAS_H)  // ~157px
  const scale    = previewH / CANVAS_H

  const sizePct = parseInt(size) / 100
  const xPct    = parseInt(posX) / 100   // 0–1, centre H
  const yPct    = parseInt(posY) / 100   // 0–1, centre V

  const miniW  = Math.max(4, Math.round(MAX_VIDEO_W * sizePct * scale))
  const miniH  = Math.max(4, Math.round(MAX_MINI_H  * sizePct * scale))
  const bw     = Math.max(1, Math.round(BORDER_W * scale))
  const totalW = miniW + bw * 2
  const totalH = miniH + bw * 2
  const edgeM  = EDGE_MARGIN * scale

  // Miroir exact du backend _compute_position_pct
  const rawBx = previewW * xPct - totalW / 2
  const rawBy = previewH * yPct - totalH / 2
  const bx = Math.max(edgeM, Math.min(previewW - totalW - edgeM, rawBx))
  const by = Math.max(edgeM, Math.min(previewH - totalH - edgeM, rawBy))

  const logoLinePx = LOGO_H * scale

  return (
    <div
      className="relative bg-gray-950 rounded-lg overflow-hidden border border-gray-700 flex-shrink-0"
      style={{ width: previewW, height: previewH }}
      title="Position exacte · Taille approchée (dépend du ratio de la vidéo source)"
    >
      <div className="absolute inset-0" style={{ background: 'rgba(15,15,28,0.98)' }} />

      {/* Zone logo — repère discret */}
      <div
        className="absolute left-0 right-0 flex items-center justify-center"
        style={{ top: 0, height: logoLinePx, background: 'rgba(28,28,48,0.7)' }}
      >
        <span className="text-[7px] text-gray-700 font-mono uppercase tracking-widest">logo</span>
      </div>
      <div
        className="absolute left-0 right-0"
        style={{ top: logoLinePx, height: 0, borderTop: '1px dashed rgba(90,90,130,0.4)' }}
      />

      {/* Mini-vidéo — suit les sliders en temps réel */}
      <div
        className="absolute rounded flex items-center justify-center"
        style={{
          left: bx,
          top: by,
          width: totalW,
          height: totalH,
          background: 'rgba(124,58,237,0.82)',
          border: `${bw}px solid rgba(255,255,255,0.85)`,
          boxSizing: 'border-box',
          transition: 'left 0.08s linear, top 0.08s linear, width 0.12s ease, height 0.12s ease',
          zIndex: 2,
        }}
      >
        <span className="text-[7px] text-white font-bold leading-none">{size}%</span>
      </div>

      <div className="absolute bottom-1 left-0 right-0 flex justify-center" style={{ zIndex: 3 }}>
        <span className="text-[7px] text-gray-700 font-mono">aperçu</span>
      </div>
    </div>
  )
}

/**
 * Miniature du canvas wave 1080×1920.
 * Montre la waveform en bas et la mini-vidéo positionnée au-dessus.
 */
function WaveMiniPreview({ size, posX, posY }: { size: string; posX: string; posY: string }) {
  const CANVAS_W    = 1080
  const CANVAS_H    = 1920
  const WAVE_H      = 300
  const WAVE_Y      = CANVAS_H - WAVE_H - 80
  const MINI_W      = 680   // identique à MAX_VIDEO_W du pipeline portrait
  const MINI_H      = 760   // identique à MAX_MINI_H du pipeline portrait
  const EDGE_MARGIN = 20

  const previewH = 220
  const previewW = Math.round(previewH * CANVAS_W / CANVAS_H)
  const scale    = previewH / CANVAS_H

  const sizePct  = parseInt(size) / 100
  const scaledW  = Math.max(4, Math.round(MINI_W * sizePct * scale))
  const scaledH  = Math.max(4, Math.round(MINI_H * sizePct * scale))

  // Miroir exact de _compute_mini_position dans wave.py
  const edgeM = EDGE_MARGIN * scale
  const cx    = CANVAS_W * parseFloat(posX) / 100 * scale
  const cy    = CANVAS_H * parseFloat(posY) / 100 * scale
  const maxX  = previewW - scaledW - edgeM
  const maxY  = previewH - scaledH - edgeM
  const miniX = Math.max(edgeM, Math.min(cx - scaledW / 2, maxX))
  const miniY = Math.max(edgeM, Math.min(cy - scaledH / 2, maxY))

  return (
    <div
      className="relative bg-gray-950 rounded-lg overflow-hidden border border-gray-700 flex-shrink-0"
      style={{ width: previewW, height: previewH }}
      title="Aperçu de la disposition finale — taille approchée"
    >
      {/* Background */}
      <div className="absolute inset-0" style={{ background: 'rgba(15,15,25,0.95)' }} />

      {/* Waveform zone */}
      <div
        className="absolute left-0 right-0 flex items-center justify-center"
        style={{
          top: WAVE_Y * scale,
          height: WAVE_H * scale,
          background: 'rgba(6,182,212,0.15)',
          borderTop: '1px solid rgba(6,182,212,0.4)',
        }}
      >
        <span className="text-[7px] text-cyan-700 font-mono">waveform</span>
      </div>

      {/* Mini-vidéo */}
      <div
        className="absolute rounded flex items-center justify-center"
        style={{
          left: miniX,
          top: miniY,
          width: scaledW,
          height: scaledH,
          background: 'rgba(124,58,237,0.75)',
          border: '1px solid rgba(255,255,255,0.7)',
          transition: 'left 0.12s ease, top 0.12s ease, width 0.12s ease, height 0.12s ease',
        }}
      >
        <span className="text-[7px] text-white font-bold">{size}%</span>
      </div>

      <div className="absolute bottom-1 left-0 right-0 flex justify-center">
        <span className="text-[7px] text-gray-700 font-mono">aperçu</span>
      </div>
    </div>
  )
}

/** Grille 3×3 de sélection de position (pour portrait) */
const POSITION_GRID = [
  ['top-left',    'top',    'top-right'],
  ['left',        'center', 'right'],
  ['bottom-left', 'bottom', 'bottom-right'],
] as const

const POSITION_ARROWS: Record<string, string> = {
  'top-left': '↖', 'top': '↑', 'top-right': '↗',
  'left': '←',     'center': '◉', 'right': '→',
  'bottom-left': '↙', 'bottom': '↓', 'bottom-right': '↘',
}

function PositionPicker9({
  name, value, onChange,
}: { name: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <div className="grid grid-cols-3 gap-1" style={{ width: 96 }}>
        {POSITION_GRID.map(row =>
          row.map(pos => (
            <button
              key={pos}
              type="button"
              title={pos}
              onClick={() => onChange(pos)}
              className={`h-8 rounded text-sm font-mono transition-all ${
                value === pos
                  ? 'bg-violet-500 text-white shadow-md'
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-400'
              }`}
            >
              {POSITION_ARROWS[pos]}
            </button>
          ))
        )}
      </div>
      <input type="hidden" name={name} value={value} />
    </div>
  )
}

/** Sélecteur de position horizontal (gauche / centre / droite) */
function PositionPickerH({
  name, value, onChange,
}: { name: string; value: string; onChange: (v: string) => void }) {
  const opts = [
    { v: 'left',   label: '← Gauche' },
    { v: 'center', label: '◉ Centre' },
    { v: 'right',  label: 'Droite →' },
  ]
  return (
    <div className="flex gap-1">
      {opts.map(o => (
        <button
          key={o.v}
          type="button"
          onClick={() => onChange(o.v)}
          className={`flex-1 py-1.5 text-xs rounded transition-all ${
            value === o.v
              ? 'bg-violet-500 text-white'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-400'
          }`}
        >
          {o.label}
        </button>
      ))}
      <input type="hidden" name={name} value={value} />
    </div>
  )
}

// ─── Formulaires par style ────────────────────────────────────────────────────

function ExtractForm({ onReady }: { onReady: (ok: boolean) => void }) {
  const [file,  setFile]  = useState(false)
  const [start, setStart] = useState('')
  const [end,   setEnd]   = useState('')

  useEffect(() => {
    onReady(file && start.trim() !== '' && end.trim() !== '')
  }, [file, start, end, onReady])

  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo source <Required /></Label>
        <FileInput name="video_file" label="Choisir une vidéo" accept="video/*" onPicked={setFile} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Début (HH:MM:SS ou secondes) <Required /></Label>
          <Input name="start_time" placeholder="00:01:30" value={start} onChange={setStart} />
        </div>
        <div>
          <Label>Fin (HH:MM:SS ou secondes) <Required /></Label>
          <Input name="end_time" placeholder="00:02:45" value={end} onChange={setEnd} />
        </div>
      </div>
    </div>
  )
}

function CropForm({ onReady }: { onReady: (ok: boolean) => void }) {
  const fileRef  = useRef<HTMLInputElement>(null)
  const [file,   setFile]   = useState<File | null>(null)
  const [gpu,    setGpu]    = useState(true)
  const [crop,   setCrop]   = useState<CropValues>({ top: 0, bottom: 0, left: 0, right: 0 })

  useEffect(() => { onReady(file !== null) }, [file, onReady])

  const handleCropChange = useCallback((v: CropValues) => setCrop(v), [])

  const noCrop = crop.top === 0 && crop.bottom === 0 && crop.left === 0 && crop.right === 0

  return (
    <div className="space-y-4">
      {/* Upload vidéo */}
      <div>
        <Label>Vidéo source <Required /></Label>
        <input
          ref={fileRef}
          type="file"
          name="video_file"
          accept="video/*"
          className="hidden"
          onChange={e => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="flex items-center gap-2 w-full bg-gray-800 border border-dashed border-gray-600 hover:border-violet-500 rounded-lg px-3 py-3 text-sm text-gray-400 hover:text-gray-200 transition-colors"
        >
          <Upload size={15} />
          {file ? file.name : 'Choisir une vidéo'}
        </button>
      </div>

      {/* Sélecteur visuel — affiché dès qu'un fichier est choisi */}
      {file && (
        <div>
          <Label>
            Sélectionner la zone à garder{' '}
            <span className="text-gray-500 font-normal">(glisser les poignées blanches)</span>
          </Label>
          <CropSelector file={file} onChange={handleCropChange} />
        </div>
      )}

      {/* Champs numériques en lecture seule — affichage + valeurs envoyées */}
      {file && (
        <div className="grid grid-cols-2 gap-3">
          {(['top', 'bottom', 'left', 'right'] as const).map(side => (
            <div key={side} className="bg-gray-800 rounded-lg px-3 py-2 flex justify-between items-center">
              <span className="text-xs text-gray-400 capitalize">{
                side === 'top' ? '↑ Haut' : side === 'bottom' ? '↓ Bas' : side === 'left' ? '← Gauche' : '→ Droite'
              }</span>
              <span className="text-sm font-mono text-white">{crop[side]} px</span>
            </div>
          ))}
        </div>
      )}

      {/* Avertissement si aucun crop */}
      {file && noCrop && (
        <p className="text-xs text-yellow-500">
          Aucun crop sélectionné — la vidéo sera copiée sans modification.
        </p>
      )}

      {/* Hidden inputs pour le form */}
      <input type="hidden" name="crop_top"    value={crop.top} />
      <input type="hidden" name="crop_bottom" value={crop.bottom} />
      <input type="hidden" name="crop_left"   value={crop.left} />
      <input type="hidden" name="crop_right"  value={crop.right} />

      <Checkbox name="use_gpu" label="Encodage GPU (h264_nvenc) — fallback CPU auto" checked={gpu} onChange={setGpu} />
      <input type="hidden" name="use_gpu" value={gpu ? 'true' : 'false'} />
    </div>
  )
}

function MergeForm({ onReady }: { onReady: (ok: boolean) => void }) {
  const [slots,   setSlots]   = useState<{ id: number; filename: string | null }[]>([
    { id: 0, filename: null },
    { id: 1, filename: null },
  ])
  const [reverse, setReverse] = useState(false)
  const nextId = useRef(2)

  const filledCount = slots.filter(s => s.filename !== null).length
  useEffect(() => { onReady(filledCount >= 2) }, [filledCount, onReady])

  function addSlot() {
    setSlots(prev => [...prev, { id: nextId.current++, filename: null }])
  }

  function removeSlot(id: number) {
    setSlots(prev => prev.filter(s => s.id !== id))
  }

  function setFilename(id: number, name: string | null) {
    setSlots(prev => prev.map(s => s.id === id ? { ...s, filename: name } : s))
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Vidéos à fusionner <Required /></Label>
        {slots.map((slot, i) => (
          <div key={slot.id} className="flex items-center gap-2">
            <label className={`flex-1 flex items-center gap-2 border border-dashed rounded-lg px-3 py-2.5 text-sm cursor-pointer transition-colors ${
              slot.filename
                ? 'bg-gray-800 border-violet-500 text-gray-200'
                : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-violet-500 hover:text-gray-200'
            }`}>
              <Upload size={13} className="shrink-0" />
              <span className="truncate">{slot.filename ?? `Vidéo ${i + 1} — cliquer pour choisir`}</span>
              <input
                type="file"
                name="video_files"
                accept="video/*"
                className="hidden"
                onChange={e => setFilename(slot.id, e.target.files?.[0]?.name ?? null)}
              />
            </label>
            {slots.length > 2 && (
              <button
                type="button"
                onClick={() => removeSlot(slot.id)}
                className="text-gray-600 hover:text-red-400 transition-colors shrink-0"
                title="Retirer cette vidéo"
              >
                <X size={15} />
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addSlot}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-violet-300 border border-dashed border-gray-700 hover:border-violet-600 rounded-lg px-3 py-2 w-full transition-colors"
        >
          <Plus size={14} />
          Ajouter une vidéo
        </button>
      </div>
      <Checkbox name="reverse_order" label="Inverser l'ordre" checked={reverse} onChange={setReverse} />
      <input type="hidden" name="reverse_order" value={reverse ? 'true' : 'false'} />
    </div>
  )
}

function PodcastForm({ config, onReady, preselectedJobId }: {
  config: AppConfig; onReady: (ok: boolean) => void; preselectedJobId?: string | null
}) {
  const [bg,    setBg]    = useState(false)
  const [audio, setAudio] = useState(!!preselectedJobId)
  const [speed, setSpeed] = useState('1.0')

  useEffect(() => { onReady(bg && audio) }, [bg, audio, onReady])

  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div>
        <Label>Audio / Vidéo source <Required /></Label>
        <JobPicker
          name="audio_file"
          jobRefName="audio_job_ref"
          label="Choisir audio ou vidéo"
          accept="audio/*,video/*"
          onReady={setAudio}
          preselectedJobId={preselectedJobId}
        />
      </div>
      <div>
        <Label>Vitesse audio</Label>
        <Select name="speed_factor" value={speed} onChange={setSpeed}>
          {config.speed_factors.map(s => (
            <option key={s} value={String(s)}>{s === 1.0 ? 'Normale (1×)' : `Accélérée (${s}×)`}</option>
          ))}
        </Select>
      </div>
    </div>
  )
}

function WaveForm({ config, onReady, preselectedJobId }: {
  config: AppConfig; onReady: (ok: boolean) => void; preselectedJobId?: string | null
}) {
  const [audio,      setAudio]      = useState(!!preselectedJobId)
  const [mini,       setMini]       = useState(false)
  const [waveStyle,  setWaveStyle]  = useState('sine')
  const [videoMode,  setVideoMode]  = useState('audio')
  const [speed,      setSpeed]      = useState('1.0')
  const [color,      setColor]      = useState('white')
  const [miniSize,   setMiniSize]   = useState('80')
  const [miniPosX,   setMiniPosX]   = useState('50')
  const [miniPosY,   setMiniPosY]   = useState('40')

  const needsMini = videoMode === 'mini' || videoMode === 'hybrid'

  useEffect(() => {
    onReady(audio && (!needsMini || mini))
  }, [audio, mini, needsMini, onReady])

  return (
    <div className="space-y-4">
      <div>
        <Label>Audio / Vidéo source <Required /></Label>
        <JobPicker
          name="audio_file"
          jobRefName="audio_job_ref"
          label="Choisir audio ou vidéo"
          accept="audio/*,video/*"
          onReady={setAudio}
          preselectedJobId={preselectedJobId}
        />
      </div>
      <div>
        <Label>Vidéo de fond <span className="text-gray-500 font-normal">(optionnel — fond noir si absent)</span></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Label>Style waveform</Label>
          <Select name="wave_style" value={waveStyle} onChange={setWaveStyle}>
            {config.wave_styles.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Mode vidéo</Label>
          <Select name="video_mode" value={videoMode} onChange={setVideoMode}>
            <option value="audio">Audio seulement</option>
            <option value="mini">Mini-vidéo + waveform</option>
            <option value="hybrid">Hybride côte à côte</option>
          </Select>
        </div>
        <div>
          <Label>Vitesse</Label>
          <Select name="speed_factor" value={speed} onChange={setSpeed}>
            {config.speed_factors.map(s => (
              <option key={s} value={String(s)}>{s === 1.0 ? 'Normale (1×)' : `Accélérée (${s}×)`}</option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Couleur waveform</Label>
          <Select name="wave_color" value={color} onChange={setColor}>
            {['white', 'cyan', 'lime', 'orange', 'red', 'magenta', 'yellow'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>
        </div>
      </div>

      {needsMini && (
        <>
          <div>
            <Label>Vidéo du mini-overlay <Required /> <span className="text-gray-500 font-normal">(requise pour mode mini/hybrid)</span></Label>
            <FileInput name="content_video" label="Choisir la vidéo à afficher" accept="video/*" onPicked={setMini} />
          </div>

          {/* Taille + Position mini-vidéo */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-3">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Mini-vidéo overlay</p>
            <div className="flex flex-col md:flex-row md:items-start gap-4">
              {/* Contrôles */}
              <div className="flex-1 space-y-3">
                <div>
                  <Label>Taille ({miniSize}%)</Label>
                  <input
                    type="range" name="mini_size_percent" min="20" max="100" value={miniSize}
                    onChange={e => setMiniSize(e.target.value)}
                    className="w-full accent-violet-500"
                  />
                </div>
                <div>
                  <Label>Position horizontale ({miniPosX}%)</Label>
                  <input
                    type="range" name="mini_position_x" min="0" max="100" value={miniPosX}
                    onChange={e => setMiniPosX(e.target.value)}
                    className="w-full accent-violet-500"
                  />
                </div>
                <div>
                  <Label>Position verticale ({miniPosY}%)</Label>
                  <input
                    type="range" name="mini_position_y" min="0" max="100" value={miniPosY}
                    onChange={e => setMiniPosY(e.target.value)}
                    className="w-full accent-violet-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => { setMiniPosX('50'); setMiniPosY('40') }}
                  className="bg-violet-700 hover:bg-violet-600 text-white text-xs font-medium px-4 py-1.5 rounded-full transition-colors"
                >
                  Réinitialiser la position
                </button>
              </div>
              {/* Preview */}
              <div className="flex flex-col items-center gap-1 md:pt-1">
                <span className="text-[10px] text-gray-500 uppercase tracking-wide font-medium">Aperçu</span>
                <WaveMiniPreview size={miniSize} posX={miniPosX} posY={miniPosY} />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function PortraitForm({ onReady, preselectedJobId }: {
  onReady: (ok: boolean) => void; preselectedJobId?: string | null
}) {
  const [bg,          setBg]          = useState(false)
  const [content,     setContent]     = useState(!!preselectedJobId)
  const [audioOnly,   setAudioOnly]   = useState(false)
  const [borderColor, setBorderColor] = useState('white')
  const [useGpu,      setUseGpu]      = useState(true)
  const [size,        setSize]        = useState('90')
  const [posX,        setPosX]        = useState('50')   // % centre H, défaut centré
  const [posY,        setPosY]        = useState('75')   // % centre V, défaut zone mini-vidéo

  useEffect(() => { onReady(bg && content) }, [bg, content, onReady])

  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo de fond 1080×1920 <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div>
        <Label>Contenu à intégrer (vidéo ou audio) <Required /></Label>
        <JobPicker
          name="content_video"
          jobRefName="content_job_ref"
          label="Choisir vidéo ou audio"
          accept="audio/*,video/*"
          onReady={setContent}
          preselectedJobId={preselectedJobId}
        />
      </div>

      {/* Taille + Position mini-vidéo */}
      {!audioOnly && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-3">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Mini-vidéo</p>
          <div className="flex flex-col md:flex-row md:items-start gap-4">
            {/* Contrôles */}
            <div className="flex-1 space-y-3">
              <div>
                <Label>Taille ({size}%)</Label>
                <input
                  type="range" min="20" max="100"
                  name="portrait_size_percent"
                  value={size}
                  onChange={e => setSize(e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
              <div>
                <Label>Position horizontale ({posX}%)</Label>
                <input
                  type="range" min="0" max="100"
                  name="portrait_position_x"
                  value={posX}
                  onChange={e => setPosX(e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
              <div>
                <Label>Position verticale ({posY}%)</Label>
                <input
                  type="range" min="0" max="100"
                  name="portrait_position_y"
                  value={posY}
                  onChange={e => setPosY(e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
              <button
                type="button"
                onClick={() => { setPosX('50'); setPosY('75') }}
                className="inline-flex items-center gap-2 bg-violet-700 hover:bg-violet-600 text-white text-xs font-medium px-4 py-2 rounded-xl transition-colors"
              >
                Réinitialiser la position
              </button>
            </div>
            {/* Preview */}
            <div className="flex flex-col items-center gap-1 md:pt-1">
              <span className="text-[10px] text-gray-500 uppercase tracking-wide font-medium">Aperçu</span>
              <PortraitPreview size={size} posX={posX} posY={posY} />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Label>Couleur de bordure</Label>
          <Select name="border_color" value={borderColor} onChange={setBorderColor}>
            {['white', 'black', 'gold', 'silver', 'red', 'cyan'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>
        </div>
        <div className="sm:pt-6">
          <Checkbox
            name="use_gpu"
            label="Utiliser le GPU (h264_nvenc)"
            checked={useGpu}
            onChange={setUseGpu}
          />
        </div>
      </div>
      <Checkbox name="audio_only" label="Mode audio pur (pas de mini-vidéo)" checked={audioOnly} onChange={setAudioOnly} />
      <input type="hidden" name="audio_only" value={audioOnly ? 'true' : 'false'} />
      <input type="hidden" name="use_gpu" value={useGpu ? 'true' : 'false'} />
    </div>
  )
}

/**
 * Miniature du canvas landscape 1920×1080.
 * Miroir exact du pipeline landscape.py.
 */
function LandscapePreview({ size, posX, posY }: { size: string; posX: string; posY: string }) {
  const CANVAS_W    = 1920
  const CANVAS_H    = 1080
  const MAX_MINI_W  = 760
  const MAX_MINI_H  = 680
  const BORDER_W    = 3
  const EDGE_MARGIN = 20

  const previewW = 280
  const previewH = Math.round(previewW * CANVAS_H / CANVAS_W)  // ~158px
  const scale    = previewW / CANVAS_W

  const sizePct = parseInt(size) / 100
  const xPct    = parseInt(posX) / 100
  const yPct    = parseInt(posY) / 100

  const miniW  = Math.max(4, Math.round(MAX_MINI_W * sizePct * scale))
  const miniH  = Math.max(4, Math.round(MAX_MINI_H * sizePct * scale))
  const bw     = Math.max(1, Math.round(BORDER_W * scale))
  const totalW = miniW + bw * 2
  const totalH = miniH + bw * 2
  const edgeM  = EDGE_MARGIN * scale

  const rawBx = previewW * xPct - totalW / 2
  const rawBy = previewH * yPct - totalH / 2
  const bx = Math.max(edgeM, Math.min(previewW - totalW - edgeM, rawBx))
  const by = Math.max(edgeM, Math.min(previewH - totalH - edgeM, rawBy))

  return (
    <div
      className="relative bg-gray-950 rounded-lg overflow-hidden border border-gray-700 flex-shrink-0"
      style={{ width: previewW, height: previewH }}
      title="Position exacte · Taille approchée (dépend du ratio de la vidéo source)"
    >
      <div className="absolute inset-0" style={{ background: 'rgba(15,15,28,0.98)' }} />

      {/* Mini-vidéo */}
      <div
        className="absolute rounded flex items-center justify-center"
        style={{
          left: bx,
          top: by,
          width: totalW,
          height: totalH,
          background: 'rgba(124,58,237,0.82)',
          border: `${bw}px solid rgba(255,255,255,0.85)`,
          boxSizing: 'border-box',
          transition: 'left 0.08s linear, top 0.08s linear, width 0.12s ease, height 0.12s ease',
          zIndex: 2,
        }}
      >
        <span className="text-[7px] text-white font-bold leading-none">{size}%</span>
      </div>

      <div className="absolute bottom-1 left-0 right-0 flex justify-center" style={{ zIndex: 3 }}>
        <span className="text-[7px] text-gray-700 font-mono">aperçu</span>
      </div>
    </div>
  )
}

function LandscapeForm({ onReady, preselectedJobId }: {
  onReady: (ok: boolean) => void; preselectedJobId?: string | null
}) {
  const [bg,          setBg]          = useState(false)
  const [content,     setContent]     = useState(!!preselectedJobId)
  const [audioOnly,   setAudioOnly]   = useState(false)
  const [borderColor, setBorderColor] = useState('white')
  const [useGpu,      setUseGpu]      = useState(true)
  const [size,        setSize]        = useState('90')
  const [posX,        setPosX]        = useState('75')   // % centre H, défaut droite
  const [posY,        setPosY]        = useState('50')   // % centre V, défaut milieu vertical

  useEffect(() => { onReady(bg && content) }, [bg, content, onReady])

  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo de fond 1920×1080 <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div>
        <Label>Contenu à intégrer (vidéo ou audio) <Required /></Label>
        <JobPicker
          name="content_video"
          jobRefName="content_job_ref"
          label="Choisir vidéo ou audio"
          accept="audio/*,video/*"
          onReady={setContent}
          preselectedJobId={preselectedJobId}
        />
      </div>

      {/* Taille + Position mini-vidéo */}
      {!audioOnly && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-3">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Mini-vidéo</p>
          <div className="flex flex-col md:flex-row md:items-start gap-4">
            {/* Contrôles */}
            <div className="flex-1 space-y-3">
              <div>
                <Label>Taille ({size}%)</Label>
                <input
                  type="range" min="20" max="100"
                  name="landscape_size_percent"
                  value={size}
                  onChange={e => setSize(e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
              <div>
                <Label>Position horizontale ({posX}%)</Label>
                <input
                  type="range" min="0" max="100"
                  name="landscape_position_x"
                  value={posX}
                  onChange={e => setPosX(e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
              <div>
                <Label>Position verticale ({posY}%)</Label>
                <input
                  type="range" min="0" max="100"
                  name="landscape_position_y"
                  value={posY}
                  onChange={e => setPosY(e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
              <button
                type="button"
                onClick={() => { setPosX('75'); setPosY('50') }}
                className="inline-flex items-center gap-2 bg-violet-700 hover:bg-violet-600 text-white text-xs font-medium px-4 py-2 rounded-xl transition-colors"
              >
                Réinitialiser la position
              </button>
            </div>
            {/* Preview */}
            <div className="flex flex-col items-center gap-1 md:pt-1">
              <span className="text-[10px] text-gray-500 uppercase tracking-wide font-medium">Aperçu</span>
              <LandscapePreview size={size} posX={posX} posY={posY} />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Label>Couleur de bordure</Label>
          <Select name="border_color" value={borderColor} onChange={setBorderColor}>
            {['white', 'black', 'gold', 'silver', 'red', 'cyan'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>
        </div>
        <div className="sm:pt-6">
          <Checkbox
            name="use_gpu"
            label="Utiliser le GPU (h264_nvenc)"
            checked={useGpu}
            onChange={setUseGpu}
          />
        </div>
      </div>
      <Checkbox name="audio_only" label="Mode audio pur (pas de mini-vidéo)" checked={audioOnly} onChange={setAudioOnly} />
      <input type="hidden" name="audio_only" value={audioOnly ? 'true' : 'false'} />
      <input type="hidden" name="use_gpu" value={useGpu ? 'true' : 'false'} />
    </div>
  )
}

// ─── Page principale ──────────────────────────────────────────────────────────

// ─── Composants débat ─────────────────────────────────────────────────────────

/** Diagramme visuel de la disposition des speakers sur le fond */
/**
 * Preview dynamique pour les formulaires débat.
 * Canvas 1920×1080 → miniature 260×146px.
 *
 * Double   : blocs clampés aux bords du canvas, jamais de débordement.
 * Diagonal : positions distribuées dynamiquement le long de la diagonale
 *            pour éviter les chevauchements, tout en restant dans les bords.
 */
function DebateSizePreview({ type, size }: { type: 'single' | 'double' | 'diagonal'; size: string }) {
  const OUT_W = 1920
  const OUT_H = 1080

  const previewW = 260
  const previewH = Math.round(previewW * OUT_H / OUT_W)  // 146px
  const scale    = previewW / OUT_W

  const sizePct = parseInt(size) / 100
  const w = OUT_W * sizePct * scale
  const h = OUT_H * sizePct * scale
  // Coordonnée depuis un % backend → pixels preview
  const pxPos = (pctX: number, pctY: number) => ({
    x: OUT_W * pctX / 100 * scale,
    y: OUT_H * pctY / 100 * scale,
  })

  // ── Single ── centré (identique à composite_single.py)
  const single = pxPos((100 - sizePct * 100) / 2, (100 - sizePct * 100) / 2)

  // ── Double ──
  // Gauche : ancré coin haut-gauche → grandit droite/bas
  const dL = pxPos(2.6, 4.6)
  // Droit  : ancré coin bas-droit → grandit gauche/haut (miroir exact du backend)
  const RIGHT_X_END_PCT = 97.4
  const RIGHT_Y_END_PCT = 95.4
  const dR = {
    x: Math.max(0, OUT_W * RIGHT_X_END_PCT / 100 * scale - w),
    y: Math.max(0, OUT_H * RIGHT_Y_END_PCT / 100 * scale - h),
  }

  // ── Diagonal ── positions fixes exactes du backend (composite_diagonal.py)
  // Les blocs peuvent se chevaucher à taille élevée, comme dans la vidéo réelle.
  const diagG = pxPos(5,  8 )
  const diagC = pxPos(36, 36)
  const diagD = pxPos(67, 64)

  const transition = 'left 0.12s ease, top 0.12s ease, width 0.12s ease, height 0.12s ease'

  const block = (pos: { x: number; y: number }, bg: string, border: string, label: string, z = 1) => (
    <div style={{
      position: 'absolute',
      left: pos.x, top: pos.y, width: w, height: h,
      background: bg, border: `1px solid ${border}`,
      borderRadius: 3, zIndex: z, transition,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <span className="text-[8px] text-white font-bold">{label}</span>
    </div>
  )

  return (
    <div
      className="relative bg-gray-800 rounded-lg overflow-hidden border border-gray-700 flex-shrink-0"
      style={{ width: previewW, height: previewH }}
      title="Aperçu de la disposition — mise à jour en temps réel"
    >
      <span className="absolute inset-0 flex items-center justify-center text-[9px] text-gray-600 font-mono uppercase tracking-widest">
        fond
      </span>

      {type === 'single' && block(single,  'rgba(139,92,246,0.82)', 'rgba(167,139,250,0.9)', 'speaker', 1)}

      {type === 'double'   && block(dL,    'rgba(59,130,246,0.82)', 'rgba(96,165,250,0.9)',  'G',       1)}
      {type === 'double'   && block(dR,    'rgba(245,158,11,0.82)', 'rgba(251,191,36,0.9)',  'D',       2)}

      {type === 'diagonal' && block(diagG, 'rgba(59,130,246,0.82)', 'rgba(96,165,250,0.9)',  'G',       1)}
      {type === 'diagonal' && block(diagC, 'rgba(16,185,129,0.82)', 'rgba(52,211,153,0.9)',  'C',       2)}
      {type === 'diagonal' && block(diagD, 'rgba(245,158,11,0.82)', 'rgba(251,191,36,0.9)',  'D',       3)}

      <div className="absolute bottom-1 right-1.5" style={{ zIndex: 10 }}>
        <span className="text-[8px] text-gray-500 font-mono">{size}%</span>
      </div>
    </div>
  )
}

function LayoutPreview({ type }: { type: 'single' | 'double' | 'diagonal' }) {
  return (
    <div className="relative bg-gray-800 rounded-lg overflow-hidden border border-gray-700"
      style={{ width: 160, height: 90 }}>
      {/* Background label */}
      <span className="absolute inset-0 flex items-center justify-center text-[9px] text-gray-600 font-mono uppercase tracking-widest">
        fond
      </span>
      {type === 'single' && (
        <div className="absolute bg-violet-500/70 border border-violet-400 rounded text-[8px] text-white flex items-center justify-center font-bold"
          style={{ left: '22%', top: '22%', width: '55%', height: '55%' }}>
          speaker
        </div>
      )}
      {(type === 'double' || type === 'diagonal') && (
        <div className="absolute bg-blue-500/70 border border-blue-400 rounded text-[8px] text-white flex items-center justify-center font-bold"
          style={{ left: '5%', top: '8%', width: '33%', height: '33%' }}>
          gauche
        </div>
      )}
      {type === 'diagonal' && (
        <div className="absolute bg-emerald-500/70 border border-emerald-400 rounded text-[8px] text-white flex items-center justify-center font-bold"
          style={{ left: '34%', top: '34%', width: '30%', height: '30%' }}>
          centre
        </div>
      )}
      {(type === 'double' || type === 'diagonal') && (
        <div className="absolute bg-amber-500/70 border border-amber-400 rounded text-[8px] text-white flex items-center justify-center font-bold"
          style={{ left: type === 'double' ? '62%' : '63%', top: type === 'double' ? '58%' : '60%', width: '33%', height: '33%' }}>
          droite
        </div>
      )}
    </div>
  )
}

const QUALITY_OPTIONS = [
  { label: 'Rapide (CRF 28)', value: '28' },
  { label: 'Bonne (CRF 23)',  value: '23' },
  { label: 'Haute (CRF 18)',  value: '18' },
]

function DebateSingleForm({ onReady }: { onReady: (ok: boolean) => void }) {
  const [bg,   setBg]   = useState(false)
  const [spk,  setSpk]  = useState(false)
  const [size, setSize] = useState('55')
  const [crf,  setCrf]  = useState('23')

  useEffect(() => { onReady(bg && spk) }, [bg, spk, onReady])

  return (
    <div className="space-y-4">
      <div className="text-xs text-gray-400 space-y-1">
        <p>• 1 speaker centré sur le fond</p>
        <p>• Durée = durée du speaker • Audio extrait du speaker</p>
      </div>
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div>
        <Label>Vidéo du speaker <Required /></Label>
        <FileInput name="speaker_left" label="Choisir la vidéo du speaker" accept="video/*" onPicked={setSpk} />
      </div>
      <div className="flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-1 space-y-3">
          <div>
            <Label>Taille speaker ({size}%)</Label>
            <input type="range" name="size_percent" min="30" max="70" value={size}
              onChange={e => setSize(e.target.value)}
              className="w-full accent-violet-500" />
          </div>
          <div>
            <Label>Qualité</Label>
            <Select name="quality_crf" value={crf} onChange={setCrf}>
              {QUALITY_OPTIONS.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
            </Select>
          </div>
        </div>
        <div className="flex flex-col items-center gap-1 md:pb-0.5">
          <span className="text-[10px] text-gray-500 uppercase tracking-wide font-medium">Aperçu</span>
          <DebateSizePreview type="single" size={size} />
        </div>
      </div>
    </div>
  )
}

function DebateDoubleForm({ onReady }: { onReady: (ok: boolean) => void }) {
  const [bg,    setBg]    = useState(false)
  const [left,  setLeft]  = useState(false)
  const [right, setRight] = useState(false)
  const [size,  setSize]  = useState('35')
  const [crf,   setCrf]   = useState('23')

  useEffect(() => { onReady(bg && left && right) }, [bg, left, right, onReady])

  return (
    <div className="space-y-4">
      <div className="text-xs text-gray-400 space-y-1">
        <p>• <span className="text-blue-400 font-medium">Gauche</span> joue en 1er, droite figée • <span className="text-amber-400 font-medium">Droite</span> joue en 2ème, gauche figée</p>
        <p>• Les deux toujours visibles • Durée = gauche + droite</p>
      </div>
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Label><span className="text-blue-400">■</span> Speaker gauche (1er) <Required /></Label>
          <FileInput name="speaker_left" label="Vidéo gauche" accept="video/*" onPicked={setLeft} />
        </div>
        <div>
          <Label><span className="text-amber-400">■</span> Speaker droite (2ème) <Required /></Label>
          <FileInput name="speaker_right" label="Vidéo droite" accept="video/*" onPicked={setRight} />
        </div>
      </div>
      <div className="flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-1 space-y-3">
          <div>
            <Label>Taille speakers ({size}%)</Label>
            <input type="range" name="size_percent" min="20" max="50" value={size}
              onChange={e => setSize(e.target.value)}
              className="w-full accent-violet-500" />
          </div>
          <div>
            <Label>Qualité</Label>
            <Select name="quality_crf" value={crf} onChange={setCrf}>
              {QUALITY_OPTIONS.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
            </Select>
          </div>
        </div>
        <div className="flex flex-col items-center gap-1 md:pb-0.5">
          <span className="text-[10px] text-gray-500 uppercase tracking-wide font-medium">Aperçu</span>
          <DebateSizePreview type="double" size={size} />
        </div>
      </div>
    </div>
  )
}

function DebateDiagonalForm({ onReady }: { onReady: (ok: boolean) => void }) {
  const [bg,     setBg]     = useState(false)
  const [left,   setLeft]   = useState(false)
  const [center, setCenter] = useState(false)
  const [right,  setRight]  = useState(false)
  const [size,   setSize]   = useState('28')
  const [crf,    setCrf]    = useState('23')

  useEffect(() => { onReady(bg && left && center && right) }, [bg, left, center, right, onReady])

  return (
    <div className="space-y-4">
      <div className="text-xs text-gray-400 space-y-1">
        <p>• <span className="text-blue-400 font-medium">Gauche</span> 1er · <span className="text-emerald-400 font-medium">Centre</span> 2ème · <span className="text-amber-400 font-medium">Droite</span> 3ème — tous toujours visibles (freeze)</p>
        <p>• Durée = G + C + D</p>
      </div>
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <Label><span className="text-blue-400">■</span> Gauche (1er) <Required /></Label>
          <FileInput name="speaker_left" label="Vidéo gauche" accept="video/*" onPicked={setLeft} />
        </div>
        <div>
          <Label><span className="text-emerald-400">■</span> Centre (2ème) <Required /></Label>
          <FileInput name="speaker_center" label="Vidéo centre" accept="video/*" onPicked={setCenter} />
        </div>
        <div>
          <Label><span className="text-amber-400">■</span> Droite (3ème) <Required /></Label>
          <FileInput name="speaker_right" label="Vidéo droite" accept="video/*" onPicked={setRight} />
        </div>
      </div>
      <div className="flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-1 space-y-3">
          <div>
            <Label>Taille speakers ({size}%)</Label>
            <input type="range" name="size_percent" min="15" max="35" value={size}
              onChange={e => setSize(e.target.value)}
              className="w-full accent-violet-500" />
          </div>
          <div>
            <Label>Qualité</Label>
            <Select name="quality_crf" value={crf} onChange={setCrf}>
              {QUALITY_OPTIONS.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
            </Select>
          </div>
        </div>
        <div className="flex flex-col items-center gap-1 md:pb-0.5">
          <span className="text-[10px] text-gray-500 uppercase tracking-wide font-medium">Aperçu</span>
          <DebateSizePreview type="diagonal" size={size} />
        </div>
      </div>
    </div>
  )
}

// ─── Icônes + groupes de styles ────────────────────────────────────────────────

const STYLE_ICONS: Record<string, string> = {
  extract:          '✂️',
  crop:             '🖼️',
  merge:            '🔗',
  podcast:          '🎙️',
  landscape:        '🖥️',
  wave:             '🌊',
  portrait:         '📱',
  debate_single:    '🎤',
  debate_double:    '👥',
  debate_diagonal:  '🎭',
}

export default function NewJob() {
  const navigate  = useNavigate()
  const location  = useLocation()

  // État passé depuis JobDetail via navigate("/", { state: { style, jobId } })
  const navState = location.state as { style?: string; jobId?: string } | null

  const [config,  setConfig]  = useState<AppConfig | null>(null)
  const [style,   setStyle]   = useState(navState?.style ?? 'merge')
  const [title,   setTitle]   = useState('')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [canSubmit, setCanSubmit] = useState(false)

  // YouTube section
  const [ytOpen,        setYtOpen]        = useState(false)
  const [ytEnabled,     setYtEnabled]     = useState(false)
  const [ytAuth,        setYtAuth]        = useState<boolean | null>(null)
  const [ytPlaylists,   setYtPlaylists]   = useState<YoutubePlaylist[]>([])
  const [ytCategories,  setYtCategories]  = useState<YoutubeCategory[]>([])
  const [ytLanguages,   setYtLanguages]   = useState<YoutubeLanguage[]>([])
  const [ytTitle,       setYtTitle]       = useState('')
  const [ytDescription, setYtDescription] = useState('')
  const [ytTags,        setYtTags]        = useState('')
  const [ytCategory,    setYtCategory]    = useState('25')
  const [ytPrivacy,     setYtPrivacy]     = useState('private')
  const [ytLanguage,    setYtLanguage]    = useState('fr')
  const [ytLicense,     setYtLicense]     = useState('youtube')
  const [ytEmbeddable,  setYtEmbeddable]  = useState(true)
  const [ytPlaylistId,  setYtPlaylistId]  = useState('')

  // Job pré-sélectionné depuis le bouton "Utiliser dans..." de JobDetail
  const preselectedJobId = navState?.jobId ?? null

  const onReady = useCallback((ok: boolean) => setCanSubmit(ok), [])

  useEffect(() => {
    fetchConfig().then(setConfig).catch(() => setError('Backend inaccessible'))
    // Charger les métadonnées YouTube et vérifier l'auth dès le début
    fetchYoutubeMeta().then(m => { setYtCategories(m.categories); setYtLanguages(m.languages) })
    getYoutubeAuthStatus().then(s => {
      setYtAuth(s.authenticated)
      if (s.authenticated) {
        getYoutubePlaylists().then(setYtPlaylists).catch(() => {})
      }
    }).catch(() => {})
  }, [])

  // Reset validité quand on change de style
  useEffect(() => {
    setCanSubmit(!!preselectedJobId)
  }, [style, preselectedJobId])

  // Pré-remplir le titre YouTube avec le titre du job (si non encore modifié)
  useEffect(() => {
    setYtTitle(prev => prev || title)
  }, [title])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const fd = new FormData(e.currentTarget)
      fd.set('style', style)
      if (title) fd.set('title', title)
      // Champs YouTube
      fd.set('yt_auto_upload',  ytEnabled ? 'true' : 'false')
      fd.set('yt_title',        ytTitle || title || '')
      fd.set('yt_description',  ytDescription)
      fd.set('yt_tags',         ytTags)
      fd.set('yt_category',     ytCategory)
      fd.set('yt_privacy',      ytPrivacy)
      fd.set('yt_language',     ytLanguage)
      fd.set('yt_license',      ytLicense)
      fd.set('yt_embeddable',   ytEmbeddable ? 'true' : 'false')
      fd.set('yt_playlist_id',  ytPlaylistId)
      const job = await createJob(fd)
      navigate(`/jobs/${job.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
      setLoading(false)
    }
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        {error ? (
          <div className="text-red-400 text-center">
            <p className="font-medium">Connexion impossible au backend</p>
            <p className="text-sm mt-1">Assurez-vous que start_backend.bat est lancé (port 8001)</p>
          </div>
        ) : (
          <div className="animate-pulse">Chargement...</div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Nouveau job</h1>
        <p className="text-gray-400 text-sm mt-1">Sélectionnez un type de traitement et configurez vos fichiers</p>
      </div>

      {/* Sélection du style — groupé par catégorie */}
      <div className="space-y-3">
        {[
          { label: 'Préparation', keys: ['merge'], gridClass: 'grid grid-cols-1 gap-2' },
          { label: 'Génération', keys: ['podcast', 'wave', 'portrait', 'landscape'], gridClass: 'grid grid-cols-2 gap-2' },
          { label: 'Débat / Composite', keys: ['debate_single', 'debate_double', 'debate_diagonal'], gridClass: 'grid grid-cols-1 sm:grid-cols-3 gap-2' },
        ].map(group => (
          <div key={group.label}>
            <p className="text-xs text-gray-600 font-medium uppercase tracking-wider mb-2">{group.label}</p>
            <div className={group.gridClass}>
              {group.keys.map(key => {
                const desc = config.job_styles[key] ?? ''
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setStyle(key)}
                    className={`text-left p-3 rounded-xl border transition-all ${
                      style === key
                        ? 'border-violet-500 bg-violet-500/10 text-white'
                        : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-xl mb-1">{STYLE_ICONS[key] ?? '🎬'}</div>
                    <div className="text-xs font-medium">{desc.split('—')[0].trim()}</div>
                    {desc.includes('—') && (
                      <div className="text-[10px] text-gray-600 mt-0.5">{desc.split('—')[1].trim()}</div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Formulaire */}
      <form onSubmit={handleSubmit} className="bg-gray-900 rounded-2xl p-4 sm:p-6 space-y-5">
        <div>
          <Label>Titre du job (optionnel)</Label>
          <Input name="title" placeholder="Ex: Clip conférence 5 min" value={title} onChange={setTitle} />
        </div>

        {/* ── Section YouTube ────────────────────────────────────────────────── */}
        <div className="border border-gray-800 rounded-xl overflow-hidden">
          {/* Header toggle */}
          <button
            type="button"
            onClick={() => setYtOpen(v => !v)}
            className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/60 hover:bg-gray-800 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Youtube size={15} className="text-red-400" />
              <span className="text-sm font-medium text-gray-200">Publication YouTube</span>
              {ytEnabled && (
                <span className="text-[10px] bg-red-600/30 text-red-300 border border-red-600/30 rounded-full px-2 py-0.5">
                  Auto-upload activé
                </span>
              )}
              {ytAuth === false && (
                <span className="text-[10px] text-gray-500">(non connecté)</span>
              )}
            </div>
            {ytOpen ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
          </button>

          {ytOpen && (
            <div className="px-4 py-4 space-y-4 border-t border-gray-800">
              {ytAuth === false ? (
                <p className="text-xs text-gray-500 bg-gray-800/50 rounded-lg px-3 py-2">
                  Connectez votre compte YouTube depuis la page d'un job terminé, puis revenez ici.
                </p>
              ) : (
                <>
                  {/* Toggle auto-upload */}
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={ytEnabled}
                      onChange={e => setYtEnabled(e.target.checked)}
                      className="w-4 h-4 accent-red-500"
                    />
                    <span className="text-sm text-gray-200 font-medium">
                      Uploader automatiquement sur YouTube à la fin du job
                    </span>
                  </label>

                  {ytEnabled && (
                    <div className="space-y-3 text-xs">
                      {/* Titre YouTube */}
                      <div>
                        <label className="block text-gray-400 mb-1">
                          Titre YouTube
                          <span className="text-gray-600 ml-1">(pré-rempli avec le titre du job)</span>
                        </label>
                        <input
                          type="text"
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                          placeholder="Titre de la vidéo sur YouTube"
                          value={ytTitle}
                          onChange={e => setYtTitle(e.target.value)}
                        />
                      </div>

                      {/* Description */}
                      <div>
                        <label className="block text-gray-400 mb-1">Description</label>
                        <textarea
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs min-h-[80px] text-gray-200 resize-y"
                          placeholder="Description de la vidéo..."
                          value={ytDescription}
                          onChange={e => setYtDescription(e.target.value)}
                        />
                      </div>

                      {/* Tags */}
                      <div>
                        <label className="block text-gray-400 mb-1">Tags <span className="text-gray-600">(séparés par virgule)</span></label>
                        <input
                          type="text"
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                          placeholder="politique,actualité,france"
                          value={ytTags}
                          onChange={e => setYtTags(e.target.value)}
                        />
                      </div>

                      {/* Row: catégorie + confidentialité */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-gray-400 mb-1">Catégorie</label>
                          <select
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                            value={ytCategory}
                            onChange={e => setYtCategory(e.target.value)}
                          >
                            {ytCategories.length > 0
                              ? ytCategories.map(c => <option key={c.id} value={c.id}>{c.label}</option>)
                              : <option value="25">News &amp; Politics</option>
                            }
                          </select>
                        </div>
                        <div>
                          <label className="block text-gray-400 mb-1">
                            Confidentialité{' '}
                            <span className="text-yellow-500/80">⚠ Privé par défaut</span>
                          </label>
                          <select
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                            value={ytPrivacy}
                            onChange={e => setYtPrivacy(e.target.value)}
                          >
                            <option value="private">Privé</option>
                            <option value="unlisted">Non répertorié</option>
                            <option value="public">Public</option>
                          </select>
                        </div>
                      </div>

                      {/* Row: langue + licence */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-gray-400 mb-1">Langue de la vidéo</label>
                          <select
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                            value={ytLanguage}
                            onChange={e => setYtLanguage(e.target.value)}
                          >
                            {ytLanguages.length > 0
                              ? ytLanguages.map(l => <option key={l.code} value={l.code}>{l.label}</option>)
                              : <option value="fr">Français</option>
                            }
                          </select>
                        </div>
                        <div>
                          <label className="block text-gray-400 mb-1">Licence</label>
                          <select
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                            value={ytLicense}
                            onChange={e => setYtLicense(e.target.value)}
                          >
                            <option value="youtube">Licence YouTube standard</option>
                            <option value="creativeCommon">Creative Commons (CC BY)</option>
                          </select>
                        </div>
                      </div>

                      {/* Row: playlist + embedding */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-end">
                        <div>
                          <label className="block text-gray-400 mb-1">Playlist</label>
                          <select
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                            value={ytPlaylistId}
                            onChange={e => setYtPlaylistId(e.target.value)}
                          >
                            <option value="">(aucune)</option>
                            {ytPlaylists.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
                          </select>
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer pb-1">
                          <input
                            type="checkbox"
                            checked={ytEmbeddable}
                            onChange={e => setYtEmbeddable(e.target.checked)}
                            className="w-4 h-4 accent-red-500"
                          />
                          <span className="text-gray-300">Autoriser l'intégration</span>
                        </label>
                      </div>

                      <p className="text-[10px] text-gray-600 bg-gray-800/50 rounded px-2 py-1.5 leading-relaxed">
                        La vidéo sera uploadée en <strong className="text-gray-400">Privé</strong> par défaut.
                        Passez-la en Public depuis YouTube Studio après vérification.
                        Le titre utilisé sera celui du job.
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        <hr className="border-gray-800" />

        {style === 'extract'          && <ExtractForm        onReady={onReady} />}
        {style === 'crop'             && <CropForm           onReady={onReady} />}
        {style === 'merge'            && <MergeForm          onReady={onReady} />}
        {style === 'podcast'          && <PodcastForm        config={config} onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'wave'             && <WaveForm           config={config} onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'portrait'         && <PortraitForm       onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'landscape'        && <LandscapeForm      onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'debate_single'    && <DebateSingleForm   onReady={onReady} />}
        {style === 'debate_double'    && <DebateDoubleForm   onReady={onReady} />}
        {style === 'debate_diagonal'  && <DebateDiagonalForm onReady={onReady} />}

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="flex items-center justify-center gap-2 w-full sm:w-auto bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium px-6 py-3 sm:py-2.5 rounded-xl transition-colors"
          >
            <Play size={16} />
            {loading ? 'Lancement...' : 'Lancer le job'}
          </button>
          {!canSubmit && !loading && (
            <p className="text-xs text-gray-500">
              Sélectionnez les fichiers requis <span className="text-red-400">*</span> pour continuer
            </p>
          )}
        </div>
      </form>
    </div>
  )
}
