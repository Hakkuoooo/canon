import { Aperture, Circle, Settings2 } from 'lucide-react'

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-bone/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-[1220px] items-center justify-between px-6 md:px-10">
        <div className="flex items-center gap-3">
          <Aperture className="h-5 w-5 text-ink" strokeWidth={1.5} />
          <span className="font-display text-[22px] leading-none tracking-tight text-ink">Canon</span>
          <span className="ml-2 hidden text-[11px] uppercase tracking-[0.22em] text-ink-soft sm:inline">
            Serial Drama Studio
          </span>
        </div>
        <div className="flex items-center gap-5">
          <span className="hidden items-center gap-2 text-[12px] text-ink-soft md:flex">
            <Circle className="breathe h-2 w-2 fill-sage text-sage" strokeWidth={0} />
            Model Studio · connected
          </span>
          <button
            aria-label="Settings"
            className="grid h-9 w-9 place-items-center rounded-full border border-line text-ink-soft transition-colors hover:border-ink/30 hover:text-ink"
          >
            <Settings2 className="h-4 w-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </header>
  )
}
