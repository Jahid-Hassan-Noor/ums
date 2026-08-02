"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import {
  Archive,
  ArrowUpRight,
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

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ROLE_ZONES,
  type UmsIconKey,
  type UmsNavItem,
  type UserRole,
} from "@/lib/ums-roles"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  filterUmsNavItemsByFeatures,
  loadPublicUmsSettings,
  type UmsPublicSettings,
} from "@/lib/ums-settings"

type DashboardRole = Exclude<UserRole, "applicant">

type NavigationDashboardProps = {
  role: DashboardRole
  executiveHasAcademicWorkflows?: boolean
}

type DashboardLink = UmsNavItem & {
  href: string
  destinationLabel: string
}

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

const catererCheckoutLink: UmsNavItem = {
  title: "Student Card Checkout",
  url: "#student-card-checkout",
  icon: "records",
  description:
    "Search a student card, confirm the bill, and deduct it from the current balance.",
}

export function AdminDashboard() {
  return <NavigationDashboard role="admin" />
}

export function ExecutiveDashboard({
  executiveHasAcademicWorkflows,
}: {
  executiveHasAcademicWorkflows: boolean
}) {
  return (
    <NavigationDashboard
      role="executive"
      executiveHasAcademicWorkflows={executiveHasAcademicWorkflows}
    />
  )
}

export function TeacherDashboard() {
  return <NavigationDashboard role="teacher" />
}

export function StudentDashboard() {
  return <NavigationDashboard role="student" />
}

export function LibrarianDashboard() {
  return <NavigationDashboard role="librarian" />
}

export function TechnicianDashboard() {
  return <NavigationDashboard role="technician" />
}

export function AccountantDashboard() {
  return <NavigationDashboard role="accountant" />
}

export function HrDashboard() {
  return <NavigationDashboard role="hr" />
}

export function CatererDashboard() {
  return <NavigationDashboard role="caterer" />
}

function NavigationDashboard({
  role,
  executiveHasAcademicWorkflows = true,
}: NavigationDashboardProps) {
  const zone = ROLE_ZONES[role]
  const [publicSettings, setPublicSettings] = useState(
    DEFAULT_UMS_PUBLIC_SETTINGS
  )
  useEffect(() => {
    let ignore = false
    void loadPublicUmsSettings().then((settings) => {
      if (!ignore) setPublicSettings(settings)
    })
    return () => {
      ignore = true
    }
  }, [])

  const navItems = useMemo(
    () =>
      getRoleNavigationItems(
        role,
        executiveHasAcademicWorkflows,
        publicSettings
      ),
    [executiveHasAcademicWorkflows, publicSettings, role]
  )
  const links = navItems.map(toDashboardLink)
  const compactCards = publicSettings.uiCustomization.card_density === "compact"
  const showDescriptions = publicSettings.uiCustomization.show_link_descriptions

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <section className="space-y-3 border-b border-border/70 pb-5">
        {publicSettings.uiCustomization.show_scope_badge ? (
          <Badge variant="outline" className="bg-background">
            {zone.scope}
          </Badge>
        ) : null}
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {zone.headline}
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Choose a destination to continue your work in the UMS.
          </p>
        </div>
      </section>

      <section className="space-y-4" aria-labelledby={`${role}-quick-links`}>
        <div>
          <h2
            id={`${role}-quick-links`}
            className="text-lg font-semibold tracking-tight"
          >
            Important links
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Open the tools and pages most relevant to your role.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {links.map((item) => (
            <NavigationCard
              key={`${item.title}-${item.href}`}
              item={item}
              compact={compactCards}
              showDescription={showDescriptions}
            />
          ))}
        </div>
      </section>
    </div>
  )
}

function NavigationCard({
  item,
  compact,
  showDescription,
}: {
  item: DashboardLink
  compact: boolean
  showDescription: boolean
}) {
  const Icon = iconMap[item.icon]
  const toolCount = item.items?.length ?? 0

  return (
    <Link
      href={item.href}
      className="group block h-full rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      <Card className="h-full border-border/70 bg-card/95 shadow-sm transition duration-200 group-hover:-translate-y-0.5 group-hover:border-primary/35 group-hover:shadow-md">
        <CardHeader className={compact ? "gap-3 p-4" : "gap-4"}>
          <div className="flex items-start justify-between gap-3">
            <span
              className={`inline-flex items-center justify-center rounded-xl border border-primary/15 bg-primary/10 text-primary ${
                compact ? "size-10" : "size-12"
              }`}
              style={{ color: "var(--ums-dashboard-accent)" }}
            >
              <Icon className={compact ? "size-5" : "size-6"} aria-hidden="true" />
            </span>
            <ArrowUpRight className="size-5 text-muted-foreground transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary" />
          </div>
          <div className={compact ? "space-y-1" : "space-y-2"}>
            <CardTitle className={compact ? "text-base" : "text-lg"}>
              {item.title}
            </CardTitle>
            {showDescription ? (
              <CardDescription className="line-clamp-2 leading-5">
                {item.description || `Open ${item.title}.`}
              </CardDescription>
            ) : null}
          </div>
        </CardHeader>
        <CardContent
          className={`mt-auto flex items-center justify-between gap-3 border-t border-border/60 text-xs text-muted-foreground ${
            compact ? "p-4 pt-3" : "pt-4"
          }`}
        >
          <span className="truncate">Open {item.destinationLabel}</span>
          {toolCount > 0 ? (
            <Badge variant="secondary">
              {toolCount} {toolCount === 1 ? "tool" : "tools"}
            </Badge>
          ) : null}
        </CardContent>
      </Card>
    </Link>
  )
}

function toDashboardLink(item: UmsNavItem): DashboardLink {
  const destination = item.items?.[0]

  return {
    ...item,
    href: destination?.url ?? item.url,
    destinationLabel: destination?.title ?? item.title,
  }
}

function getRoleNavigationItems(
  role: DashboardRole,
  executiveHasAcademicWorkflows: boolean,
  publicSettings: UmsPublicSettings
) {
  const zone = ROLE_ZONES[role]
  let mainItems = zone.navMain.filter(
    (item) => item.url !== zone.dashboardPath
  )

  if (role === "executive" && !executiveHasAcademicWorkflows) {
    const hiddenTopLevel = new Set([
      "/executive/courses",
      "/executive/results",
    ])
    const hiddenChildren = new Set([
      "/executive/manage/students",
      "/executive/manage/schedule",
    ])

    mainItems = mainItems
      .filter((item) => !hiddenTopLevel.has(item.url))
      .map((item) => ({
        ...item,
        items: item.items?.filter((child) => !hiddenChildren.has(child.url)),
      }))
  }

  if (role === "caterer") {
    mainItems = [catererCheckoutLink, ...mainItems]
  }

  return filterUmsNavItemsByFeatures(
    [...mainItems, ...zone.navSecondary],
    publicSettings.features
  )
}
