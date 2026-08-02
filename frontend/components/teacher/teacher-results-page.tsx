"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  CheckCircle2,
  ClipboardList,
  FilePenLine,
  Loader2,
  RefreshCw,
  Save,
  Send,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import {
  ResultBatchHeader,
  ResultSummaryCards,
  ResultTabsNav,
} from "@/components/results/result-display"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

export type TeacherResultsView = "overview" | "submit" | "draft" | "completed"

type Offering = {
  id: number
  course_code: string
  course_title: string
  credits: string
  section: string
  semester_id: number
  semester: string
  semester_active: boolean
  teacher: string
}

type ResultRecord = {
  id?: number
  student_id: number
  student_number: string
  student_name: string
  score: string
  grade: string
  grade_points: string
  remarks: string
}

type ResultBatch = {
  id: number
  status: "draft" | "review" | "approved" | "published"
  status_label: string
  offering: Offering
  created_by: string
  record_count: number
  enrollment_count: number
  submitted_at: string | null
  reviewed_at: string | null
  published_at: string | null
  updated_at: string | null
  latest_review: {
    status: string
    note: string
    author: string
    created_at: string
  } | null
  records?: ResultRecord[]
}

type OfferingRow = Offering & {
  student_count: number
  batch: ResultBatch | null
  status: "not_started" | ResultBatch["status"]
  status_label: string
}

type ResultsResponse = {
  title: string
  summary: {
    offerings: number
    not_started: number
    draft: number
    review: number
    approved: number
    published: number
  }
  offerings: OfferingRow[]
  selected_offering: Offering | null
  selected_batch: ResultBatch | null
  roster: ResultRecord[]
}

const TABS: Array<{ view: TeacherResultsView; label: string; href: string }> = [
  { view: "overview", label: "Overview", href: "/teacher/results" },
  { view: "submit", label: "Enter & Submit", href: "/teacher/results/submit" },
  { view: "draft", label: "Drafts", href: "/teacher/results/draft" },
  { view: "completed", label: "Submitted", href: "/teacher/results/completed" },
]

function endpointForView(view: TeacherResultsView, offeringId?: number | null) {
  if (view === "overview") return "/teacher/results"
  const endpoint = `/teacher/results/${view}`
  if (view === "submit" && offeringId)
    return `${endpoint}?offering_id=${offeringId}`
  return endpoint
}

function formatDate(value: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString()
}

function Summary({ data }: { data: ResultsResponse["summary"] }) {
  return (
    <ResultSummaryCards
      cards={[
        { label: "Course offerings", value: data.offerings, icon: ClipboardList },
        { label: "Draft batches", value: data.draft, icon: FilePenLine },
        { label: "Under review", value: data.review, icon: Send },
        { label: "Published", value: data.published, icon: CheckCircle2 },
      ]}
    />
  )
}

function OfferingCards({ rows }: { rows: OfferingRow[] }) {
  if (!rows.length) {
    return (
      <p className="rounded-xl border border-dashed bg-background p-6 text-sm text-muted-foreground">
        No course offerings match this result stage.
      </p>
    )
  }
  return (
    <section className="grid gap-4 lg:grid-cols-2">
      {rows.map((row) => (
        <Card key={row.id} className="border-border/70 shadow-sm">
          <ResultBatchHeader
            title={`${row.course_code} · ${row.course_title}`}
            description={`${row.semester} · Section ${
              row.section || "—"
            } · ${row.student_count} students`}
            status={row.status}
            statusLabel={row.status_label}
          />
          <CardContent className="space-y-3 text-sm">
            {row.batch?.latest_review ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800">
                <strong>Latest review:</strong> {row.batch.latest_review.note}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-muted-foreground">
              <span>
                Records: {row.batch?.record_count ?? 0}/{row.student_count}
              </span>
              <span>
                Submitted: {formatDate(row.batch?.submitted_at ?? null)}
              </span>
              <span>
                Published: {formatDate(row.batch?.published_at ?? null)}
              </span>
            </div>
            {(row.status === "not_started" || row.status === "draft") && (
              <Link
                href={`/teacher/results/submit?offering_id=${row.id}`}
                className="inline-flex h-8 items-center justify-center rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground shadow-sm transition hover:bg-primary/90"
              >
                {row.status === "draft" ? "Continue draft" : "Enter results"}
              </Link>
            )}
          </CardContent>
        </Card>
      ))}
    </section>
  )
}

function ResultEditor({
  data,
  selectedOfferingId,
  onOfferingChange,
  onSaved,
}: {
  data: ResultsResponse
  selectedOfferingId: number | null
  onOfferingChange: (offeringId: number) => void
  onSaved: (offeringId: number) => Promise<void>
}) {
  const [records, setRecords] = useState<ResultRecord[]>(data.roster ?? [])
  const [busy, setBusy] = useState<"save" | "submit" | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const locked = ["review", "approved", "published"].includes(
    data.selected_batch?.status ?? ""
  )
  const scored = records.filter((record) => record.score !== "").length

  function updateRecord(
    index: number,
    field: "score" | "remarks",
    value: string
  ) {
    setRecords((current) =>
      current.map((record, recordIndex) =>
        recordIndex === index ? { ...record, [field]: value } : record
      )
    )
  }

  async function save(action: "save" | "submit") {
    if (!data.selected_offering) return
    setBusy(action)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string }>(
        "/teacher/results/submit",
        {
          method: "POST",
          body: JSON.stringify({
            offering_id: data.selected_offering.id,
            action,
            records: records.map((record) => ({
              student_id: record.student_id,
              score: record.score,
              remarks: record.remarks,
            })),
          }),
        }
      )
      setSuccess(response.message)
      await onSaved(data.selected_offering.id)
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to save results."
      )
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="space-y-4">
      <Card className="border-border/70 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg">Select course offering</CardTitle>
          <CardDescription>
            Drafts can be edited until they are submitted for executive review.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <select
            value={selectedOfferingId ?? ""}
            onChange={(event) => onOfferingChange(Number(event.target.value))}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          >
            {data.offerings.map((offering) => (
              <option key={offering.id} value={offering.id}>
                {offering.course_code} · {offering.course_title} ·{" "}
                {offering.semester}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      {data.selected_offering ? (
        <Card className="border-border/70 shadow-sm">
          <ResultBatchHeader
            title={`${data.selected_offering.course_code} · ${data.selected_offering.course_title}`}
            description={`${data.selected_offering.semester} · Section ${
              data.selected_offering.section || "—"
            } · ${scored}/${records.length} scores entered`}
            status={data.selected_batch?.status ?? "not_started"}
            statusLabel={data.selected_batch?.status_label ?? "Not started"}
          />
          <CardContent className="space-y-4">
            {data.selected_batch?.latest_review ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                <strong>Executive note:</strong>{" "}
                {data.selected_batch.latest_review.note}
              </p>
            ) : null}
            {error ? (
              <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            ) : null}
            {success ? (
              <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                {success}
              </p>
            ) : null}
            {!records.length ? (
              <p className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
                No active enrollments were found for this offering.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[820px] border-collapse text-sm">
                  <thead>
                    <tr className="border-b bg-muted/60 text-left">
                      <th className="px-3 py-2 font-medium">Student</th>
                      <th className="px-3 py-2 font-medium">Student ID</th>
                      <th className="w-32 px-3 py-2 font-medium">
                        Score / 100
                      </th>
                      <th className="px-3 py-2 font-medium">Grade</th>
                      <th className="min-w-64 px-3 py-2 font-medium">
                        Remarks
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record, index) => (
                      <tr
                        key={record.student_id}
                        className="border-b last:border-0"
                      >
                        <td className="px-3 py-2 font-medium">
                          {record.student_name}
                        </td>
                        <td className="px-3 py-2">
                          {record.student_number || "—"}
                        </td>
                        <td className="px-3 py-2">
                          <Input
                            type="number"
                            min="0"
                            max="100"
                            step="0.01"
                            value={record.score}
                            disabled={locked}
                            onChange={(event) =>
                              updateRecord(index, "score", event.target.value)
                            }
                          />
                        </td>
                        <td className="px-3 py-2 font-semibold">
                          {record.grade || "Calculated on save"}
                        </td>
                        <td className="px-3 py-2">
                          <Textarea
                            value={record.remarks}
                            disabled={locked}
                            rows={2}
                            onChange={(event) =>
                              updateRecord(index, "remarks", event.target.value)
                            }
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="flex flex-wrap justify-end gap-2">
              <Button
                variant="outline"
                disabled={locked || !records.length || busy !== null}
                onClick={() => void save("save")}
              >
                {busy === "save" ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Save />
                )}
                Save draft
              </Button>
              <Button
                disabled={locked || !records.length || busy !== null}
                onClick={() => void save("submit")}
              >
                {busy === "submit" ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Send />
                )}
                Submit for review
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <p className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
          No assigned course offerings are available.
        </p>
      )}
    </section>
  )
}

export function TeacherResultsPage({ view }: { view: TeacherResultsView }) {
  const initialOfferingId = useMemo(() => {
    if (typeof window === "undefined") return null
    const value = new URLSearchParams(window.location.search).get("offering_id")
    return value ? Number(value) : null
  }, [])
  const [selectedOfferingId, setSelectedOfferingId] = useState<number | null>(
    initialOfferingId
  )
  const [data, setData] = useState<ResultsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(
    async (offeringId = selectedOfferingId) => {
      const response = await apiFetch<ResultsResponse>(
        endpointForView(view, offeringId)
      )
      setData(response)
      if (view === "submit" && response.selected_offering) {
        setSelectedOfferingId(response.selected_offering.id)
      }
    },
    [selectedOfferingId, view]
  )

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          if (active)
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load results."
            )
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [loadData])

  async function chooseOffering(offeringId: number) {
    setSelectedOfferingId(offeringId)
    setLoading(true)
    setError("")
    try {
      await loadData(offeringId)
      window.history.replaceState(
        null,
        "",
        `/teacher/results/submit?offering_id=${offeringId}`
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load the course roster."
      )
    } finally {
      setLoading(false)
    }
  }

  const activeTab = TABS.find((tab) => tab.view === view)
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/results", title: "Results" },
          ...(view === "overview"
            ? []
            : [
                {
                  href: activeTab?.href ?? "/teacher/results",
                  title: activeTab?.label ?? "Results",
                },
              ]),
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="space-y-4 border-b border-border/70 pb-5">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {activeTab?.label ?? "Results"}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                Record final marks, keep partial work as a draft, and submit
                complete batches for executive approval.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => void loadData()}
              disabled={loading}
            >
              <RefreshCw className={loading ? "animate-spin" : ""} />
              Refresh
            </Button>
          </div>
          <ResultTabsNav tabs={TABS} active={view} />
        </section>

        {loading && !data ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Loading result workspace
          </p>
        ) : null}
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        {data ? <Summary data={data.summary} /> : null}
        {data && view === "submit" ? (
          <ResultEditor
            key={`${data.selected_offering?.id ?? "none"}-${data.selected_batch?.updated_at ?? "new"}`}
            data={data}
            selectedOfferingId={selectedOfferingId}
            onOfferingChange={(offeringId) => void chooseOffering(offeringId)}
            onSaved={async (offeringId) => {
              await loadData(offeringId)
            }}
          />
        ) : null}
        {data && view !== "submit" ? (
          <OfferingCards rows={data.offerings} />
        ) : null}
      </main>
    </div>
  )
}
