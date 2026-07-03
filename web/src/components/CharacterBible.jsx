import { Lock, Hash, Users } from 'lucide-react'

export default function CharacterBible({ characters = [], styleName }) {
  return (
    <div>
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
        <span className="h-px w-6 bg-sage/50" />
        Story bible
      </div>

      {characters.length === 0 ? (
        <div className="mt-5 flex items-center gap-3 rounded-2xl border border-dashed border-line bg-cream/50 px-6 py-8 text-[13.5px] text-ink-soft">
          <Users className="h-4 w-4 shrink-0 text-sage" strokeWidth={1.5} />
          The cast and their locked seeds appear here after the first episode, then persist unchanged
          across every episode after it.
        </div>
      ) : (
        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {characters.map((c) => (
            <div key={`${c.name}-${c.seed}`} className="rounded-2xl border border-line bg-cream p-6">
              <div className="font-display text-[20px] leading-none text-ink">{c.name}</div>
              <p className="mt-4 text-[14px] leading-relaxed text-ink-soft">{c.descriptor}</p>
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
          {styleName && (
            <div className="rounded-2xl border border-ink bg-ink p-6 text-cream">
              <div className="text-[11px] uppercase tracking-[0.22em] text-cream/50">Visual canon</div>
              <div className="mt-4 font-display text-[22px] leading-tight">{styleName}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
