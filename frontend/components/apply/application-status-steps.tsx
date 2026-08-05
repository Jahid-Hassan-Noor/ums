const DEFAULT_STEPS = [
  "Programme Selection",
  "Personal Information",
  "Academic Information",
  "Scholarship Application",
  "Documents Upload",
  "Statement of Truth",
]

export type ApplicationStatusOption = {
  value: string
  label: string
  enabled?: boolean
}

export const applicationStatusLabels: Record<string, string> = {
  draft: "Draft",
  submitted: "Submitted",
  screening: "Screening",
  info_requested: "Information Requested",
  scholarship_review: "Scholarship Review",
  interview: "Interview",
  offered: "Offered",
  waitlisted: "Waitlisted",
  rejected: "Rejected",
  enrolled: "Enrolled",
  withdrawn: "Withdrawn",
}

export function applicationStatusLabel(
  status: string | null | undefined,
  options?: ApplicationStatusOption[]
) {
  if (!status) return "Not Started"
  const configured = options?.find((option) => option.value === status)
  if (configured) return configured.label
  return applicationStatusLabels[status] ?? status
}

export function ApplicationStatusSteps({
  steps = DEFAULT_STEPS,
}: {
  steps?: string[]
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {steps.map((step, index) => (
        <div
          key={step}
          className="rounded-lg border border-border bg-muted/30 p-3"
        >
          <p className="text-xs font-bold text-teal-700 dark:text-teal-300">
            Step {index + 1}
          </p>
          <p className="mt-1 text-sm font-medium">{step}</p>
        </div>
      ))}
    </div>
  )
}
