import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Download, ArrowLeft, CheckCircle, XCircle, Loader, Clock, ArrowRight } from 'lucide-react'
import { getJobLogs, getJob, downloadUrl, type JobLogs, type Job } from '../api'

const STATUS_CONFIG = {
  pending:   { icon: Clock,        color: 'text-gray-400',  label: 'En attente' },
  running:   { icon: Loader,       color: 'text-violet-400 animate-spin', label: 'En cours...' },
  completed: { icon: CheckCircle,  color: 'text-green-400', label: 'Terminé' },
  failed:    { icon: XCircle,      color: 'text-red-400',   label: 'Échoué' },
}

function ProgressBar({ status }: { status: string }) {
  const pct = status === 'completed' ? 100 : status === 'failed' ? 100 : status === 'running' ? 60 : 5
  const color = status === 'failed' ? 'bg-red-500' : status === 'completed' ? 'bg-green-500' : 'bg-violet-500'
  return (
    <div className="w-full bg-gray-800 rounded-full h-2">
      <div
        className={`${color} h-2 rounded-full transition-all duration-700 ${status === 'running' ? 'animate-pulse' : ''}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

const PREP_STYLES = ['extract', 'crop', 'merge']

// Boutons "Utiliser dans →" pour les jobs de préparation complétés
function UseAsSourceButtons({ jobId, style }: { jobId: string; style: string }) {
  const navigate = useNavigate()
  if (!PREP_STYLES.includes(style)) return null

  const targets = [
    { style: 'podcast',  label: 'Podcast',  icon: '🎙️' },
    { style: 'wave',     label: 'Wave',     icon: '🌊' },
    { style: 'portrait', label: 'Portrait', icon: '📱' },
  ]

  return (
    <div className="bg-gray-900 rounded-2xl p-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-300">
        <ArrowRight size={15} className="text-violet-400" />
        Utiliser ce résultat dans…
      </div>
      <div className="flex gap-2 flex-wrap">
        {targets.map(t => (
          <button
            key={t.style}
            type="button"
            onClick={() => navigate('/', { state: { style: t.style, jobId } })}
            className="flex items-center gap-2 bg-gray-800 hover:bg-violet-600 border border-gray-700 hover:border-violet-500 text-gray-300 hover:text-white text-sm px-3 py-2 rounded-xl transition-all"
          >
            <span>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const [data,    setData]    = useState<JobLogs | null>(null)
  const [jobMeta, setJobMeta] = useState<Job | null>(null)
  const [error,   setError]   = useState<string | null>(null)
  const logsRef = useRef<HTMLPreElement>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  async function poll() {
    if (!id) return
    try {
      const d = await getJobLogs(id)
      setData(d)
      // Charger les métadonnées complètes (style, etc.) une fois
      if (!jobMeta) {
        const meta = await getJob(id).catch(() => null)
        if (meta) setJobMeta(meta)
      }
      // Auto-scroll logs vers le bas
      if (logsRef.current) {
        logsRef.current.scrollTop = logsRef.current.scrollHeight
      }
      // Arrêter le polling si terminé
      if (d.status === 'completed' || d.status === 'failed') {
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    } catch {
      setError('Impossible de charger les données du job')
    }
  }

  useEffect(() => {
    poll()
    intervalRef.current = setInterval(poll, 3000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [id])

  if (error) {
    return (
      <div className="text-center text-red-400 py-20">
        <XCircle size={40} className="mx-auto mb-3" />
        <p>{error}</p>
        <Link to="/" className="text-violet-400 hover:underline text-sm mt-2 inline-block">← Retour</Link>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 animate-pulse">
        Chargement...
      </div>
    )
  }

  const cfg = STATUS_CONFIG[data.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.pending
  const StatusIcon = cfg.icon

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center gap-3">
        <Link to="/history" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-white">Détail du job</h1>
          <p className="text-xs text-gray-500 font-mono mt-0.5">{id}</p>
        </div>
      </div>

      {/* Carte statut */}
      <div className="bg-gray-900 rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-3">
          <StatusIcon size={24} className={cfg.color} />
          <div>
            <p className="font-semibold text-white">{cfg.label}</p>
            <p className="text-xs text-gray-500 capitalize">{data.status}</p>
          </div>
        </div>

        <ProgressBar status={data.status} />

        {/* Bouton download */}
        {data.status === 'completed' && data.output_video_path && (
          <a
            href={downloadUrl(data.id)}
            className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white font-medium px-5 py-2.5 rounded-xl transition-colors"
          >
            <Download size={16} />
            Télécharger la vidéo
          </a>
        )}

        {data.status === 'failed' && (
          <div className="text-red-400 text-sm bg-red-900/20 border border-red-800 rounded-lg px-4 py-3">
            Le job a échoué. Consultez les logs ci-dessous.
          </div>
        )}
      </div>

      {/* Logs */}
      <div className="bg-gray-900 rounded-2xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-300">Logs en temps réel</h2>
          {data.status === 'running' && (
            <span className="text-xs text-violet-400 animate-pulse">● mise à jour toutes les 3s</span>
          )}
        </div>
        <pre
          ref={logsRef}
          className="text-xs font-mono text-gray-400 bg-gray-950 rounded-lg p-4 overflow-auto max-h-96 whitespace-pre-wrap"
        >
          {data.logs || 'Aucun log disponible pour le moment...'}
        </pre>
      </div>

      {/* Utiliser dans... (seulement pour extract/crop/merge complétés) */}
      {data.status === 'completed' && jobMeta && (
        <UseAsSourceButtons jobId={data.id} style={jobMeta.style} />
      )}

      {/* Navigation */}
      {(data.status === 'completed' || data.status === 'failed') && (
        <div className="flex gap-3">
          <Link
            to="/"
            className="bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors"
          >
            Nouveau job
          </Link>
          <Link
            to="/history"
            className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded-xl text-sm font-medium transition-colors"
          >
            Historique
          </Link>
        </div>
      )}
    </div>
  )
}
