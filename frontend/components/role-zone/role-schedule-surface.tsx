"use client"

import * as React from "react"
import Link from "next/link"
import {
  ArrowRight,
  CalendarDays,
  Clock3,
  LayoutGrid,
  MapPin,
  Rows3,
} from "lucide-react"

import { AcademicCalendarSurface } from "@/components/role-zone/academic-calendar-surface"
import { MinaSchedulerPanel } from "@/components/role-zone/mina-scheduler-panel"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  getScheduleSummary,
  getTodaySchedule,
  type ScheduleEvent,
  type ScheduleRouteConfig,
} from "@/lib/role-schedule"
import {
  fetchRoleSchedule,
  type RoleScheduleData,
} from "@/lib/schedule-api"
import type { UserRole } from "@/lib/ums-roles"
import { cn } from "@/lib/utils"

type ScheduledRole = Extract<UserRole, "student" | "teacher">

type RoleScheduleSurfaceProps = {
  role: ScheduledRole
  config: ScheduleRouteConfig
}

const categoryLabels: Record<ScheduleEvent["category"], string> = {
  assessment: "Assessment",
  class: "Class",
  lab: "Lab",
  meeting: "Meeting",
  "office-hours": "Office hours",
}

const variantBorderClasses: Record<ScheduleEvent["variant"], string> = {
  primary: "border-l-blue-500",
  success: "border-l-emerald-500",
  warning: "border-l-amber-500",
  danger: "border-l-rose-500",
  default: "border-l-slate-400",
}

export function RoleScheduleSurface({
  role,
  config,
}: RoleScheduleSurfaceProps) {
  const referenceDate = React.useMemo(() => new Date(), [])
  const [scheduleData, setScheduleData] =
    React.useState<RoleScheduleData | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState("")
  const [retryKey, setRetryKey] = React.useState(0)
  const events = React.useMemo(() => scheduleData?.events ?? [], [scheduleData])
  const semester = scheduleData?.semester ?? null
  const todayEvents = React.useMemo(
    () => getTodaySchedule(events, referenceDate),
    [events, referenceDate]
  )
  const summary = React.useMemo(() => getScheduleSummary(events), [events])

  React.useEffect(() => {
    let isActive = true

    fetchRoleSchedule(role, config.kind)
      .then((nextSchedule) => {
        if (!isActive) return
        setScheduleData(nextSchedule)
      })
      .catch((caught) => {
        if (!isActive) return
        setError(caught instanceof Error ? caught.message : "Unable to load the schedule.")
      })
      .finally(() => {
        if (isActive) setLoading(false)
      })

    return () => {
      isActive = false
    }
  }, [config.kind, role, retryKey])

  if (loading) {
    return <p className="rounded-lg border bg-card p-6 text-sm text-muted-foreground" role="status">Loading schedule…</p>
  }

  if (error) {
    return (
      <Card role="alert">
        <CardHeader>
          <CardTitle className="text-base">Schedule unavailable</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => { setScheduleData(null); setError(""); setLoading(true); setRetryKey((value) => value + 1) }}>Try again</Button>
        </CardContent>
      </Card>
    )
  }

  if (config.kind === "calendar") {
    return (
      <section className="space-y-4">
        <AcademicCalendarSurface events={events} semester={semester} />
      </section>
    )
  }

  if (config.kind === "today") {
    return (
      <section className="space-y-4">
        <MinaSchedulerPanel events={events} mode="today" semester={semester} />
      </section>
    )
  }

  if (config.kind === "weekly") {
    return (
      <section className="space-y-4">
        <MinaSchedulerPanel events={events} mode="weekly" semester={semester} />
      </section>
    )
  }

  return (
    <section className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        <SummaryCard
          icon={CalendarDays}
          label="Week Items"
          value={String(summary.total)}
        />
        <SummaryCard
          icon={Rows3}
          label={role === "teacher" ? "Teaching Blocks" : "Class Blocks"}
          value={String(summary.classes)}
        />
        <SummaryCard
          icon={LayoutGrid}
          label="Assessment Items"
          value={String(summary.assessments)}
        />
      </div>
      <div className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
        <div className="space-y-4">
          <ScheduleList
            title="Today's Schedule"
            description={config.description}
            events={todayEvents}
            emptyText="No schedule items are planned for today."
          />
          <DashboardLinks role={role} />
        </div>
        <div className="space-y-4">
          <MinaSchedulerPanel
            events={events}
            mode="dashboard"
            semester={semester}
          />
          <WeekAgenda events={events} compact />
        </div>
      </div>
    </section>
  )
}

function SummaryCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof CalendarDays
  label: string
  value: string
}) {
  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-3">
          <CardDescription className="text-sm font-medium">
            {label}
          </CardDescription>
          <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
            <Icon className="size-4" />
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  )
}

function ScheduleList({
  title,
  description,
  events,
  emptyText,
}: {
  title: string
  description: string
  events: ScheduleEvent[]
  emptyText: string
}) {
  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {events.length > 0 ? (
          events.map((event) => <ScheduleItem key={event.id} event={event} />)
        ) : (
          <p className="rounded-lg border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground">
            {emptyText}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

function WeekAgenda({
  events,
  compact = false,
}: {
  events: ScheduleEvent[]
  compact?: boolean
}) {
  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle className="text-base">Weekly Schedule</CardTitle>
        <CardDescription>
          Monday to Friday academic blocks for the current week.
        </CardDescription>
      </CardHeader>
      <CardContent
        className={cn(
          "grid gap-3",
          compact ? "md:grid-cols-2" : "md:grid-cols-2 xl:grid-cols-3"
        )}
      >
        {events.map((event) => (
          <ScheduleItem key={event.id} event={event} />
        ))}
      </CardContent>
    </Card>
  )
}

function ScheduleItem({ event }: { event: ScheduleEvent }) {
  return (
    <article
      className={cn(
        "rounded-lg border border-l-4 border-border bg-background p-3",
        variantBorderClasses[event.variant]
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 space-y-1">
          <p className="leading-snug font-medium text-foreground">
            {event.title}
          </p>
          <p className="text-xs leading-5 text-muted-foreground">
            {event.description}
          </p>
        </div>
        <Badge variant="secondary">{categoryLabels[event.category]}</Badge>
      </div>
      <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
        <span className="flex items-center gap-1.5">
          <Clock3 className="size-3.5" />
          {event.dayLabel}, {event.timeLabel}
        </span>
        <span className="flex items-center gap-1.5">
          <MapPin className="size-3.5" />
          {event.location}
        </span>
      </div>
    </article>
  )
}

function DashboardLinks({ role }: { role: ScheduledRole }) {
  const basePath = `/${role}`
  const links = [
    { href: `${basePath}/calendar`, label: "Open calendar" },
    { href: `${basePath}/timetable/today`, label: "Today" },
    { href: `${basePath}/timetable/weekly`, label: "Week" },
  ]

  return (
    <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-1">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className="group flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium transition-colors hover:bg-muted/60"
        >
          <span>{link.label}</span>
          <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
        </Link>
      ))}
    </div>
  )
}
