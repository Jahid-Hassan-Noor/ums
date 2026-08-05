"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  Archive,
  CheckCircle2,
  Edit3,
  Loader2,
  Plus,
  Save,
  Search,
  X,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type Scope = {
  kind: "school" | "center" | null
  id: number | null
  code: string
  name: string
  academic_workflows: boolean
}

type Programme = {
  id: number
  code: string
  name: string
  program_type: "academic" | "center_program"
  level: string
  duration_years: number | null
  description: string
  is_active: boolean
}

type ProgrammesResponse = {
  scope: Scope
  program_types: { value: Programme["program_type"]; label: string }[]
  programmes: Programme[]
}

type ProgrammeForm = {
  code: string
  name: string
  program_type: Programme["program_type"]
  level: string
  duration_years: string
  description: string
  is_active: boolean
}

const emptyForm: ProgrammeForm = {
  code: "",
  name: "",
  program_type: "academic",
  level: "",
  duration_years: "",
  description: "",
  is_active: true,
}

function formFromProgramme(programme: Programme): ProgrammeForm {
  return {
    code: programme.code,
    name: programme.name,
    program_type: programme.program_type,
    level: programme.level ?? "",
    duration_years: programme.duration_years ? String(programme.duration_years) : "",
    description: programme.description ?? "",
    is_active: programme.is_active,
  }
}

export function ExecutiveProgramsPage() {
  const [scope, setScope] = useState<Scope | null>(null)
  const [programTypes, setProgramTypes] = useState<ProgrammesResponse["program_types"]>([])
  const [programmes, setProgrammes] = useState<Programme[]>([])
  const [form, setForm] = useState<ProgrammeForm>(emptyForm)
  const [editingProgramme, setEditingProgramme] = useState<Programme | null>(null)
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    const data = await apiFetch<ProgrammesResponse>("/executive/programs")
    setScope(data.scope)
    setProgramTypes(data.program_types ?? [])
    setProgrammes(data.programmes ?? [])
    setForm((current) => ({
      ...current,
      program_type: data.scope.academic_workflows ? current.program_type : "center_program",
    }))
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          setError(caught instanceof Error ? caught.message : "Unable to load programmes.")
        })
        .finally(() => setIsLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  const filteredProgrammes = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return programmes
    return programmes.filter((programme) =>
      [programme.code, programme.name, programme.level, programme.description]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [programmes, query])

  function updateField(field: keyof ProgrammeForm, value: string | boolean) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function startEdit(programme: Programme) {
    setEditingProgramme(programme)
    setForm(formFromProgramme(programme))
    setError("")
    setSuccess("")
  }

  function resetForm() {
    setEditingProgramme(null)
    setForm({
      ...emptyForm,
      program_type: scope?.academic_workflows === false ? "center_program" : "academic",
    })
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")
    setIsSaving(true)

    try {
      const payload = {
        ...form,
        code: form.code.trim().toUpperCase(),
        duration_years: form.duration_years ? Number(form.duration_years) : null,
      }
      if (editingProgramme) {
        await apiFetch(`/executive/programs?programme_id=${editingProgramme.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        })
        setSuccess("Programme updated successfully.")
      } else {
        await apiFetch("/executive/programs", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess("Programme created successfully.")
      }
      await loadData()
      resetForm()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save programme.")
    } finally {
      setIsSaving(false)
    }
  }

  async function archiveProgramme(programme: Programme) {
    if (!confirm(`Archive ${programme.name}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/programs?programme_id=${programme.id}`, {
        method: "DELETE",
      })
      setSuccess("Programme archived successfully.")
      await loadData()
      if (editingProgramme?.id === programme.id) resetForm()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to archive programme.")
    }
  }

  const canChooseType = scope?.kind === "center" && scope.academic_workflows

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/programs", title: "Programmes" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Programmes
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Add and maintain programmes for your assigned school or centre.
            </p>
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

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <CardTitle className="text-lg">Programme Directory</CardTitle>
                    <CardDescription>
                      {scope?.name ?? "Assigned organisation"}
                    </CardDescription>
                  </div>
                  <div className="relative md:w-72">
                    <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      className="pl-9"
                      placeholder="Search programmes"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {filteredProgrammes.map((programme) => (
                  <div
                    key={programme.id}
                    className="rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold">{programme.name}</p>
                          <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {programme.code}
                          </span>
                          <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {programme.program_type === "academic" ? "Academic" : "Centre programme"}
                          </span>
                          {!programme.is_active ? (
                            <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
                              Archived
                            </span>
                          ) : null}
                        </div>
                        {programme.description ? (
                          <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">
                            {programme.description}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => startEdit(programme)}>
                          <Edit3 className="size-4" />
                          Edit
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => archiveProgramme(programme)}>
                          <Archive className="size-4" />
                          Archive
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredProgrammes.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                    No programmes found.
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Plus className="size-5 text-primary" />
                  {editingProgramme ? "Edit Programme" : "Add Programme"}
                </CardTitle>
                <CardDescription>
                  {scope?.academic_workflows
                    ? "Academic programmes can connect to courses and schedules."
                    : "This centre uses centre programmes only."}
                </CardDescription>
              </CardHeader>
              <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="programme-code">Code</Label>
                    <Input
                      id="programme-code"
                      value={form.code}
                      onChange={(event) => updateField("code", event.target.value.toUpperCase())}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="programme-name">Name</Label>
                    <Input
                      id="programme-name"
                      value={form.name}
                      onChange={(event) => updateField("name", event.target.value)}
                      required
                    />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="programme-level">Level</Label>
                      <Input
                        id="programme-level"
                        value={form.level}
                        onChange={(event) => updateField("level", event.target.value)}
                        placeholder="Degree, course, service"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="programme-duration">Years</Label>
                      <Input
                        id="programme-duration"
                        type="number"
                        min="1"
                        value={form.duration_years}
                        onChange={(event) => updateField("duration_years", event.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="programme-type">Type</Label>
                    <select
                      id="programme-type"
                      value={form.program_type}
                      disabled={!canChooseType}
                      onChange={(event) =>
                        updateField("program_type", event.target.value as Programme["program_type"])
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:opacity-70"
                    >
                      {programTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="programme-description">Description</Label>
                    <Textarea
                      id="programme-description"
                      value={form.description}
                      onChange={(event) => updateField("description", event.target.value)}
                      rows={5}
                    />
                  </div>
                </CardContent>
                <div className="flex justify-between gap-3 border-t p-4">
                  {editingProgramme ? (
                    <Button type="button" variant="outline" onClick={resetForm}>
                      <X className="size-4" />
                      Cancel
                    </Button>
                  ) : (
                    <span />
                  )}
                  <Button type="submit" disabled={isSaving}>
                    {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                    {isSaving ? "Saving..." : editingProgramme ? "Save Programme" : "Add Programme"}
                  </Button>
                </div>
              </form>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}
