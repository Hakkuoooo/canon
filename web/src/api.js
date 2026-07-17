// Client for the Canon FastAPI tier. Base overridable via VITE_API_BASE (defaults to local dev).
const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function createSeries() {
  const r = await fetch(`${BASE}/api/series`, { method: 'POST' })
  if (!r.ok) throw new Error('Could not start a series')
  return (await r.json()).series_id
}

export async function listEpisodes(seriesId) {
  const r = await fetch(`${BASE}/api/series/${seriesId}/episodes`)
  if (!r.ok) throw new Error('series not found')
  const { episodes } = await r.json()
  return episodes.map((e) => ({ ...e, video_url: `${BASE}${e.video_url}` }))
}

export async function getProgress(seriesId) {
  const r = await fetch(`${BASE}/api/series/${seriesId}/progress`)
  if (!r.ok) throw new Error('progress unavailable')
  return r.json()
}

export async function generateEpisode(seriesId, premise, style, shots) {
  const r = await fetch(`${BASE}/api/series/${seriesId}/episodes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ premise, style, shots }),
  })
  if (!r.ok) throw new Error(`Generation failed (${r.status})`)
  const data = await r.json()
  return { ...data, video_url: `${BASE}${data.video_url}` } // absolute URL for the <video> tag
}
