"use client"

import { useCallback, useEffect, useState } from "react"
import {
  CheckCircle2,
  ClipboardCheck,
  FileClock,
  FileStack,
  Loader2,
  RefreshCw,
  RotateCcw,
  Send,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import {
  ResultBatchHeader,
  ResultSummaryCards,
  ResultTabsNav,
} from "@/components/results/result-display"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

export type ExecutiveResultsView =
  | "overview"
  | "semester"
  | "review"
  | "publication"
  | "previous"

type Scope = {
  kind: "school" | "center" | null
  id: number | null
  code: string
  name: string
  academic_workflows: boolean
}

type ResultRecord = {
  id: number
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
  offering: {
    id: number
    course_code: string
    course_title: string
    credits: string
    section: string
    semester: string
    semester_active: boolean
    teacher: string
  }
  created_by: string
  record_count: number
  enrollment_count: number
  submitted_at: string | null
  reviewed_at: string | null
  published_at: string | null
  latest_review: {
    status: string
    note: string
    author: string
    created_at: string
  } | null
  records: ResultRecord[]
}

type ResultsResponse = {
  title: string
  scope: Scope
  scope_error: string | null
  summary: {
    batches: number
    records: number
    draft: number
    review: number
    approved: number
    published: number
  }
  batches: ResultBatch[]
}

const TABS: Array<{ view: ExecutiveResultsView; label: string; href: string }> =
  [
    { view: "overview", label: "Overview", href: "/executive/results" },
    {
      view: "semester",
      label: "Current Semester",
      href: "/executive/results/semester",
    },
    { view: "review", label: "Review", href: "/executive/results/review" },
    {
      view: "publication",
      label: "Publication",
      href: "/executive/results/publication",
    },
    {
      view: "previous",
      label: "Published",
      href: "/executive/results/previous",
    },
  ]

function endpointForView(view: ExecutiveResultsView) {
  return view === "overview"
    ? "/executive/results"
    : `/executive/results/${view}`
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
        { label: "Result batches", value: data.batches, icon: FileStack },
        { label: "Under review", value: data.review, icon: FileClock },
        { label: "Approved", value: data.approved, icon: ClipboardCheck },
        { label: "Published", value: data.published, icon: CheckCircle2 },
      ]}
    />
  )
}

function BatchCard({
  batch,
  view,
  note,
  busy,
  onNoteChange,
  onAction,
}: {
  batch: ResultBatch
  view: ExecutiveResultsView
  note: string
  busy: number | null
  onNoteChange: (note: string) => void
  onAction: (
    batch: ResultBatch,
    action: "approve" | "return" | "publish"
  ) => Promise<void>
}) {
  return (
    <Card className="border-border/70 shadow-sm">
      <ResultBatchHeader
        title={`${batch.offering.course_code} · ${batch.offering.course_title}`}
        description={`${batch.offering.semester} · Section ${
          batch.offering.section || "—"
        } · Teacher ${batch.offering.teacher || batch.created_by || "—"}`}
        status={batch.status}
        statusLabel={batch.status_label}
      />
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <span>
            Records: {batch.record_count}/{batch.enrollment_count}
          </span>
          <span>Submitted: {formatDate(batch.submitted_at)}</span>
          <span>Reviewed: {formatDate(batch.reviewed_at)}</span>
          <span>Published: {formatDate(batch.published_at)}</span>
        </div>
        {batch.latest_review ? (
          <p className="rounded-lg border bg-muted/40 p-3 text-sm">
            <strong>{batch.latest_review.author || "Reviewer"}:</strong>{" "}
            {batch.latest_review.note}
          </p>
        ) : null}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-sm">
            <thead>
              <tr className="border-b bg-muted/60 text-left">
                <th className="px-3 py-2 font-medium">Student</th>
                <th className="px-3 py-2 font-medium">Student ID</th>
                <th className="px-3 py-2 text-center font-medium">Score</th>
                <th className="px-3 py-2 text-center font-medium">Grade</th>
                <th className="px-3 py-2 font-medium">Remarks</th>
              </tr>
            </thead>
            <tbody>
              {batch.records.map((record) => (
                <tr key={record.id} className="border-b last:border-0">
                  <td className="px-3 py-2 font-medium">
                    {record.student_name}
                  </td>
                  <td className="px-3 py-2">{record.student_number || "—"}</td>
                  <td className="px-3 py-2 text-center">
                    {record.score || "—"}
                  </td>
                  <td className="px-3 py-2 text-center font-semibold">
                    {record.grade || "—"}
                  </td>
                  <td className="px-3 py-2">{record.remarks || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {view === "review" || view === "publication" ? (
          <div className="space-y-3 border-t pt-4">
            <Textarea
              value={note}
              rows={3}
              placeholder={
                view === "review"
                  ? "Add an approval note, or explain what the teacher must correct before returning the batch."
                  : "Optional publication note."
              }
              onChange={(event) => onNoteChange(event.target.value)}
            />
            <div className="flex flex-wrap justify-end gap-2">
              {view === "review" ? (
                <>
                  <Button
                    variant="outline"
                    disabled={busy !== null}
                    onClick={() => void onAction(batch, "return")}
                  >
                    {busy === batch.id ? (
                      <Loader2 className="animate-spin" />
                    ) : (
                      <RotateCcw />
                    )}
                    Return to teacher
                  </Button>
                  <Button
                    disabled={busy !== null}
                    onClick={() => void onAction(batch, "approve")}
                  >
                    {busy === batch.id ? (
                      <Loader2 className="animate-spin" />
                    ) : (
                      <CheckCircle2 />
                    )}
                    Approve batch
                  </Button>
                </>
              ) : (
                <Button
                  disabled={busy !== null}
                  onClick={() => void onAction(batch, "publish")}
                >
                  {busy === batch.id ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    <Send />
                  )}
                  Publish results
                </Button>
              )}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

export function ExecutiveResultsPage({ view }: { view: ExecutiveResultsView }) {
  const [data, setData] = useState<ResultsResponse | null>(null)
  const [notes, setNotes] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    setData(await apiFetch<ResultsResponse>(endpointForView(view)))
  }, [view])

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) => {
          if (active)
            setError(
              caught instanceof Error
                ? caught.message
                : "Unable to load result batches."
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

  async function performAction(
    batch: ResultBatch,
    action: "approve" | "return" | "publish"
  ) {
    setBusy(batch.id)
    setError("")
    setSuccess("")
    try {
      const endpoint =
        action === "publish"
          ? "/executive/results/publication"
          : "/executive/results/review"
      const response = await apiFetch<{ message: string }>(endpoint, {
        method: "POST",
        body: JSON.stringify({
          batch_id: batch.id,
          action,
          note: notes[batch.id] ?? "",
        }),
      })
      setSuccess(response.message)
      setNotes((current) => ({ ...current, [batch.id]: "" }))
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to update this result batch."
      )
    } finally {
      setBusy(null)
    }
  }

  const activeTab = TABS.find((tab) => tab.view === view)
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/results", title: "Results" },
          ...(view === "overview"
            ? []
            : [
                {
                  href: activeTab?.href ?? "/executive/results",
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
                Review teacher submissions within your academic scope, return
                corrections, approve complete batches, and publish them to
                student transcripts.
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
            <Loader2 className="size-4 animate-spin" /> Loading result batches
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
        {data?.scope_error ? (
          <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            {data.scope_error}
          </p>
        ) : null}
        {data ? <Summary data={data.summary} /> : null}
        {data?.batches.length ? (
          <section className="space-y-4">
            {data.batches.map((batch) => (
              <BatchCard
                key={batch.id}
                batch={batch}
                view={view}
                note={notes[batch.id] ?? ""}
                busy={busy}
                onNoteChange={(note) =>
                  setNotes((current) => ({ ...current, [batch.id]: note }))
                }
                onAction={performAction}
              />
            ))}
          </section>
        ) : data && !loading ? (
          <p className="rounded-xl border border-dashed bg-background p-6 text-sm text-muted-foreground">
            No result batches are currently available in this stage.
          </p>
        ) : null}
      </main>
    </div>
  )
}
