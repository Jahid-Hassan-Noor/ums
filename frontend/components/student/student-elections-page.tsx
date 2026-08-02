"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Send,
  Trophy,
  Vote,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"
import {
  formatDateTime,
  formatDuration,
  secondsUntil,
  statusTone,
  titleCase,
  type ElectionBallot,
  type ElectionCandidate,
  type ElectionCategory,
  type ElectionRecord,
  type ElectionResultGroup,
} from "@/lib/elections"

type StudentElectionsResponse = {
  school: {
    id: number | null
    code: string
    name: string
  }
  elections: ElectionRecord[]
}

type SelectionState = Record<string, number[]>

function selectionKey(electionId: number, category: ElectionCategory) {
  return `${electionId}:${category}`
}

function resultWidth(candidate: ElectionCandidate, group: ElectionResultGroup) {
  const maxVotes = Math.max(1, ...group.candidates.map((row) => row.vote_count))
  return `${Math.max(4, (candidate.vote_count / maxVotes) * 100)}%`
}

function ResultGroup({ group }: { group: ElectionResultGroup }) {
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-semibold">{group.label}</h3>
          <p className="text-sm text-muted-foreground">{group.total_votes} total votes</p>
        </div>
        <Badge variant="outline">{titleCase(group.category)}</Badge>
      </div>
      <div className="mt-4 space-y-3">
        {group.candidates.length ? (
          group.candidates.map((candidate, index) => (
            <div key={candidate.id} className="space-y-1.5">
              <div className="flex items-center justify-between gap-3 text-sm">
                <div className="min-w-0">
                  <p className="truncate font-medium">
                    {index === 0 ? <Trophy className="mr-1 inline size-4 text-amber-500" /> : null}
                    {candidate.display_name}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {[candidate.student_identifier, candidate.school_detail?.code].filter(Boolean).join(" / ") || "Candidate"}
                  </p>
                </div>
                <span className="shrink-0 font-semibold">{candidate.vote_count}</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div className="h-2 rounded-full bg-primary" style={{ width: resultWidth(candidate, group) }} />
              </div>
            </div>
          ))
        ) : (
          <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
            No candidates in this result group.
          </p>
        )}
      </div>
    </div>
  )
}

function BallotSection({
  election,
  ballot,
  selectedIds,
  isSubmitting,
  onToggle,
  onSubmit,
}: {
  election: ElectionRecord
  ballot: ElectionBallot
  selectedIds: number[]
  isSubmitting: boolean
  onToggle: (candidateId: number) => void
  onSubmit: () => void
}) {
  const requiredCount = ballot.required_count
  const canSubmit =
    election.can_vote &&
    !ballot.submitted &&
    selectedIds.length === requiredCount &&
    requiredCount > 0

  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="font-semibold">{ballot.label}</h3>
          <p className="text-sm text-muted-foreground">
            {ballot.submitted
              ? `${ballot.selected_candidate_ids.length} selections submitted`
              : `${selectedIds.length} of ${requiredCount} selected`}
          </p>
        </div>
        {ballot.submitted ? (
          <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700" variant="outline">
            Submitted
          </Badge>
        ) : null}
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {ballot.candidates.map((candidate) => {
          const checked = selectedIds.includes(candidate.id)
          const locked = ballot.submitted || !election.can_vote
          return (
            <label
              key={candidate.id}
              className={`flex min-h-28 gap-3 rounded-lg border p-3 text-sm transition ${
                checked ? "border-primary bg-primary/5" : "border-border bg-card"
              } ${locked ? "opacity-80" : "hover:bg-muted/40"}`}
            >
              <input
                type="checkbox"
                className="mt-1 size-4 shrink-0"
                checked={checked}
                disabled={locked}
                onChange={() => onToggle(candidate.id)}
              />
              <span className="min-w-0 space-y-1">
                <span className="block font-medium">{candidate.display_name}</span>
                <span className="block text-xs text-muted-foreground">
                  {[candidate.student_identifier, candidate.school_detail?.code].filter(Boolean).join(" / ") || "Candidate"}
                </span>
                {candidate.details ? (
                  <span className="line-clamp-2 block text-xs leading-5 text-muted-foreground">
                    {candidate.details}
                  </span>
                ) : null}
                {candidate.manifesto ? (
                  <span className="line-clamp-2 block text-xs leading-5 text-muted-foreground">
                    {candidate.manifesto}
                  </span>
                ) : null}
              </span>
            </label>
          )
        })}
      </div>
      {!ballot.candidates.length ? (
        <p className="mt-4 rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
          No candidates available for this ballot.
        </p>
      ) : null}
      <div className="mt-4 flex justify-end">
        <Button onClick={onSubmit} disabled={!canSubmit || isSubmitting}>
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          Submit Ballot
        </Button>
      </div>
    </div>
  )
}

export function StudentElectionsPage() {
  const [school, setSchool] = useState<StudentElectionsResponse["school"]>({
    id: null,
    code: "",
    name: "",
  })
  const [elections, setElections] = useState<ElectionRecord[]>([])
  const [selectedElectionId, setSelectedElectionId] = useState("")
  const [selections, setSelections] = useState<SelectionState>({})
  const [isLoading, setIsLoading] = useState(true)
  const [submittingKey, setSubmittingKey] = useState("")
  const [now, setNow] = useState(0)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    const data = await apiFetch<StudentElectionsResponse>("/student/elections")
    setSchool(
      data.school ?? {
        id: null,
        code: "",
        name: "",
      }
    )
    setElections(data.elections ?? [])
    setSelectedElectionId((current) => current || (data.elections?.[0] ? String(data.elections[0].id) : ""))
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load elections."))
        .finally(() => setIsLoading(false))
      setNow(Date.now())
    }, 0)

    const poll = window.setInterval(() => {
      void loadData().catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to refresh elections."))
    }, 10_000)
    const clock = window.setInterval(() => setNow(Date.now()), 1_000)

    return () => {
      window.clearTimeout(timer)
      window.clearInterval(poll)
      window.clearInterval(clock)
    }
  }, [])

  const selectedElection = useMemo(
    () => elections.find((election) => String(election.id) === selectedElectionId) ?? elections[0] ?? null,
    [elections, selectedElectionId]
  )

  function countdownText(election: ElectionRecord) {
    const target = election.countdown?.target_at
    const seconds = now ? secondsUntil(target, now) : election.countdown?.seconds_remaining ?? 0
    if (!seconds) return election.countdown?.label ?? titleCase(election.computed_status)
    return `${election.countdown.label} ${formatDuration(seconds)}`
  }

  function selectedFor(ballot: ElectionBallot, electionId: number) {
    const key = selectionKey(electionId, ballot.category)
    return ballot.submitted ? ballot.selected_candidate_ids : selections[key] ?? []
  }

  function toggleCandidate(electionId: number, ballot: ElectionBallot, candidateId: number) {
    if (ballot.submitted) return
    setError("")
    const key = selectionKey(electionId, ballot.category)
    setSelections((current) => {
      const selected = current[key] ?? []
      if (selected.includes(candidateId)) {
        return { ...current, [key]: selected.filter((id) => id !== candidateId) }
      }
      if (selected.length >= ballot.required_count) {
        setError(`Select exactly ${ballot.required_count} candidate${ballot.required_count === 1 ? "" : "s"} for ${ballot.label}.`)
        return current
      }
      return { ...current, [key]: [...selected, candidateId] }
    })
  }

  async function submitBallot(election: ElectionRecord, ballot: ElectionBallot) {
    const key = selectionKey(election.id, ballot.category)
    const selectedIds = selections[key] ?? []
    setSubmittingKey(key)
    setError("")
    setSuccess("")
    try {
      await apiFetch<{ message: string }>(`/student/elections/${election.id}/vote`, {
        method: "POST",
        body: JSON.stringify({
          category: ballot.category,
          candidate_ids: selectedIds,
        }),
      })
      setSelections((current) => ({ ...current, [key]: [] }))
      setSuccess(`${ballot.label} submitted successfully.`)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit ballot.")
    } finally {
      setSubmittingKey("")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/elections", title: "Elections" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Elections</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {school.name ? `${school.name} ballot access and live vote counts.` : "Student ballot access and live vote counts."}
            </p>
          </div>
          <Button variant="outline" onClick={() => void loadData()} disabled={isLoading}>
            <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{success}</p>
          </div>
        ) : null}

        <section className="grid gap-4 lg:grid-cols-[20rem_minmax(0,1fr)]">
          <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Available Elections</CardTitle>
              <CardDescription>{elections.length} visible ballots</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="size-7 animate-spin text-muted-foreground" />
                </div>
              ) : elections.length ? (
                <div className="space-y-2">
                  {elections.map((election) => (
                    <button
                      key={election.id}
                      type="button"
                      className={`w-full rounded-lg border p-3 text-left text-sm transition ${
                        selectedElection?.id === election.id
                          ? "border-primary bg-primary/5"
                          : "border-border bg-background hover:bg-muted/40"
                      }`}
                      onClick={() => setSelectedElectionId(String(election.id))}
                    >
                      <span className="block font-medium">{election.title}</span>
                      <span className="mt-1 block text-xs text-muted-foreground">
                        {election.election_type_label}
                      </span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                  No elections are available.
                </p>
              )}
            </CardContent>
          </Card>

          <div className="space-y-4">
            {selectedElection ? (
              <>
                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardHeader>
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <CardTitle className="text-xl">{selectedElection.title}</CardTitle>
                          <Badge className={statusTone(selectedElection.computed_status)} variant="outline">
                            {titleCase(selectedElection.computed_status)}
                          </Badge>
                          <Badge variant="outline">{selectedElection.election_type_label}</Badge>
                        </div>
                        {selectedElection.description ? (
                          <CardDescription>{selectedElection.description}</CardDescription>
                        ) : null}
                      </div>
                      <div className="rounded-lg border border-border bg-background px-3 py-2 text-sm">
                        <p className="flex items-center gap-2 font-medium">
                          <CalendarClock className="size-4 text-muted-foreground" />
                          {countdownText(selectedElection)}
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="grid gap-3 text-sm md:grid-cols-3">
                    <div>
                      <p className="text-xs font-medium uppercase text-muted-foreground">Starts</p>
                      <p className="mt-1">{formatDateTime(selectedElection.starts_at)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase text-muted-foreground">Ends</p>
                      <p className="mt-1">{formatDateTime(selectedElection.ends_at)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium uppercase text-muted-foreground">Scope</p>
                      <p className="mt-1">{selectedElection.school_detail?.name ?? "All schools"}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                        <Vote className="size-5" />
                      </span>
                      <div>
                        <CardTitle className="text-lg">Ballots</CardTitle>
                        <CardDescription>{selectedElection.ballots?.length ?? 0} voting sections</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {selectedElection.ballots?.length ? (
                      selectedElection.ballots.map((ballot) => {
                        const key = selectionKey(selectedElection.id, ballot.category)
                        return (
                          <BallotSection
                            key={key}
                            election={selectedElection}
                            ballot={ballot}
                            selectedIds={selectedFor(ballot, selectedElection.id)}
                            isSubmitting={submittingKey === key}
                            onToggle={(candidateId) => toggleCandidate(selectedElection.id, ballot, candidateId)}
                            onSubmit={() => void submitBallot(selectedElection, ballot)}
                          />
                        )
                      })
                    ) : (
                      <p className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
                        No ballots are available for this election.
                      </p>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-lg">Live Results</CardTitle>
                    <CardDescription>{selectedElection.results?.length ?? 0} result groups</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {selectedElection.results?.length ? (
                      selectedElection.results.map((group) => (
                        <ResultGroup key={`${group.label}-${group.category}`} group={group} />
                      ))
                    ) : (
                      <p className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
                        No live results are available.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardContent className="p-8 text-center text-sm text-muted-foreground">
                  Select an election to continue.
                </CardContent>
              </Card>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
