"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  Archive,
  CheckCircle2,
  Edit3,
  Loader2,
  Search,
  Save,
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
}

type Course = {
  id: number
  code: string
  title: string
  credits: number
  description: string
  is_active: boolean
  prerequisites: number[]
}

type CoursesResponse = {
  title: string
  section: string
  scope: Scope
  scope_error?: string | null
  courses: Course[]
  prerequisite_options: Course[]
}

type CourseForm = {
  code: string
  title: string
  credits: string
  description: string
  is_active: boolean
  prerequisites: number[]
}

function formFromCourse(course: Course): CourseForm {
  return {
    code: course.code,
    title: course.title,
    credits: String(course.credits),
    description: course.description ?? "",
    is_active: course.is_active,
    prerequisites: course.prerequisites ?? [],
  }
}

export default function ExecutiveAllCoursesPage() {
  const [scope, setScope] = useState<Scope | null>(null)
  const [scopeError, setScopeError] = useState("")
  const [courses, setCourses] = useState<Course[]>([])
  const [prerequisiteOptions, setPrerequisiteOptions] = useState<Course[]>([])
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [form, setForm] = useState<CourseForm | null>(null)
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    try {
      setIsLoading(true)
      const data = await apiFetch<CoursesResponse>("/executive/courses/all")
      setScope(data.scope)
      setScopeError(data.scope_error ?? "")
      setCourses(data.courses ?? [])
      setPrerequisiteOptions(data.prerequisite_options ?? [])
      setError("")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load courses.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial data hydration needs to sync state after the API response arrives.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData()
  }, [])

  const filteredCourses = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return courses
    return courses.filter((course) =>
      [course.code, course.title, course.description]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    )
  }, [courses, query])

  function startEditing(course: Course) {
    setEditingCourse(course)
    setForm(formFromCourse(course))
    setSuccess("")
    setError("")
  }

  function updateField(field: Exclude<keyof CourseForm, "prerequisites">, value: string | boolean) {
    setForm((current) => (current ? { ...current, [field]: value } : current))
  }

  function togglePrerequisite(courseId: number, checked: boolean) {
    setForm((current) =>
      current
        ? {
            ...current,
            prerequisites: checked
              ? [...current.prerequisites, courseId]
              : current.prerequisites.filter((id) => id !== courseId),
          }
        : current
    )
  }

  async function saveCourse(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingCourse || !form) return

    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/courses/all?course_id=${editingCourse.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...form,
          credits: Number(form.credits),
        }),
      })
      setSuccess("Course updated successfully.")
      setEditingCourse(null)
      setForm(null)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update course.")
    } finally {
      setIsSaving(false)
    }
  }

  async function archiveCourse(course: Course) {
    if (!confirm(`Archive ${course.code}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/executive/courses/all?course_id=${course.id}`, {
        method: "DELETE",
      })
      setSuccess("Course archived successfully.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to archive course.")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/courses", title: "Courses" },
          { href: "/executive/courses/all", title: "All Courses" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              All Courses
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Check and manage the course catalogue for your assigned school or centre.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-background px-3 py-2 text-sm">
            <span className="font-medium">{scope?.name ?? "Unassigned"}</span>
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
        {scopeError ? (
          <div className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-800">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{scopeError}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_24rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle className="text-lg">Course Catalogue</CardTitle>
                  <CardDescription>
                    {filteredCourses.length} of {courses.length} courses shown.
                  </CardDescription>
                </div>
                <div className="relative w-full sm:w-72">
                  <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search courses..."
                    className="pl-9"
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {filteredCourses.length === 0 ? (
                  <p className="py-10 text-center text-sm text-muted-foreground">
                    No courses found.
                  </p>
                ) : (
                  filteredCourses.map((course) => (
                    <div
                      key={course.id}
                      className="rounded-lg border border-border bg-background p-4 shadow-sm"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0 space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-sm font-semibold text-primary">
                              {course.code}
                            </span>
                            <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              {course.credits} credits
                            </span>
                            {!course.is_active ? (
                              <span className="rounded-md border border-border px-2 py-0.5 text-xs text-muted-foreground">
                                Archived
                              </span>
                            ) : null}
                          </div>
                          <h2 className="text-base font-semibold">{course.title}</h2>
                          <p className="line-clamp-2 text-sm leading-6 text-muted-foreground">
                            {course.description || "No description added."}
                          </p>
                          {course.prerequisites.length ? (
                            <p className="text-xs text-muted-foreground">
                              Prerequisites:{" "}
                              {course.prerequisites
                                .map((id) => courses.find((option) => option.id === id)?.code)
                                .filter(Boolean)
                                .join(", ")}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => startEditing(course)}>
                            <Edit3 className="size-4" />
                            Edit
                          </Button>
                          {course.is_active ? (
                            <Button variant="outline" size="sm" onClick={() => archiveCourse(course)}>
                              <Archive className="size-4" />
                              Archive
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">
                  {editingCourse ? "Edit Course" : "Course Editor"}
                </CardTitle>
                <CardDescription>
                  Select a course from the catalogue to update its details.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {editingCourse && form ? (
                  <form className="space-y-4" onSubmit={saveCourse}>
                    <div className="grid gap-3 sm:grid-cols-[1fr_7rem]">
                      <div className="space-y-2">
                        <Label htmlFor="edit-code">Course Code</Label>
                        <Input
                          id="edit-code"
                          value={form.code}
                          onChange={(event) => updateField("code", event.target.value.toUpperCase())}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="edit-credits">Credits</Label>
                        <Input
                          id="edit-credits"
                          type="number"
                          min="1"
                          value={form.credits}
                          onChange={(event) => updateField("credits", event.target.value)}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-title">Course Title</Label>
                      <Input
                        id="edit-title"
                        value={form.title}
                        onChange={(event) => updateField("title", event.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-description">Description</Label>
                      <Textarea
                        id="edit-description"
                        value={form.description}
                        rows={6}
                        onChange={(event) => updateField("description", event.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Prerequisite Courses</Label>
                      <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border border-border p-3">
                        {prerequisiteOptions
                          .filter((course) => course.id !== editingCourse.id)
                          .map((course) => (
                            <label key={course.id} className="flex items-start gap-2 text-sm">
                              <input
                                type="checkbox"
                                checked={form.prerequisites.includes(course.id)}
                                onChange={(event) => togglePrerequisite(course.id, event.target.checked)}
                              />
                              <span>
                                <span className="font-medium">{course.code}</span>
                                <span className="text-muted-foreground"> - {course.title}</span>
                              </span>
                            </label>
                          ))}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Students must complete every selected course before registering.
                      </p>
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={form.is_active}
                        onChange={(event) => updateField("is_active", event.target.checked)}
                      />
                      Active course
                    </label>
                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => {
                          setEditingCourse(null)
                          setForm(null)
                        }}
                      >
                        <X className="size-4" />
                        Cancel
                      </Button>
                      <Button type="submit" disabled={isSaving}>
                        {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                        {isSaving ? "Saving..." : "Save"}
                      </Button>
                    </div>
                  </form>
                ) : (
                  <p className="text-sm leading-6 text-muted-foreground">
                    The editor opens after you choose a course.
                  </p>
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}
