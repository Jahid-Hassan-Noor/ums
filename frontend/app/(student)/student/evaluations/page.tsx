"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { AlertCircle, CheckCircle2, ClipboardCheck, Loader2 } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"

type StudentSurvey = {
  id: number
  title: string
  offering: {
    course: { code: string; title: string }
    semester: { name: string; academic_session: string }
    section: string
    instructor: { name: string } | null
  }
  state: string
  is_required: boolean
  opens_at: string | null
  closes_at: string | null
  submitted: boolean
  submitted_at: string | null
}

type EvaluationsResponse = {
  summary: { total: number; pending: number; submitted: number }
  surveys: StudentSurvey[]
}

function formatDateTime(value: string | null) {
  if (!value) return "No limit"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? "Not set" : date.toLocaleString()
}

export default function StudentEvaluationsPage() {
  const [data, setData] = useState<EvaluationsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let active = true
    apiFetch<EvaluationsResponse>("/student/evaluations")
      .then((payload) => {
        if (active) setData(payload)
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to load evaluations.")
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/evaluations", title: "Course Evaluations" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Course Content and Teaching Evaluations</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Complete SEC-SET feedback for the courses you are taking. Required evaluations must be
            submitted before you can register courses for the next semester.
          </p>
        </section>

        {error ? <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="size-4" />{error}</div> : null}
        {isLoading ? (
          <div className="flex h-64 items-center justify-center"><Loader2 className="size-8 animate-spin text-muted-foreground" /></div>
        ) : data ? (
          <>
            <section className="grid gap-4 md:grid-cols-3">
              {[
                ["Assigned", data.summary.total],
                ["Pending", data.summary.pending],
                ["Submitted", data.summary.submitted],
              ].map(([label, value]) => (
                <Card key={label}><CardContent className="p-5"><p className="text-sm text-muted-foreground">{label}</p><p className="mt-1 text-3xl font-semibold">{value}</p></CardContent></Card>
              ))}
            </section>

            {data.summary.pending ? (
              <div className="flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                <AlertCircle className="mt-0.5 size-5 shrink-0" />
                <div><p className="font-semibold">Registration requirement pending</p><p className="mt-1">Submit every required evaluation below before next-semester course registration.</p></div>
              </div>
            ) : (
              <div className="flex gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                <CheckCircle2 className="mt-0.5 size-5 shrink-0" />
                <div><p className="font-semibold">All assigned evaluations are complete</p><p className="mt-1">There is no SEC-SET hold on your next-semester registration.</p></div>
              </div>
            )}

            <Card>
              <CardHeader><CardTitle>My evaluations</CardTitle><CardDescription>Feedback is accepted only during the activity window.</CardDescription></CardHeader>
              <CardContent className="grid gap-3 lg:grid-cols-2">
                {data.surveys.map((survey) => (
                  <div key={survey.id} className="rounded-lg border border-border bg-background p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold">{survey.offering.course.code} / {survey.offering.section || "Main"}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{survey.offering.course.title}</p>
                      </div>
                      {survey.submitted ? <Badge className="bg-emerald-600">Submitted</Badge> : <Badge variant="outline" className="border-amber-300 text-amber-700">Pending</Badge>}
                    </div>
                    <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                      <p>{survey.offering.semester.name}</p>
                      <p>Lecturer: {survey.offering.instructor?.name || "Not assigned"}</p>
                      <p>{formatDateTime(survey.opens_at)} - {formatDateTime(survey.closes_at)}</p>
                    </div>
                    <Button className="mt-4 w-full" variant={survey.submitted ? "outline" : "default"} render={<Link href={`/student/evaluations/${survey.id}`} />}>
                      <ClipboardCheck className="size-4" />
                      {survey.submitted ? "View submission" : survey.state === "open" ? "Complete evaluation" : `Evaluation ${survey.state}`}
                    </Button>
                  </div>
                ))}
                {!data.surveys.length ? <p className="text-sm text-muted-foreground">No course evaluations have been assigned yet.</p> : null}
              </CardContent>
            </Card>
          </>
        ) : null}
      </main>
    </div>
  )
}
