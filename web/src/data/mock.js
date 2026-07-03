// Mock data. Swapped for the real pipeline (canon/pipeline.py) behind a thin API later.

export const style = { name: "Flat Anime", note: "soft cel shading · muted palette" }

export const characters = [
  {
    name: "Mara",
    role: "The fixer",
    descriptor: "crimson field jacket, cropped black hair, single jade earring",
    seed: 40719,
    swatch: "#8c3b34",
  },
  {
    name: "Iven",
    role: "The archivist",
    descriptor: "ash-grey overcoat, wire spectacles, silver stubble",
    seed: 20884,
    swatch: "#6b6e74",
  },
]

export const pipeline = [
  { id: "writer", label: "Writer", note: "6 scenes · 940 words", state: "done" },
  { id: "cinematographer", label: "Cinematographer", note: "6 shots framed", state: "done" },
  { id: "generator", label: "Generator", note: "shot 4 of 6", state: "running" },
  { id: "qc", label: "QC Critic", note: "caught 1 drift · regenerated", state: "flag" },
  { id: "editor", label: "Editor", note: "voice · subtitles · final cut", state: "idle" },
]

export const episodes = [
  { id: 1, title: "The Vault", runtime: "1:04", shots: 6 },
  { id: 2, title: "The Ledger", runtime: "1:11", shots: 6 },
]

export const shots = [
  "Cold open — rain on the vault door",
  "Mara forces the mechanism",
  "Iven reads the ledger aloud",
  "The memory, in flashback",
  "The argument breaks",
  "The door swings — cut to black",
]
