/**
 * Store module-level pour l'éditeur de clips.
 * Persiste en mémoire pendant toute la session (navigation entre pages).
 * Se remet à zéro si l'utilisateur recharge la page (F5).
 */
import type { SourceInfo, ClipMark } from './api'

export interface StoredClip extends ClipMark {
  id: string
}

export interface EditorState {
  source:       SourceInfo | null
  clips:        StoredClip[]
  pendingStart: number | null
  lastTime:     number          // position vidéo pour restaurer le seek
}

const DEFAULT: EditorState = {
  source:       null,
  clips:        [],
  pendingStart: null,
  lastTime:     0,
}

let _state: EditorState = { ...DEFAULT }

export function getEditorState(): EditorState {
  return _state
}

export function setEditorState(patch: Partial<EditorState>): void {
  _state = { ..._state, ...patch }
}

export function resetEditorState(): void {
  _state = { ...DEFAULT }
}

/** Nombre de clips actuellement marqués (pour le badge navbar). */
export function editorClipCount(): number {
  return _state.clips.length
}
