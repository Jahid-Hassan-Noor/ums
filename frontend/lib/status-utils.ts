export type BadgeVariant =
  | "default"
  | "secondary"
  | "destructive"
  | "outline"
  | "ghost"
  | "link"

const SUCCESS_STATUSES = new Set([
  "accepted",
  "active",
  "addressed",
  "approved",
  "completed",
  "deducted",
  "enrolled",
  "graded",
  "paid",
  "passed",
  "published",
  "resolved",
  "solved",
  "submitted",
  "verified",
])

const WARNING_STATUSES = new Set([
  "draft",
  "in_progress",
  "info_requested",
  "interview",
  "not_started",
  "pending",
  "processing",
  "review",
  "running",
  "screening",
  "scholarship_review",
  "submitted_late",
  "upcoming",
  "waitlisted",
])

const DANGER_STATUSES = new Set([
  "banned",
  "dropped",
  "failed",
  "inactive",
  "overdue",
  "rejected",
  "revoked",
  "withdrawn",
])

export function normalizeStatus(status: string | null | undefined) {
  return String(status ?? "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
}

export function statusBadgeVariant(
  status: string | null | undefined
): BadgeVariant {
  const normalized = normalizeStatus(status)
  if (DANGER_STATUSES.has(normalized)) return "destructive"
  if (SUCCESS_STATUSES.has(normalized)) return "default"
  if (WARNING_STATUSES.has(normalized)) return "secondary"
  return "outline"
}

export function statusClassName(status: string | null | undefined): string {
  const normalized = normalizeStatus(status)
  if (DANGER_STATUSES.has(normalized)) {
    return "border-red-200 bg-red-50 text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200"
  }
  if (SUCCESS_STATUSES.has(normalized)) {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
  }
  if (WARNING_STATUSES.has(normalized)) {
    return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200"
  }
  return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-500/40 dark:bg-slate-500/10 dark:text-slate-200"
}
