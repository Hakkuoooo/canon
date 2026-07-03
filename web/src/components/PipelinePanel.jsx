import { PenLine, Camera, Clapperboard, ScanEye, Scissors, Check, TriangleAlert } from 'lucide-react'

const STEPS = [
  { id: 'writer', label: 'Writer', icon: PenLine, note: 'script + cast' },
  { id: 'cinematographer', label: 'Cinematographer', icon: Camera, note: 'shot list' },
  { id: 'generator', label: 'Generator', icon: Clapperboard, note: 'frames + motion' },
  { id: 'qc', label: 'QC Critic', icon: ScanEye, note: 'consistency check' },
  { id: 'editor', label: 'Editor', icon: Scissors, note: 'voice + final cut' },
]

function Dot({ state }) {
  if (state === 'done') return <Check className="h-4 w-4 text-sage" strokeWidth={2} />
  if (state === 'running') return <span className="breathe h-2 w-2 rounded-full bg-sage" />
  return <span className="h-2 w-2 rounded-full border border-line" />
}

export default function PipelinePanel({ status = 'idle', error = '' }) {
  const stepState = status === 'done' ? 'done' : status === 'running' ? 'running' : 'idle'
  const label = status === 'running' ? 'working' : status === 'done' ? 'complete' : 'ready'

  return (
    <div className="h-full rounded-2xl border border-line bg-cream p-6 md:p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
          <span className="h-px w-6 bg-sage/50" />
          Agents
        </div>
        <span className="text-[12px] text-ink-soft">{label}</span>
      </div>

      <ul className="mt-6 space-y-1">
        {STEPS.map((s, i) => {
          const Icon = s.icon
          const active = stepState === 'running'
          return (
            <li
              key={s.id}
              className={`flex items-center gap-4 rounded-xl px-3 py-3.5 transition-colors ${
                active ? 'bg-sage-soft' : 'hover:bg-bone/60'
              }`}
            >
              <div
                className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border ${
                  active ? 'border-sage/40 bg-cream' : 'border-line bg-bone'
                }`}
              >
                <Icon className="h-4 w-4 text-ink" strokeWidth={1.5} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-display text-[16px] text-ink">{s.label}</span>
                  <span className="text-[11px] tabular-nums text-ink-soft">0{i + 1}</span>
                </div>
                <div className="mt-0.5 truncate text-[12.5px] text-ink-soft">{s.note}</div>
              </div>
              <Dot state={stepState} />
            </li>
          )
        })}
      </ul>

      {status === 'error' ? (
        <div className="mt-6 flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[12.5px] text-red-700">
          <TriangleAlert className="h-4 w-4 shrink-0" strokeWidth={1.5} />
          {error || 'Something went wrong. Is the engine running on :8000?'}
        </div>
      ) : (
        <div className="mt-6 flex items-center gap-2.5 rounded-xl border border-line bg-bone/50 px-4 py-3 text-[12.5px] leading-snug text-ink-soft">
          <ScanEye className="h-4 w-4 shrink-0 text-sage" strokeWidth={1.5} />
          Consistency enforced across episodes — the critic re-rolls any shot that drifts.
        </div>
      )}
    </div>
  )
}
