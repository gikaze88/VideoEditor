import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Play } from 'lucide-react'
import { createJob, fetchConfig, type AppConfig } from '../api'
import CropSelector, { type CropValues } from '../CropSelector'

// ─── Composants utilitaires ──────────────────────────────────────────────────

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-gray-300 mb-1">{children}</label>
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
  name, label, accept, multiple = false,
}: { name: string; label: string; accept?: string; multiple?: boolean }) {
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
        }}
      />
      <button
        type="button"
        onClick={() => ref.current?.click()}
        className="flex items-center gap-2 w-full bg-gray-800 border border-dashed border-gray-600 hover:border-violet-500 rounded-lg px-3 py-3 text-sm text-gray-400 hover:text-gray-200 transition-colors"
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

function ExtractForm() {
  const [start, setStart] = useState('')
  const [end, setEnd]     = useState('')
  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo source</Label>
        <FileInput name="video_file" label="Choisir une vidéo" accept="video/*" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Début (HH:MM:SS ou secondes)</Label>
          <Input name="start_time" placeholder="00:01:30" value={start} onChange={setStart} />
        </div>
        <div>
          <Label>Fin (HH:MM:SS ou secondes)</Label>
          <Input name="end_time" placeholder="00:02:45" value={end} onChange={setEnd} />
        </div>
      </div>
    </div>
  )
}

function CropForm() {
  const fileRef  = useRef<HTMLInputElement>(null)
  const [file,   setFile]   = useState<File | null>(null)
  const [gpu,    setGpu]    = useState(true)
  const [crop,   setCrop]   = useState<CropValues>({ top: 0, bottom: 0, left: 0, right: 0 })

  const handleCropChange = useCallback((v: CropValues) => setCrop(v), [])

  const noCrop = crop.top === 0 && crop.bottom === 0 && crop.left === 0 && crop.right === 0

  return (
    <div className="space-y-4">
      {/* Upload vidéo */}
      <div>
        <Label>Vidéo source</Label>
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

function MergeForm() {
  const [reverse, setReverse] = useState(false)
  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéos à fusionner (ordre alphabétique par défaut)</Label>
        <FileInput name="video_files" label="Choisir plusieurs vidéos" accept="video/*" multiple />
      </div>
      <Checkbox name="reverse_order" label="Inverser l'ordre" checked={reverse} onChange={setReverse} />
      <input type="hidden" name="reverse_order" value={reverse ? 'true' : 'false'} />
    </div>
  )
}

function PodcastForm({ config }: { config: AppConfig }) {
  const [speed, setSpeed] = useState('1.0')
  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo de fond (background_video)</Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" />
      </div>
      <div>
        <Label>Audio / Vidéo source</Label>
        <FileInput name="audio_file" label="Choisir audio ou vidéo" accept="audio/*,video/*" />
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

function WaveForm({ config }: { config: AppConfig }) {
  const [waveStyle,  setWaveStyle]  = useState('sine')
  const [videoMode,  setVideoMode]  = useState('audio')
  const [speed,      setSpeed]      = useState('1.0')
  const [color,      setColor]      = useState('white')

  const needsMini = videoMode === 'mini' || videoMode === 'hybrid'

  return (
    <div className="space-y-4">
      <div>
        <Label>Audio / Vidéo source</Label>
        <FileInput name="audio_file" label="Choisir audio ou vidéo" accept="audio/*,video/*" />
      </div>
      <div>
        <Label>Vidéo de fond (optionnel — fond noir si absent)</Label>
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
          <Label>Vidéo du mini-overlay (requise pour mode mini/hybrid)</Label>
          <FileInput name="content_video" label="Choisir la vidéo à afficher" accept="video/*" />
        </div>
      )}
    </div>
  )
}

function PortraitForm() {
  const [audioOnly,    setAudioOnly]    = useState(false)
  const [borderColor,  setBorderColor]  = useState('white')

  return (
    <div className="space-y-4">
      <div>
        <Label>Vidéo de fond 1080×1920 (background)</Label>
        <FileInput name="background_video" label="Choisir la vidéo de fond" accept="video/*" />
      </div>
      <div>
        <Label>Contenu à intégrer (vidéo ou audio)</Label>
        <FileInput name="content_video" label="Choisir vidéo ou audio" accept="audio/*,video/*" />
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
      </div>
      <Checkbox name="audio_only" label="Mode audio pur (pas de mini-vidéo)" checked={audioOnly} onChange={setAudioOnly} />
      <input type="hidden" name="audio_only" value={audioOnly ? 'true' : 'false'} />
    </div>
  )
}

// ─── Page principale ──────────────────────────────────────────────────────────

const STYLE_ICONS: Record<string, string> = {
  extract:  '✂️',
  crop:     '🖼️',
  merge:    '🔗',
  podcast:  '🎙️',
  wave:     '🌊',
  portrait: '📱',
}

export default function NewJob() {
  const navigate = useNavigate()
  const [config, setConfig]   = useState<AppConfig | null>(null)
  const [style,  setStyle]    = useState('extract')
  const [title,  setTitle]    = useState('')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    fetchConfig().then(setConfig).catch(() => setError('Backend inaccessible'))
  }, [])

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

      {/* Sélection du style */}
      <div className="grid grid-cols-3 gap-3">
        {Object.entries(config.job_styles).map(([key, desc]) => (
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
            <div className="text-sm font-medium capitalize">{key}</div>
            <div className="text-xs text-gray-500 mt-0.5">{desc}</div>
          </button>
        ))}
      </div>

      {/* Formulaire */}
      <form onSubmit={handleSubmit} className="bg-gray-900 rounded-2xl p-6 space-y-5">
        <div>
          <Label>Titre du job (optionnel)</Label>
          <Input name="title" placeholder="Ex: Clip conférence 5 min" value={title} onChange={setTitle} />
        </div>

        <hr className="border-gray-800" />

        {style === 'extract'  && <ExtractForm />}
        {style === 'crop'     && <CropForm />}
        {style === 'merge'    && <MergeForm />}
        {style === 'podcast'  && <PodcastForm config={config} />}
        {style === 'wave'     && <WaveForm config={config} />}
        {style === 'portrait' && <PortraitForm />}

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-6 py-2.5 rounded-xl transition-colors"
        >
          <Play size={16} />
          {loading ? 'Lancement...' : 'Lancer le job'}
        </button>
      </form>
    </div>
  )
}
