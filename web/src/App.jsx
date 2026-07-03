import { Circle } from 'lucide-react'
import Header from './components/Header.jsx'
import Composer from './components/Composer.jsx'
import PipelinePanel from './components/PipelinePanel.jsx'
import EpisodeViewer from './components/EpisodeViewer.jsx'
import CharacterBible from './components/CharacterBible.jsx'

function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex w-full max-w-[1220px] flex-col items-center justify-between gap-3 px-6 py-8 text-[12px] text-ink-soft sm:flex-row md:px-10">
        <span>Canon — built on Qwen Cloud</span>
        <span className="flex items-center gap-2">
          <Circle className="h-2 w-2 fill-sage text-sage" strokeWidth={0} />
          mock preview · pipeline not yet wired
        </span>
      </div>
    </footer>
  )
}

export default function App() {
  return (
    <div className="grain min-h-screen">
      <Header />
      <main className="mx-auto w-full max-w-[1220px] px-6 md:px-10">
        <section className="grid grid-cols-1 gap-6 pt-10 pb-8 md:pt-16 lg:grid-cols-12 lg:gap-8">
          <div className="reveal lg:col-span-7" style={{ animationDelay: '80ms' }}>
            <Composer />
          </div>
          <div className="reveal lg:col-span-5" style={{ animationDelay: '180ms' }}>
            <PipelinePanel />
          </div>
        </section>

        <section className="reveal pb-10" style={{ animationDelay: '260ms' }}>
          <EpisodeViewer />
        </section>

        <section className="reveal pb-20" style={{ animationDelay: '340ms' }}>
          <CharacterBible />
        </section>
      </main>
      <Footer />
    </div>
  )
}
