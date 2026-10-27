"use client"

import { useEffect, useState } from "react"
import Link from "next/link"

import { Header } from "@/components/layout/header"
import { AcademicCalendarSurface } from "@/components/role-zone/academic-calendar-surface"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"
import { normalizeScheduleApiEvents, type ScheduleApiEvent } from "@/lib/role-schedule"

type CalendarResponse = {
  scope: { name: string; academic_workflows: boolean }
  schedule: { events: ScheduleApiEvent[]; semester: null }
}

export function ExecutiveCalendarPage() {
  const [data, setData] = useState<CalendarResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    let active = true
    apiFetch<CalendarResponse>("/executive/calendar")
      .then((response) => {
        if (active) setData(response)
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to load the calendar.")
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [retryKey])

  const events = data ? normalizeScheduleApiEvents("executive", data.schedule.events) : []

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/executive", title: "Executive" }, { href: "/executive/calendar", title: "Calendar" }]} />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Calendar</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Academic events for {data?.scope.name ?? "your assigned school or centre"}.
          </p>
          {data?.scope.academic_workflows ? (
            <Button className="mt-4" variant="outline" render={<Link href="/executive/manage/schedule" />}>
              Manage class schedule
            </Button>
          ) : null}
        </section>
        {loading ? (
          <p className="rounded-lg border bg-card p-6 text-sm text-muted-foreground" role="status">Loading calendar…</p>
        ) : error ? (
          <Card role="alert">
            <CardHeader>
              <CardTitle className="text-base">Calendar unavailable</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" onClick={() => { setData(null); setError(""); setLoading(true); setRetryKey((value) => value + 1) }}>Try again</Button>
            </CardContent>
          </Card>
        ) : (
          <AcademicCalendarSurface events={events} semester={null} />
        )}
      </main>
    </div>
  )
}
