const BASE = '/api'

export interface Job {
  id: string
  style: string
  title: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string | null
  started_at: string | null
  completed_at: string | null
  output_video_path: string | null
  output_dir: string | null
  log_file: string | null
  error_message: string | null
}

export interface JobLogs {
  id: string
  status: string
  logs: string
  output_video_path: string | null
}

export interface AppConfig {
  job_styles: Record<string, string>
  wave_styles: string[]
  video_modes: string[]
  speed_factors: number[]
}

export interface SourceInfo {
  source_id: string
  filename:  string
  path:      string
  duration:  number
  width:     number
  height:    number
  fps:       number
}

export interface ClipMark {
  start: number
  end:   number
}

export async function createBatchExtractJob(data: {
  source_id: string
  clips:     ClipMark[]
  merge:     boolean
  title?:    string
}): Promise<Job> {
  const r = await fetch('/api/jobs/batch-extract', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(data),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export interface PrepJob {
  id: string
  style: string
  title: string | null
  output_video_path: string | null
  completed_at: string | null
}

export async function fetchPrepJobs(): Promise<PrepJob[]> {
  const r = await fetch('/api/assets/prep-jobs')
  if (!r.ok) return []
  return r.json()
}

export async function fetchConfig(): Promise<AppConfig> {
  const r = await fetch('/api/assets/config')
  if (!r.ok) throw new Error('Erreur config')
  return r.json()
}

export async function listJobs(): Promise<Job[]> {
  const r = await fetch(`${BASE}/jobs`)
  if (!r.ok) throw new Error('Erreur liste jobs')
  return r.json()
}

export async function getJob(id: string): Promise<Job> {
  const r = await fetch(`${BASE}/jobs/${id}`)
  if (!r.ok) throw new Error('Job introuvable')
  return r.json()
}

export async function getJobLogs(id: string): Promise<JobLogs> {
  const r = await fetch(`${BASE}/jobs/${id}/logs`)
  if (!r.ok) throw new Error('Erreur logs')
  return r.json()
}

export async function createJob(formData: FormData): Promise<Job> {
  const r = await fetch(`${BASE}/jobs`, { method: 'POST', body: formData })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }))
    throw new Error(err.detail || 'Erreur création job')
  }
  return r.json()
}

export async function deleteJob(id: string): Promise<void> {
  const r = await fetch(`${BASE}/jobs/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Erreur suppression')
}

export function downloadUrl(id: string): string {
  return `${BASE}/jobs/${id}/download`
}
