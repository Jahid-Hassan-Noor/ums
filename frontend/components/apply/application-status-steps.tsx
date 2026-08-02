const DEFAULT_STEPS = [
  "Programme Selection",
  "Personal Information",
  "Academic Information",
  "Scholarship Application",
  "Documents Upload",
  "Statement of Truth",
]

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

export function applicationStatusLabel(status: string | null | undefined) {
  if (!status) return "Not Started"
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
