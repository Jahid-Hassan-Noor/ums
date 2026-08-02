import { notFound, redirect } from "next/navigation"
import {
  Archive,
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FileText,
  GraduationCap,
  Home,
  LayoutDashboard,
  Palette,
  Settings,
  Upload,
  Users,
  Vote,
  type LucideIcon,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { RoleScheduleSurface } from "@/components/role-zone/role-schedule-surface"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card"
import {
  getUmsNavItemByUrl,
  ROLE_ZONES,
  type UmsIconKey,
  type UserRole,
} from "@/lib/ums-roles"
import { getScheduleRouteConfig } from "@/lib/role-schedule"

const iconMap: Record<UmsIconKey, LucideIcon> = {
  academic: Building2,
  assignments: FileText,
  attendance: ClipboardCheck,
  calendar: CalendarDays,
  courses: BookOpen,
  dashboard: LayoutDashboard,
  elections: Vote,
  hostels: Home,
  imports: Upload,
  leave: ClipboardList,
  notifications: Bell,
  palette: Palette,
  records: Archive,
  results: GraduationCap,
  semesters: CalendarDays,
  settings: Settings,
  statistics: BarChart3,
  users: Users,
}

function titleFromSegment(segment: string) {
  const mapping: Record<string, string> = {
    timetable: "Schedule",
    today: "Today's",
    weekly: "Weekly",
  }

  if (mapping[segment]) return mapping[segment]

  return segment
    .replace(/[-_]/g, " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

function breadcrumbsForUrl(url: string) {
  const parts = url.split("/").filter(Boolean)

  return parts.map((part, index) => ({
    href: `/${parts.slice(0, index + 1).join("/")}`,
    title: titleFromSegment(part),
  }))
}

function zonePath(role: UserRole, path: string[] = []) {
  return `/${[role, ...path].join("/")}`.replace(/\/+$/, "")
}

type RoleSchedulePageProps = {
  role: Extract<UserRole, "student" | "teacher">
  path?: string[]
}

export function RoleSchedulePage({ role, path = [] }: RoleSchedulePageProps) {
  const zone = ROLE_ZONES[role]

  if (path.length === 0) {
    redirect(zone.dashboardPath)
  }

  const currentUrl = zonePath(role, path)
  const isDashboard = currentUrl === zone.dashboardPath
  const page = isDashboard
    ? {
        title: zone.headline,
        description: zone.description,
      }
    : getUmsNavItemByUrl(role, currentUrl)
  const scheduleConfig = getScheduleRouteConfig(role, path)

  if (!page || !scheduleConfig) {
    notFound()
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={breadcrumbsForUrl(currentUrl)} />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {page.title}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {page.description}
            </p>
          </div>
        </section>

        {isDashboard ? (
          <section className="grid gap-4 md:grid-cols-3">
            {zone.metrics.map((metric) => {
              const MetricIcon = iconMap[metric.icon]

              return (
                <Card
                  key={metric.title}
                  className="border-border/70 bg-card/95 shadow-sm"
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between gap-3">
                      <CardDescription className="text-sm font-medium">
                        {metric.title}
                      </CardDescription>
                      <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                        <MetricIcon className="size-5" />
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-1">
                    <p className="text-2xl font-semibold tracking-tight">
                      {metric.value}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {metric.subtitle}
                    </p>
                  </CardContent>
                </Card>
              )
            })}
          </section>
        ) : null}

        <RoleScheduleSurface role={role} config={scheduleConfig} />
      </main>
    </div>
  )
}
