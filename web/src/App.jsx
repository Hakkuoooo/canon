import { useState } from 'react'
import { Circle } from 'lucide-react'
import Header from './components/Header.jsx'
import Composer from './components/Composer.jsx'
import PipelinePanel from './components/PipelinePanel.jsx'
import EpisodeViewer from './components/EpisodeViewer.jsx'
import CharacterBible from './components/CharacterBible.jsx'
import { createSeries, generateEpisode } from './api.js'

function Footer({ status }) {
  const online = status !== 'error'
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex w-full max-w-[1220px] flex-col items-center justify-between gap-3 px-6 py-8 text-[12px] text-ink-soft sm:flex-row md:px-10">
        <span>Canon — built on Qwen Cloud</span>
        <span className="flex items-center gap-2">
          <Circle className={`h-2 w-2 ${online ? 'fill-sage text-sage' : 'fill-red-400 text-red-400'}`} strokeWidth={0} />
          {online ? 'engine connected' : 'engine unreachable'}
        </span>
      </div>
    </footer>
  )
}

export default function App() {
  const [seriesId, setSeriesId] = useState(null)
  const [episodes, setEpisodes] = useState([]) // [{ episode, video_url, characters, style }]
  const [status, setStatus] = useState('idle') // idle | running | done | error
  const [error, setError] = useState('')

  async function onGenerate(premise, style, shots) {
    setStatus('running')
    setError('')
    try {
      let sid = seriesId
      if (!sid) {
        sid = await createSeries()
        setSeriesId(sid)
      }
      const ep = await generateEpisode(sid, premise, style, shots)
      setEpisodes((prev) => [...prev, ep])
      setStatus('done')
    } catch (e) {
      setError(String(e.message || e))
      setStatus('error')
    }
  }

  const latest = episodes[episodes.length - 1]

  return (
    <div className="grain min-h-screen">
      <Header />
      <main className="mx-auto w-full max-w-[1220px] px-6 md:px-10">
        <section className="grid grid-cols-1 gap-6 pt-10 pb-8 md:pt-16 lg:grid-cols-12 lg:gap-8">
          <div className="reveal lg:col-span-7" style={{ animationDelay: '80ms' }}>
            <Composer onGenerate={onGenerate} status={status} />
          </div>
          <div className="reveal lg:col-span-5" style={{ animationDelay: '180ms' }}>
            <PipelinePanel status={status} error={error} />
          </div>
        </section>

        <section className="reveal pb-10" style={{ animationDelay: '260ms' }}>
          <EpisodeViewer episodes={episodes} />
        </section>

        <section className="reveal pb-20" style={{ animationDelay: '340ms' }}>
          <CharacterBible characters={latest?.characters || []} styleName={latest?.style} />
        </section>
      </main>
      <Footer status={status} />
    </div>
  )
}
