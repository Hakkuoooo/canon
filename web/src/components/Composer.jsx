import { useState } from 'react'
import { Sparkles, ArrowRight, Hash, Film, Loader } from 'lucide-react'

const STYLES = ['Flat Anime', 'Ink Wash', 'Cel Noir', 'Storybook']
const LENGTHS = [
  { label: 'Short', n: 3 },
  { label: 'Standard', n: 6 },
  { label: 'Long', n: 9 },
]

export default function Composer({ onGenerate, status }) {
  const [premise, setPremise] = useState(
    'Two estranged siblings inherit a locked vault, and the only key is a memory neither of them trusts.',
  )
  const [active, setActive] = useState('Flat Anime')
  const [shots, setShots] = useState(6)
  const busy = status === 'running'

  return (
    <div className="rounded-2xl border border-line bg-cream p-6 shadow-[0_1px_0_rgba(0,0,0,0.02),0_24px_48px_-36px_rgba(38,32,25,0.4)] md:p-8">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
        <span className="h-px w-6 bg-sage/50" />
        Premise
      </div>

      <textarea
        value={premise}
        onChange={(e) => setPremise(e.target.value)}
        rows={4}
        placeholder="Describe the story you want to serialize…"
        className="mt-4 w-full resize-none bg-transparent font-display text-[26px] leading-[1.28] tracking-[-0.01em] text-ink placeholder:text-ink-soft/50 focus:outline-none md:text-[30px]"
      />

      <div className="mt-6 h-px w-full bg-line" />

      <div className="mt-6">
        <div className="text-[11px] uppercase tracking-[0.22em] text-ink-soft">Visual style</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {STYLES.map((s) => (
            <button
              key={s}
              onClick={() => setActive(s)}
              className={`rounded-full px-4 py-2 text-[13px] transition-all ${
                active === s
                  ? 'bg-ink text-cream'
                  : 'border border-line text-ink-soft hover:border-ink/30 hover:text-ink'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <div className="text-[11px] uppercase tracking-[0.22em] text-ink-soft">Length</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {LENGTHS.map((l) => (
            <button
              key={l.n}
              onClick={() => setShots(l.n)}
              className={`rounded-full px-4 py-2 text-[13px] transition-all ${
                shots === l.n
                  ? 'bg-ink text-cream'
                  : 'border border-line text-ink-soft hover:border-ink/30 hover:text-ink'
              }`}
            >
              {l.label} · {l.n}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4 text-[12px] text-ink-soft">
          <span className="flex items-center gap-1.5">
            <Hash className="h-3.5 w-3.5" strokeWidth={1.5} />
            seed locked
          </span>
          <span className="flex items-center gap-1.5">
            <Film className="h-3.5 w-3.5" strokeWidth={1.5} />
            {shots} shots
          </span>
        </div>
        <button
          onClick={() => onGenerate?.(premise, active, shots)}
          disabled={busy || !premise.trim()}
          className="group inline-flex items-center justify-center gap-2 rounded-full bg-ink px-6 py-3 text-[14px] font-medium text-cream transition-transform active:scale-[0.98] disabled:opacity-50"
        >
          {busy ? (
            <Loader className="h-4 w-4 animate-spin text-sage" strokeWidth={1.5} />
          ) : (
            <Sparkles className="h-4 w-4 text-sage" strokeWidth={1.5} />
          )}
          {busy ? 'Generating…' : 'Generate episode'}
          {!busy && (
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" strokeWidth={1.5} />
          )}
        </button>
      </div>
    </div>
  )
}
