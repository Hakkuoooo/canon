import { Lock, Hash } from 'lucide-react'
import { characters, style } from '../data/mock.js'

const PALETTE = ['#e7e2d6', '#8c3b34', '#6b6e74', '#74856a', '#262019']

export default function CharacterBible() {
  return (
    <div>
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
        <span className="h-px w-6 bg-sage/50" />
        Story bible
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {characters.map((c) => (
          <div key={c.name} className="rounded-2xl border border-line bg-cream p-6">
            <div className="flex items-center gap-4">
              <span
                className="h-11 w-11 rounded-full border border-line"
                style={{ backgroundColor: c.swatch }}
              />
              <div>
                <div className="font-display text-[20px] leading-none text-ink">{c.name}</div>
                <div className="mt-1.5 text-[11px] uppercase tracking-[0.18em] text-ink-soft">
                  {c.role}
                </div>
              </div>
            </div>
            <p className="mt-5 text-[14px] leading-relaxed text-ink-soft">{c.descriptor}</p>
            <div className="mt-5 flex items-center justify-between border-t border-line pt-4 text-[12px]">
              <span className="flex items-center gap-1.5 text-ink-soft">
                <Hash className="h-3.5 w-3.5" strokeWidth={1.5} />
                <span className="font-mono tabular-nums text-ink">{c.seed}</span>
              </span>
              <span className="flex items-center gap-1.5 text-sage">
                <Lock className="h-3.5 w-3.5" strokeWidth={1.5} />
                locked
              </span>
            </div>
          </div>
        ))}

        <div className="rounded-2xl border border-ink bg-ink p-6 text-cream">
          <div className="text-[11px] uppercase tracking-[0.22em] text-cream/50">Visual canon</div>
          <div className="mt-4 font-display text-[22px] leading-tight">{style.name}</div>
          <p className="mt-2 text-[13.5px] text-cream/70">{style.note}</p>
          <div className="mt-6 flex gap-2">
            {PALETTE.map((h) => (
              <span key={h} className="h-6 flex-1 rounded-md" style={{ backgroundColor: h }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
