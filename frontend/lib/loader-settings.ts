export const DEFAULT_UMS_LOADER_SPINNER = "dna"
export const DEFAULT_UMS_LOADER_SIZE = 80
export const MIN_UMS_LOADER_SIZE = 32
export const MAX_UMS_LOADER_SIZE = 160

export const UMS_LOADER_SPINNER_OPTIONS = [
  { value: "audio", label: "Audio" },
  { value: "ball-triangle", label: "Ball Triangle" },
  { value: "bars", label: "Bars" },
  { value: "blocks", label: "Blocks" },
  { value: "circles-with-bar", label: "Circles With Bar" },
  { value: "circles", label: "Circles" },
  { value: "circular-progress", label: "Circular Progress" },
  { value: "color-ring", label: "Color Ring" },
  { value: "comment", label: "Comment" },
  { value: "discuss", label: "Discuss" },
  { value: "dna", label: "DNA" },
  { value: "falling-lines", label: "Falling Lines" },
  { value: "fidget-spinner", label: "Fidget Spinner" },
  { value: "grid", label: "Grid" },
  { value: "hearts", label: "Hearts" },
  { value: "hourglass", label: "Hourglass" },
  { value: "infinity-spin", label: "Infinity Spin" },
  { value: "line-wave", label: "Line Wave" },
  { value: "magnifying-glass", label: "Magnifying Glass" },
  { value: "mutating-dots", label: "Mutating Dots" },
  { value: "oval", label: "Oval" },
  { value: "progress-bar", label: "Progress Bar" },
  { value: "puff", label: "Puff" },
  { value: "radio", label: "Radio" },
  { value: "revolving-dot", label: "Revolving Dot" },
  { value: "rings", label: "Rings" },
  { value: "rotating-lines", label: "Rotating Lines" },
  { value: "rotating-square", label: "Rotating Square" },
  { value: "rotating-triangles", label: "Rotating Triangles" },
  { value: "tail-spin", label: "Tail Spin" },
  { value: "three-circles", label: "Three Circles" },
  { value: "three-dots", label: "Three Dots" },
  { value: "triangle", label: "Triangle" },
  { value: "vortex", label: "Vortex" },
  { value: "watch", label: "Watch" },
] as const

export type UmsLoaderSpinner =
  (typeof UMS_LOADER_SPINNER_OPTIONS)[number]["value"]

const UMS_LOADER_VALUES = new Set<string>(
  UMS_LOADER_SPINNER_OPTIONS.map((option) => option.value)
)

export function normalizeUmsLoaderSpinner(value: unknown): UmsLoaderSpinner {
  if (typeof value === "string" && UMS_LOADER_VALUES.has(value)) {
    return value as UmsLoaderSpinner
  }
  return DEFAULT_UMS_LOADER_SPINNER
}

export function normalizeUmsLoaderSize(value: unknown): number {
  const numericValue = typeof value === "number" ? value : Number(value)
  if (!Number.isFinite(numericValue)) return DEFAULT_UMS_LOADER_SIZE
  return Math.min(
    MAX_UMS_LOADER_SIZE,
    Math.max(MIN_UMS_LOADER_SIZE, Math.round(numericValue))
  )
}
