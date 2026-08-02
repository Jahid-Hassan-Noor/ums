import type { UserRole } from "@/lib/ums-roles"

export type ScheduleVariant =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "default"

export type ScheduleCategory =
  | "class"
  | "lab"
  | "assessment"
  | "meeting"
  | "office-hours"

export type ScheduleTemplate = {
  id: string
  role: Extract<UserRole, "student" | "teacher">
  title: string
  description: string
  location: string
  category: ScheduleCategory
  weekday: number
  startTime: string
  endTime: string
  variant: ScheduleVariant
}

export type ScheduleEvent = ScheduleTemplate & {
  startsAt: string
  endsAt: string
  dayLabel: string
  timeLabel: string
  eventType?: string
  courseCode?: string
  courseTitle?: string
  offeringId?: number
  href?: string
}

export type ScheduleApiEvent = {
  id: string | number
  title?: string
  description?: string
  starts_at?: string
  ends_at?: string | null
  category?: string
  location?: string
  variant?: string
  event_type?: string
  course_code?: string
  course_title?: string
  offering_id?: number
  href?: string
}

export type ScheduleRouteKind = "dashboard" | "calendar" | "today" | "weekly"

export type ScheduleRouteConfig = {
  kind: ScheduleRouteKind
  heading: string
  description: string
}

const dayFormatter = new Intl.DateTimeFormat("en", {
  weekday: "short",
  month: "short",
  day: "numeric",
})

const timeFormatter = new Intl.DateTimeFormat("en", {
  hour: "numeric",
  minute: "2-digit",
})

const scheduleTemplates: Record<
  Extract<UserRole, "student" | "teacher">,
  ScheduleTemplate[]
> = {
  student: [
    {
      id: "student-web-systems",
      role: "student",
      title: "Web Systems Lecture",
      description: "CSC 201 with Dr. Farah",
      location: "Lecture Hall B",
      category: "class",
      weekday: 1,
      startTime: "09:00",
      endTime: "10:30",
      variant: "primary",
    },
    {
      id: "student-quant-methods",
      role: "student",
      title: "Quantitative Methods Lab",
      description: "MAT 120 applied lab",
      location: "Computing Lab 3",
      category: "lab",
      weekday: 2,
      startTime: "14:00",
      endTime: "16:00",
      variant: "success",
    },
    {
      id: "student-writing",
      role: "student",
      title: "Academic Writing Tutorial",
      description: "ENG 210 small group session",
      location: "Room 2.15",
      category: "class",
      weekday: 3,
      startTime: "11:00",
      endTime: "12:30",
      variant: "default",
    },
    {
      id: "student-advisor",
      role: "student",
      title: "Advisor Check-in",
      description: "Semester progress review",
      location: "Student Affairs Office",
      category: "meeting",
      weekday: 4,
      startTime: "10:00",
      endTime: "10:45",
      variant: "warning",
    },
    {
      id: "student-project-brief",
      role: "student",
      title: "Project Brief Due",
      description: "Submit CSC 201 proposal",
      location: "Learning portal",
      category: "assessment",
      weekday: 5,
      startTime: "15:00",
      endTime: "15:30",
      variant: "danger",
    },
  ],
  teacher: [
    {
      id: "teacher-web-systems",
      role: "teacher",
      title: "Teach Web Systems",
      description: "CSC 201 lecture block",
      location: "Lecture Hall B",
      category: "class",
      weekday: 1,
      startTime: "09:00",
      endTime: "10:30",
      variant: "primary",
    },
    {
      id: "teacher-consultation",
      role: "teacher",
      title: "Student Consultations",
      description: "Open office hour",
      location: "Faculty Office 4.08",
      category: "office-hours",
      weekday: 2,
      startTime: "11:00",
      endTime: "12:00",
      variant: "success",
    },
    {
      id: "teacher-lab-supervision",
      role: "teacher",
      title: "Supervise App Lab",
      description: "CSC 302 practical",
      location: "Computing Lab 1",
      category: "lab",
      weekday: 3,
      startTime: "14:00",
      endTime: "16:00",
      variant: "default",
    },
    {
      id: "teacher-results-review",
      role: "teacher",
      title: "Results Review",
      description: "Draft marks moderation",
      location: "Academic Office",
      category: "meeting",
      weekday: 4,
      startTime: "13:30",
      endTime: "14:30",
      variant: "warning",
    },
    {
      id: "teacher-assignment-deadline",
      role: "teacher",
      title: "Assignment Feedback Due",
      description: "Return CSC 201 feedback",
      location: "Learning portal",
      category: "assessment",
      weekday: 5,
      startTime: "16:00",
      endTime: "16:30",
      variant: "danger",
    },
  ],
}

export function getScheduleRouteConfig(
  role: UserRole,
  path: readonly string[]
): ScheduleRouteConfig | null {
  if (role !== "student" && role !== "teacher") return null

  const [section, detail] = path

  if (section === "dashboard") {
    return {
      kind: "dashboard",
      heading: "Schedule Snapshot",
      description:
        "Calendar, today, and week views for the current academic schedule.",
    }
  }

  if (section === "calendar") {
    return {
      kind: "calendar",
      heading: role === "teacher" ? "Teaching Calendar" : "Academic Calendar",
      description:
        role === "teacher"
          ? "Classes, office hours, review sessions, and deadlines in one calendar."
          : "Classes, advisor sessions, assessment deadlines, and campus schedule items in one calendar.",
    }
  }

  if (section === "timetable" && detail === "today") {
    return {
      kind: "today",
      heading: "Today's Schedule",
      description:
        role === "teacher"
          ? "Teaching slots and work blocks planned for today."
          : "Class blocks and academic items planned for today.",
    }
  }

  if (
    section === "timetable" &&
    (detail === "weekly" || detail === undefined)
  ) {
    return {
      kind: "weekly",
      heading: "Weekly Schedule",
      description:
        role === "teacher"
          ? "A week-at-a-glance view of assigned teaching and academic work."
          : "A week-at-a-glance view of classes, activities, and academic deadlines.",
    }
  }

  return null
}

export function buildScheduleEvents(
  role: Extract<UserRole, "student" | "teacher">,
  referenceDate = new Date()
): ScheduleEvent[] {
  const weekStart = startOfWeek(referenceDate)

  return scheduleTemplates[role].map((item) => {
    const day = new Date(weekStart)
    day.setDate(weekStart.getDate() + item.weekday - 1)

    const startsAt = applyTime(day, item.startTime)
    const endsAt = applyTime(day, item.endTime)

    return {
      ...item,
      startsAt: startsAt.toISOString(),
      endsAt: endsAt.toISOString(),
      dayLabel: dayFormatter.format(startsAt),
      timeLabel: `${timeFormatter.format(startsAt)} - ${timeFormatter.format(endsAt)}`,
    }
  })
}

export function normalizeScheduleApiEvents(
  role: Extract<UserRole, "student" | "teacher">,
  apiEvents: readonly ScheduleApiEvent[]
): ScheduleEvent[] {
  return apiEvents
    .map((event) => {
      if (!event.starts_at) return null

      const startsAt = new Date(event.starts_at)
      const endsAt = event.ends_at
        ? new Date(event.ends_at)
        : new Date(startsAt.getTime() + 60 * 60 * 1000)

      if (Number.isNaN(startsAt.getTime()) || Number.isNaN(endsAt.getTime())) {
        return null
      }

      const category = normalizeCategory(event.category)
      const variant = normalizeVariant(event.variant)

      const normalizedEvent: ScheduleEvent = {
        id: String(event.id),
        role,
        title: event.title?.trim() || "Scheduled event",
        description: event.description?.trim() || "Academic schedule item",
        location: event.location?.trim() || "Campus",
        category,
        weekday: startsAt.getDay() === 0 ? 7 : startsAt.getDay(),
        startTime: formatClock(startsAt),
        endTime: formatClock(endsAt),
        variant,
        startsAt: startsAt.toISOString(),
        endsAt: endsAt.toISOString(),
        dayLabel: dayFormatter.format(startsAt),
        timeLabel: `${timeFormatter.format(startsAt)} - ${timeFormatter.format(endsAt)}`,
        eventType: event.event_type,
        courseCode: event.course_code,
        courseTitle: event.course_title,
        offeringId: event.offering_id,
        href: event.href,
      }

      return normalizedEvent
    })
    .filter((event): event is ScheduleEvent => event !== null)
}

export function getTodaySchedule(
  events: readonly ScheduleEvent[],
  referenceDate = new Date()
) {
  return events.filter((event) =>
    isSameLocalDay(new Date(event.startsAt), referenceDate)
  )
}

export function getScheduleSummary(events: readonly ScheduleEvent[]) {
  return {
    total: events.length,
    classes: events.filter(
      (event) => event.category === "class" || event.category === "lab"
    ).length,
    assessments: events.filter((event) => event.category === "assessment")
      .length,
  }
}

function startOfWeek(date: Date) {
  const start = new Date(date)
  const day = start.getDay()
  const mondayOffset = (day + 6) % 7
  start.setDate(start.getDate() - mondayOffset)
  start.setHours(0, 0, 0, 0)
  return start
}

function applyTime(date: Date, time: string) {
  const [hour = "0", minute = "0"] = time.split(":")
  const nextDate = new Date(date)
  nextDate.setHours(Number(hour), Number(minute), 0, 0)
  return nextDate
}

function formatClock(date: Date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes()
  ).padStart(2, "0")}`
}

function normalizeCategory(category: string | null | undefined) {
  const categories = new Set<ScheduleCategory>([
    "assessment",
    "class",
    "lab",
    "meeting",
    "office-hours",
  ])

  return categories.has(category as ScheduleCategory)
    ? (category as ScheduleCategory)
    : "class"
}

function normalizeVariant(variant: string | null | undefined) {
  const variants = new Set<ScheduleVariant>([
    "danger",
    "default",
    "primary",
    "success",
    "warning",
  ])

  return variants.has(variant as ScheduleVariant)
    ? (variant as ScheduleVariant)
    : "default"
}

function isSameLocalDay(left: Date, right: Date) {
  return (
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()
  )
}
