"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Save,
  Trophy,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"
import {
  formatDateTime,
  selectClass,
  statusTone,
  titleCase,
  type ElectionRecord,
  type ElectionResultGroup,
} from "@/lib/elections"

type ResultsResponse = {
  elections: ElectionRecord[]
}

const ELECTION_RESULTS_API = "/ict-helpdesk/technician/elections/results"

function ResultGroup({ group }: { group: ElectionResultGroup }) {
  const maxVotes = Math.max(1, ...group.candidates.map((candidate) => candidate.vote_count))

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
          group.candidates.map((candidate, index) => {
            const width = `${Math.max(4, (candidate.vote_count / maxVotes) * 100)}%`
            return (
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
                  <div className="h-2 rounded-full bg-primary" style={{ width }} />
                </div>
              </div>
            )
          })
        ) : (
          <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
            No approved candidates in this group.
          </p>
        )}
      </div>
    </div>
  )
}

export function TechnicianElectionResultsPage() {
  const [elections, setElections] = useState<ElectionRecord[]>([])
  const [selectedElectionId, setSelectedElectionId] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    setError("")
    const data = await apiFetch<ResultsResponse>(ELECTION_RESULTS_API)
    setElections(data.elections ?? [])
    setSelectedElectionId((current) => current || (data.elections?.[0] ? String(data.elections[0].id) : ""))
    setLastUpdated(new Date())
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load election results."))
        .finally(() => setIsLoading(false))
    }, 0)

    const interval = window.setInterval(() => {
      void loadData().catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Unable to refresh election results.")
      })
    }, 10_000)

    return () => {
      window.clearTimeout(timer)
      window.clearInterval(interval)
    }
  }, [])

  const selectedElection = useMemo(
    () => elections.find((election) => String(election.id) === selectedElectionId) ?? elections[0] ?? null,
    [elections, selectedElectionId]
  )

  async function saveSnapshot() {
    if (!selectedElection) return
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch<{ message: string }>(ELECTION_RESULTS_API, {
        method: "POST",
        body: JSON.stringify({ election: selectedElection.id }),
      })
      setSuccess("Election results snapshot saved.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save results snapshot.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/technician", title: "Technician" },
          { href: "/technician/elections", title: "Elections" },
          { href: "/technician/elections/results", title: "Results" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Election Results</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Live vote counts grouped by election category and school scope.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => void loadData()} disabled={isLoading}>
              <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button onClick={() => void saveSnapshot()} disabled={!selectedElection || isSaving}>
              {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
              Snapshot
            </Button>
          </div>
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
              <CardTitle className="text-lg">Election</CardTitle>
              <CardDescription>
                {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Waiting for results"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <select
                className={selectClass}
                value={selectedElection ? String(selectedElection.id) : ""}
                onChange={(event) => setSelectedElectionId(event.target.value)}
              >
                {elections.map((election) => (
                  <option key={election.id} value={election.id}>
                    {election.title}
                  </option>
                ))}
              </select>
              {selectedElection ? (
                <div className="space-y-3 rounded-lg border border-border bg-background p-3 text-sm">
                  <div className="flex flex-wrap gap-2">
                    <Badge className={statusTone(selectedElection.computed_status)} variant="outline">
                      {titleCase(selectedElection.computed_status)}
                    </Badge>
                    <Badge variant="outline">{selectedElection.election_type_label}</Badge>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">School</p>
                    <p className="mt-1">{selectedElection.school_detail?.name ?? "All schools"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Voting Window</p>
                    <p className="mt-1">
                      {formatDateTime(selectedElection.starts_at)} to {formatDateTime(selectedElection.ends_at)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Votes</p>
                    <p className="mt-1">{selectedElection.vote_count ?? 0}</p>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-3">
                <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                  <BarChart3 className="size-5" />
                </span>
                <div>
                  <CardTitle className="text-lg">{selectedElection?.title ?? "Live Results"}</CardTitle>
                  <CardDescription>
                    {selectedElection?.results?.length ?? 0} result groups
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex h-64 items-center justify-center">
                  <Loader2 className="size-8 animate-spin text-muted-foreground" />
                </div>
              ) : selectedElection?.results?.length ? (
                <div className="space-y-4">
                  {selectedElection.results.map((group) => (
                    <ResultGroup key={`${group.label}-${group.category}`} group={group} />
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                  No result groups available.
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}
