"use client"

import * as React from "react"
import Link from "next/link"
import {
  ArrowUpRight,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  FlaskConical,
  GraduationCap,
  Presentation,
  Search,
} from "lucide-react"

import { MinaSchedulerPanel } from "@/components/role-zone/mina-scheduler-panel"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import type { ScheduleEvent } from "@/lib/role-schedule"
import type { ScheduleSemester } from "@/lib/schedule-api"
import { cn } from "@/lib/utils"

type AcademicCalendarSurfaceProps = {
  events: ScheduleEvent[]
  semester?: ScheduleSemester | null
}

type DurationFilter = "7" | "30" | "90" | "all"
type TimelineSort = "date" | "course"

type TimelineGroup = {
  key: string
  title: string
  subtitle?: string
  events: ScheduleEvent[]
}

const dateHeadingFormatter = new Intl.DateTimeFormat("en", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
})

const shortDateFormatter = new Intl.DateTimeFormat("en", {
  day: "numeric",
  month: "short",
  year: "numeric",
})

const timeFormatter = new Intl.DateTimeFormat("en", {
  hour: "2-digit",
  minute: "2-digit",
})

const typeStyles = {
  assignment: {
    label: "Assignment",
    icon: ClipboardList,
    iconClass: "bg-pink-500 text-white",
  },
  exam: {
    label: "Exam",
    icon: GraduationCap,
    iconClass: "bg-rose-500 text-white",
  },
  lab: {
    label: "Lab work",
    icon: FlaskConical,
    iconClass: "bg-emerald-500 text-white",
  },
  presentation: {
    label: "Presentation",
    icon: Presentation,
    iconClass: "bg-blue-500 text-white",
  },
  schedule: {
    label: "Academic event",
    icon: CalendarDays,
    iconClass: "bg-slate-600 text-white",
  },
} as const

function localDateKey(value: string) {
  const date = new Date(value)
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-")
}

function eventType(event: ScheduleEvent) {
  const rawType = event.eventType?.toLowerCase()
  if (rawType === "presentation") return "presentation"
  if (rawType === "lab_work" || rawType === "lab_activity") return "lab"
  if (rawType === "assignment") return "assignment"
  if (
    rawType === "exam" ||
    rawType === "final_exam" ||
    rawType === "quiz" ||
    rawType === "test"
  ) {
    return "exam"
  }
  if (event.category === "lab") return "lab"
  if (event.category === "assessment") return "assignment"
  return "schedule"
}

function buildGroups(events: ScheduleEvent[], sort: TimelineSort) {
  const grouped = new Map<string, TimelineGroup>()

  for (const event of events) {
    const date = new Date(event.startsAt)
    const key =
      sort === "date"
        ? localDateKey(event.startsAt)
        : event.courseCode || "general"
    const title =
      sort === "date"
        ? dateHeadingFormatter.format(date)
        : event.courseCode || "General academic events"

    if (!grouped.has(key)) {
      grouped.set(key, {
        key,
        title,
        subtitle: sort === "course" ? event.courseTitle : undefined,
        events: [],
      })
    }
    grouped.get(key)?.events.push(event)
  }

  return [...grouped.values()]
}

export function AcademicCalendarSurface({
  events,
  semester,
}: AcademicCalendarSurfaceProps) {
  const referenceDate = React.useMemo(() => new Date(), [])
  const [duration, setDuration] = React.useState<DurationFilter>("30")
  const [sort, setSort] = React.useState<TimelineSort>("date")
  const [search, setSearch] = React.useState("")

  const filteredEvents = React.useMemo(() => {
    const query = search.trim().toLowerCase()
    const rangeStart = new Date(referenceDate)
    rangeStart.setHours(0, 0, 0, 0)
    const rangeEnd =
      duration === "all"
        ? null
        : new Date(
            rangeStart.getTime() + Number(duration) * 24 * 60 * 60 * 1000
          )

    return [...events]
      .filter((event) => {
        const startsAt = new Date(event.startsAt)
        const isInRange =
          duration === "all" ||
          (startsAt >= rangeStart && Boolean(rangeEnd && startsAt < rangeEnd))
        if (!isInRange) return false
        if (!query) return true
        return [
          event.title,
          event.description,
          event.courseCode,
          event.courseTitle,
          typeStyles[eventType(event)].label,
        ]
          .filter(Boolean)
          .some((value) => value?.toLowerCase().includes(query))
      })
      .sort((left, right) => {
        if (sort === "course") {
          const courseComparison = (left.courseCode || "ZZZ").localeCompare(
            right.courseCode || "ZZZ"
          )
          if (courseComparison !== 0) return courseComparison
        }
        return (
          new Date(left.startsAt).getTime() - new Date(right.startsAt).getTime()
        )
      })
  }, [duration, events, referenceDate, search, sort])

  const groups = React.useMemo(
    () => buildGroups(filteredEvents, sort),
    [filteredEvents, sort]
  )

  return (
    <div className="space-y-6">
      <MinaSchedulerPanel
        events={events}
        mode="calendar"
        semester={semester}
      />

      <Card className="border-border/70 bg-card/95 shadow-sm">
        <CardHeader className="gap-4 border-b border-border/70">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <CardTitle className="text-xl">Timeline</CardTitle>
              <CardDescription className="mt-1">
                Upcoming exams, assignments, presentations, lab work, and
                academic events.
              </CardDescription>
            </div>
            <Badge variant="secondary">
              {filteredEvents.length}{" "}
              {filteredEvents.length === 1 ? "activity" : "activities"}
            </Badge>
          </div>

          <div className="grid gap-3 lg:grid-cols-[12rem_13rem_minmax(16rem,1fr)]">
            <label className="space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground">
                Duration
              </span>
              <select
                value={duration}
                onChange={(event) =>
                  setDuration(event.target.value as DurationFilter)
                }
                className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
              >
                <option value="7">Next 7 days</option>
                <option value="30">Next 30 days</option>
                <option value="90">Next 90 days</option>
                <option value="all">All dates</option>
              </select>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground">
                Sort timeline
              </span>
              <select
                value={sort}
                onChange={(event) =>
                  setSort(event.target.value as TimelineSort)
                }
                className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
              >
                <option value="date">Sort by dates</option>
                <option value="course">Sort by courses</option>
              </select>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground">
                Search
              </span>
              <span className="relative block">
                <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search by activity type, name, or course"
                  className="h-10 pl-9"
                />
              </span>
            </label>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {groups.length ? (
            <div>
              {groups.map((group) => (
                <section
                  key={group.key}
                  className="border-b border-border/70 last:border-b-0"
                >
                  <div className="bg-muted/25 px-4 py-3 sm:px-6">
                    <h3 className="font-semibold">{group.title}</h3>
                    {group.subtitle ? (
                      <p className="mt-0.5 text-sm text-muted-foreground">
                        {group.subtitle}
                      </p>
                    ) : null}
                  </div>
                  <div className="divide-y divide-border/70">
                    {group.events.map((event) => (
                      <TimelineEvent key={event.id} event={event} sort={sort} />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <div className="flex min-h-48 flex-col items-center justify-center gap-2 px-6 text-center">
              <CalendarClock className="size-8 text-muted-foreground" />
              <p className="font-medium">No activities match these filters.</p>
              <p className="text-sm text-muted-foreground">
                Try a longer duration or clear the search field.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function TimelineEvent({
  event,
  sort,
}: {
  event: ScheduleEvent
  sort: TimelineSort
}) {
  const style = typeStyles[eventType(event)]
  const Icon = style.icon
  const startsAt = new Date(event.startsAt)
  const content = (
    <>
      <div className="w-16 shrink-0 pt-1 text-sm font-medium tabular-nums sm:w-20">
        {timeFormatter.format(startsAt)}
      </div>
      <span
        className={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-xl shadow-sm",
          style.iconClass
        )}
      >
        <Icon className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold text-primary">{event.title}</p>
          <Badge variant="outline">{style.label}</Badge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {event.description}
          {event.courseCode ? ` · ${event.courseCode}` : ""}
          {sort === "course" ? ` · ${shortDateFormatter.format(startsAt)}` : ""}
        </p>
        {event.location ? (
          <p className="mt-1 text-xs text-muted-foreground">{event.location}</p>
        ) : null}
      </div>
      {event.href ? (
        <ArrowUpRight className="mt-1 size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
      ) : null}
    </>
  )

  if (!event.href) {
    return <article className="flex gap-3 px-4 py-4 sm:px-6">{content}</article>
  }

  return (
    <Link
      href={event.href}
      className="group flex gap-3 px-4 py-4 transition-colors hover:bg-muted/35 sm:px-6"
    >
      {content}
    </Link>
  )
}
