"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  Edit3,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  X,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"
import {
  formatDateTime,
  formatDuration,
  selectClass,
  statusTone,
  titleCase,
  toDateTimeLocal,
  type ElectionChoice,
  type ElectionRecord,
  type ElectionSchool,
  type ElectionType,
} from "@/lib/elections"

type ElectionsResponse = {
  elections: ElectionRecord[]
  schools: ElectionSchool[]
  type_options: ElectionChoice[]
  status_options: ElectionChoice[]
  summary: {
    total: number
    active: number
    upcoming: number
    closed: number
  }
}

type ElectionForm = {
  title: string
  description: string
  election_type: ElectionType
  school: string
  starts_at: string
  ends_at: string
  general_selection_count: string
  school_selection_count: string
  school_seats: Record<string, string>
  status: string
  is_active: boolean
}

const emptyForm: ElectionForm = {
  title: "",
  description: "",
  election_type: "src",
  school: "",
  starts_at: "",
  ends_at: "",
  general_selection_count: "10",
  school_selection_count: "3",
  school_seats: {},
  status: "upcoming",
  is_active: true,
}

const ELECTIONS_API = "/ict-helpdesk/technician/elections"

function schoolSeatsFromRecord(election: ElectionRecord): Record<string, string> {
  const seats: Record<string, string> = {}
  if (election.school_seats) {
    for (const s of election.school_seats) {
      seats[String(s.school_id)] = String(s.seat_count)
    }
  }
  return seats
}

function formFromElection(election: ElectionRecord): ElectionForm {
  return {
    title: election.title,
    description: election.description,
    election_type: election.election_type,
    school: election.school ? String(election.school) : "",
    starts_at: toDateTimeLocal(election.starts_at),
    ends_at: toDateTimeLocal(election.ends_at),
    general_selection_count: String(election.general_selection_count ?? 0),
    school_selection_count: String(election.school_selection_count ?? 0),
    school_seats: schoolSeatsFromRecord(election),
    status: election.status,
    is_active: election.is_active,
  }
}

function countdownText(election: ElectionRecord) {
  const seconds = election.countdown?.seconds_remaining ?? 0
  if (!seconds) return election.countdown?.label ?? titleCase(election.computed_status)
  return `${election.countdown.label} ${formatDuration(seconds)}`
}

function initSchoolSeatsSeats(schools: ElectionSchool[], existing?: Record<string, string>): Record<string, string> {
  const seats: Record<string, string> = {}
  for (const school of schools) {
    seats[String(school.id)] = existing?.[String(school.id)] ?? "0"
  }
  return seats
}

export function TechnicianElectionsPage() {
  const [elections, setElections] = useState<ElectionRecord[]>([])
  const [schools, setSchools] = useState<ElectionSchool[]>([])
  const [typeOptions, setTypeOptions] = useState<ElectionChoice[]>([])
  const [statusOptions, setStatusOptions] = useState<ElectionChoice[]>([])
  const [summary, setSummary] = useState<ElectionsResponse["summary"]>({
    total: 0,
    active: 0,
    upcoming: 0,
    closed: 0,
  })
  const [form, setForm] = useState<ElectionForm>(emptyForm)
  const [editingElection, setEditingElection] = useState<ElectionRecord | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    setError("")
    const data = await apiFetch<ElectionsResponse>(ELECTIONS_API)
    setElections(data.elections ?? [])
    setSchools(data.schools ?? [])
    setTypeOptions(data.type_options ?? [])
    setStatusOptions(data.status_options ?? [])
    setSummary(
      data.summary ?? {
        total: data.elections?.length ?? 0,
        active: 0,
        upcoming: 0,
        closed: 0,
      }
    )
    setForm((current) => ({
      ...current,
      school_seats: initSchoolSeatsSeats(data.schools ?? [], current.school_seats),
    }))
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load elections."))
        .finally(() => setIsLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [loadData])

  const sortedElections = useMemo(
    () =>
      [...elections].sort((a, b) => {
        const aTime = a.starts_at ? new Date(a.starts_at).getTime() : 0
        const bTime = b.starts_at ? new Date(b.starts_at).getTime() : 0
        return bTime - aTime
      }),
    [elections]
  )

  function resetForm() {
    setEditingElection(null)
    setForm({ ...emptyForm, school_seats: initSchoolSeatsSeats(schools) })
    setError("")
    setSuccess("")
  }

  function updateForm(field: keyof ElectionForm, value: string | boolean) {
    setForm((current) => {
      const next = { ...current, [field]: value }
      if (field === "election_type" && value === "school_committee") {
        next.general_selection_count = "0"
      }
      if (field === "election_type" && value === "src") {
        next.school = ""
        if (next.general_selection_count === "0") next.general_selection_count = "10"
        if (Object.keys(next.school_seats).length === 0) {
          next.school_seats = initSchoolSeatsSeats(schools)
        }
      }
      return next
    })
  }

  function updateSchoolSeat(schoolId: string, seatCount: string) {
    setForm((current) => ({
      ...current,
      school_seats: { ...current.school_seats, [schoolId]: seatCount },
    }))
  }

  function buildPayload() {
    const isCommittee = form.election_type === "school_committee"
    return {
      title: form.title.trim(),
      description: form.description,
      election_type: form.election_type,
      school: isCommittee && form.school ? Number(form.school) : null,
      starts_at: form.starts_at || null,
      ends_at: form.ends_at || null,
      general_selection_count: isCommittee ? 0 : Number(form.general_selection_count || 0),
      school_selection_count: isCommittee ? Number(form.school_selection_count || 0) : 0,
      school_seats: isCommittee
        ? undefined
        : Object.entries(form.school_seats).map(([schoolId, seatCount]) => ({
            school_id: Number(schoolId),
            seat_count: Number(seatCount || 0),
          })),
      status: form.status,
      is_active: form.is_active,
    }
  }

  async function saveElection(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const endpoint = editingElection ? `${ELECTIONS_API}/${editingElection.id}` : ELECTIONS_API
      const data = await apiFetch<{ message: string; election: ElectionRecord }>(endpoint, {
        method: editingElection ? "PATCH" : "POST",
        body: JSON.stringify(buildPayload()),
      })
      setSuccess(data.message || "Election saved successfully.")
      resetForm()
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save election.")
    } finally {
      setIsSaving(false)
    }
  }

  async function deleteElection(election: ElectionRecord) {
    if (!window.confirm(`Delete ${election.title}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch<{ message: string }>(`${ELECTIONS_API}/${election.id}`, {
        method: "DELETE",
      })
      setSuccess("Election deleted successfully.")
      if (editingElection?.id === election.id) resetForm()
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete election.")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/technician", title: "Technician" },
          { href: "/technician/elections", title: "Elections" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Election Setup</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Schedule SRC and school committee ballots, set school scope, and define required candidate selections.
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

        <section className="grid gap-4 md:grid-cols-4">
          {[
            ["Total", summary.total],
            ["Active", summary.active],
            ["Upcoming", summary.upcoming],
            ["Closed", summary.closed],
          ].map(([label, value]) => (
            <Card key={label} className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="pb-2">
                <CardDescription>{label}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold tracking-tight">{value}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-4 xl:grid-cols-[25rem_minmax(0,1fr)]">
          <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-lg">
                    {editingElection ? "Edit Election" : "New Election"}
                  </CardTitle>
                  <CardDescription>
                    {editingElection ? editingElection.title : "Create a scheduled ballot."}
                  </CardDescription>
                </div>
                {editingElection ? (
                  <Button type="button" variant="ghost" size="icon" onClick={resetForm} aria-label="Cancel edit">
                    <X className="size-4" />
                  </Button>
                ) : (
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <Plus className="size-5" />
                  </span>
                )}
              </div>
            </CardHeader>
            <form onSubmit={saveElection}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="election-title">Title</Label>
                  <Input
                    id="election-title"
                    value={form.title}
                    onChange={(event) => updateForm("title", event.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="election-description">Description</Label>
                  <Textarea
                    id="election-description"
                    value={form.description}
                    onChange={(event) => updateForm("description", event.target.value)}
                    rows={3}
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="election-type">Type</Label>
                    <select
                      id="election-type"
                      className={selectClass}
                      value={form.election_type}
                      onChange={(event) => updateForm("election_type", event.target.value as ElectionType)}
                    >
                      {typeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="election-status">Status</Label>
                    <select
                      id="election-status"
                      className={selectClass}
                      value={form.status}
                      onChange={(event) => updateForm("status", event.target.value)}
                    >
                      {statusOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                {form.election_type === "school_committee" ? (
                  <div className="space-y-2">
                    <Label htmlFor="election-school">School</Label>
                    <select
                      id="election-school"
                      className={selectClass}
                      value={form.school}
                      onChange={(event) => updateForm("school", event.target.value)}
                      required
                    >
                      <option value="">Select school</option>
                      {schools.map((school) => (
                        <option key={school.id} value={school.id}>
                          {school.code} - {school.name}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : null}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="election-start">Voting Starts</Label>
                    <Input
                      id="election-start"
                      type="datetime-local"
                      value={form.starts_at}
                      onChange={(event) => updateForm("starts_at", event.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="election-end">Voting Ends</Label>
                    <Input
                      id="election-end"
                      type="datetime-local"
                      value={form.ends_at}
                      onChange={(event) => updateForm("ends_at", event.target.value)}
                      required
                    />
                  </div>
                </div>
                {form.election_type === "src" ? (
                  <div className="space-y-2">
                    <Label htmlFor="election-general-count">SRC General Picks</Label>
                    <Input
                      id="election-general-count"
                      type="number"
                      min={0}
                      value={form.general_selection_count}
                      onChange={(event) => updateForm("general_selection_count", event.target.value)}
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label htmlFor="election-school-count">Committee Picks</Label>
                    <Input
                      id="election-school-count"
                      type="number"
                      min={1}
                      value={form.school_selection_count}
                      onChange={(event) => updateForm("school_selection_count", event.target.value)}
                      required
                    />
                  </div>
                )}
                {form.election_type === "src" && schools.length > 0 ? (
                  <div className="space-y-2">
                    <Label>School Seats</Label>
                    <div className="rounded-lg border border-border bg-background">
                      {schools.map((school) => (
                        <div
                          key={school.id}
                          className="flex items-center gap-3 border-b border-border px-3 py-2 last:border-b-0"
                        >
                          <span className="min-w-0 flex-1 text-sm font-medium truncate">
                            {school.code}
                          </span>
                          <Input
                            type="number"
                            min={0}
                            className="h-8 w-20"
                            value={form.school_seats[String(school.id)] ?? "0"}
                            onChange={(event) => updateSchoolSeat(String(school.id), event.target.value)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
                <label className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    className="size-4"
                    checked={form.is_active}
                    onChange={(event) => updateForm("is_active", event.target.checked)}
                  />
                  Visible in student election pages
                </label>
                <Button type="submit" className="w-full" disabled={isSaving}>
                  {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                  {editingElection ? "Save Election" : "Create Election"}
                </Button>
              </CardContent>
            </form>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Scheduled Elections</CardTitle>
              <CardDescription>{sortedElections.length} configured ballots</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex h-48 items-center justify-center">
                  <Loader2 className="size-8 animate-spin text-muted-foreground" />
                </div>
              ) : sortedElections.length ? (
                <div className="space-y-3">
                  {sortedElections.map((election) => (
                    <div
                      key={election.id}
                      className="rounded-lg border border-border bg-background p-4"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-semibold">{election.title}</h3>
                            <Badge className={statusTone(election.computed_status)} variant="outline">
                              {titleCase(election.computed_status)}
                            </Badge>
                            <Badge variant="outline">{election.election_type_label}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {election.school_detail?.name ?? "All schools"}
                          </p>
                          {election.description ? (
                            <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">
                              {election.description}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex shrink-0 gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={() => {
                              setEditingElection(election)
                              setForm(formFromElection(election))
                              setError("")
                              setSuccess("")
                            }}
                            aria-label={`Edit ${election.title}`}
                          >
                            <Edit3 className="size-4" />
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            onClick={() => void deleteElection(election)}
                            aria-label={`Delete ${election.title}`}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Starts</p>
                          <p className="mt-1">{formatDateTime(election.starts_at)}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Ends</p>
                          <p className="mt-1">{formatDateTime(election.ends_at)}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Selections</p>
                          <p className="mt-1">
                            {election.election_type === "src"
                              ? `${election.general_selection_count} general / ${election.school_seats?.length ?? 0} schools`
                              : `${election.school_selection_count} committee`}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Countdown</p>
                          <p className="mt-1 flex items-center gap-1.5">
                            <CalendarClock className="size-4 text-muted-foreground" />
                            {countdownText(election)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                  No elections configured.
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}
