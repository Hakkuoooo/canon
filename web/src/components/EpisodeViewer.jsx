import { useState, useEffect } from 'react'
import { Lock, Clapperboard } from 'lucide-react'

export default function EpisodeViewer({ episodes = [] }) {
  const [active, setActive] = useState(0)
  useEffect(() => {
    if (episodes.length) setActive(episodes.length - 1) // jump to the newest episode
  }, [episodes.length])

  const current = episodes[active]

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
            <span className="h-px w-6 bg-sage/50" />
            Screening room
          </div>
          <h2 className="mt-3 font-display text-[30px] leading-none tracking-[-0.01em] text-ink md:text-[38px]">
            {episodes.length ? `Episode ${String(current?.episode).padStart(2, '0')}` : 'No episodes yet'}
          </h2>
        </div>
        {episodes.length > 0 && (
          <div className="flex items-center gap-1 rounded-full border border-line bg-cream p-1">
            {episodes.map((e, i) => (
              <button
                key={e.episode}
                onClick={() => setActive(i)}
                className={`rounded-full px-4 py-2 text-[13px] transition-colors ${
                  active === i ? 'bg-ink text-cream' : 'text-ink-soft hover:text-ink'
                }`}
              >
                Ep {String(e.episode).padStart(2, '0')}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6">
        <div
          className="relative aspect-video overflow-hidden rounded-2xl border border-line"
          style={{ background: 'radial-gradient(120% 120% at 30% 15%, #3a3428 0%, #262019 45%, #14110c 100%)' }}
        >
          {current ? (
            <video key={current.video_url} src={current.video_url} controls className="h-full w-full object-cover" />
          ) : (
            <div className="absolute inset-0 grid place-items-center px-6 text-center">
              <div className="flex flex-col items-center gap-3 text-cream/60">
                <Clapperboard className="h-8 w-8" strokeWidth={1.25} />
                <span className="text-[13px]">Your episode screens here once the agents finish.</span>
              </div>
            </div>
          )}
          {current && (
            <div className="pointer-events-none absolute left-5 top-5 flex items-center gap-2 text-[12px] text-cream/70">
              <Lock className="h-3.5 w-3.5 text-sage" strokeWidth={1.5} />
              Consistency locked
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
