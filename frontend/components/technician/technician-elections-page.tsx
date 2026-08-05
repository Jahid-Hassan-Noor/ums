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
  type ElectionConstituencyType,
  type ElectionRecord,
  type ElectionSchool,
  type ElectionSeatRule,
  type ElectionType,
} from "@/lib/elections"

type ConstituencyOptions = Record<string, ElectionSchool[]>

type ElectionsResponse = {
  elections: ElectionRecord[]
  schools: ElectionSchool[]
  type_options: ElectionChoice[]
  status_options: ElectionChoice[]
  constituency_type_options: ElectionChoice[]
  constituency_options: ConstituencyOptions
  seat_scope_options: ElectionChoice[]
  summary: {
    total: number
    active: number
    upcoming: number
    closed: number
  }
}

type SeatRuleForm = {
  key: string
  label: string
  selection_count: string
  scope_type: string
  scope_id: string
}

type ElectionForm = {
  title: string
  description: string
  election_type: ElectionType
  election_type_label: string
  constituency_type: ElectionConstituencyType | string
  constituency_id: string
  constituency_label: string
  starts_at: string
  ends_at: string
  seat_rules: SeatRuleForm[]
  status: string
  is_active: boolean
  require_student_profile: boolean
  candidate_must_match_constituency: boolean
  publish_after_close: boolean
  show_live_results: boolean
}

const defaultSeatRule: SeatRuleForm = {
  key: "representatives",
  label: "Representatives",
  selection_count: "1",
  scope_type: "constituency",
  scope_id: "",
}

const emptyForm: ElectionForm = {
  title: "",
  description: "",
  election_type: "student_council",
  election_type_label: "Student council election",
  constituency_type: "university",
  constituency_id: "",
  constituency_label: "",
  starts_at: "",
  ends_at: "",
  seat_rules: [{ ...defaultSeatRule }],
  status: "upcoming",
  is_active: true,
  require_student_profile: false,
  candidate_must_match_constituency: true,
  publish_after_close: false,
  show_live_results: true,
}

const ELECTIONS_API = "/ict-helpdesk/technician/elections"

function slugKey(value: string) {
  return (
    value
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "") || "custom"
  )
}

function policyBool(policy: Record<string, unknown> | undefined, key: string, fallback: boolean) {
  const value = policy?.[key]
  return typeof value === "boolean" ? value : fallback
}

function seatRulesFromRecord(election: ElectionRecord): SeatRuleForm[] {
  const rules = election.seat_rules?.length ? election.seat_rules : []
  if (!rules.length) return [{ ...defaultSeatRule }]
  return rules.map((rule: ElectionSeatRule) => ({
    key: rule.key,
    label: rule.label,
    selection_count: String(rule.selection_count ?? 0),
    scope_type: rule.scope_type || "constituency",
    scope_id: rule.scope_id ? String(rule.scope_id) : "",
  }))
}

function formFromElection(election: ElectionRecord): ElectionForm {
  return {
    title: election.title,
    description: election.description,
    election_type: election.election_type,
    election_type_label: election.election_type_label,
    constituency_type: election.constituency_type || "university",
    constituency_id: election.constituency_id ? String(election.constituency_id) : "",
    constituency_label: election.constituency_label || "",
    starts_at: toDateTimeLocal(election.starts_at),
    ends_at: toDateTimeLocal(election.ends_at),
    seat_rules: seatRulesFromRecord(election),
    status: election.status,
    is_active: election.is_active,
    require_student_profile: policyBool(election.nomination_rules, "require_student_profile", false),
    candidate_must_match_constituency: policyBool(
      election.nomination_rules,
      "candidate_must_match_constituency",
      true
    ),
    publish_after_close: policyBool(election.result_publication_rules, "publish_after_close", false),
    show_live_results: policyBool(election.result_publication_rules, "show_live_results", true),
  }
}

function countdownText(election: ElectionRecord) {
  const seconds = election.countdown?.seconds_remaining ?? 0
  if (!seconds) return election.countdown?.label ?? titleCase(election.computed_status)
  return `${election.countdown.label} ${formatDuration(seconds)}`
}

function electionSeatSummary(election: ElectionRecord) {
  const rules = election.seat_rules ?? []
  if (!rules.length) return "No ballot categories"
  return rules.map((rule) => `${rule.selection_count} ${rule.label.toLowerCase()}`).join(" / ")
}

export function TechnicianElectionsPage() {
  const [elections, setElections] = useState<ElectionRecord[]>([])
  const [typeOptions, setTypeOptions] = useState<ElectionChoice[]>([])
  const [statusOptions, setStatusOptions] = useState<ElectionChoice[]>([])
  const [constituencyTypeOptions, setConstituencyTypeOptions] = useState<ElectionChoice[]>([])
  const [constituencyOptions, setConstituencyOptions] = useState<ConstituencyOptions>({})
  const [seatScopeOptions, setSeatScopeOptions] = useState<ElectionChoice[]>([])
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
    setTypeOptions(data.type_options ?? [])
    setStatusOptions(data.status_options ?? [])
    setConstituencyTypeOptions(data.constituency_type_options ?? [])
    setConstituencyOptions(data.constituency_options ?? {})
    setSeatScopeOptions(data.seat_scope_options ?? [])
    setSummary(
      data.summary ?? {
        total: data.elections?.length ?? 0,
        active: 0,
        upcoming: 0,
        closed: 0,
      }
    )
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

  const visibleTypeOptions = useMemo(() => {
    if (typeOptions.some((option) => option.value === form.election_type)) return typeOptions
    return [...typeOptions, { value: form.election_type, label: form.election_type_label || titleCase(form.election_type) }]
  }, [form.election_type, form.election_type_label, typeOptions])

  const selectedConstituencyOptions = constituencyOptions[form.constituency_type] ?? []
  const needsConstituencySelection = form.constituency_type !== "university"

  function resetForm() {
    setEditingElection(null)
    setForm(emptyForm)
    setError("")
    setSuccess("")
  }

  function updateForm(field: keyof ElectionForm, value: string | boolean) {
    setForm((current) => {
      const next = { ...current, [field]: value }
      if (field === "election_type") {
        const option = typeOptions.find((item) => item.value === value)
        next.election_type_label = option?.label ?? next.election_type_label
      }
      if (field === "election_type_label" && typeof value === "string") {
        next.election_type = slugKey(value)
      }
      if (field === "constituency_type") {
        next.constituency_id = ""
        next.constituency_label = ""
      }
      return next
    })
  }

  function updateSeatRule(index: number, field: keyof SeatRuleForm, value: string) {
    setForm((current) => {
      const seatRules = current.seat_rules.map((rule, ruleIndex) => {
        if (ruleIndex !== index) return rule
        const next = { ...rule, [field]: value }
        if (field === "label") next.key = slugKey(value)
        if (field === "scope_type") next.scope_id = ""
        return next
      })
      return { ...current, seat_rules: seatRules }
    })
  }

  function addSeatRule() {
    setForm((current) => ({
      ...current,
      seat_rules: [
        ...current.seat_rules,
        {
          ...defaultSeatRule,
          key: `representatives_${current.seat_rules.length + 1}`,
          label: `Representatives ${current.seat_rules.length + 1}`,
        },
      ],
    }))
  }

  function removeSeatRule(index: number) {
    setForm((current) => ({
      ...current,
      seat_rules: current.seat_rules.filter((_rule, ruleIndex) => ruleIndex !== index),
    }))
  }

  function constituencyLabel() {
    if (form.constituency_type === "university") return "University-wide"
    const selected = selectedConstituencyOptions.find((option) => String(option.id) === form.constituency_id)
    return selected?.name || selected?.label || form.constituency_label
  }

  function buildPayload() {
    const constituencyId = form.constituency_id ? Number(form.constituency_id) : null
    return {
      title: form.title.trim(),
      description: form.description,
      election_type: form.election_type.trim() || slugKey(form.election_type_label),
      election_type_label: form.election_type_label.trim(),
      constituency_type: form.constituency_type,
      constituency_id: constituencyId,
      constituency_label: constituencyLabel(),
      school: form.constituency_type === "school" ? constituencyId : null,
      starts_at: form.starts_at || null,
      ends_at: form.ends_at || null,
      general_selection_count: 0,
      school_selection_count: 0,
      seat_rules: form.seat_rules.map((rule) => ({
        key: slugKey(rule.key || rule.label),
        label: rule.label.trim(),
        selection_count: Number(rule.selection_count || 0),
        scope_type: rule.scope_type,
        scope_id: rule.scope_id ? Number(rule.scope_id) : null,
      })),
      nomination_rules: {
        require_student_profile: form.require_student_profile,
        candidate_must_match_constituency: form.candidate_must_match_constituency,
      },
      voter_eligibility: {},
      result_publication_rules: {
        publish_after_close: form.publish_after_close,
        show_live_results: form.show_live_results,
      },
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
              Configure voting windows, constituencies, ballot categories, nomination checks, and publication rules.
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

        <section className="grid gap-4 xl:grid-cols-[28rem_minmax(0,1fr)]">
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
                    <Label htmlFor="election-type">Type Template</Label>
                    <select
                      id="election-type"
                      className={selectClass}
                      value={form.election_type}
                      onChange={(event) => updateForm("election_type", event.target.value)}
                    >
                      {visibleTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="election-type-label">Type Label</Label>
                    <Input
                      id="election-type-label"
                      value={form.election_type_label}
                      onChange={(event) => updateForm("election_type_label", event.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="election-constituency-type">Constituency</Label>
                    <select
                      id="election-constituency-type"
                      className={selectClass}
                      value={form.constituency_type}
                      onChange={(event) => updateForm("constituency_type", event.target.value)}
                    >
                      {constituencyTypeOptions.map((option) => (
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
                {needsConstituencySelection ? (
                  selectedConstituencyOptions.length ? (
                    <div className="space-y-2">
                      <Label htmlFor="election-constituency-id">Constituency Unit</Label>
                      <select
                        id="election-constituency-id"
                        className={selectClass}
                        value={form.constituency_id}
                        onChange={(event) => updateForm("constituency_id", event.target.value)}
                        required
                      >
                        <option value="">Select constituency</option>
                        {selectedConstituencyOptions.map((option) => (
                          <option key={option.id} value={option.id}>
                            {option.label ?? `${option.code} - ${option.name}`}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : (
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="election-constituency-id">Constituency Value</Label>
                        <Input
                          id="election-constituency-id"
                          type="number"
                          min={1}
                          value={form.constituency_id}
                          onChange={(event) => updateForm("constituency_id", event.target.value)}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="election-constituency-label">Constituency Label</Label>
                        <Input
                          id="election-constituency-label"
                          value={form.constituency_label}
                          onChange={(event) => updateForm("constituency_label", event.target.value)}
                        />
                      </div>
                    </div>
                  )
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
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <Label>Ballot Categories</Label>
                    <Button type="button" size="sm" variant="outline" onClick={addSeatRule}>
                      <Plus className="size-4" />
                      Add
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {form.seat_rules.map((rule, index) => (
                      <div key={`${rule.key}-${index}`} className="rounded-lg border border-border bg-background p-3">
                        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_6rem]">
                          <div className="space-y-2">
                            <Label htmlFor={`seat-label-${index}`}>Label</Label>
                            <Input
                              id={`seat-label-${index}`}
                              value={rule.label}
                              onChange={(event) => updateSeatRule(index, "label", event.target.value)}
                              required
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`seat-count-${index}`}>Picks</Label>
                            <Input
                              id={`seat-count-${index}`}
                              type="number"
                              min={1}
                              value={rule.selection_count}
                              onChange={(event) => updateSeatRule(index, "selection_count", event.target.value)}
                              required
                            />
                          </div>
                        </div>
                        <div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_2.5rem]">
                          <div className="space-y-2">
                            <Label htmlFor={`seat-scope-${index}`}>Scope</Label>
                            <select
                              id={`seat-scope-${index}`}
                              className={selectClass}
                              value={rule.scope_type}
                              onChange={(event) => updateSeatRule(index, "scope_type", event.target.value)}
                            >
                              {seatScopeOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="self-end"
                            onClick={() => removeSeatRule(index)}
                            disabled={form.seat_rules.length === 1}
                            aria-label={`Remove ${rule.label}`}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid gap-2">
                  <label className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-4"
                      checked={form.is_active}
                      onChange={(event) => updateForm("is_active", event.target.checked)}
                    />
                    Visible to eligible voters
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-4"
                      checked={form.require_student_profile}
                      onChange={(event) => updateForm("require_student_profile", event.target.checked)}
                    />
                    Require linked student candidates
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-4"
                      checked={form.candidate_must_match_constituency}
                      onChange={(event) => updateForm("candidate_must_match_constituency", event.target.checked)}
                    />
                    Candidates must match constituency
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-4"
                      checked={form.publish_after_close}
                      onChange={(event) => updateForm("publish_after_close", event.target.checked)}
                    />
                    Publish only after voting closes
                  </label>
                  <label className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm">
                    <input
                      type="checkbox"
                      className="size-4"
                      checked={form.show_live_results}
                      onChange={(event) => updateForm("show_live_results", event.target.checked)}
                    />
                    Show live results to voters
                  </label>
                </div>
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
                    <div key={election.id} className="rounded-lg border border-border bg-background p-4">
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
                            {election.constituency_label || election.constituency_detail?.label || "University-wide"}
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
                          <p className="mt-1">{electionSeatSummary(election)}</p>
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
