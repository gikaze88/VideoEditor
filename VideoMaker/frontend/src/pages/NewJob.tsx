import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Upload, Play } from 'lucide-react'
import { createJob, fetchConfig, type AppConfig } from '../api'
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
  const [files,   setFiles]   = useState(false)
  const [reverse, setReverse] = useState(false)

  useEffect(() => { onReady(files) }, [files, onReady])

  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéos à fusionner <Required /></Label>
        <FileInput name="video_files" label="Choisir plusieurs vidéos" accept="video/*" multiple onPicked={setFiles} />
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
      <div className="grid grid-cols-2 gap-4">
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
        <div>
          <Label>Vidéo du mini-overlay <Required /> <span className="text-gray-500 font-normal">(requise pour mode mini/hybrid)</span></Label>
          <FileInput name="content_video" label="Choisir la vidéo à afficher" accept="video/*" onPicked={setMini} />
        </div>
      )}
    </div>
  )
}

function PortraitForm({ onReady, preselectedJobId }: {
  onReady: (ok: boolean) => void; preselectedJobId?: string | null
}) {
  const [bg,           setBg]           = useState(false)
  const [content,      setContent]      = useState(!!preselectedJobId)
  const [audioOnly,    setAudioOnly]    = useState(false)
  const [borderColor,  setBorderColor]  = useState('white')
  const [useGpu,       setUseGpu]       = useState(true)

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
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Couleur de bordure</Label>
          <Select name="border_color" value={borderColor} onChange={setBorderColor}>
            {['white', 'black', 'gold', 'silver', 'red', 'cyan'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>
        </div>
        <div className="pt-6">
          <Checkbox
            name="use_gpu"
            label="Utiliser le GPU (h264_nvenc) si disponible"
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
      <div className="flex items-start gap-6">
        <div>
          <p className="text-xs text-gray-500 mb-1.5 font-medium">Disposition</p>
          <LayoutPreview type="single" />
        </div>
        <div className="text-xs text-gray-400 space-y-1 pt-6">
          <p>• 1 speaker centré sur le fond</p>
          <p>• Durée = durée du speaker</p>
          <p>• Audio extrait du speaker</p>
        </div>
      </div>
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div>
        <Label>Vidéo du speaker <Required /></Label>
        <FileInput name="speaker_left" label="Choisir la vidéo du speaker" accept="video/*" onPicked={setSpk} />
      </div>
      <div className="grid grid-cols-2 gap-4">
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
      <div className="flex items-start gap-6">
        <div>
          <p className="text-xs text-gray-500 mb-1.5 font-medium">Disposition</p>
          <LayoutPreview type="double" />
        </div>
        <div className="text-xs text-gray-400 space-y-1 pt-6">
          <p>• Gauche joue en 1er, droite figée</p>
          <p>• Droite joue en 2ème, gauche figée</p>
          <p>• Les deux toujours visibles</p>
          <p>• Durée = gauche + droite</p>
        </div>
      </div>
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label><span className="text-blue-400">■</span> Speaker gauche (1er) <Required /></Label>
          <FileInput name="speaker_left" label="Vidéo gauche" accept="video/*" onPicked={setLeft} />
        </div>
        <div>
          <Label><span className="text-amber-400">■</span> Speaker droite (2ème) <Required /></Label>
          <FileInput name="speaker_right" label="Vidéo droite" accept="video/*" onPicked={setRight} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
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
      <div className="flex items-start gap-6">
        <div>
          <p className="text-xs text-gray-500 mb-1.5 font-medium">Disposition</p>
          <LayoutPreview type="diagonal" />
        </div>
        <div className="text-xs text-gray-400 space-y-1 pt-4">
          <p>• Gauche joue en 1er</p>
          <p>• Centre joue en 2ème</p>
          <p>• Droite joue en 3ème</p>
          <p>• Les 3 toujours visibles (freeze)</p>
          <p>• Durée = G + C + D</p>
        </div>
      </div>
      <div>
        <Label>Vidéo de fond <Required /></Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" onPicked={setBg} />
      </div>
      <div className="grid grid-cols-3 gap-3">
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
      <div className="grid grid-cols-2 gap-4">
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
    </div>
  )
}

// ─── Icônes + groupes de styles ────────────────────────────────────────────────

const STYLE_ICONS: Record<string, string> = {
  extract:          '✂️',
  crop:             '🖼️',
  merge:            '🔗',
  podcast:          '🎙️',
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
  const [style,   setStyle]   = useState(navState?.style ?? 'extract')
  const [title,   setTitle]   = useState('')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [canSubmit, setCanSubmit] = useState(false)

  // Job pré-sélectionné depuis le bouton "Utiliser dans..." de JobDetail
  const preselectedJobId = navState?.jobId ?? null

  const onReady = useCallback((ok: boolean) => setCanSubmit(ok), [])

  useEffect(() => {
    fetchConfig().then(setConfig).catch(() => setError('Backend inaccessible'))
  }, [])

  // Reset validité quand on change de style
  useEffect(() => {
    setCanSubmit(!!preselectedJobId)
  }, [style, preselectedJobId])

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const fd = new FormData(e.currentTarget)
      fd.set('style', style)
      if (title) fd.set('title', title)
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
          { label: 'Préparation', keys: ['extract', 'crop', 'merge'] },
          { label: 'Génération', keys: ['podcast', 'wave', 'portrait'] },
          { label: 'Débat / Composite', keys: ['debate_single', 'debate_double', 'debate_diagonal'] },
        ].map(group => (
          <div key={group.label}>
            <p className="text-xs text-gray-600 font-medium uppercase tracking-wider mb-2">{group.label}</p>
            <div className="grid grid-cols-3 gap-2">
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
      <form onSubmit={handleSubmit} className="bg-gray-900 rounded-2xl p-6 space-y-5">
        <div>
          <Label>Titre du job (optionnel)</Label>
          <Input name="title" placeholder="Ex: Clip conférence 5 min" value={title} onChange={setTitle} />
        </div>

        <hr className="border-gray-800" />

        {style === 'extract'          && <ExtractForm        onReady={onReady} />}
        {style === 'crop'             && <CropForm           onReady={onReady} />}
        {style === 'merge'            && <MergeForm          onReady={onReady} />}
        {style === 'podcast'          && <PodcastForm        config={config} onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'wave'             && <WaveForm           config={config} onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'portrait'         && <PortraitForm       onReady={onReady} preselectedJobId={preselectedJobId} />}
        {style === 'debate_single'    && <DebateSingleForm   onReady={onReady} />}
        {style === 'debate_double'    && <DebateDoubleForm   onReady={onReady} />}
        {style === 'debate_diagonal'  && <DebateDiagonalForm onReady={onReady} />}

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium px-6 py-2.5 rounded-xl transition-colors"
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
