"use client"

import {
  Armchair,
  BookOpen,
  Building2,
  FileText,
  Home,
  Layers,
  RefreshCw,
  School as SchoolIcon,
  Users,
} from "lucide-react"

import { StatisticsDataPage } from "@/components/role-zone/role-statistics-page"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { apiFetch } from "@/lib/auth"
import { useIsDarkMode } from "@/hooks/use-dark-mode"
import { ValueBarChart } from "@/components/charts/value-bar-chart"

type UserStats = {
  student: number
  teacher: number
  executive: number
  librarian: number
  admin: number
  applicant: number
  total: number
}

type AcademicUnitsStats = {
  schools: number
  centers: number
  departments: number
  programs: number
  active_semesters: number
}

type InfrastructureStats = {
  buildings: number
  venues: number
  venue_capacity: number
  hostels: number
  hostel_rooms: number
  hostel_capacity: number
}

type ApplicationsStats = {
  total: number
  draft: number
  submitted: number
  screening: number
  info_requested: number
  scholarship_review: number
  interview: number
  offered: number
  waitlisted: number
  rejected: number
  enrolled: number
  withdrawn: number
}

type AcademicsStats = {
  courses: number
  offerings: number
  meetings: number
}

type StatisticsData = {
  title: string
  section: string
  users: UserStats
  academic_units: AcademicUnitsStats
  infrastructure: InfrastructureStats
  applications: ApplicationsStats
  academics: AcademicsStats
  notifications: {
    unread: number
  }
  insights: Array<{
    key: string
    label: string
    value: number
    total: number
    level: "healthy" | "watch" | "risk"
    description: string
    action: string
  }>
  recent_audit_logs: Array<{
    id: number
    action: string
    user: string | null
    timestamp: string
  }>
}

const adminStatisticsBreadcrumb = [
  { href: "/admin", title: "Admin" },
  { href: "/admin/statistics", title: "Statistics" },
]

function loadAdminStatistics() {
  return apiFetch<StatisticsData>("/admin/statistics")
}

function adminStatisticsErrorMessage(caught: unknown) {
  return caught instanceof Error ? caught.message : "Failed to load portal statistics."
}

export default function AdminStatisticsPage() {
  const isDark = useIsDarkMode()

  return (
    <StatisticsDataPage
      breadcrumbItems={adminStatisticsBreadcrumb}
      loadData={loadAdminStatistics}
      getErrorMessage={adminStatisticsErrorMessage}
      errorFallback="An unexpected error occurred while fetching system metrics."
      renderContent={({ data: stats, isRefreshing, refresh }) => (
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        {/* Header Section */}
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <Badge variant="outline" className="bg-background">
              System-wide Configuration & Reporting
            </Badge>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                System Statistics
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Real-time dashboard aggregates across users, academic organizational structure, applicant funnel, and physical infrastructure.
              </p>
            </div>
          </div>
          <div>
            <Button
              variant="outline"
              disabled={isRefreshing}
              onClick={() => void refresh(true)}
              className="gap-2"
            >
              <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
              {isRefreshing ? "Refreshing..." : "Refresh Stats"}
            </Button>
          </div>
        </section>

        {/* Overview Metric Grid */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardDescription className="text-sm font-medium">Total Portal Users</CardDescription>
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-blue-500">
                <Users className="size-4" />
              </span>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-2xl font-bold tracking-tight">{stats.users.total}</p>
              <p className="text-xs text-muted-foreground">Active student, staff & admin accounts</p>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardDescription className="text-sm font-medium">Academic Structure</CardDescription>
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-emerald-500">
                <Building2 className="size-4" />
              </span>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-2xl font-bold tracking-tight">
                {stats.academic_units.schools + stats.academic_units.centers} Units
              </p>
              <p className="text-xs text-muted-foreground">
                {stats.academic_units.programs} programs, {stats.academic_units.departments} departments
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardDescription className="text-sm font-medium">Physical Infrastructure</CardDescription>
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-purple-500">
                <Layers className="size-4" />
              </span>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-2xl font-bold tracking-tight">{stats.infrastructure.venues} Venues</p>
              <p className="text-xs text-muted-foreground">
                {stats.infrastructure.venue_capacity} seats classroom seating capacity
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardDescription className="text-sm font-medium">Semester & Offerings</CardDescription>
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-amber-500">
                <BookOpen className="size-4" />
              </span>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-2xl font-bold tracking-tight">{stats.academics.offerings} Active Offerings</p>
              <p className="text-xs text-muted-foreground">
                {stats.academics.meetings} sessions scheduled in term
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Charts & Graphical Data */}
        <section className="grid gap-6 lg:grid-cols-2">
          {/* User Distribution Chart */}
          <ValueBarChart
            title="User Accounts by Role"
            subtitle="Portal registrations distributed across primary user roles"
            labels={["Students", "Teachers", "Executives", "Librarians", "Admins", "Applicants"]}
            values={[
              stats.users.student,
              stats.users.teacher,
              stats.users.executive,
              stats.users.librarian,
              stats.users.admin,
              stats.users.applicant,
            ]}
            isDark={isDark}
            formatter={(value) => String(Math.round(value))}
            gradientId="user-roles-gradient"
            startColor="#3b82f6"
            endColor="#60a5fa"
            totalLabel="Total Registered Users"
            peakLabel="Highest Role Count"
          />

          {/* Admission Applications Chart */}
          {stats.applications.total > 0 ? (
            <ValueBarChart
              title="Admissions Funnel"
              subtitle="Distribution of prospective student applications by status"
              labels={["Draft", "Submitted", "Screening", "Offered", "Rejected", "Enrolled"]}
              values={[
                stats.applications.draft,
                stats.applications.submitted,
                stats.applications.screening,
                stats.applications.offered,
                stats.applications.rejected,
                stats.applications.enrolled,
              ]}
              isDark={isDark}
              formatter={(value) => String(Math.round(value))}
              gradientId="applications-gradient"
              startColor="#10b981"
              endColor="#34d399"
              totalLabel="Total Applications"
              peakLabel="Highest Stage Count"
            />
          ) : (
            <Card className="flex flex-col justify-between border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="space-y-1 pb-2">
                <CardTitle className="text-base text-foreground">Admissions Funnel</CardTitle>
                <CardDescription className="text-sm text-muted-foreground">
                  Distribution of prospective student applications
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col items-center justify-center py-12 text-center">
                <FileText className="size-12 text-muted-foreground/40 mb-3" />
                <p className="text-sm font-semibold text-foreground">No Applications Yet</p>
                <p className="text-xs text-muted-foreground max-w-sm mt-1">
                  Once prospective applicants submit their admissions requests, stages and status charts will compile here.
                </p>
              </CardContent>
            </Card>
          )}

          <ValueBarChart
            title="Campus Capacity"
            subtitle="Physical campus resources available for teaching and residence"
            labels={["Buildings", "Venues", "Venue Seats", "Hostels", "Rooms", "Beds"]}
            values={[
              stats.infrastructure.buildings,
              stats.infrastructure.venues,
              stats.infrastructure.venue_capacity,
              stats.infrastructure.hostels,
              stats.infrastructure.hostel_rooms,
              stats.infrastructure.hostel_capacity,
            ]}
            isDark={isDark}
            formatter={(value) => String(Math.round(value))}
            gradientId="campus-capacity-gradient"
            startColor="#8b5cf6"
            endColor="#a78bfa"
            totalLabel="Capacity Records"
            peakLabel="Largest Capacity"
          />

          <ValueBarChart
            title="Academic Operations"
            subtitle="Academic directory and timetable records across the portal"
            labels={["Schools", "Centres", "Departments", "Programs", "Courses", "Meetings"]}
            values={[
              stats.academic_units.schools,
              stats.academic_units.centers,
              stats.academic_units.departments,
              stats.academic_units.programs,
              stats.academics.courses,
              stats.academics.meetings,
            ]}
            isDark={isDark}
            formatter={(value) => String(Math.round(value))}
            gradientId="academic-operations-gradient"
            startColor="#f59e0b"
            endColor="#fbbf24"
            totalLabel="Academic Records"
            peakLabel="Largest Record Set"
          />
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {stats.insights.map((item) => (
            <Card key={item.key} className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="space-y-2 pb-2">
                <div className="flex items-center justify-between gap-3">
                  <CardDescription className="text-sm font-medium">{item.label}</CardDescription>
                  <Badge
                    variant="outline"
                    className={
                      item.level === "healthy"
                        ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                        : item.level === "watch"
                          ? "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300"
                          : "border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300"
                    }
                  >
                    {item.level === "healthy" ? "Healthy" : item.level === "watch" ? "Watch" : "Risk"}
                  </Badge>
                </div>
                <CardTitle className="text-2xl">
                  {item.value}
                  {item.total ? <span className="text-sm font-medium text-muted-foreground"> / {item.total}</span> : null}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm leading-6 text-muted-foreground">{item.description}</p>
                <p className="text-xs font-medium text-foreground">{item.action}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        {/* Detailed Breakdown Lists */}
        <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Academic Structure Card */}
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Academic Units</CardTitle>
              <CardDescription>School and center counts across the institution</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <SchoolIcon className="size-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">Schools</span>
                </div>
                <Badge variant="secondary">{stats.academic_units.schools}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="size-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">Academic Centres</span>
                </div>
                <Badge variant="secondary">{stats.academic_units.centers}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="size-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">Departments</span>
                </div>
                <Badge variant="secondary">{stats.academic_units.departments}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="size-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">Programmes of Study</span>
                </div>
                <Badge variant="secondary">{stats.academic_units.programs}</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Infrastructure Capacity Card */}
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Campus Infrastructure</CardTitle>
              <CardDescription>Academic and housing accommodations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="size-4 text-purple-500" />
                  <span className="text-sm font-medium text-foreground">Buildings</span>
                </div>
                <Badge variant="secondary">{stats.infrastructure.buildings}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="size-4 text-purple-500" />
                  <span className="text-sm font-medium text-foreground">Lecture Venues</span>
                </div>
                <Badge variant="secondary">{stats.infrastructure.venues}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Armchair className="size-4 text-purple-500" />
                  <span className="text-sm font-medium text-foreground">Seating Capacity</span>
                </div>
                <Badge variant="secondary">{stats.infrastructure.venue_capacity} seats</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Home className="size-4 text-purple-500" />
                  <span className="text-sm font-medium text-foreground">Hostel Capacity</span>
                </div>
                <Badge variant="secondary">
                  {stats.infrastructure.hostel_rooms} rooms ({stats.infrastructure.hostel_capacity} beds)
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* System Insights Card */}
          <Card className="border-border/70 bg-card/95 shadow-sm lg:col-span-1 md:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Operational Insights</CardTitle>
              <CardDescription>Ratios and system health metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Average Room Size</span>
                <span className="text-sm font-semibold text-foreground">
                  {stats.infrastructure.venues > 0
                    ? Math.round(stats.infrastructure.venue_capacity / stats.infrastructure.venues)
                    : 0}{" "}
                  seats/room
                </span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Faculty Member Ratio</span>
                <span className="text-sm font-semibold text-foreground">
                  1 :{" "}
                  {stats.users.teacher > 0 ? Math.round(stats.users.student / stats.users.teacher) : stats.users.student}
                </span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Course Registration Level</span>
                <span className="text-sm font-semibold text-foreground">
                  {stats.academics.offerings > 0
                    ? Math.round(stats.academics.meetings / stats.academics.offerings)
                    : 0}{" "}
                  meetings/course
                </span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Active Term Status</span>
                <Badge
                  variant={stats.academic_units.active_semesters > 0 ? "outline" : "destructive"}
                  className={stats.academic_units.active_semesters > 0 ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20 dark:bg-emerald-500/20" : ""}
                >
                  {stats.academic_units.active_semesters > 0 ? "Active Semester Live" : "No Active Terms"}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Notifications Card */}
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardDescription className="text-sm font-medium">Unread Notifications</CardDescription>
              <Badge variant="secondary" className="bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20">
                {stats.notifications.unread}
              </Badge>
            </CardHeader>
          </Card>

          {/* Recent Audit Logs Card */}
          <Card className="border-border/70 bg-card/95 shadow-sm lg:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Recent Activity</CardTitle>
              <CardDescription>Latest system audit entries</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {stats.recent_audit_logs.map((log) => (
                <div key={log.id} className="flex justify-between text-sm text-muted-foreground">
                  <span>{log.action}</span>
                  <span>{new Date(log.timestamp).toLocaleString()}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>
      </main>
      )}
    />
  )
}
