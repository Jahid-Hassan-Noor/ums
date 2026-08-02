"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Edit3,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Search,
  Trash2,
  UserRound,
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
  selectClass,
  titleCase,
  type ElectionCandidate,
  type ElectionCategory,
  type ElectionChoice,
  type ElectionRecord,
  type ElectionSchool,
  type ElectionStudent,
} from "@/lib/elections"

type CandidatesResponse = {
  candidates: ElectionCandidate[]
  elections: ElectionRecord[]
  schools: ElectionSchool[]
  students: ElectionStudent[]
  category_options: ElectionChoice[]
  status_options: ElectionChoice[]
}

type CandidateForm = {
  election: string
  student: string
  display_name: string
  student_identifier: string
  school: string
  category: ElectionCategory
  details: string
  manifesto: string
  status: string
  sort_order: string
}

const emptyForm: CandidateForm = {
  election: "",
  student: "",
  display_name: "",
  student_identifier: "",
  school: "",
  category: "general",
  details: "",
  manifesto: "",
  status: "approved",
  sort_order: "0",
}

const ELECTION_CANDIDATES_API = "/ict-helpdesk/technician/elections/candidates"

function formFromCandidate(candidate: ElectionCandidate): CandidateForm {
  return {
    election: String(candidate.election),
    student: candidate.student ? String(candidate.student) : "",
    display_name: candidate.display_name,
    student_identifier: candidate.student_identifier,
    school: candidate.school ? String(candidate.school) : "",
    category: candidate.category,
    details: candidate.details,
    manifesto: candidate.manifesto,
    status: candidate.status,
    sort_order: String(candidate.sort_order ?? 0),
  }
}

export function TechnicianElectionCandidatesPage() {
  const [candidates, setCandidates] = useState<ElectionCandidate[]>([])
  const [elections, setElections] = useState<ElectionRecord[]>([])
  const [schools, setSchools] = useState<ElectionSchool[]>([])
  const [students, setStudents] = useState<ElectionStudent[]>([])
  const [categoryOptions, setCategoryOptions] = useState<ElectionChoice[]>([])
  const [statusOptions, setStatusOptions] = useState<ElectionChoice[]>([])
  const [form, setForm] = useState<CandidateForm>(emptyForm)
  const [editingCandidate, setEditingCandidate] = useState<ElectionCandidate | null>(null)
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    setError("")
    const data = await apiFetch<CandidatesResponse>(ELECTION_CANDIDATES_API)
    setCandidates(data.candidates ?? [])
    setElections(data.elections ?? [])
    setSchools(data.schools ?? [])
    setStudents(data.students ?? [])
    setCategoryOptions(data.category_options ?? [])
    setStatusOptions(data.status_options ?? [])
    setForm((current) => {
      if (current.election || !data.elections?.[0]) return current
      return {
        ...current,
        election: String(data.elections[0].id),
        category: data.elections[0].election_type === "school_committee" ? "school" : current.category,
        school: data.elections[0].school ? String(data.elections[0].school) : current.school,
      }
    })
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load candidates."))
        .finally(() => setIsLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  const selectedElection = useMemo(
    () => elections.find((election) => String(election.id) === form.election) ?? null,
    [elections, form.election]
  )

  const filteredCandidates = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return candidates
      .filter((candidate) => !form.election || String(candidate.election) === form.election)
      .filter((candidate) => {
        if (!normalized) return true
        return [
          candidate.display_name,
          candidate.student_identifier,
          candidate.school_detail?.name,
          candidate.school_detail?.code,
          candidate.category_label,
          candidate.details,
          candidate.manifesto,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalized)
      })
  }, [candidates, form.election, query])

  function applyElectionDefaults(next: CandidateForm, electionId: string) {
    const election = elections.find((item) => String(item.id) === electionId)
    if (!election) return next
    if (election.election_type === "school_committee") {
      return {
        ...next,
        category: "school" as ElectionCategory,
        school: election.school ? String(election.school) : next.school,
      }
    }
    return next
  }

  function resetForm() {
    const next = {
      ...emptyForm,
      election: form.election || (elections[0] ? String(elections[0].id) : ""),
    }
    setEditingCandidate(null)
    setForm(applyElectionDefaults(next, next.election))
    setError("")
    setSuccess("")
  }

  function updateForm(field: keyof CandidateForm, value: string) {
    setForm((current) => {
      let next = { ...current, [field]: value }
      if (field === "election") {
        next = applyElectionDefaults(next, value)
      }
      if (field === "student") {
        const student = students.find((item) => String(item.id) === value)
        if (student) {
          next.display_name = student.name
          next.student_identifier = student.student_id
          next.school = student.school ? String(student.school) : next.school
        }
      }
      return next
    })
  }

  function buildPayload() {
    return {
      election: Number(form.election),
      student: form.student ? Number(form.student) : null,
      display_name: form.display_name.trim(),
      student_identifier: form.student_identifier.trim(),
      school: form.school ? Number(form.school) : null,
      category: selectedElection?.election_type === "school_committee" ? "school" : form.category,
      details: form.details,
      manifesto: form.manifesto,
      status: form.status,
      sort_order: Number(form.sort_order || 0),
    }
  }

  async function saveCandidate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const endpoint = editingCandidate
        ? `${ELECTION_CANDIDATES_API}/${editingCandidate.id}`
        : ELECTION_CANDIDATES_API
      const data = await apiFetch<{ message: string; candidate: ElectionCandidate }>(endpoint, {
        method: editingCandidate ? "PATCH" : "POST",
        body: JSON.stringify(buildPayload()),
      })
      setSuccess(data.message || "Candidate saved successfully.")
      resetForm()
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save candidate.")
    } finally {
      setIsSaving(false)
    }
  }

  async function deleteCandidate(candidate: ElectionCandidate) {
    if (!window.confirm(`Delete ${candidate.display_name}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch<{ message: string }>(`${ELECTION_CANDIDATES_API}/${candidate.id}`, {
        method: "DELETE",
      })
      setSuccess("Candidate deleted successfully.")
      if (editingCandidate?.id === candidate.id) resetForm()
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete candidate.")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/technician", title: "Technician" },
          { href: "/technician/elections", title: "Elections" },
          { href: "/technician/elections/candidates", title: "Candidates" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Election Candidates</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Maintain manually entered candidates, student IDs, school category placement, and candidate details.
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

        <section className="grid gap-4 xl:grid-cols-[25rem_minmax(0,1fr)]">
          <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-lg">
                    {editingCandidate ? "Edit Candidate" : "New Candidate"}
                  </CardTitle>
                  <CardDescription>
                    {editingCandidate ? editingCandidate.display_name : selectedElection?.title ?? "Select an election"}
                  </CardDescription>
                </div>
                {editingCandidate ? (
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
            <form onSubmit={saveCandidate}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="candidate-election">Election</Label>
                  <select
                    id="candidate-election"
                    className={selectClass}
                    value={form.election}
                    onChange={(event) => updateForm("election", event.target.value)}
                    required
                  >
                    <option value="">Select election</option>
                    {elections.map((election) => (
                      <option key={election.id} value={election.id}>
                        {election.title}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="candidate-student">Linked Student</Label>
                  <select
                    id="candidate-student"
                    className={selectClass}
                    value={form.student}
                    onChange={(event) => updateForm("student", event.target.value)}
                  >
                    <option value="">Manual candidate</option>
                    {students.map((student) => (
                      <option key={student.id} value={student.id}>
                        {student.name} {student.student_id ? `(${student.student_id})` : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="candidate-name">Name</Label>
                    <Input
                      id="candidate-name"
                      value={form.display_name}
                      onChange={(event) => updateForm("display_name", event.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="candidate-student-id">Student ID</Label>
                    <Input
                      id="candidate-student-id"
                      value={form.student_identifier}
                      onChange={(event) => updateForm("student_identifier", event.target.value)}
                    />
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="candidate-category">Category</Label>
                    <select
                      id="candidate-category"
                      className={selectClass}
                      value={selectedElection?.election_type === "school_committee" ? "school" : form.category}
                      onChange={(event) => updateForm("category", event.target.value as ElectionCategory)}
                      disabled={selectedElection?.election_type === "school_committee"}
                    >
                      {categoryOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="candidate-school">School</Label>
                    <select
                      id="candidate-school"
                      className={selectClass}
                      value={form.school}
                      onChange={(event) => updateForm("school", event.target.value)}
                      required={form.category === "school" || selectedElection?.election_type === "school_committee"}
                    >
                      <option value="">No school</option>
                      {schools.map((school) => (
                        <option key={school.id} value={school.id}>
                          {school.code} - {school.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="candidate-status">Status</Label>
                    <select
                      id="candidate-status"
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
                  <div className="space-y-2">
                    <Label htmlFor="candidate-order">Sort Order</Label>
                    <Input
                      id="candidate-order"
                      type="number"
                      min={0}
                      value={form.sort_order}
                      onChange={(event) => updateForm("sort_order", event.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="candidate-details">Details</Label>
                  <Textarea
                    id="candidate-details"
                    value={form.details}
                    onChange={(event) => updateForm("details", event.target.value)}
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="candidate-manifesto">Manifesto</Label>
                  <Textarea
                    id="candidate-manifesto"
                    value={form.manifesto}
                    onChange={(event) => updateForm("manifesto", event.target.value)}
                    rows={3}
                  />
                </div>
                <Button type="submit" className="w-full" disabled={isSaving || !form.election}>
                  {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                  {editingCandidate ? "Save Candidate" : "Add Candidate"}
                </Button>
              </CardContent>
            </form>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <CardTitle className="text-lg">Candidates</CardTitle>
                  <CardDescription>{filteredCandidates.length} shown for the selected election</CardDescription>
                </div>
                <div className="relative w-full lg:w-72">
                  <Search className="pointer-events-none absolute left-2.5 top-2 size-4 text-muted-foreground" />
                  <Input
                    className="pl-8"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search candidates"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex h-48 items-center justify-center">
                  <Loader2 className="size-8 animate-spin text-muted-foreground" />
                </div>
              ) : filteredCandidates.length ? (
                <div className="space-y-3">
                  {filteredCandidates.map((candidate) => (
                    <div key={candidate.id} className="rounded-lg border border-border bg-background p-4">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                              <UserRound className="size-4" />
                            </span>
                            <h3 className="font-semibold">{candidate.display_name}</h3>
                            <Badge variant="outline">{candidate.category_label}</Badge>
                            <Badge variant="outline">{titleCase(candidate.status)}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {[candidate.student_identifier, candidate.school_detail?.code].filter(Boolean).join(" / ") || "Manual candidate"}
                          </p>
                          {candidate.details || candidate.manifesto ? (
                            <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">
                              {candidate.details || candidate.manifesto}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex shrink-0 gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={() => {
                              setEditingCandidate(candidate)
                              setForm(formFromCandidate(candidate))
                              setError("")
                              setSuccess("")
                            }}
                            aria-label={`Edit ${candidate.display_name}`}
                          >
                            <Edit3 className="size-4" />
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            onClick={() => void deleteCandidate(candidate)}
                            aria-label={`Delete ${candidate.display_name}`}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="mt-3 grid gap-3 text-sm md:grid-cols-3">
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Votes</p>
                          <p className="mt-1">{candidate.vote_count}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">School</p>
                          <p className="mt-1">{candidate.school_detail?.name ?? "Not assigned"}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Order</p>
                          <p className="mt-1">{candidate.sort_order}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                  No candidates found.
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}
