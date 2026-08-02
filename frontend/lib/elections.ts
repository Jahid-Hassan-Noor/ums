export type ElectionType = "src" | "school_committee"
export type ElectionStatus = "draft" | "upcoming" | "active" | "closed" | "published"
export type ElectionCategory = "general" | "school"

export type ElectionChoice = {
  value: string
  label: string
}

export type ElectionSchool = {
  id: number
  code: string
  name: string
  label?: string
}

export type ElectionStudent = {
  id: number
  name: string
  username: string
  student_id: string
  school: number | null
  school_code: string
  school_name: string
}

export type ElectionCandidate = {
  id: number
  election: number
  student: number | null
  student_detail?: ElectionStudent | null
  display_name: string
  student_identifier: string
  school: number | null
  school_detail?: ElectionSchool | null
  category: ElectionCategory
  category_label: string
  details: string
  manifesto: string
  photo_url: string
  status: string
  status_label: string
  sort_order: number
  vote_count: number
}

export type ElectionResultGroup = {
  label: string
  category: ElectionCategory
  total_votes: number
  candidates: ElectionCandidate[]
}

export type ElectionBallot = {
  category: ElectionCategory
  label: string
  required_count: number
  submitted: boolean
  selected_candidate_ids: number[]
  candidates: ElectionCandidate[]
}

export type SchoolSeat = {
  school_id: number
  school_code: string
  school_name: string
  seat_count: number
}

export type ElectionRecord = {
  id: number
  title: string
  description: string
  election_type: ElectionType
  election_type_label: string
  school: number | null
  school_detail: ElectionSchool | null
  starts_at: string | null
  ends_at: string | null
  general_selection_count: number
  school_selection_count: number
  school_seats: SchoolSeat[]
  status: ElectionStatus
  computed_status: ElectionStatus
  is_active: boolean
  results_published_at: string | null
  candidate_count: number | null
  vote_count: number | null
  countdown: {
    label: string
    target_at: string | null
    seconds_remaining: number
  }
  ballots?: ElectionBallot[]
  results?: ElectionResultGroup[]
  can_vote?: boolean
}

export const selectClass =
  "h-8 w-full rounded-lg border border-input bg-background px-2.5 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

export function formatDateTime(value: string | null) {
  if (!value) return "Not scheduled"
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

export function toDateTimeLocal(value: string | null) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  const offset = date.getTimezoneOffset()
  const local = new Date(date.getTime() - offset * 60_000)
  return local.toISOString().slice(0, 16)
}

export function formatDuration(totalSeconds: number) {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds))
  const days = Math.floor(safeSeconds / 86_400)
  const hours = Math.floor((safeSeconds % 86_400) / 3_600)
  const minutes = Math.floor((safeSeconds % 3_600) / 60)
  const seconds = safeSeconds % 60
  const parts = [
    days ? `${days}d` : "",
    days || hours ? `${hours}h` : "",
    days || hours || minutes ? `${minutes}m` : "",
    `${seconds}s`,
  ].filter(Boolean)
  return parts.join(" ")
}

export function secondsUntil(value: string | null, now: number) {
  if (!value) return 0
  return Math.max(0, Math.floor((new Date(value).getTime() - now) / 1000))
}

export function statusTone(status: ElectionStatus) {
  if (status === "active") return "border-emerald-200 bg-emerald-50 text-emerald-700"
  if (status === "upcoming") return "border-sky-200 bg-sky-50 text-sky-700"
  if (status === "published") return "border-violet-200 bg-violet-50 text-violet-700"
  if (status === "closed") return "border-zinc-200 bg-zinc-50 text-zinc-700"
  return "border-amber-200 bg-amber-50 text-amber-700"
}

export function titleCase(value: string) {
  return value
    .replace(/_/g, " ")
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}
