import { PenLine, Camera, Clapperboard, ScanEye, Scissors, Check, TriangleAlert } from 'lucide-react'

const STEPS = [
  { id: 'writer', label: 'Writer', icon: PenLine, note: 'script + cast' },
  { id: 'cinematographer', label: 'Cinematographer', icon: Camera, note: 'framing + motion' },
  { id: 'generator', label: 'Generator', icon: Clapperboard, note: 'render, fix drift' },
  { id: 'qc', label: 'QC Critic', icon: ScanEye, note: 'consistency check' },
  { id: 'editor', label: 'Editor', icon: Scissors, note: 'title + voice + cut' },
]

// Which agent row a reported stage belongs to. The engine reports data; the voice lives here.
const AGENT_FOR = { writer: 'writer', casting: 'generator', framing: 'cinematographer', title: 'editor', stitch: 'editor' }

function activeAgent(p) {
  if (!p) return null
  if (p.stage === 'shot') return p.phase === 'check' ? 'qc' : 'generator'
  return AGENT_FOR[p.stage] || null
}

function nowLine(p) {
  if (!p) return 'Warming up the engine'
  switch (p.stage) {
    case 'writer':
      return 'Writing the script, casting the leads'
    case 'casting':
      return p.character ? `Reference portrait · ${p.character}` : 'Painting reference portraits'
    case 'framing':
      return 'Framing every shot'
    case 'title':
      return 'Naming the episode'
    case 'stitch':
      return 'Stitching the final cut'
    case 'shot': {
      const where = `Shot ${p.shot} of ${p.total}`
      if (p.phase === 'check') return `${where} · critic checks it against the Bible`
      if (p.phase === 'rerender') return `${where} · drift caught, re-rolling`
      if (p.phase === 'animate') return `${where} · animating motion`
      return `${where} · rendering the still`
    }
    default:
      return 'Working'
  }
}

function subLine(p) {
  if (p?.stage === 'shot' && p.phase === 'animate')
    return 'Video is the slow part, a minute or two per shot. Nothing is stuck.'
  if (p?.stage === 'shot' && p.phase === 'rerender')
    return 'The critic flagged an inconsistency; the Generator fixes it before moving on.'
  if (p?.stage === 'casting') return 'Locking each face before a single shot is rendered.'
  return 'Live from the engine, each step reports as it happens.'
}

// Rough completion for the hairline bar. Shots dominate wall-clock, so early stages sit at 4%.
const PHASE_FRAC = { render: 0.15, check: 0.35, rerender: 0.4, animate: 0.55 }
function fraction(p) {
  if (!p) return null
  if (p.stage === 'shot' && p.total) {
    const slice = 1 / p.total
    return (p.shot - 1) * slice + slice * (PHASE_FRAC[p.phase] ?? 0.1)
  }
  if (p.stage === 'stitch') return 0.97
  return null // indeterminate: writer / casting / framing / title
}

function etaLabel(p, elapsed) {
  // Only once at least one full shot is behind us; hedged wording, it is a pace not a promise.
  if (p?.stage !== 'shot' || !p.total || p.shot <= 1 || elapsed < 10) return null
  const perShot = elapsed / (p.shot - 1)
  const mins = Math.round((perShot * (p.total - p.shot + 1)) / 60)
  return mins < 1 ? 'under a minute left at this pace' : `about ${mins} min left at this pace`
}

const fmtClock = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

export default function PipelinePanel({ status = 'idle', error = '', progress = null, elapsed = 0 }) {
  const running = status === 'running'
  const label = running ? `working · ${fmtClock(elapsed)}` : status === 'done' ? 'complete' : 'ready'
  const active = running ? activeAgent(progress) : null
  const frac = fraction(progress)
  const eta = etaLabel(progress, elapsed)

  return (
    <div className="h-full rounded-2xl border border-line bg-cream p-6 md:p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-sage">
          <span className="h-px w-6 bg-sage/50" />
          Agents
        </div>
        <span className="text-[12px] tabular-nums text-ink-soft">{label}</span>
      </div>

      <ul className="mt-6 space-y-1">
        {STEPS.map((s, i) => {
          const Icon = s.icon
          const isActive = active === s.id
          const state = status === 'done' ? 'done' : isActive ? 'running' : 'idle'
          return (
            <li
              key={s.id}
              className={`flex items-center gap-4 rounded-xl px-3 py-3.5 transition-colors duration-500 ${
                isActive ? 'bg-sage-soft' : 'hover:bg-bone/60'
              }`}
            >
              <div
                className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border transition-colors duration-500 ${
                  isActive ? 'border-sage/40 bg-cream' : 'border-line bg-bone'
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
              {state === 'done' ? (
                <Check className="h-4 w-4 text-sage" strokeWidth={2} />
              ) : state === 'running' ? (
                <span className="breathe h-2 w-2 rounded-full bg-sage" />
              ) : (
                <span className="h-2 w-2 rounded-full border border-line" />
              )}
            </li>
          )
        })}
      </ul>

      {status === 'error' ? (
        <div className="mt-6 flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[12.5px] text-red-700">
          <TriangleAlert className="h-4 w-4 shrink-0" strokeWidth={1.5} />
          {error || 'Something went wrong. Is the engine running on :8000?'}
        </div>
      ) : running ? (
        <div className="mt-6 rounded-xl border border-sage/30 bg-bone/50 px-4 py-3.5">
          <div className="font-display text-[15.5px] leading-snug text-ink">{nowLine(progress)}</div>
          <div className="mt-1 text-[12px] leading-snug text-ink-soft">
            {subLine(progress)}
            {eta && <span> · {eta}</span>}
          </div>
          <div className="relative mt-3 h-1 overflow-hidden rounded-full bg-line/70">
            {frac === null ? (
              <span className="drift absolute inset-y-0 left-0 w-1/4 rounded-full bg-sage/70" />
            ) : (
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-sage transition-all duration-700 ease-out"
                style={{ width: `${Math.max(2, Math.round(frac * 100))}%` }}
              />
            )}
          </div>
        </div>
      ) : (
        <div className="mt-6 flex items-center gap-2.5 rounded-xl border border-line bg-bone/50 px-4 py-3 text-[12.5px] leading-snug text-ink-soft">
          <ScanEye className="h-4 w-4 shrink-0 text-sage" strokeWidth={1.5} />
          Consistency enforced across episodes: the critic re-rolls any shot that drifts.
        </div>
      )}
    </div>
  )
}
