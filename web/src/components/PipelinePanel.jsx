import { PenLine, Camera, Clapperboard, ScanEye, Scissors, Check, TriangleAlert } from 'lucide-react'
import { pipeline } from '../data/mock.js'

const ICONS = {
  writer: PenLine,
  cinematographer: Camera,
  generator: Clapperboard,
  qc: ScanEye,
  editor: Scissors,
}

function Status({ state }) {
  if (state === 'done') return <Check className="h-4 w-4 text-sage" strokeWidth={2} />
  if (state === 'running') return <span className="breathe h-2 w-2 rounded-full bg-sage" />
  if (state === 'flag') return <TriangleAlert className="h-4 w-4 text-sage" strokeWidth={1.5} />
  return <span className="h-2 w-2 rounded-full border border-line" />
}

export default function PipelinePanel() {
  return (
    <div className="h-full rounded-2xl border border-line bg-cream p-6 md:p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
          <span className="h-px w-6 bg-sage/50" />
          Agents
        </div>
        <span className="text-[12px] text-ink-soft">live</span>
      </div>

      <ul className="mt-6 space-y-1">
        {pipeline.map((step, i) => {
          const Icon = ICONS[step.id]
          const activeRow = step.state === 'running' || step.state === 'flag'
          return (
            <li
              key={step.id}
              className={`flex items-center gap-4 rounded-xl px-3 py-3.5 transition-colors ${
                activeRow ? 'bg-sage-soft' : 'hover:bg-bone/60'
              }`}
            >
              <div
                className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border ${
                  activeRow ? 'border-sage/40 bg-cream' : 'border-line bg-bone'
                }`}
              >
                <Icon className="h-4 w-4 text-ink" strokeWidth={1.5} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-display text-[16px] text-ink">{step.label}</span>
                  <span className="text-[11px] tabular-nums text-ink-soft">0{i + 1}</span>
                </div>
                <div className="mt-0.5 truncate text-[12.5px] text-ink-soft">{step.note}</div>
              </div>
              <Status state={step.state} />
            </li>
          )
        })}
      </ul>

      <div className="mt-6 flex items-center gap-2.5 rounded-xl border border-line bg-bone/50 px-4 py-3 text-[12.5px] leading-snug text-ink-soft">
        <ScanEye className="h-4 w-4 shrink-0 text-sage" strokeWidth={1.5} />
        Consistency enforced across episodes — the critic re-rolls any shot that drifts.
      </div>
    </div>
  )
}
