import { useState } from 'react'
import { Play, Lock, ChevronRight } from 'lucide-react'
import { episodes, shots } from '../data/mock.js'

export default function EpisodeViewer() {
  const [active, setActive] = useState(1)
  const ep = episodes.find((e) => e.id === active)

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
            <span className="h-px w-6 bg-sage/50" />
            Screening room
          </div>
          <h2 className="mt-3 font-display text-[30px] leading-none tracking-[-0.01em] text-ink md:text-[38px]">
            {ep.title}
          </h2>
        </div>
        <div className="flex items-center gap-1 rounded-full border border-line bg-cream p-1">
          {episodes.map((e) => (
            <button
              key={e.id}
              onClick={() => setActive(e.id)}
              className={`rounded-full px-4 py-2 text-[13px] transition-colors ${
                active === e.id ? 'bg-ink text-cream' : 'text-ink-soft hover:text-ink'
              }`}
            >
              Ep {String(e.id).padStart(2, '0')}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <div className="group relative aspect-video overflow-hidden rounded-2xl border border-line">
            <div
              className="absolute inset-0"
              style={{
                background:
                  'radial-gradient(120% 120% at 30% 15%, #3a3428 0%, #262019 45%, #14110c 100%)',
              }}
            />
            <div className="absolute left-5 top-5 flex items-center gap-2 text-[12px] text-cream/70">
              <Lock className="h-3.5 w-3.5 text-sage" strokeWidth={1.5} />
              Consistency locked
            </div>
            <button aria-label="Play episode" className="absolute inset-0 grid place-items-center">
              <span className="grid h-16 w-16 place-items-center rounded-full bg-cream/95 text-ink transition-transform group-hover:scale-105">
                <Play className="h-6 w-6 translate-x-0.5" strokeWidth={1.5} fill="currentColor" />
              </span>
            </button>
            <div className="absolute bottom-5 left-5 right-5 flex items-center justify-between text-[12px] text-cream/70">
              <span className="tabular-nums">{ep.runtime}</span>
              <span>{ep.shots} shots</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-4">
          <div className="text-[11px] uppercase tracking-[0.22em] text-ink-soft">Shot list</div>
          <ul className="mt-3 divide-y divide-line rounded-2xl border border-line bg-cream">
            {shots.map((s, i) => (
              <li key={i} className="flex items-center gap-3 px-4 py-3">
                <span className="w-6 font-display text-[13px] tabular-nums text-sage">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span className="flex-1 truncate text-[13.5px] text-ink">{s}</span>
                <ChevronRight className="h-4 w-4 shrink-0 text-ink-soft" strokeWidth={1.5} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
