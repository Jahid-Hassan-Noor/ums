import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { cookies } from "next/headers"
import {
  ArrowUpRight,
  Archive,
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  CalendarDays,
  CheckCircle2,
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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  type UmsIconKey,
  type UmsNavItem,
  type UserRole,
} from "@/lib/ums-roles"
import {
  applyUmsTerminology,
  disabledUmsRouteModules,
  filterUmsNavItemsBySettings,
  isUmsRoleFeaturePathEnabled,
  loadPublicUmsSettings,
  zoneForUmsRole,
} from "@/lib/ums-settings"

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

  if (mapping[segment]) {
    return mapping[segment]
  }

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

const nonAcademicExecutiveHiddenUrls = new Set([
  "/executive/courses",
  "/executive/courses/offered",
  "/executive/courses/offer",
  "/executive/courses/add",
  "/executive/courses/all",
  "/executive/manage/students",
  "/executive/manage/schedule",
  "/executive/results",
  "/executive/results/semester",
  "/executive/results/previous",
  "/executive/results/review",
  "/executive/results/publication",
])

function filterExecutivePages<T extends { url: string }>(items: T[], academicWorkflows: boolean) {
  if (academicWorkflows) return items
  return items.filter((item) => !nonAcademicExecutiveHiddenUrls.has(item.url))
}

function getNavItemByUrl(items: UmsNavItem[], url: string) {
  for (const item of items) {
    if (item.url === url) return item
    const subItem = item.items?.find((candidate) => candidate.url === url)
    if (subItem) {
      return {
        ...subItem,
        icon: item.icon,
      }
    }
  }
  return null
}

type RoleZonePageProps = {
  role: UserRole
  path?: string[]
}

export async function RoleZonePage({ role, path = [] }: RoleZonePageProps) {
  const publicSettings = await loadPublicUmsSettings()
  const zone = zoneForUmsRole(role, publicSettings)
  const cookieStore = await cookies()
  const executiveHasAcademicWorkflows =
    role !== "executive" ||
    cookieStore.get("ums_academic_workflows")?.value !== "0"

  if (path.length === 0) {
    redirect(zone.dashboardPath)
  }

  const currentUrl = zonePath(role, path)
  if (!isUmsRoleFeaturePathEnabled(currentUrl, publicSettings, role)) {
    const params = new URLSearchParams({ next: currentUrl })
    const modules = disabledUmsRouteModules(currentUrl, publicSettings, role)
    if (modules.length) {
      params.set("modules", modules.join(","))
    }
    redirect(`/module-unavailable?${params.toString()}`)
  }
  if (
    role === "executive" &&
    !executiveHasAcademicWorkflows &&
    nonAcademicExecutiveHiddenUrls.has(currentUrl)
  ) {
    redirect("/executive/programs")
  }

  const isDashboard = currentUrl === zone.dashboardPath
  const filteredNavMain = filterUmsNavItemsBySettings(
    zone.navMain,
    publicSettings,
    role
  )
  const page = isDashboard
    ? {
        title:
          role === "executive" && !executiveHasAcademicWorkflows
            ? "Executive Dashboard"
            : zone.headline,
        url: zone.dashboardPath,
        description:
          role === "executive" && !executiveHasAcademicWorkflows
            ? applyUmsTerminology(
                "A centre workspace for public centre details, centre programmes, calendar items, and notifications.",
                publicSettings
              )
            : zone.description,
        icon: "dashboard" as UmsIconKey,
      }
    : getNavItemByUrl(filteredNavMain, currentUrl)

  if (!page) {
    notFound()
  }

  const availablePages = filterExecutivePages(
    filteredNavMain.flatMap((item) => [
    {
      title: item.title,
      url: item.url,
      description: item.description,
      groupTitle: null as string | null,
    },
    ...(item.items?.map((subItem) => ({
      title: subItem.title,
      url: subItem.url,
      description: subItem.description,
      groupTitle: item.title,
    })) ?? []),
    ]),
    executiveHasAcademicWorkflows
  )
  const priorities =
    role === "executive" && !executiveHasAcademicWorkflows
      ? [
          "Maintain the assigned centre profile and public centre details.",
          "Add and update centre programmes that do not require class scheduling.",
          "Coordinate centre activities without course offering or timetable workflows.",
        ].map((priority) =>
          applyUmsTerminology(priority, publicSettings)
        )
      : zone.priorities
  const metrics =
    role === "executive" && !executiveHasAcademicWorkflows
      ? [
          {
            title: "Centre Profile",
            value: "Live",
            subtitle: "Public centre details can be maintained here.",
            icon: "academic" as UmsIconKey,
          },
          {
            title: "Centre Programmes",
            value: "Managed",
            subtitle: "Programmes do not require class schedules.",
            icon: "records" as UmsIconKey,
          },
          {
            title: "Academic Workflows",
            value: "Off",
            subtitle: "Course and timetable workflows are hidden for this centre.",
            icon: "settings" as UmsIconKey,
          },
        ].map((metric) => ({
          ...metric,
          title: applyUmsTerminology(metric.title, publicSettings),
          subtitle: applyUmsTerminology(metric.subtitle, publicSettings),
        }))
      : zone.metrics

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
            {metrics.map((metric) => {
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

        <section className="grid gap-4 lg:grid-cols-[22rem_minmax(0,1fr)]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">
                Primary Responsibilities
              </CardTitle>
              <CardDescription>{zone.scope}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {priorities.map((priority) => (
                <div
                  key={priority}
                  className="flex gap-2 text-muted-foreground"
                >
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600" />
                  <p>{priority}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">
                Available In This Zone
              </CardTitle>
              <CardDescription>
                Every primary page linked from the sidebar.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {availablePages.map((item, i) => (
                <Link
                  key={`${item.url ?? ""}-${item.title ?? ""}-${i}`}
                  href={item.url}
                  aria-current={item.url === currentUrl ? "page" : undefined}
                  className="group rounded-lg border border-border bg-background p-3 text-sm transition-colors hover:bg-muted/60 aria-current:border-primary/40 aria-current:bg-muted"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      {item.groupTitle ? (
                        <p className="truncate text-xs font-medium text-muted-foreground">
                          {item.groupTitle}
                        </p>
                      ) : null}
                      <p className="truncate font-medium text-foreground">
                        {item.title}
                      </p>
                    </div>
                    <ArrowUpRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </div>
                  {item.description ? (
                    <p className="mt-2 line-clamp-2 text-xs leading-5 text-muted-foreground">
                      {item.description}
                    </p>
                  ) : null}
                </Link>
              ))}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}
