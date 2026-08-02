"use client"

import { useMemo } from "react"
import {
  Activity,
  AlertCircle,
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  ClipboardList,
  FileCheck2,
  GraduationCap,
  Layers,
  RefreshCw,
  Users,
} from "lucide-react"

import { StatisticsDataPage } from "@/components/role-zone/role-statistics-page"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ValueBarChart } from "@/components/charts/value-bar-chart"
import { useIsDarkMode } from "@/hooks/use-dark-mode"
import { apiFetch } from "@/lib/auth"

type ScopePayload = {
  kind: string | null
  id: number | null
  code: string
  name: string
  academic_workflows: boolean
}

type ExecutiveStatisticsData = {
  title: string
  section: string
  scope: ScopePayload
  scope_error: string | null
  people: {
    students: number
    teachers: number
    student_enrollment: {
      active: number
      inactive: number
      graduated: number
      other: number
    }
  }
  academic_units: {
    programs: number
    academic_programs: number
    departments: number
    active_semesters: number
  }
  academics: {
    courses: number
    active_courses: number
    offerings: number
    active_offerings: number
    offering_capacity: number
    active_semesters: number
  }
  schedule: {
    meetings: number
    by_status: {
      imported: number
      scheduled: number
      cancelled: number
    }
    by_type: {
      lecture: number
      lab: number
    }
  }
  results: {
    batches: number
    draft: number
    review: number
    approved: number
    published: number
    records: number
    publications: number
  }
  course_proposals: {
    total: number
    draft: number
    submitted: number
    approved: number
    rejected: number
    offered: number
  }
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

const numberFormatter = new Intl.NumberFormat("en-US")

function formatNumber(value: number) {
  return numberFormatter.format(value)
}

function percentage(part: number, total: number) {
  if (!total) return "0%"
  return `${Math.round((part / total) * 100)}%`
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function StatCard({
  title,
  value,
  detail,
  icon: Icon,
  tone,
}: {
  title: string
  value: string
  detail: string
  icon: typeof Users
  tone: string
}) {
  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between gap-3 pb-2">
        <CardDescription className="text-sm font-medium">
          {title}
        </CardDescription>
        <span
          className={`rounded-lg border border-border bg-muted/50 p-2 ${tone}`}
        >
          <Icon className="size-4" />
        </span>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs leading-5 text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  )
}

function StatusRow({
  label,
  value,
  total,
}: {
  label: string
  value: number
  total: number
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="min-w-0">
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">
          {percentage(value, total)} of total
        </p>
      </div>
      <Badge variant="secondary">{formatNumber(value)}</Badge>
    </div>
  )
}

const executiveStatisticsBreadcrumb = [
  { href: "/executive", title: "Executive" },
  { href: "/executive/statistics", title: "Statistics" },
]

function loadExecutiveStatistics() {
  return apiFetch<ExecutiveStatisticsData>("/executive/statistics")
}

function executiveStatisticsErrorMessage(caught: unknown) {
  return caught instanceof Error
    ? caught.message
    : "Unable to load executive statistics."
}

function ExecutiveStatisticsContent({
  stats,
  isDark,
  isRefreshing,
  refresh,
}: {
  stats: ExecutiveStatisticsData
  isDark: boolean
  isRefreshing: boolean
  refresh: (silent?: boolean) => Promise<void>
}) {
  const derived = useMemo(() => {
    return {
      peopleTotal: stats.people.students + stats.people.teachers,
      scheduledActive:
        stats.schedule.by_status.imported + stats.schedule.by_status.scheduled,
      avgSeatsPerOffering: stats.academics.offerings
        ? Math.round(
            stats.academics.offering_capacity / stats.academics.offerings
          )
        : 0,
    }
  }, [stats])

  return (
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <Badge variant="outline" className="w-fit bg-background">
              {stats.scope.kind
                ? `Assigned ${stats.scope.kind}`
                : "Unassigned scope"}
            </Badge>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold sm:text-3xl">
                Executive Statistics
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                {stats.scope.id
                  ? `${stats.scope.code} - ${stats.scope.name}`
                  : "Statistics become available after this executive account is assigned to one school or centre."}
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Badge
              variant={stats.scope.academic_workflows ? "secondary" : "outline"}
              className="justify-center"
            >
              {stats.scope.academic_workflows
                ? "Academic workflows active"
                : "Academic workflows inactive"}
            </Badge>
            <Button
              variant="outline"
              disabled={isRefreshing}
              onClick={() => void refresh(true)}
              className="gap-2"
            >
              <RefreshCw
                className={`size-4 ${isRefreshing ? "animate-spin" : ""}`}
              />
              {isRefreshing ? "Refreshing..." : "Refresh"}
            </Button>
          </div>
        </section>

        {stats.scope_error ? (
          <p className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">
            <AlertCircle className="size-4 shrink-0" />
            {stats.scope_error}
          </p>
        ) : null}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Students in Scope"
            value={formatNumber(stats.people.students)}
            detail={`${formatNumber(stats.people.student_enrollment.active)} active enrollment records`}
            icon={GraduationCap}
            tone="text-sky-500"
          />
          <StatCard
            title="Teachers in Scope"
            value={formatNumber(stats.people.teachers)}
            detail={`${formatNumber(derived.peopleTotal)} people across students and teachers`}
            icon={Users}
            tone="text-emerald-500"
          />
          <StatCard
            title="Course Offerings"
            value={formatNumber(stats.academics.offerings)}
            detail={`${formatNumber(stats.academics.offering_capacity)} total seats, ${formatNumber(derived.avgSeatsPerOffering)} avg seats`}
            icon={BookOpen}
            tone="text-amber-500"
          />
          <StatCard
            title="Review Workload"
            value={formatNumber(stats.results.review)}
            detail={`${formatNumber(stats.results.review)} result batches under review`}
            icon={ClipboardList}
            tone="text-rose-500"
          />
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <ValueBarChart
            title="People and Academic Coverage"
            subtitle="Current records inside the assigned school or centre"
            labels={[
              "Students",
              "Teachers",
              "Programs",
              "Courses",
              "Offerings",
            ]}
            values={[
              stats.people.students,
              stats.people.teachers,
              stats.academic_units.programs,
              stats.academics.courses,
              stats.academics.offerings,
            ]}
            isDark={isDark}
            formatter={(value) => formatNumber(Math.round(value))}
            gradientId="executive-coverage-gradient"
            startColor="#0ea5e9"
            endColor="#38bdf8"
            totalLabel="Combined Records"
            peakLabel="Largest Category"
          />

          <ValueBarChart
            title="Operational Workload"
            subtitle="Schedule, proposal, and result records"
            labels={["Classes", "Offerings", "Proposals", "Batches", "Records"]}
            values={[
              stats.schedule.meetings,
              stats.academics.offerings,
              stats.course_proposals.total,
              stats.results.batches,
              stats.results.records,
            ]}
            isDark={isDark}
            formatter={(value) => formatNumber(Math.round(value))}
            gradientId="executive-workload-gradient"
            startColor="#10b981"
            endColor="#34d399"
            totalLabel="Operational Records"
            peakLabel="Largest Work Queue"
          />

          <ValueBarChart
            title="Result Pipeline"
            subtitle="Result batches by executive review and publication state"
            labels={["Draft", "Review", "Approved", "Published", "Records"]}
            values={[
              stats.results.draft,
              stats.results.review,
              stats.results.approved,
              stats.results.published,
              stats.results.records,
            ]}
            isDark={isDark}
            formatter={(value) => formatNumber(Math.round(value))}
            gradientId="executive-result-pipeline-gradient"
            startColor="#f59e0b"
            endColor="#fbbf24"
            totalLabel="Result Records"
            peakLabel="Largest Result State"
          />

          <ValueBarChart
            title="Schedule Status Mix"
            subtitle="Class meetings by active, cancelled, and class-type buckets"
            labels={["Imported", "Scheduled", "Cancelled", "Lecture", "Lab"]}
            values={[
              stats.schedule.by_status.imported,
              stats.schedule.by_status.scheduled,
              stats.schedule.by_status.cancelled,
              stats.schedule.by_type.lecture,
              stats.schedule.by_type.lab,
            ]}
            isDark={isDark}
            formatter={(value) => formatNumber(Math.round(value))}
            gradientId="executive-schedule-mix-gradient"
            startColor="#8b5cf6"
            endColor="#a78bfa"
            totalLabel="Schedule Records"
            peakLabel="Largest Schedule Bucket"
          />
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {stats.insights.map((item) => (
            <Card key={item.key} className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="space-y-2 pb-2">
                <div className="flex items-center justify-between gap-3">
                  <CardDescription className="text-sm font-medium">
                    {item.label}
                  </CardDescription>
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
                  {formatNumber(item.value)}
                  {item.total ? (
                    <span className="text-sm font-medium text-muted-foreground">
                      {" "}
                      / {formatNumber(item.total)}
                    </span>
                  ) : null}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm leading-6 text-muted-foreground">{item.description}</p>
                <p className="text-xs font-medium text-foreground">{item.action}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">Academic Coverage</CardTitle>
                  <CardDescription>
                    Programmes, departments, courses, and semesters
                  </CardDescription>
                </div>
                <Layers className="size-5 text-sky-500" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatusRow
                label="Departments"
                value={stats.academic_units.departments}
                total={stats.academic_units.departments}
              />
              <Separator />
              <StatusRow
                label="Programmes"
                value={stats.academic_units.programs}
                total={stats.academic_units.programs}
              />
              <Separator />
              <StatusRow
                label="Academic programmes"
                value={stats.academic_units.academic_programs}
                total={stats.academic_units.programs}
              />
              <Separator />
              <StatusRow
                label="Active courses"
                value={stats.academics.active_courses}
                total={stats.academics.courses}
              />
              <Separator />
              <StatusRow
                label="Active semesters"
                value={stats.academics.active_semesters}
                total={stats.academics.active_semesters}
              />
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">Result Pipeline</CardTitle>
                  <CardDescription>
                    Batch review and publication status
                  </CardDescription>
                </div>
                <FileCheck2 className="size-5 text-amber-500" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatusRow
                label="Draft batches"
                value={stats.results.draft}
                total={stats.results.batches}
              />
              <Separator />
              <StatusRow
                label="Under review"
                value={stats.results.review}
                total={stats.results.batches}
              />
              <Separator />
              <StatusRow
                label="Approved"
                value={stats.results.approved}
                total={stats.results.batches}
              />
              <Separator />
              <StatusRow
                label="Published"
                value={stats.results.published}
                total={stats.results.batches}
              />
              <Separator />
              <StatusRow
                label="Result records"
                value={stats.results.records}
                total={stats.results.records}
              />
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">Schedule Mix</CardTitle>
                  <CardDescription>
                    Class meetings by status and type
                  </CardDescription>
                </div>
                <CalendarDays className="size-5 text-cyan-500" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatusRow
                label="Imported"
                value={stats.schedule.by_status.imported}
                total={stats.schedule.meetings}
              />
              <Separator />
              <StatusRow
                label="Scheduled"
                value={stats.schedule.by_status.scheduled}
                total={stats.schedule.meetings}
              />
              <Separator />
              <StatusRow
                label="Cancelled"
                value={stats.schedule.by_status.cancelled}
                total={stats.schedule.meetings}
              />
              <Separator />
              <StatusRow
                label="Lecture classes"
                value={stats.schedule.by_type.lecture}
                total={stats.schedule.meetings}
              />
              <Separator />
              <StatusRow
                label="Lab classes"
                value={stats.schedule.by_type.lab}
                total={stats.schedule.meetings}
              />
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">
                    Course Proposal Queue
                  </CardTitle>
                  <CardDescription>
                    Course-offer proposal lifecycle
                  </CardDescription>
                </div>
                <BarChart3 className="size-5 text-violet-500" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <StatusRow
                label="Draft"
                value={stats.course_proposals.draft}
                total={stats.course_proposals.total}
              />
              <Separator />
              <StatusRow
                label="Submitted"
                value={stats.course_proposals.submitted}
                total={stats.course_proposals.total}
              />
              <Separator />
              <StatusRow
                label="Approved"
                value={stats.course_proposals.approved}
                total={stats.course_proposals.total}
              />
              <Separator />
              <StatusRow
                label="Rejected"
                value={stats.course_proposals.rejected}
                total={stats.course_proposals.total}
              />
              <Separator />
              <StatusRow
                label="Offered"
                value={stats.course_proposals.offered}
                total={stats.course_proposals.total}
              />
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">
                    Operational Signals
                  </CardTitle>
                  <CardDescription>
                    Schedule progress and inbox load
                  </CardDescription>
                </div>
                <Activity className="size-5 text-rose-500" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">
                  Active schedule share
                </span>
                <span className="text-sm font-semibold">
                  {percentage(derived.scheduledActive, stats.schedule.meetings)}
                </span>
              </div>
              <Separator />
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">
                  Result publications
                </span>
                <span className="text-sm font-semibold">
                  {formatNumber(stats.results.publications)}
                </span>
              </div>
              <Separator />
              <div className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Bell className="size-4" />
                  Unread notifications
                </span>
                <Badge variant="secondary">
                  {formatNumber(stats.notifications.unread)}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">
              Recent Executive Activity
            </CardTitle>
            <CardDescription>
              Latest audit entries recorded for this assigned scope
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats.recent_audit_logs.length ? (
              stats.recent_audit_logs.map((log) => (
                <div
                  key={log.id}
                  className="flex flex-col gap-1 rounded-lg border border-border/70 bg-muted/30 px-3 py-2 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">
                      {log.action}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {log.user || "System"}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(log.timestamp)}
                  </p>
                </div>
              ))
            ) : (
              <div className="flex min-h-28 items-center justify-center rounded-lg border border-dashed border-border/80 bg-muted/20 px-4 text-center">
                <p className="max-w-md text-sm text-muted-foreground">
                  No executive audit activity has been recorded for this scope
                  yet.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
  )
}

export default function ExecutiveStatisticsPage() {
  const isDark = useIsDarkMode()

  return (
    <StatisticsDataPage
      breadcrumbItems={executiveStatisticsBreadcrumb}
      loadData={loadExecutiveStatistics}
      getErrorMessage={executiveStatisticsErrorMessage}
      renderContent={({ data: stats, isRefreshing, refresh }) => (
        <ExecutiveStatisticsContent
          stats={stats}
          isDark={isDark}
          isRefreshing={isRefreshing}
          refresh={refresh}
        />
      )}
    />
  )
}
