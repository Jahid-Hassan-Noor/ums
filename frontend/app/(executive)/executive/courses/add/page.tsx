"use client"

import { useEffect, useState } from "react"
import {
  AlertCircle,
  BookPlus,
  CheckCircle2,
  Loader2,
  Save,
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

type AddCourseResponse = {
  title: string
  section: string
  scope: Scope
  scope_error?: string | null
  prerequisite_options: CourseOption[]
}

type CourseOption = {
  id: number
  code: string
  title: string
}

const emptyForm = {
  code: "",
  title: "",
  credits: "3",
  description: "",
  prerequisites: [] as number[],
}

export default function ExecutiveAddCoursesPage() {
  const [scope, setScope] = useState<Scope | null>(null)
  const [scopeError, setScopeError] = useState("")
  const [prerequisiteOptions, setPrerequisiteOptions] = useState<CourseOption[]>([])
  const [form, setForm] = useState(emptyForm)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    async function loadData() {
      try {
        const data = await apiFetch<AddCourseResponse>("/executive/courses/add")
        setScope(data.scope)
        setScopeError(data.scope_error ?? "")
        setPrerequisiteOptions(data.prerequisite_options ?? [])
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to load course form.")
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  function updateField(field: Exclude<keyof typeof emptyForm, "prerequisites">, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function togglePrerequisite(courseId: number, checked: boolean) {
    setForm((current) => ({
      ...current,
      prerequisites: checked
        ? [...current.prerequisites, courseId]
        : current.prerequisites.filter((id) => id !== courseId),
    }))
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")
    setIsSubmitting(true)

    try {
      await apiFetch("/executive/courses/add", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          credits: Number(form.credits),
        }),
      })
      setSuccess("Course added successfully.")
      setForm(emptyForm)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to add course.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const canSubmit = Boolean(scope?.kind) && !scopeError

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/courses", title: "Courses" },
          { href: "/executive/courses/add", title: "Add Courses" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Add Courses
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Create academic courses for the school or centre assigned to your executive account.
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
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BookPlus className="size-5 text-primary" />
                  Course Details
                </CardTitle>
                <CardDescription>
                  Course code, title, credits, and catalogue description.
                </CardDescription>
              </CardHeader>
              <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-[12rem_minmax(0,1fr)_8rem]">
                    <div className="space-y-2">
                      <Label htmlFor="course-code">Course Code</Label>
                      <Input
                        id="course-code"
                        value={form.code}
                        placeholder="CSC101"
                        onChange={(event) => updateField("code", event.target.value.toUpperCase())}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="course-title">Course Title</Label>
                      <Input
                        id="course-title"
                        value={form.title}
                        onChange={(event) => updateField("title", event.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="course-credits">Credits</Label>
                      <Input
                        id="course-credits"
                        type="number"
                        min="1"
                        value={form.credits}
                        onChange={(event) => updateField("credits", event.target.value)}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="course-description">Description</Label>
                    <Textarea
                      id="course-description"
                      value={form.description}
                      onChange={(event) => updateField("description", event.target.value)}
                      rows={7}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Prerequisite Courses</Label>
                    <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border border-border p-3">
                      {prerequisiteOptions.length ? (
                        prerequisiteOptions.map((course) => (
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
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">No prerequisite courses are available.</p>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Students must complete every selected course before registering.
                    </p>
                  </div>
                </CardContent>
                <div className="flex justify-end border-t p-4">
                  <Button type="submit" disabled={isSubmitting || !canSubmit}>
                    {isSubmitting ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Save className="size-4" />
                    )}
                    {isSubmitting ? "Saving..." : "Add Course"}
                  </Button>
                </div>
              </form>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Offering Unit</CardTitle>
                <CardDescription>
                  New courses are attached to your assigned scope.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="font-medium">{scope?.name ?? "Unassigned"}</p>
                <p className="text-muted-foreground">
                  {scope?.kind ? `${scope.kind === "school" ? "School" : "Centre"} ${scope.code}` : "No active assignment"}
                </p>
              </CardContent>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}
