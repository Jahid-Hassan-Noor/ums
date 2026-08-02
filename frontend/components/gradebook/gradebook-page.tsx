"use client"

import { useCallback, useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react"
import {
  Calculator,
  CheckCircle2,
  Eye,
  FileSpreadsheet,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Send,
  Settings,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  loadAdminGradebook,
  loadStudentGradebook,
  loadTeacherGradebook,
  runTeacherGradebookAction,
  saveGradebookScale,
  type AdminGradebookResponse,
  type GradebookCourse,
  type GradebookGrade,
  type GradebookScale,
  type GradebookScaleRange,
  type TeacherGradebookAction,
  type TeacherGradebookResponse,
} from "@/lib/gradebook"

type GradeStatus = GradebookGrade["status"]

const selectClass =
  "h-9 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"

const statusOptions: Array<{ value: GradeStatus; label: string }> = [
  { value: "draft", label: "Draft" },
  { value: "released", label: "Released" },
  { value: "missing", label: "Missing" },
  { value: "excused", label: "Excused" },
]

function formatDate(value: string | null) {
  if (!value) return "Not updated"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? "Not updated" : date.toLocaleString()
}

function cloneScale(scale: GradebookScale): GradebookScale {
  return {
    ...scale,
    ranges: scale.ranges.map((row) => ({ ...row })),
  }
}

function EmptyState({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-dashed bg-muted/20 p-6 text-sm text-muted-foreground">
      {children}
    </div>
  )
}

function Message({ error, success }: { error: string; success: string }) {
  if (!error && !success) return null
  return (
    <div
      className={`rounded-lg border p-3 text-sm ${
        error
          ? "border-destructive/30 bg-destructive/10 text-destructive"
          : "border-emerald-200 bg-emerald-50 text-emerald-800"
      }`}
    >
      {error || success}
    </div>
  )
}

export function AdminGradebookPage() {
  const [data, setData] = useState<AdminGradebookResponse | null>(null)
  const [draft, setDraft] = useState<GradebookScale | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const response = await loadAdminGradebook()
      setData(response)
      const scale = response.scales.find((item) => item.is_default) ?? response.scales[0]
      setDraft(scale ? cloneScale(scale) : null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load gradebook settings.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  function updateRange(index: number, field: keyof GradebookScaleRange, value: string | boolean) {
    if (!draft) return
    setDraft({
      ...draft,
      ranges: draft.ranges.map((row, rowIndex) =>
        rowIndex === index ? { ...row, [field]: value } : row
      ),
    })
    setSuccess("")
  }

  function addRange() {
    if (!draft) return
    setDraft({
      ...draft,
      ranges: [
        ...draft.ranges,
        {
          letter: "",
          min_score: "0.00",
          max_score: "0.00",
          grade_points: "0.00",
          outcome: "",
          is_passing: false,
          sort_order: draft.ranges.length + 1,
        },
      ],
    })
  }

  async function save() {
    if (!draft) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await saveGradebookScale(draft)
      setData(response)
      const scale = response.scales.find((item) => item.id === draft.id) ?? response.scales[0]
      setDraft(scale ? cloneScale(scale) : null)
      setSuccess(response.message ?? "Grade scale saved.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save grade scale.")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <Header />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 pb-8">
        <section className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Gradebook Criteria</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {data?.summary.scales ?? 0} scales · {data?.summary.items ?? 0} items · {data?.summary.grades ?? 0} grades
            </p>
          </div>
          <Button variant="outline" onClick={() => void load()}>
            <RefreshCw /> Refresh
          </Button>
        </section>

        <Message error={error} success={success} />

        {draft ? (
          <Card className="border-border/70 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Settings className="size-5" /> Active Scale
              </CardTitle>
              <CardDescription>
                Updated {formatDate(draft.updated_at)}{draft.updated_by ? ` by ${draft.updated_by}` : ""}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-4 md:grid-cols-[1fr_2fr]">
                <div className="space-y-2">
                  <Label htmlFor="scale-name">Scale name</Label>
                  <Input
                    id="scale-name"
                    value={draft.name}
                    onChange={(event) => setDraft({ ...draft, name: event.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="scale-description">Description</Label>
                  <Input
                    id="scale-description"
                    value={draft.description}
                    onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                  />
                </div>
              </div>

              <div className="overflow-x-auto rounded-lg border">
                <table className="w-full min-w-[760px] text-sm">
                  <thead className="bg-muted/60 text-left">
                    <tr>
                      <th className="px-3 py-2 font-medium">Grade</th>
                      <th className="px-3 py-2 font-medium">Minimum</th>
                      <th className="px-3 py-2 font-medium">Maximum</th>
                      <th className="px-3 py-2 font-medium">Points</th>
                      <th className="px-3 py-2 font-medium">Outcome</th>
                      <th className="px-3 py-2 font-medium">Passing</th>
                    </tr>
                  </thead>
                  <tbody>
                    {draft.ranges.map((row, index) => (
                      <tr key={`${row.id ?? "new"}-${index}`} className="border-t">
                        <td className="px-3 py-2">
                          <Input value={row.letter} onChange={(event) => updateRange(index, "letter", event.target.value)} />
                        </td>
                        <td className="px-3 py-2">
                          <Input value={row.min_score} onChange={(event) => updateRange(index, "min_score", event.target.value)} />
                        </td>
                        <td className="px-3 py-2">
                          <Input value={row.max_score} onChange={(event) => updateRange(index, "max_score", event.target.value)} />
                        </td>
                        <td className="px-3 py-2">
                          <Input value={row.grade_points} onChange={(event) => updateRange(index, "grade_points", event.target.value)} />
                        </td>
                        <td className="px-3 py-2">
                          <Input value={row.outcome} onChange={(event) => updateRange(index, "outcome", event.target.value)} />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            className="size-4 accent-primary"
                            type="checkbox"
                            checked={row.is_passing}
                            onChange={(event) => updateRange(index, "is_passing", event.target.checked)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-wrap justify-between gap-3">
                <Button variant="outline" onClick={addRange}>
                  <Plus /> Add Range
                </Button>
                <Button onClick={() => void save()} disabled={saving}>
                  {saving ? <Loader2 className="animate-spin" /> : <Save />} Save Scale
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <EmptyState>No grade scale is available.</EmptyState>
        )}
      </main>
    </div>
  )
}

type TeacherFormState = {
  categoryTitle: string
  categoryWeight: string
  itemTitle: string
  itemMaxScore: string
  itemWeight: string
  itemCategoryId: string
}

const initialTeacherForm: TeacherFormState = {
  categoryTitle: "",
  categoryWeight: "0",
  itemTitle: "",
  itemMaxScore: "100",
  itemWeight: "0",
  itemCategoryId: "",
}

export function TeacherGradebookPage() {
  const [data, setData] = useState<TeacherGradebookResponse | null>(null)
  const [selectedOfferingId, setSelectedOfferingId] = useState<number | null>(null)
  const [form, setForm] = useState(initialTeacherForm)
  const [gradeDrafts, setGradeDrafts] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const load = useCallback(async (offeringId?: number | null) => {
    setLoading(true)
    setError("")
    try {
      const response = await loadTeacherGradebook(offeringId)
      setData(response)
      setSelectedOfferingId(response.selected?.offering.id ?? response.offerings[0]?.id ?? null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load gradebook.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(null), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const selected = data?.selected ?? null

  const gradeMap = useMemo(() => {
    const map = new Map<string, GradebookGrade>()
    selected?.grades.forEach((grade) => {
      map.set(`${grade.item_id}:${grade.student_id}`, grade)
    })
    return map
  }, [selected])

  async function run(action: TeacherGradebookAction, busyKey: string) {
    setBusy(busyKey)
    setError("")
    setSuccess("")
    try {
      const response = await runTeacherGradebookAction(action)
      setData(response)
      setSuccess(response.message ?? "Gradebook updated.")
      if (action.action === "save_category" || action.action === "save_item") {
        setForm(initialTeacherForm)
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update gradebook.")
    } finally {
      setBusy("")
    }
  }

  function gradeValue(itemId: number, studentId: number) {
    const key = `${itemId}:${studentId}`
    if (gradeDrafts[key] !== undefined) return gradeDrafts[key]
    return gradeMap.get(key)?.raw_score ?? ""
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <Header />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 pb-8">
        <section className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Gradebook</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {selected ? `${selected.offering.course_code} · ${selected.offering.semester}` : "No assigned offering"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => void load(selectedOfferingId)}>
              <RefreshCw /> Refresh
            </Button>
            {selected ? (
              <Button
                variant="outline"
                onClick={() =>
                  void run({ action: "sync_sources", offering_id: selected.offering.id }, "sync")
                }
                disabled={busy === "sync"}
              >
                {busy === "sync" ? <Loader2 className="animate-spin" /> : <FileSpreadsheet />} Sync Sources
              </Button>
            ) : null}
          </div>
        </section>

        <Message error={error} success={success} />

        {data?.offerings.length ? (
          <div className="max-w-xl space-y-2">
            <Label htmlFor="gradebook-offering">Course offering</Label>
            <select
              id="gradebook-offering"
              className={selectClass}
              value={selectedOfferingId ?? ""}
              onChange={(event) => {
                const value = Number(event.target.value)
                setSelectedOfferingId(value)
                void load(value)
              }}
            >
              {data.offerings.map((offering) => (
                <option key={offering.id} value={offering.id}>
                  {offering.course_code} · {offering.course_title} · {offering.section || "Main"} · {offering.semester}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {selected ? (
          <>
            <section className="grid gap-4 lg:grid-cols-2">
              <Card className="border-border/70 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">Categories</CardTitle>
                  <CardDescription>{selected.categories.length} configured</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-[1fr_8rem_auto]">
                    <Input
                      placeholder="Category title"
                      value={form.categoryTitle}
                      onChange={(event) => setForm({ ...form, categoryTitle: event.target.value })}
                    />
                    <Input
                      placeholder="Weight"
                      value={form.categoryWeight}
                      onChange={(event) => setForm({ ...form, categoryWeight: event.target.value })}
                    />
                    <Button
                      onClick={() =>
                        void run(
                          {
                            action: "save_category",
                            offering_id: selected.offering.id,
                            title: form.categoryTitle,
                            weight: form.categoryWeight,
                            release_to_students: false,
                            is_active: true,
                            sort_order: selected.categories.length + 1,
                          },
                          "category"
                        )
                      }
                      disabled={busy === "category"}
                    >
                      {busy === "category" ? <Loader2 className="animate-spin" /> : <Plus />} Add
                    </Button>
                  </div>
                  {selected.categories.length ? (
                    <div className="flex flex-wrap gap-2">
                      {selected.categories.map((category) => (
                        <Badge key={category.id} variant="outline">
                          {category.title} · {category.weight}%
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <EmptyState>No categories yet.</EmptyState>
                  )}
                </CardContent>
              </Card>

              <Card className="border-border/70 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">Grade Items</CardTitle>
                  <CardDescription>{selected.items.length} active items</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input
                      placeholder="Item title"
                      value={form.itemTitle}
                      onChange={(event) => setForm({ ...form, itemTitle: event.target.value })}
                    />
                    <select
                      className={selectClass}
                      value={form.itemCategoryId}
                      onChange={(event) => setForm({ ...form, itemCategoryId: event.target.value })}
                    >
                      <option value="">Uncategorized</option>
                      {selected.categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.title}
                        </option>
                      ))}
                    </select>
                    <Input
                      placeholder="Max score"
                      value={form.itemMaxScore}
                      onChange={(event) => setForm({ ...form, itemMaxScore: event.target.value })}
                    />
                    <Input
                      placeholder="Weight"
                      value={form.itemWeight}
                      onChange={(event) => setForm({ ...form, itemWeight: event.target.value })}
                    />
                  </div>
                  <Button
                    onClick={() =>
                      void run(
                        {
                          action: "save_item",
                          offering_id: selected.offering.id,
                          category_id: form.itemCategoryId ? Number(form.itemCategoryId) : null,
                          title: form.itemTitle,
                          item_type: "manual",
                          max_score: form.itemMaxScore,
                          weight: form.itemWeight,
                          release_to_students: false,
                          is_extra_credit: false,
                          is_active: true,
                          sort_order: selected.items.length + 1,
                        },
                        "item"
                      )
                    }
                    disabled={busy === "item"}
                  >
                    {busy === "item" ? <Loader2 className="animate-spin" /> : <Plus />} Add Item
                  </Button>
                </CardContent>
              </Card>
            </section>

            <GradebookMatrix
              course={selected}
              gradeMap={gradeMap}
              gradeValue={gradeValue}
              setGradeDrafts={setGradeDrafts}
              busy={busy}
              onRun={run}
            />

            <Card className="border-border/70 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Send className="size-5" /> Official Result Draft
                </CardTitle>
                <CardDescription>{selected.totals.length} student totals available</CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={() =>
                    void run(
                      { action: "send_to_result_draft", offering_id: selected.offering.id },
                      "result-draft"
                    )
                  }
                  disabled={busy === "result-draft"}
                >
                  {busy === "result-draft" ? <Loader2 className="animate-spin" /> : <Calculator />}
                  Copy Totals To Result Draft
                </Button>
              </CardContent>
            </Card>
          </>
        ) : (
          <EmptyState>No assigned course offering is available for gradebook management.</EmptyState>
        )}
      </main>
    </div>
  )
}

function GradebookMatrix({
  course,
  gradeMap,
  gradeValue,
  setGradeDrafts,
  busy,
  onRun,
}: {
  course: GradebookCourse
  gradeMap: Map<string, GradebookGrade>
  gradeValue: (itemId: number, studentId: number) => string
  setGradeDrafts: Dispatch<SetStateAction<Record<string, string>>>
  busy: string
  onRun: (action: TeacherGradebookAction, busyKey: string) => Promise<void>
}) {
  const totalMap = useMemo(() => {
    const map = new Map<number, string>()
    course.totals.forEach((total) => map.set(total.student_id, `${total.score || "0.00"} ${total.grade}`.trim()))
    return map
  }, [course.totals])

  if (!course.items.length) {
    return <EmptyState>No grade items are available for this course offering.</EmptyState>
  }

  return (
    <Card className="border-border/70 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">Grade Entry</CardTitle>
        <CardDescription>{course.students.length} students · {course.items.length} items</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full min-w-[900px] text-sm">
            <thead className="bg-muted/60 text-left">
              <tr>
                <th className="sticky left-0 z-10 bg-muted/60 px-3 py-2 font-medium">Student</th>
                {course.items.map((item) => (
                  <th key={item.id} className="px-3 py-2 font-medium">
                    <div className="flex min-w-36 flex-col gap-1">
                      <span>{item.title}</span>
                      <span className="text-xs font-normal text-muted-foreground">
                        {item.item_type_label} · /{item.max_score}
                      </span>
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() =>
                          void onRun(
                            { action: "release_item", offering_id: course.offering.id, item_id: item.id },
                            `release-${item.id}`
                          )
                        }
                        disabled={busy === `release-${item.id}`}
                      >
                        {item.release_to_students ? <CheckCircle2 /> : <Eye />}
                        {item.release_to_students ? "Released" : "Release"}
                      </Button>
                    </div>
                  </th>
                ))}
                <th className="px-3 py-2 font-medium">Total</th>
              </tr>
            </thead>
            <tbody>
              {course.students.map((student) => (
                <tr key={student.id} className="border-t align-top">
                  <td className="sticky left-0 z-10 min-w-48 bg-background px-3 py-3">
                    <div className="font-medium">{student.name}</div>
                    <div className="text-xs text-muted-foreground">{student.student_number || student.username}</div>
                  </td>
                  {course.items.map((item) => {
                    const key = `${item.id}:${student.id}`
                    const grade = gradeMap.get(key)
                    const status = grade?.status ?? "draft"
                    return (
                      <td key={item.id} className="px-3 py-3">
                        <div className="flex min-w-36 flex-col gap-2">
                          <Input
                            value={gradeValue(item.id, student.id)}
                            onChange={(event) =>
                              setGradeDrafts((current) => ({
                                ...current,
                                [key]: event.target.value,
                              }))
                            }
                          />
                          <select
                            className={selectClass}
                            defaultValue={status}
                            onChange={(event) =>
                              void onRun(
                                {
                                  action: "update_grade",
                                  offering_id: course.offering.id,
                                  item_id: item.id,
                                  student_id: student.id,
                                  raw_score: gradeValue(item.id, student.id),
                                  status: event.target.value as GradeStatus,
                                },
                                key
                              )
                            }
                          >
                            {statusOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              void onRun(
                                {
                                  action: "update_grade",
                                  offering_id: course.offering.id,
                                  item_id: item.id,
                                  student_id: student.id,
                                  raw_score: gradeValue(item.id, student.id),
                                  status,
                                },
                                key
                              )
                            }
                            disabled={busy === key}
                          >
                            {busy === key ? <Loader2 className="animate-spin" /> : <Save />} Save
                          </Button>
                        </div>
                      </td>
                    )
                  })}
                  <td className="px-3 py-3 font-medium">{totalMap.get(student.id) || "0.00"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

export function StudentGradebookPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof loadStudentGradebook>> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError("")
      try {
        setData(await loadStudentGradebook())
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to load gradebook.")
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <Header />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 pb-8">
        <section className="border-b border-border pb-4">
          <h1 className="text-2xl font-semibold tracking-tight">My Gradebook</h1>
          <p className="mt-1 text-sm text-muted-foreground">{data?.courses.length ?? 0} current courses</p>
        </section>
        {error ? <Message error={error} success="" /> : null}
        {data?.courses.length ? (
          <div className="grid gap-4">
            {data.courses.map((course) => (
              <StudentCourseCard key={course.offering.id} course={course} />
            ))}
          </div>
        ) : (
          <EmptyState>No released formative grades are available.</EmptyState>
        )}
      </main>
    </div>
  )
}

function StudentCourseCard({ course }: { course: GradebookCourse }) {
  const total = course.totals[0]
  const gradeByItem = useMemo(() => {
    const map = new Map<number, GradebookGrade>()
    course.grades.forEach((grade) => map.set(grade.item_id, grade))
    return map
  }, [course.grades])

  return (
    <Card className="border-border/70 shadow-sm">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-lg">
              {course.offering.course_code} · {course.offering.course_title}
            </CardTitle>
            <CardDescription>
              {course.offering.semester} · Section {course.offering.section || "Main"}
            </CardDescription>
          </div>
          <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">
            {total?.score || "0.00"} {total?.grade || ""}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {course.items.length ? (
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="bg-muted/60 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Item</th>
                  <th className="px-3 py-2 font-medium">Type</th>
                  <th className="px-3 py-2 font-medium">Score</th>
                  <th className="px-3 py-2 font-medium">Feedback</th>
                </tr>
              </thead>
              <tbody>
                {course.items.map((item) => {
                  const grade = gradeByItem.get(item.id)
                  return (
                    <tr key={item.id} className="border-t">
                      <td className="px-3 py-2 font-medium">{item.title}</td>
                      <td className="px-3 py-2">{item.item_type_label}</td>
                      <td className="px-3 py-2">
                        {grade?.raw_score || "0.00"} / {item.max_score}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {grade?.feedback || "—"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState>No released grade items for this course.</EmptyState>
        )}
      </CardContent>
    </Card>
  )
}
