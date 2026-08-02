"use client"

import { useEffect, useState } from "react"
import { CalendarClock, Clock3, Loader2, MapPin, Phone, RefreshCw, UserRound } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"

type WardenScheduleEntry = {
  day: string
  time_range: string
  warden_name: string
  phone: string
  location: string
  notes: string
}

type WardenScheduleResponse = {
  schedule: WardenScheduleEntry[]
  updated_at: string | null
}

function formatUpdatedAt(value: string | null) {
  if (!value) return "Not updated yet"
  return new Date(value).toLocaleString()
}

export function StudentWardenSchedulePage() {
  const [schedule, setSchedule] = useState<WardenScheduleEntry[]>([])
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState("")

  async function loadSchedule() {
    const response = await apiFetch<WardenScheduleResponse>("/student/warden-schedule")
    setSchedule(response.schedule ?? [])
    setUpdatedAt(response.updated_at ?? null)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadSchedule()
        .catch((caught) =>
          setError(caught instanceof Error ? caught.message : "Unable to load warden schedule.")
        )
        .finally(() => setLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  async function refreshSchedule() {
    setRefreshing(true)
    setError("")
    try {
      await loadSchedule()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to refresh warden schedule.")
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/warden-schedule", title: "Warden Schedule" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Warden Schedule</h1>
            <p className="text-sm text-muted-foreground">Last updated: {formatUpdatedAt(updatedAt)}</p>
          </div>
          <Button variant="outline" onClick={refreshSchedule} disabled={refreshing}>
            {refreshing ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </Button>
        </section>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>
        ) : null}

        {loading ? (
          <div className="flex h-52 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : schedule.length ? (
          <section className="grid gap-4 lg:grid-cols-2">
            {schedule.map((entry, index) => (
              <Card key={`${entry.day}-${entry.time_range}-${index}`} className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardDescription>Schedule {index + 1}</CardDescription>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <CalendarClock className="size-5" />
                    {entry.day}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <p className="flex items-center gap-2 text-muted-foreground">
                    <Clock3 className="size-4" />
                    {entry.time_range}
                  </p>
                  <p className="flex items-center gap-2">
                    <UserRound className="size-4 text-muted-foreground" />
                    <span className="font-medium">{entry.warden_name}</span>
                  </p>
                  {entry.phone ? (
                    <p className="flex items-center gap-2">
                      <Phone className="size-4 text-muted-foreground" />
                      <a className="font-medium text-primary" href={`tel:${entry.phone}`}>
                        {entry.phone}
                      </a>
                    </p>
                  ) : null}
                  {entry.location ? (
                    <p className="flex items-center gap-2 text-muted-foreground">
                      <MapPin className="size-4" />
                      {entry.location}
                    </p>
                  ) : null}
                  {entry.notes ? (
                    <p className="border-t border-border/70 pt-3 leading-6 text-muted-foreground">
                      {entry.notes}
                    </p>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </section>
        ) : (
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <CalendarClock className="size-8 text-muted-foreground" />
              <p className="font-medium">No warden schedule is available.</p>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
