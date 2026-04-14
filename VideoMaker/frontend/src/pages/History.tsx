import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Trash2, Eye, CheckCircle, XCircle, Loader, Clock, RefreshCw } from 'lucide-react'
import { listJobs, deleteJob, downloadUrl, type Job } from '../api'

const STATUS_BADGE: Record<string, string> = {
  pending:   'bg-gray-700 text-gray-300',
  running:   'bg-violet-800 text-violet-200',
  completed: 'bg-green-800 text-green-200',
  failed:    'bg-red-800 text-red-200',
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  pending:   <Clock size={13} />,
  running:   <Loader size={13} className="animate-spin" />,
  completed: <CheckCircle size={13} />,
  failed:    <XCircle size={13} />,
}

const STYLE_ICONS: Record<string, string> = {
  extract: '✂️', crop: '🖼️', merge: '🔗',
  podcast: '🎙️', wave: '🌊', portrait: '📱',
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso + 'Z').toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function History() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const list = await listJobs().catch(() => [])
    setJobs(list)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function handleDelete(id: string) {
    if (!confirm('Supprimer ce job et ses fichiers ?')) return
    await deleteJob(id).catch(console.error)
    setJobs(prev => prev.filter(j => j.id !== id))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 animate-pulse">
        Chargement...
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Historique</h1>
          <p className="text-gray-400 text-sm mt-1">{jobs.length} job{jobs.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-colors"
        >
          <RefreshCw size={14} />
          Actualiser
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center text-gray-500 py-20">
          <p className="text-4xl mb-3">📭</p>
          <p>Aucun job pour l'instant</p>
          <Link to="/" className="text-violet-400 hover:underline text-sm mt-2 inline-block">
            Créer votre premier job
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map(job => (
            <div key={job.id} className="bg-gray-900 rounded-2xl p-3 sm:p-4 flex items-center gap-3 sm:gap-4">
              {/* Icône style */}
              <div className="text-2xl shrink-0">{STYLE_ICONS[job.style] ?? '🎬'}</div>

              {/* Infos */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-white text-sm truncate">
                    {job.title || `Job ${job.style}`}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[job.status] ?? STATUS_BADGE.pending}`}
                  >
                    {STATUS_ICON[job.status]}
                    {job.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  Créé le {formatDate(job.created_at)}
                  {job.completed_at && ` · Terminé le ${formatDate(job.completed_at)}`}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/jobs/${job.id}`}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                  title="Voir les détails"
                >
                  <Eye size={16} />
                </Link>
                {job.status === 'completed' && job.output_video_path && (
                  <a
                    href={downloadUrl(job.id)}
                    className="p-2 text-green-400 hover:text-green-300 hover:bg-gray-800 rounded-lg transition-colors"
                    title="Télécharger"
                  >
                    <Download size={16} />
                  </a>
                )}
                <button
                  onClick={() => handleDelete(job.id)}
                  className="p-2 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors"
                  title="Supprimer"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
