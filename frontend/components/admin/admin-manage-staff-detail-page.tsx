"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, ArrowLeft, BriefcaseBusiness, CheckCircle2, Loader2, Save } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import type { AdminDirectoryOption } from "@/lib/admin-directory"

type StaffKind = "teachers" | "executives"

type ScopedOption = AdminDirectoryOption & {
  school?: number | null
  center?: number | null
  department?: number | null
}

type StaffMember = {
  id: number
  username: string
  name: string
  email: string
  staff_id: string
  designation: string
  phone: string
  school: number | null
  school_name: string
  center: number | null
  center_name: string
  unit: number | null
  unit_name: string
  department: number | null
  department_name: string
  academic_rank?: string
  specialization?: string
  office_location?: string
  responsibility_area?: string
}

type StaffDetailResponse = {
  teacher?: StaffMember
  executive?: StaffMember
  options: {
    schools: AdminDirectoryOption[]
    centers: AdminDirectoryOption[]
    units: ScopedOption[]
    departments: ScopedOption[]
  }
}

type StaffForm = {
  designation: string
  assignment_type: "" | "school" | "center"
  school_id: string
  center_id: string
  unit_id: string
  department_id: string
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

const labels: Record<StaffKind, { singular: string; plural: string; apiKey: "teacher" | "executive" }> = {
  teachers: { singular: "Teacher", plural: "Teachers", apiKey: "teacher" },
  executives: { singular: "Executive", plural: "Executives", apiKey: "executive" },
}

function formFromMember(member: StaffMember | null): StaffForm {
  return {
    designation: member?.designation ?? "",
    assignment_type: member?.school ? "school" : member?.center ? "center" : "",
    school_id: member?.school ? String(member.school) : "",
    center_id: member?.center ? String(member.center) : "",
    unit_id: member?.unit ? String(member.unit) : "",
    department_id: member?.department ? String(member.department) : "",
  }
}

function scopeText(member: StaffMember) {
  return [
    member.school_name || member.center_name,
    member.department_name,
    member.unit_name,
  ]
    .filter(Boolean)
    .join(" / ")
}

export function AdminManageStaffDetailPage({
  kind,
  profileId,
}: {
  kind: StaffKind
  profileId: string
}) {
  const config = labels[kind]
  const [member, setMember] = useState<StaffMember | null>(null)
  const [schools, setSchools] = useState<AdminDirectoryOption[]>([])
  const [centers, setCenters] = useState<AdminDirectoryOption[]>([])
  const [units, setUnits] = useState<ScopedOption[]>([])
  const [departments, setDepartments] = useState<ScopedOption[]>([])
  const [form, setForm] = useState<StaffForm>(formFromMember(null))
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    async function loadData() {
      setError("")
      const data = await apiFetch<StaffDetailResponse>(`/admin/manage/${kind}/${profileId}`)
      const nextMember = data[config.apiKey] ?? null
      setMember(nextMember)
      setSchools(data.options?.schools ?? [])
      setCenters(data.options?.centers ?? [])
      setUnits(data.options?.units ?? [])
      setDepartments(data.options?.departments ?? [])
      setForm(formFromMember(nextMember))
    }

    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : `Unable to load ${config.singular.toLowerCase()}.`))
        .finally(() => setIsLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [kind, profileId, config.apiKey, config.singular])

  const scopedUnits = useMemo(() => {
    return units.filter((unit) =>
      form.assignment_type === "school"
        ? String(unit.school ?? "") === form.school_id
        : form.assignment_type === "center"
          ? String(unit.center ?? "") === form.center_id
          : false
    )
  }, [units, form.assignment_type, form.school_id, form.center_id])

  const scopedDepartments = useMemo(() => {
    return departments.filter((department) =>
      form.assignment_type === "school"
        ? String(department.school ?? "") === form.school_id
        : form.assignment_type === "center"
          ? String(department.center ?? "") === form.center_id
          : false
    )
  }, [departments, form.assignment_type, form.school_id, form.center_id])

  function updateForm(field: keyof StaffForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function saveMember(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const data = await apiFetch<StaffDetailResponse & { message?: string }>(
        `/admin/manage/${kind}/${profileId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            designation: form.designation,
            school_id: form.assignment_type === "school" ? Number(form.school_id) : null,
            center_id: form.assignment_type === "center" ? Number(form.center_id) : null,
            unit_id: form.unit_id ? Number(form.unit_id) : null,
            department_id: form.department_id ? Number(form.department_id) : null,
          }),
        }
      )
      const nextMember = data[config.apiKey] ?? null
      setMember(nextMember)
      setForm(formFromMember(nextMember))
      setSuccess(data.message || `${config.singular} details updated successfully.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : `Unable to update ${config.singular.toLowerCase()}.`)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: `/admin/manage/${kind}`, title: config.plural },
          { href: `/admin/manage/${kind}/${profileId}`, title: member?.name ?? `${config.singular} Detail` },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {member?.name ?? `${config.singular} Detail`}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Review account details and update designation or organisation assignment.
            </p>
          </div>
          <Button variant="outline" render={<Link href={`/admin/manage/${kind}`} />}>
            <ArrowLeft className="size-4" />
            {config.plural}
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

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : member ? (
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <BriefcaseBusiness className="size-5" />
                  </span>
                  <div>
                    <CardTitle className="text-lg">{member.name}</CardTitle>
                    <CardDescription>{member.staff_id || member.username}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 text-sm md:grid-cols-2">
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Email</p>
                  <p className="mt-1">{member.email || "Not set"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Designation</p>
                  <p className="mt-1">{member.designation || "Not set"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Assignment</p>
                  <p className="mt-1">{scopeText(member) || "Unassigned"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Office</p>
                  <p className="mt-1">{member.office_location || "Not set"}</p>
                </div>
                {kind === "teachers" ? (
                  <div className="md:col-span-2">
                    <p className="text-xs font-medium uppercase text-muted-foreground">Specialization</p>
                    <p className="mt-1">{member.specialization || "Not set"}</p>
                  </div>
                ) : (
                  <div className="md:col-span-2">
                    <p className="text-xs font-medium uppercase text-muted-foreground">Responsibility Area</p>
                    <p className="mt-1">{member.responsibility_area || "Not set"}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Editable Details</CardTitle>
                <CardDescription>Change designation and school, centre, unit, or department assignment.</CardDescription>
              </CardHeader>
              <form onSubmit={saveMember}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="designation">Designation</Label>
                    <Input
                      id="designation"
                      value={form.designation}
                      onChange={(event) => updateForm("designation", event.target.value)}
                      placeholder="Lecturer, Associate Prof, Dean, HOP"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="assignment-type">Assigned Unit Type</Label>
                    <select
                      id="assignment-type"
                      className={selectClass}
                      value={form.assignment_type}
                      onChange={(event) => {
                        const value = event.target.value as StaffForm["assignment_type"]
                        setForm((current) => ({
                          ...current,
                          assignment_type: value,
                          school_id: value === "school" ? current.school_id : "",
                          center_id: value === "center" ? current.center_id : "",
                          unit_id: "",
                          department_id: "",
                        }))
                      }}
                      required
                    >
                      <option value="">Select assignment</option>
                      <option value="school">School</option>
                      <option value="center">Centre</option>
                    </select>
                  </div>
                  {form.assignment_type === "school" ? (
                    <div className="space-y-2">
                      <Label htmlFor="school-id">School</Label>
                      <select
                        id="school-id"
                        className={selectClass}
                        value={form.school_id}
                        onChange={(event) => {
                          updateForm("school_id", event.target.value)
                          updateForm("unit_id", "")
                          updateForm("department_id", "")
                        }}
                        required
                      >
                        <option value="">Select school</option>
                        {schools.map((school) => (
                          <option key={school.value} value={school.value}>
                            {school.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : null}
                  {form.assignment_type === "center" ? (
                    <div className="space-y-2">
                      <Label htmlFor="center-id">Centre</Label>
                      <select
                        id="center-id"
                        className={selectClass}
                        value={form.center_id}
                        onChange={(event) => {
                          updateForm("center_id", event.target.value)
                          updateForm("unit_id", "")
                          updateForm("department_id", "")
                        }}
                        required
                      >
                        <option value="">Select centre</option>
                        {centers.map((center) => (
                          <option key={center.value} value={center.value}>
                            {center.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : null}
                  <div className="space-y-2">
                    <Label htmlFor="department-id">Department</Label>
                    <select
                      id="department-id"
                      className={selectClass}
                      value={form.department_id}
                      onChange={(event) => updateForm("department_id", event.target.value)}
                    >
                      <option value="">No department</option>
                      {scopedDepartments.map((department) => (
                        <option key={department.value} value={department.value}>
                          {department.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="unit-id">Unit</Label>
                    <select
                      id="unit-id"
                      className={selectClass}
                      value={form.unit_id}
                      onChange={(event) => {
                        const nextUnitId = event.target.value
                        const unit = units.find((item) => item.value === nextUnitId)
                        setForm((current) => ({
                          ...current,
                          unit_id: nextUnitId,
                          department_id: unit?.department ? String(unit.department) : current.department_id,
                        }))
                      }}
                      required={kind === "executives"}
                    >
                      <option value="">{kind === "executives" ? "Select unit" : "Direct assignment"}</option>
                      {scopedUnits.map((unit) => (
                        <option key={unit.value} value={unit.value}>
                          {unit.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </CardContent>
                <div className="flex justify-end border-t p-4">
                  <Button type="submit" disabled={isSaving}>
                    {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                    {isSaving ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </form>
            </Card>
          </section>
        ) : null}
      </main>
    </div>
  )
}
