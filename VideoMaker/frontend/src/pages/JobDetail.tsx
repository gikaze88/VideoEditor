import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  Download, ArrowLeft, CheckCircle, XCircle, Loader, Clock, ArrowRight, Upload,
} from 'lucide-react'
import {
  getJobLogs,
  getJob,
  downloadUrl,
  type JobLogs,
  type Job,
  getYoutubeAuthStatus,
  getYoutubeAuthUrl,
  getYoutubePlaylists,
  uploadToYoutube,
  getYoutubeJobStatus,
  fetchYoutubeMeta,
  type YoutubePlaylist,
  type YoutubeUploadResult,
  type YoutubeJobStatus,
  type YoutubeCategory,
  type YoutubeLanguage,
} from '../api'

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

  // YouTube state
  const [ytAuth,       setYtAuth]       = useState<boolean | null>(null)
  const [ytPlaylists,  setYtPlaylists]  = useState<YoutubePlaylist[]>([])
  const [ytCategories, setYtCategories] = useState<YoutubeCategory[]>([])
  const [ytLanguages,  setYtLanguages]  = useState<YoutubeLanguage[]>([])
  const [ytStatus,     setYtStatus]     = useState<YoutubeJobStatus | null>(null)
  const [ytForm,       setYtForm]       = useState({
    title: '',
    description: '',
    tags: '',
    privacy: 'private',
    categoryId: '25',
    playlistId: '',
    filename: '',
    language: 'fr',
    licenseType: 'youtube',
    embeddable: true,
  })
  const [ytThumb,      setYtThumb]      = useState<File | null>(null)
  const [ytUploading,  setYtUploading]  = useState(false)
  const [ytResult,     setYtResult]     = useState<YoutubeUploadResult | null>(null)
  const [ytError,      setYtError]      = useState<string | null>(null)

  async function poll() {
    if (!id) return
    try {
      const d = await getJobLogs(id)
      setData(d)
      // Charger les métadonnées complètes (style, etc.) une fois
      if (!jobMeta) {
        const meta = await getJob(id).catch(() => null)
        if (meta) {
          setJobMeta(meta)
          // Pré-remplir le titre YouTube avec le titre du job
          if (meta.title) setYtForm(prev => ({ ...prev, title: prev.title || meta.title }))
        }
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

  // Charger le statut YouTube au montage (pour rattraper un upload déjà en cours)
  useEffect(() => {
    if (!id) return
    getYoutubeJobStatus(id).then(setYtStatus).catch(() => {})
  }, [id])

  // Charger statut YouTube + playlists + meta quand le job est terminé
  useEffect(() => {
    if (!id) return
    if (!data || data.status !== 'completed') return

    ;(async () => {
      try {
        const st = await getYoutubeJobStatus(id)
        setYtStatus(st)
        const auth = await getYoutubeAuthStatus()
        setYtAuth(auth.authenticated)
        const meta = await fetchYoutubeMeta()
        setYtCategories(meta.categories)
        setYtLanguages(meta.languages)
        if (auth.authenticated) {
          const pls = await getYoutubePlaylists()
          setYtPlaylists(pls)
        }
      } catch {
        // ignore soft errors ici
      }
    })()
  }, [id, data?.status])  // dépend seulement du changement de statut, pas de chaque re-render data

  // Polling du statut YouTube — démarre dès qu'un upload auto est en cours/en attente
  const ytPollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  useEffect(() => {
    if (!id) return

    const isActive = (s: string | null | undefined) =>
      s === 'uploading' || s === 'pending_upload'

    if (!isActive(ytStatus?.youtube_status)) {
      if (ytPollRef.current) { clearInterval(ytPollRef.current); ytPollRef.current = null }
      return
    }

    if (ytPollRef.current) return  // déjà en cours

    ytPollRef.current = setInterval(async () => {
      try {
        const st = await getYoutubeJobStatus(id)
        setYtStatus(st)
        if (!isActive(st.youtube_status)) {
          if (ytPollRef.current) { clearInterval(ytPollRef.current); ytPollRef.current = null }
        }
      } catch { /* ignore */ }
    }, 3000)

    return () => {
      if (ytPollRef.current) { clearInterval(ytPollRef.current); ytPollRef.current = null }
    }
  }, [id, ytStatus?.youtube_status])

  function ytSetField<K extends keyof typeof ytForm>(key: K, value: (typeof ytForm)[K]) {
    setYtForm(prev => ({ ...prev, [key]: value }))
  }

  const authPollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  async function handleYoutubeAuth() {
    try {
      setYtError(null)
      const url = await getYoutubeAuthUrl()
      window.open(url, '_blank')

      if (authPollRef.current) clearInterval(authPollRef.current)
      authPollRef.current = setInterval(async () => {
        try {
          const st = await getYoutubeAuthStatus()
          if (st.authenticated) {
            if (authPollRef.current) clearInterval(authPollRef.current)
            authPollRef.current = null
            setYtAuth(true)
            const pls = await getYoutubePlaylists()
            setYtPlaylists(pls)
          }
        } catch { /* ignore poll errors */ }
      }, 2000)
    } catch (e) {
      setYtError(e instanceof Error ? e.message : 'Erreur OAuth YouTube')
    }
  }

  useEffect(() => {
    return () => {
      if (authPollRef.current) clearInterval(authPollRef.current)
    }
  }, [])

  async function handleYoutubeUpload() {
    if (!id || !data || !jobMeta) return
    try {
      setYtUploading(true)
      setYtError(null)
      setYtResult(null)
      const res = await uploadToYoutube(id, {
        ...ytForm,
        title: ytForm.title || jobMeta?.title || '',
        language: ytForm.language,
        licenseType: ytForm.licenseType,
        embeddable: ytForm.embeddable,
        thumbnail: ytThumb ?? undefined,
      })
      setYtResult(res)
      setYtStatus({
        youtube_video_id: res.video_id,
        youtube_status: 'uploaded',
        url: res.url,
        studio_url: res.studio_url,
      })
    } catch (e) {
      setYtError(e instanceof Error ? e.message : 'Erreur upload YouTube')
    } finally {
      setYtUploading(false)
    }
  }

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
      <div className="bg-gray-900 rounded-2xl p-4 sm:p-6 space-y-4">
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

      {/* YouTube upload (uniquement quand terminé) */}
      {data.status === 'completed' && jobMeta && (
        <div className="bg-gray-900 rounded-2xl p-4 sm:p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Upload size={18} className="text-red-400" />
              <h2 className="text-sm font-semibold text-gray-200">YouTube</h2>
            </div>
            {ytStatus?.youtube_video_id && (
              <a href={ytStatus.url ?? undefined} target="_blank" rel="noreferrer" className="text-xs text-red-400 hover:underline">
                Voir sur YouTube
              </a>
            )}
          </div>

          {/* Statut auto-upload */}
          {ytStatus?.youtube_status === 'pending_upload' && (
            <div className="flex items-center gap-2 text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-700/40 rounded-lg px-3 py-2">
              <Clock size={13} />
              Upload YouTube en attente (démarrera à la fin du job)...
            </div>
          )}
          {ytStatus?.youtube_status === 'uploading' && (
            <div className="flex items-center gap-2 text-xs text-blue-400 bg-blue-900/20 border border-blue-700/40 rounded-lg px-3 py-2">
              <Loader size={13} className="animate-spin" />
              Upload YouTube en cours... (actualisation auto)
            </div>
          )}
          {ytStatus?.youtube_status === 'upload_failed' && (
            <div className="text-xs text-red-400 bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2">
              L'auto-upload YouTube a échoué. Utilisez le formulaire ci-dessous.
            </div>
          )}

          {/* Déjà uploadé */}
          {(ytStatus?.youtube_status === 'uploaded' || ytStatus?.youtube_video_id) && (
            <div className="text-xs bg-green-900/20 border border-green-700/40 rounded-lg px-3 py-2 space-y-1">
              <p className="text-green-400 font-medium">Vidéo uploadée sur YouTube ✓</p>
              {ytStatus?.youtube_video_id && (
                <div className="flex gap-3 flex-wrap">
                  <a href={ytStatus.url ?? undefined} target="_blank" rel="noreferrer" className="text-red-400 hover:underline">Voir sur YouTube</a>
                  <a href={ytStatus.studio_url ?? undefined} target="_blank" rel="noreferrer" className="text-gray-400 hover:underline">YouTube Studio</a>
                </div>
              )}
            </div>
          )}

          {ytAuth === false && (
            <button type="button" onClick={handleYoutubeAuth}
              className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white text-xs font-medium px-4 py-2 rounded-xl transition-colors"
            >
              <Upload size={14} />
              Connecter mon compte YouTube
            </button>
          )}

          {ytAuth && (
            <div className="space-y-3 text-xs">
              {/* Titre + fichier */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-400 mb-1">Titre</label>
                  <input type="text"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    value={ytForm.title || jobMeta.title || ''}
                    onChange={e => ytSetField('title', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-gray-400 mb-1">Fichier <span className="text-gray-600">(vide = vidéo principale)</span></label>
                  <input type="text"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    placeholder={data.output_video_path ? data.output_video_path.split(/[\\/]/).pop() : ''}
                    value={ytForm.filename}
                    onChange={e => ytSetField('filename', e.target.value)}
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-gray-400 mb-1">Description</label>
                <textarea
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs min-h-[70px] text-gray-200 resize-y"
                  value={ytForm.description}
                  onChange={e => ytSetField('description', e.target.value)}
                />
              </div>

              {/* Tags + confidentialité + catégorie */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div>
                  <label className="block text-gray-400 mb-1">Tags <span className="text-gray-600">(virgule)</span></label>
                  <input type="text"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    placeholder="politique,actualité,france"
                    value={ytForm.tags}
                    onChange={e => ytSetField('tags', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-gray-400 mb-1">Confidentialité</label>
                  <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    value={ytForm.privacy} onChange={e => ytSetField('privacy', e.target.value)}
                  >
                    <option value="private">Privé</option>
                    <option value="unlisted">Non répertorié</option>
                    <option value="public">Public</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 mb-1">Catégorie</label>
                  <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    value={ytForm.categoryId} onChange={e => ytSetField('categoryId', e.target.value)}
                  >
                    {ytCategories.length > 0
                      ? ytCategories.map(c => <option key={c.id} value={c.id}>{c.label}</option>)
                      : <>
                          <option value="25">News &amp; Politics</option>
                          <option value="24">Entertainment</option>
                          <option value="22">People &amp; Blogs</option>
                          <option value="27">Education</option>
                          <option value="28">Science &amp; Technology</option>
                        </>
                    }
                  </select>
                </div>
              </div>

              {/* Langue + licence + embedding */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 items-end">
                <div>
                  <label className="block text-gray-400 mb-1">Langue</label>
                  <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    value={ytForm.language} onChange={e => ytSetField('language', e.target.value)}
                  >
                    {ytLanguages.length > 0
                      ? ytLanguages.map(l => <option key={l.code} value={l.code}>{l.label}</option>)
                      : <><option value="fr">Français</option><option value="en">English</option></>
                    }
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 mb-1">Licence</label>
                  <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    value={ytForm.licenseType} onChange={e => ytSetField('licenseType', e.target.value)}
                  >
                    <option value="youtube">Licence YouTube standard</option>
                    <option value="creativeCommon">Creative Commons (CC BY)</option>
                  </select>
                </div>
                <label className="flex items-center gap-2 cursor-pointer pb-1">
                  <input type="checkbox" checked={ytForm.embeddable}
                    onChange={e => ytSetField('embeddable', e.target.checked)}
                    className="w-4 h-4 accent-red-500"
                  />
                  <span className="text-gray-300">Autoriser l'intégration</span>
                </label>
              </div>

              {/* Playlist + miniature */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-400 mb-1">Playlist</label>
                  <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-200"
                    value={ytForm.playlistId} onChange={e => ytSetField('playlistId', e.target.value)}
                  >
                    <option value="">(aucune)</option>
                    {ytPlaylists.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-400 mb-1">Miniature</label>
                  <input type="file" accept="image/*"
                    className="w-full text-[11px] text-gray-400"
                    onChange={e => setYtThumb(e.target.files?.[0] ?? null)}
                  />
                </div>
              </div>

              {ytError && (
                <div className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">{ytError}</div>
              )}
              {ytResult && (
                <div className="text-xs text-green-400 bg-green-900/20 border border-green-800 rounded-lg px-3 py-2 space-y-1">
                  <p>Upload terminé.</p>
                  <div className="flex gap-3">
                    <a href={ytResult.url} target="_blank" rel="noreferrer" className="underline">Ouvrir la vidéo</a>
                    <a href={ytResult.studio_url} target="_blank" rel="noreferrer" className="underline">YouTube Studio</a>
                  </div>
                </div>
              )}

              <button
                type="button"
                onClick={handleYoutubeUpload}
                disabled={ytUploading || !(ytForm.title || jobMeta?.title)}
                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-40 text-white text-xs font-medium px-4 py-2 rounded-xl transition-colors"
              >
                {ytUploading ? <Loader size={14} className="animate-spin" /> : <Upload size={14} />}
                {ytUploading ? 'Upload en cours...' : 'Uploader sur YouTube'}
              </button>
            </div>
          )}
        </div>
      )}

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
