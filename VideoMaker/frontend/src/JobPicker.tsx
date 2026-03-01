/**
 * JobPicker — sélecteur de source vidéo avec deux modes :
 *   1. "Uploader" : input file classique
 *   2. "Job précédent" : liste des outputs extract/crop/merge complétés
 *
 * Passe au parent :
 *   - onFileReady(true/false) : indique si une source est sélectionnée
 *   - name         : nom du champ file upload
 *   - jobRefName   : nom du champ hidden pour le job ID de référence
 */
import { useEffect, useState } from 'react'
import { Upload, History, CheckCircle, Scissors, Crop, Link } from 'lucide-react'
import { fetchPrepJobs, type PrepJob } from './api'

const STYLE_ICON: Record<string, React.ReactNode> = {
  extract: <Scissors size={14} />,
  crop:    <Crop     size={14} />,
  merge:   <Link     size={14} />,
}

const STYLE_LABEL: Record<string, string> = {
  extract: 'Extrait',
  crop:    'Recadré',
  merge:   'Fusionné',
}

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso + 'Z').toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function basename(path: string | null) {
  if (!path) return ''
  return path.split(/[/\\]/).pop() ?? path
}

interface Props {
  /** Nom du champ <input type="file"> dans le formulaire */
  name: string
  /** Nom du champ hidden pour le job ID de référence */
  jobRefName: string
  /** Texte descriptif affiché dans le bouton upload */
  label: string
  /** Types de fichiers acceptés pour l'upload */
  accept?: string
  /** Appelé quand l'état "prêt" change */
  onReady: (ready: boolean) => void
  /** Job pré-sélectionné depuis l'extérieur (ex: bouton "Utiliser dans...") */
  preselectedJobId?: string | null
}

export default function JobPicker({
  name, jobRefName, label, accept, onReady, preselectedJobId,
}: Props) {
  const [mode, setMode]               = useState<'upload' | 'history'>(
    preselectedJobId ? 'history' : 'upload'
  )
  const [prepJobs, setPrepJobs]       = useState<PrepJob[]>([])
  const [selectedJob, setSelectedJob] = useState<PrepJob | null>(null)
  const [uploadedFile, setUploadedFile] = useState<string | null>(null)
  const [loading, setLoading]         = useState(false)

  // Charger les jobs de préparation
  useEffect(() => {
    setLoading(true)
    fetchPrepJobs().then(jobs => {
      setPrepJobs(jobs)
      // Pré-sélectionner si un ID est passé
      if (preselectedJobId) {
        const found = jobs.find(j => j.id === preselectedJobId)
        if (found) setSelectedJob(found)
      }
      setLoading(false)
    })
  }, [preselectedJobId])

  // Notifier le parent
  useEffect(() => {
    if (mode === 'upload') onReady(uploadedFile !== null)
    else onReady(selectedJob !== null)
  }, [mode, uploadedFile, selectedJob, onReady])

  const switchMode = (m: 'upload' | 'history') => {
    setMode(m)
    setSelectedJob(null)
    setUploadedFile(null)
  }

  return (
    <div className="space-y-2">
      {/* Toggle upload / historique */}
      <div className="flex gap-1 bg-gray-800 p-1 rounded-lg w-fit">
        <button
          type="button"
          onClick={() => switchMode('upload')}
          className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md transition-colors ${
            mode === 'upload'
              ? 'bg-violet-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Upload size={12} />
          Uploader
        </button>
        <button
          type="button"
          onClick={() => switchMode('history')}
          className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md transition-colors ${
            mode === 'history'
              ? 'bg-violet-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <History size={12} />
          Job précédent
          {prepJobs.length > 0 && (
            <span className="ml-1 bg-violet-500/30 text-violet-300 text-xs rounded-full px-1.5">
              {prepJobs.length}
            </span>
          )}
        </button>
      </div>

      {/* Mode upload */}
      {mode === 'upload' && (
        <>
          {/* Champ file réel pour le form */}
          <label className={`flex items-center gap-2 w-full border border-dashed rounded-lg px-3 py-3 text-sm cursor-pointer transition-colors ${
            uploadedFile
              ? 'bg-gray-800 border-violet-500 text-gray-200'
              : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-violet-500 hover:text-gray-200'
          }`}>
            <Upload size={15} />
            {uploadedFile ?? label}
            <input
              type="file"
              name={name}
              accept={accept}
              className="hidden"
              onChange={e => setUploadedFile(e.target.files?.[0]?.name ?? null)}
            />
          </label>
          {/* Pas de job ref en mode upload */}
          <input type="hidden" name={jobRefName} value="" />
        </>
      )}

      {/* Mode historique */}
      {mode === 'history' && (
        <>
          {/* Input file désactivé (non soumis) — valeur vide */}
          <input type="hidden" name={name} value="" />
          {/* Job ref hidden */}
          <input type="hidden" name={jobRefName} value={selectedJob?.id ?? ''} />

          {loading && (
            <p className="text-xs text-gray-500 animate-pulse px-1">Chargement...</p>
          )}

          {!loading && prepJobs.length === 0 && (
            <div className="text-center text-gray-500 text-sm py-6 bg-gray-800 rounded-xl border border-dashed border-gray-700">
              <History size={24} className="mx-auto mb-2 opacity-50" />
              <p>Aucun job de préparation terminé</p>
              <p className="text-xs mt-1">Faites d'abord un Extract, Crop ou Merge</p>
            </div>
          )}

          {!loading && prepJobs.length > 0 && (
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {prepJobs.map(job => {
                const isSelected = selectedJob?.id === job.id
                return (
                  <button
                    key={job.id}
                    type="button"
                    onClick={() => setSelectedJob(isSelected ? null : job)}
                    className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl border transition-all ${
                      isSelected
                        ? 'border-green-500 bg-green-500/10 text-white'
                        : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    {/* Icône style */}
                    <span className={`shrink-0 p-1.5 rounded-lg ${
                      isSelected ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'
                    }`}>
                      {STYLE_ICON[job.style] ?? <History size={14} />}
                    </span>

                    {/* Infos */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {job.title || basename(job.output_video_path)}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1.5">
                        <span className="uppercase font-mono text-gray-600">
                          {STYLE_LABEL[job.style] ?? job.style}
                        </span>
                        <span>·</span>
                        {formatDate(job.completed_at)}
                      </p>
                    </div>

                    {/* Checkmark */}
                    {isSelected && (
                      <CheckCircle size={16} className="shrink-0 text-green-400" />
                    )}
                  </button>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
