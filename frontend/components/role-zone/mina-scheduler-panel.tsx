"use client"

import * as React from "react"
import Link from "next/link"
import { Calendar, CalendarDays, CalendarRange } from "lucide-react"
import {
  SchedulerProvider,
  SchedularView,
  type Event as MinaEvent,
} from "mina-scheduler"

import { cn } from "@/lib/utils"
import type { ScheduleEvent, ScheduleRouteKind } from "@/lib/role-schedule"
import type { ScheduleSemester } from "@/lib/schedule-api"

type SchedulerViewName = "day" | "week" | "month"

type MinaSchedulerPanelProps = {
  events: ScheduleEvent[]
  mode: ScheduleRouteKind
  semester?: ScheduleSemester | null
  className?: string
}

const viewsByMode: Record<ScheduleRouteKind, SchedulerViewName[]> = {
  dashboard: ["month"],
  calendar: ["month"],
  today: ["day"],
  weekly: ["week"],
}

const schedulerControlSelector = [
  "button",
  "[role='tab']",
  "[data-slot='tab']",
].join(",")

const variantClasses: Record<string, string> = {
  primary:
    "border-blue-200 bg-blue-50 text-blue-950 dark:border-blue-400/30 dark:bg-blue-400/15 dark:text-blue-100",
  success:
    "border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-400/30 dark:bg-emerald-400/15 dark:text-emerald-100",
  warning:
    "border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-400/30 dark:bg-amber-400/15 dark:text-amber-100",
  danger:
    "border-rose-200 bg-rose-50 text-rose-950 dark:border-rose-400/30 dark:bg-rose-400/15 dark:text-rose-100",
  default:
    "border-slate-200 bg-slate-50 text-slate-950 dark:border-slate-400/30 dark:bg-slate-400/15 dark:text-slate-100",
}

type NavigableMinaEvent = MinaEvent & {
  href?: string
  minmized?: boolean
}

function MinaEventCard(event: NavigableMinaEvent) {
  const content = (
    <div
      className={cn(
        "min-h-full rounded-md border px-2 py-1 text-left shadow-sm transition-shadow",
        event.minmized ? "space-y-0.5" : "space-y-1",
        variantClasses[event.variant ?? "default"],
        event.href && "hover:shadow-md"
      )}
    >
      <p
        className={cn(
          "leading-tight font-medium",
          event.minmized ? "text-[0.7rem]" : "text-xs"
        )}
      >
        {event.title}
      </p>
      {event.description ? (
        <p
          className={cn(
            "line-clamp-2 leading-snug opacity-80",
            event.minmized ? "text-[0.62rem]" : "text-[0.7rem]"
          )}
        >
          {event.description}
        </p>
      ) : null}
    </div>
  )

  if (!event.href) return content

  return (
    <Link
      href={event.href}
      className="block min-h-full"
      onClick={(clickEvent) => clickEvent.stopPropagation()}
    >
      {content}
    </Link>
  )
}

function SchedulerTabLabel({
  icon: Icon,
  label,
}: {
  icon: typeof CalendarDays
  label: string
}) {
  return (
    <span className="flex items-center gap-2 text-sm font-medium text-foreground">
      <Icon className="size-4" />
      {label}
    </span>
  )
}

function stopReadOnlySchedulerClick(event: React.MouseEvent<HTMLDivElement>) {
  const target = event.target

  if (
    target instanceof HTMLElement &&
    (target.closest(schedulerControlSelector) || target.closest("a[href]"))
  ) {
    return
  }

  event.preventDefault()
  event.stopPropagation()
}

function parseDateOnly(value: string) {
  const [year, month, day] = value.split("-").map(Number)
  return new Date(year, month - 1, day)
}

function startOfWeek(value: Date) {
  const date = new Date(value)
  const dayOffset = (date.getDay() + 6) % 7
  date.setDate(date.getDate() - dayOffset)
  date.setHours(0, 0, 0, 0)
  return date
}

function semesterWeekLabel(
  date: Date,
  semester: ScheduleSemester | null | undefined
) {
  if (!semester?.start_date) return "Semester week unavailable"

  const viewedWeek = startOfWeek(date)
  const firstWeek = startOfWeek(parseDateOnly(semester.start_date))
  const lastWeek = semester.end_date
    ? startOfWeek(parseDateOnly(semester.end_date))
    : null

  if (viewedWeek < firstWeek) return "Before semester"
  if (lastWeek && viewedWeek > lastWeek) return "After semester"

  const elapsedWeeks = Math.floor(
    (viewedWeek.getTime() - firstWeek.getTime()) / (7 * 24 * 60 * 60 * 1000)
  )
  return `Week ${semester.starting_week + elapsedWeeks}`
}

export function MinaSchedulerPanel({
  events,
  mode,
  semester,
  className,
}: MinaSchedulerPanelProps) {
  const panelRef = React.useRef<HTMLDivElement>(null)
  const [weekOffset, setWeekOffset] = React.useState(0)

  React.useEffect(() => {
    const style = document.createElement("style")
    style.textContent = `
      .mina-scheduler-panel .mina-current-time,
      .mina-scheduler-panel [class*="current-time"],
      .mina-scheduler-panel [class*="currentTime"] {
        display: none !important;
      }
      .mina-scheduler-panel .all-week-events:empty {
        display: none !important;
      }
    `
    document.head.appendChild(style)
    return () => {
      document.head.removeChild(style)
    }
  }, [])
  const schedulerEvents = React.useMemo<NavigableMinaEvent[]>(
    () =>
      events.map((event) => ({
        id: event.id,
        title: event.title,
        description: `${event.timeLabel} | ${event.location}`,
        startDate: new Date(event.startsAt),
        endDate: new Date(event.endsAt),
        variant: event.variant,
        href: event.href,
      })),
    [events]
  )
  const views = viewsByMode[mode]
  const viewedWeekDate = React.useMemo(() => {
    const date = new Date()
    date.setDate(date.getDate() + weekOffset * 7)
    return date
  }, [weekOffset])
  const currentSemesterWeekLabel = semesterWeekLabel(viewedWeekDate, semester)

  React.useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      panelRef.current?.querySelector<HTMLElement>("[role='tab']")?.click()
    })

    return () => window.cancelAnimationFrame(frame)
  }, [mode, schedulerEvents.length])

  React.useEffect(() => {
    if (mode !== "weekly") return
    const frame = window.requestAnimationFrame(() => {
      const labels = panelRef.current?.querySelectorAll("span") ?? []
      const weekLabel = Array.from(labels).find((label) =>
        /^(Week \d+|Before semester|After semester|Semester week unavailable)$/.test(
          label.textContent?.trim() ?? ""
        )
      )
      if (weekLabel) weekLabel.textContent = currentSemesterWeekLabel
    })
    return () => window.cancelAnimationFrame(frame)
  }, [currentSemesterWeekLabel, mode, schedulerEvents.length])

  function handleSchedulerClick(event: React.MouseEvent<HTMLDivElement>) {
    const target = event.target
    if (mode === "weekly" && target instanceof HTMLElement) {
      const button = target.closest("button")
      const label = button?.textContent?.trim()
      if (label === "Prev") setWeekOffset((current) => current - 1)
      if (label === "Next") setWeekOffset((current) => current + 1)
    }
    stopReadOnlySchedulerClick(event)
  }

  return (
    <div
      ref={panelRef}
      className={cn(
        "mina-scheduler-panel overflow-x-auto rounded-lg border border-border bg-background p-3",
        mode === "today" && "mina-day-view",
        mode === "weekly" && "mina-week-view",
        className
      )}
      onClickCapture={handleSchedulerClick}
    >
      <SchedulerProvider initialState={schedulerEvents} weekStartsOn="monday">
        <SchedularView
          views={{
            views,
            mobileViews: views,
          }}
          CustomComponents={{
            CustomEventComponent: MinaEventCard,
            customTabs: {
              CustomDayTab: (
                <SchedulerTabLabel icon={CalendarDays} label="Day" />
              ),
              CustomWeekTab: (
                <SchedulerTabLabel icon={CalendarRange} label="Week" />
              ),
              CustomMonthTab: (
                <SchedulerTabLabel icon={Calendar} label="Month" />
              ),
            },
          }}
          classNames={{
            buttons: {
              addEvent: "hidden",
              next: "border border-border bg-background text-foreground shadow-sm hover:bg-muted",
              prev: "border border-border bg-background text-foreground shadow-sm hover:bg-muted",
            },
            tabs: {
              wrapper: "w-full",
              tabList: "hidden",
              cursor:
                "rounded-md border border-border bg-background shadow-sm dark:bg-card",
              tab: "h-9 px-3 text-muted-foreground",
              tabContent:
                "text-muted-foreground group-data-[selected=true]:text-foreground",
              panel: "pt-0",
            },
            views: {
              dayView: "min-w-[44rem] mina-day-view",
              weekView: "min-w-[58rem] mina-week-view",
              monthView: "min-w-[44rem]",
            },
          }}
        />
      </SchedulerProvider>
    </div>
  )
}
