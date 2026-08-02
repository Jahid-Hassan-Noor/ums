"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { AlertCircle, ArrowLeft, CheckCircle2, GraduationCap, Loader2, Save } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import type { AdminDirectoryOption } from "@/lib/admin-directory"

type ProgramOption = AdminDirectoryOption & {
  school?: number | null
  center?: number | null
  department?: number | null
}

type StudentDetail = {
  id: number
  username: string
  name: string
  email: string
  student_id: string
  country: string
  intake: string
  session: string
  school_name: string
  center_name: string
  program: number | null
  program_code: string
  program_name: string
  status: string
  status_label: string
  enrollment_status: string
}

type StudentDetailResponse = {
  student: StudentDetail
  options: {
    statuses: AdminDirectoryOption[]
    programs: ProgramOption[]
  }
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

export function AdminManageStudentDetailPage({ studentId }: { studentId: string }) {
  const [student, setStudent] = useState<StudentDetail | null>(null)
  const [statuses, setStatuses] = useState<AdminDirectoryOption[]>([])
  const [programs, setPrograms] = useState<ProgramOption[]>([])
  const [form, setForm] = useState({ status: "", program_id: "" })
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    async function loadData() {
      setError("")
      const data = await apiFetch<StudentDetailResponse>(`/admin/manage/students/${studentId}`)
      setStudent(data.student)
      setStatuses(data.options?.statuses ?? [])
      setPrograms(data.options?.programs ?? [])
      setForm({
        status: data.student?.status ?? "active",
        program_id: data.student?.program ? String(data.student.program) : "",
      })
    }

    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load student."))
        .finally(() => setIsLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [studentId])

  async function saveStudent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      const data = await apiFetch<{ message: string; student: StudentDetail }>(
        `/admin/manage/students/${studentId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status: form.status,
            program_id: form.program_id ? Number(form.program_id) : null,
          }),
        }
      )
      setStudent(data.student)
      setForm({
        status: data.student.status,
        program_id: data.student.program ? String(data.student.program) : "",
      })
      setSuccess(data.message || "Student details updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update student.")
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
          { href: "/admin/manage/students", title: "Students" },
          { href: `/admin/manage/students/${studentId}`, title: student?.name ?? "Student Detail" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {student?.name ?? "Student Detail"}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Review student details and update academic status or program placement.
            </p>
          </div>
          <Button variant="outline" render={<Link href="/admin/manage/students" />}>
            <ArrowLeft className="size-4" />
            Students
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
        ) : student ? (
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <GraduationCap className="size-5" />
                  </span>
                  <div>
                    <CardTitle className="text-lg">{student.name}</CardTitle>
                    <CardDescription>{student.student_id || student.username}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 text-sm md:grid-cols-2">
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Email</p>
                  <p className="mt-1">{student.email || "Not set"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Status</p>
                  <p className="mt-1">{student.status_label || "Active"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Country</p>
                  <p className="mt-1">{student.country || "Not set"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Intake / Session</p>
                  <p className="mt-1">{[student.intake, student.session].filter(Boolean).join(" / ") || "Not set"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Current Program</p>
                  <p className="mt-1">{student.program_name || student.program_code || "Not set"}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">School / Centre</p>
                  <p className="mt-1">{student.school_name || student.center_name || "Not set"}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Editable Details</CardTitle>
                <CardDescription>Change academic status or move the student to another program.</CardDescription>
              </CardHeader>
              <form onSubmit={saveStudent}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="student-status">Status</Label>
                    <select
                      id="student-status"
                      className={selectClass}
                      value={form.status}
                      onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
                      required
                    >
                      {statuses.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="student-program">Program</Label>
                    <select
                      id="student-program"
                      className={selectClass}
                      value={form.program_id}
                      onChange={(event) => setForm((current) => ({ ...current, program_id: event.target.value }))}
                    >
                      <option value="">No program assigned</option>
                      {programs.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
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
