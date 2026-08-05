"use client"

import { useCallback, useEffect, useState, type ComponentType, type ReactNode } from "react"
import {
  AlertCircle,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  FileCheck2,
  GraduationCap,
  Library,
  RefreshCw,
  Upload,
  Users,
  WalletCards,
  Wrench,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import LoadingScreen from "@/components/ui/loading-screen"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ValueBarChart } from "@/components/charts/value-bar-chart"
import { useIsDarkMode } from "@/hooks/use-dark-mode"
import { apiFetch } from "@/lib/auth"
import { loadApplyApplications, type ApplyApplication } from "@/lib/apply"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  formatUmsMoney,
  loadPublicUmsSettings,
  type UmsPublicSettings,
} from "@/lib/ums-settings"
import type { UserRole } from "@/lib/ums-roles"

type StatisticsRole = Exclude<UserRole, "admin" | "executive">

type MetricDefinition = {
  title: string
  value: string
  detail: string
  icon: ComponentType<{ className?: string }>
  tone: string
}

type ChartDefinition = {
  title: string
  subtitle: string
  labels: string[]
  values: number[]
  gradientId: string
  startColor: string
  endColor: string
  totalLabel: string
  peakLabel: string
}

type InsightDefinition = {
  title: string
  value: string
  detail: string
  level: "healthy" | "watch" | "risk"
}

type RoleStatisticsData = {
  title: string
  badge: string
  summary: string
  breadcrumb: Array<{ href: string; title: string }>
  metrics: MetricDefinition[]
  charts: ChartDefinition[]
  insights: InsightDefinition[]
  warnings?: string[]
}

export type StatisticsBreadcrumbItem = {
  href: string
  title: string
}

type StatisticsRenderProps<TData> = {
  data: TData
  isRefreshing: boolean
  refresh: (silent?: boolean) => Promise<void>
}

type StatisticsDataPageProps<TData> = {
  breadcrumbItems: StatisticsBreadcrumbItem[]
  loadData: () => Promise<TData>
  renderContent: (props: StatisticsRenderProps<TData>) => ReactNode
  getErrorMessage?: (caught: unknown) => string
  errorFallback?: string
}

type OptionalResult<T> = {
  data: T | null
  warning: string | null
}

type StudentDashboardPayload = {
  canteen_account?: {
    allowance_amount?: string
    spent_amount?: string
    balance?: string
    transactions?: unknown[]
  } | null
}

type StudentAttendancePayload = {
  courses?: Array<{
    attended?: number
    late?: number
    absent?: number
    total_classes?: number
    attendance_percentage?: number
  }>
}

type StudentAssignmentsPayload = {
  counts?: Record<string, number>
  assignments?: Array<{
    student_status?: string
    is_overdue?: boolean
    submission?: { status?: string } | null
  }>
}

type StudentRegistrationsPayload = {
  registrations?: Array<{ status?: string }>
}

type StudentTicketsPayload = {
  tickets?: Array<{ status?: string; category_label?: string }>
}

type TeacherCoursesPayload = {
  courses?: Array<{
    is_active?: boolean
    assignment_count?: number
    resource_count?: number
    section_count?: number
    student_count?: number
  }>
}

type TeacherAssignmentsPayload = {
  assignments?: Array<{
    status?: string
    submission_count?: number | null
    graded_count?: number | null
  }>
}

type TeacherSessionsPayload = {
  sessions?: Array<{ status?: string }>
}

type TeacherResultsPayload = {
  summary?: Record<string, number>
}

type LibrarianDashboardPayload = {
  summary?: Record<string, number>
}

type CatererDashboardPayload = {
  summary?: Record<string, string | number>
}

type TechnicianDashboardPayload = {
  summary?: Record<string, number>
  tickets?: Array<{ status?: string; category_label?: string }>
}

type AccountantDashboardPayload = {
  summary?: Record<string, string | number>
  plans?: Array<{ is_active?: boolean; subscription_type?: string }>
  recent_subscriptions?: Array<{ status?: string }>
}

type AccountantLedgerDashboardPayload = {
  total_students?: number
  students_with_balance?: number
  total_outstanding?: string
  active_holds?: number
  total_charges?: number
  total_charges_amount?: string
  total_entries?: number
  total_payments?: string
  overdue_charges?: number
  active_plans?: number
  category_breakdown?: Array<{ code?: string; name?: string; total?: string; count?: number }>
}

type AccountantCanteenPayload = {
  current?: {
    eligible_students?: number
    allocated?: string
    spent?: string
    manual_additions?: string
    transactions?: number
  }
  settings?: {
    monthly_allowance?: string
    current_allocation?: string
    eligible_students?: number
  }
}

type AccountantCompensationPayload = {
  summary?: {
    pending?: number
    approved?: number
    rejected?: number
  }
  requests?: Array<{ status?: string; request_type?: string }>
}

const numberFormatter = new Intl.NumberFormat("en-US")

const statusLabels: Record<string, string> = {
  addressed: "Addressed",
  approved: "Approved",
  archived: "Archived",
  closed: "Closed",
  draft: "Draft",
  dropped: "Dropped",
  enrolled: "Enrolled",
  expired: "Expired",
  graded: "Graded",
  inactive: "Inactive",
  in_progress: "In Progress",
  info_requested: "Info Requested",
  late: "Late",
  not_started: "Not Started",
  offered: "Offered",
  overdue: "Overdue",
  pending: "Pending",
  published: "Published",
  rejected: "Rejected",
  returned: "Returned",
  review: "Review",
  screening: "Screening",
  scholarship_review: "Scholarship",
  solved: "Solved",
  submitted: "Submitted",
  upcoming: "Upcoming",
  waitlisted: "Waitlisted",
  withdrawn: "Withdrawn",
}

function formatNumber(value: number) {
  return numberFormatter.format(Math.round(Number.isFinite(value) ? value : 0))
}

function formatMoney(
  value: unknown,
  settings: UmsPublicSettings = DEFAULT_UMS_PUBLIC_SETTINGS
) {
  return formatUmsMoney(toNumber(value), settings)
}

function toNumber(value: unknown) {
  const numberValue = Number(value ?? 0)
  return Number.isFinite(numberValue) ? numberValue : 0
}

function sum(values: number[]) {
  return values.reduce((total, value) => total + value, 0)
}

function percentage(part: number, total: number) {
  if (!total) return "0%"
  return `${Math.round((part / total) * 100)}%`
}

function labelFor(value: string) {
  return statusLabels[value] ?? value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function metric(
  title: string,
  value: string,
  detail: string,
  icon: MetricDefinition["icon"],
  tone: string
): MetricDefinition {
  return { title, value, detail, icon, tone }
}

function chart(
  title: string,
  subtitle: string,
  labels: string[],
  values: number[],
  gradientId: string,
  startColor: string,
  endColor: string,
  totalLabel = "Total",
  peakLabel = "Peak"
): ChartDefinition {
  return {
    title,
    subtitle,
    labels,
    values,
    gradientId,
    startColor,
    endColor,
    totalLabel,
    peakLabel,
  }
}

function insight(
  title: string,
  value: string,
  detail: string,
  level: InsightDefinition["level"]
): InsightDefinition {
  return { title, value, detail, level }
}

function countsFor<T>(
  items: T[],
  keys: string[],
  getKey: (item: T) => string | undefined | null
) {
  const counts = Object.fromEntries(keys.map((key) => [key, 0])) as Record<string, number>
  for (const item of items) {
    const key = getKey(item) || ""
    if (key in counts) counts[key] += 1
  }
  return counts
}

function topCounts<T>(
  items: T[],
  getKey: (item: T) => string | undefined | null,
  limit = 6
) {
  const counts = new Map<string, number>()
  for (const item of items) {
    const key = getKey(item)
    if (!key) continue
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
}

async function optionalLoad<T>(label: string, loader: () => Promise<T>): Promise<OptionalResult<T>> {
  try {
    return { data: await loader(), warning: null }
  } catch (caught) {
    const message = caught instanceof Error ? caught.message : "Unable to load data."
    return { data: null, warning: `${label}: ${message}` }
  }
}

function warningsFrom(results: Array<OptionalResult<unknown>>) {
  return results.flatMap((result) => (result.warning ? [result.warning] : []))
}

function roleBreadcrumb(role: StatisticsRole) {
  if (role === "applicant") {
    return [
      { href: "/apply", title: "Apply" },
      { href: "/apply/statistics", title: "Statistics" },
    ]
  }
  const label = labelFor(role)
  return [
    { href: `/${role}`, title: label },
    { href: `/${role}/statistics`, title: "Statistics" },
  ]
}

async function loadApplicantStatistics(): Promise<RoleStatisticsData> {
  const applications = await loadApplyApplications()
  const statuses = ["draft", "submitted", "screening", "offered", "enrolled", "rejected"]
  const statusCounts = countsFor(applications, statuses, (application) => application.status)
  const latest = applications[0]
  const documentCount = applications.reduce(
    (total, application) => total + (application.documents?.length ?? 0),
    0
  )
  const eventCount = applications.reduce(
    (total, application) => total + (application.status_events?.length ?? 0),
    0
  )
  const preferenceCount = applications.reduce(
    (total, application) =>
      total + (application.programme_preferences?.filter(Boolean).length ?? 0),
    0
  )
  const readinessChecks = latest
    ? [
        (latest.programme_preferences?.filter(Boolean).length ?? 0) >= 4,
        (latest.documents?.length ?? 0) > 0,
        latest.statement_accepted,
        latest.status !== "draft",
      ].filter(Boolean).length
    : 0
  const readiness = Math.round((readinessChecks / 4) * 100)

  return {
    title: "Applicant Statistics",
    badge: "Own application analytics",
    summary: "Admission progress, document activity, and application status distribution.",
    breadcrumb: roleBreadcrumb("applicant"),
    metrics: [
      metric("Applications", formatNumber(applications.length), "Draft and submitted applications.", FileCheck2, "text-teal-500"),
      metric("Documents", formatNumber(documentCount), "Uploaded files attached to your applications.", Upload, "text-sky-500"),
      metric("Programme Choices", formatNumber(preferenceCount), "Total selected programme preferences.", GraduationCap, "text-amber-500"),
      metric("Status Updates", formatNumber(eventCount), "Timeline events recorded by admissions staff.", ClipboardList, "text-violet-500"),
    ],
    charts: [
      chart(
        "Application Status",
        "Current application records by admissions stage",
        statuses.map(labelFor),
        statuses.map((key) => statusCounts[key]),
        "applicant-status-gradient",
        "#14b8a6",
        "#5eead4",
        "Applications",
        "Largest Stage"
      ),
      chart(
        "Application Activity",
        "Documents, programme choices, and review events",
        ["Applications", "Documents", "Choices", "Events"],
        [applications.length, documentCount, preferenceCount, eventCount],
        "applicant-activity-gradient",
        "#0ea5e9",
        "#38bdf8",
        "Activity Records",
        "Largest Activity"
      ),
    ],
    insights: [
      insight("Latest readiness", `${readiness}%`, latest ? "Based on choices, documents, declaration, and submission state." : "Create an application draft to begin.", readiness >= 75 ? "healthy" : readiness >= 40 ? "watch" : "risk"),
      insight("Scholarship requests", formatNumber(applications.filter((application: ApplyApplication) => application.scholarship_requested).length), "Applications requesting scholarship review.", "watch"),
    ],
  }
}

async function loadStudentStatistics(
  settings: UmsPublicSettings
): Promise<RoleStatisticsData> {
  const [dashboardResult, attendanceResult, assignmentsResult, registrationsResult, ticketsResult] =
    await Promise.all([
      optionalLoad("Dashboard", () => apiFetch<StudentDashboardPayload>("/student/dashboard")),
      optionalLoad("Attendance report", () => apiFetch<StudentAttendancePayload>("/student/attendance/report")),
      optionalLoad("Assignments", () => apiFetch<StudentAssignmentsPayload>("/student/assignments")),
      optionalLoad("Registrations", () => apiFetch<StudentRegistrationsPayload>("/student/registration/requests")),
      optionalLoad("Service desk tickets", () => apiFetch<StudentTicketsPayload>("/ict-helpdesk/student/tickets")),
    ])
  const courses = attendanceResult.data?.courses ?? []
  const attended = sum(courses.map((course) => toNumber(course.attended)))
  const late = sum(courses.map((course) => toNumber(course.late)))
  const absent = sum(courses.map((course) => toNumber(course.absent)))
  const totalClasses = sum(courses.map((course) => toNumber(course.total_classes)))
  const averageAttendance = courses.length
    ? Math.round(sum(courses.map((course) => toNumber(course.attendance_percentage))) / courses.length)
    : 0
  const assignmentCounts = assignmentsResult.data?.counts ?? {}
  const registrations = registrationsResult.data?.registrations ?? []
  const registrationCounts = countsFor(registrations, ["pending", "approved", "rejected", "dropped"], (item) => item.status)
  const tickets = ticketsResult.data?.tickets ?? []
  const ticketCounts = countsFor(tickets, ["submitted", "addressed", "in_progress", "solved"], (item) => item.status)
  const canteenAccount = dashboardResult.data?.canteen_account

  return {
    title: "Student Statistics",
    badge: "Own academic and service records",
    summary: "Attendance, assignments, registration status, canteen usage, and service desk ticket activity.",
    breadcrumb: roleBreadcrumb("student"),
    metrics: [
      metric("Average Attendance", `${averageAttendance}%`, `${formatNumber(totalClasses)} recorded class sessions.`, CalendarDays, "text-emerald-500"),
      metric("Open Assignments", formatNumber(toNumber(assignmentCounts.upcoming) + toNumber(assignmentCounts.overdue)), "Upcoming and overdue assignment work.", ClipboardList, "text-amber-500"),
      metric("Registrations", formatNumber(registrations.length), "Course registration requests in the active view.", BookOpen, "text-sky-500"),
      metric("Canteen Balance", formatMoney(canteenAccount?.balance, settings), "Current monthly student allowance balance.", WalletCards, "text-violet-500"),
    ],
    charts: [
      chart("Attendance Mix", "Present, late, and absent records across visible courses", ["Present", "Late", "Absent"], [attended, late, absent], "student-attendance-gradient", "#10b981", "#34d399", "Attendance Records", "Largest Bucket"),
      chart("Assignment Flow", "Current student assignment queue by status", ["Upcoming", "Overdue", "Submitted", "Graded"], [toNumber(assignmentCounts.upcoming), toNumber(assignmentCounts.overdue), toNumber(assignmentCounts.submitted), toNumber(assignmentCounts.graded)], "student-assignment-gradient", "#f59e0b", "#fbbf24", "Assignments", "Largest Queue"),
      chart("Registration Status", "Course registration outcomes in the selected term", ["Pending", "Approved", "Rejected", "Dropped"], [registrationCounts.pending, registrationCounts.approved, registrationCounts.rejected, registrationCounts.dropped], "student-registration-gradient", "#0ea5e9", "#38bdf8", "Registrations", "Largest Status"),
      chart("Service Desk Ticket Status", "Helpdesk issues submitted by you", ["Submitted", "Addressed", "Progress", "Solved"], [ticketCounts.submitted, ticketCounts.addressed, ticketCounts.in_progress, ticketCounts.solved], "student-ticket-gradient", "#8b5cf6", "#a78bfa", "Tickets", "Largest Status"),
    ],
    insights: [
      insight("Attendance risk", `${averageAttendance}%`, averageAttendance >= 80 ? "Attendance is above the usual intervention threshold." : "Attendance should be reviewed before it affects course standing.", averageAttendance >= 80 || totalClasses === 0 ? "healthy" : averageAttendance >= 70 ? "watch" : "risk"),
      insight("Overdue assignments", formatNumber(toNumber(assignmentCounts.overdue)), "Assignments currently past due.", toNumber(assignmentCounts.overdue) ? "risk" : "healthy"),
      insight("Open service desk tickets", formatNumber(ticketCounts.submitted + ticketCounts.addressed + ticketCounts.in_progress), "Support items still moving through the service desk.", ticketCounts.submitted + ticketCounts.addressed + ticketCounts.in_progress ? "watch" : "healthy"),
    ],
    warnings: warningsFrom([dashboardResult, attendanceResult, assignmentsResult, registrationsResult, ticketsResult]),
  }
}

async function loadTeacherStatistics(): Promise<RoleStatisticsData> {
  const [coursesResult, assignmentsResult, sessionsResult, resultsResult] = await Promise.all([
    optionalLoad("Courses", () => apiFetch<TeacherCoursesPayload>("/teacher/courses")),
    optionalLoad("Assignments", () => apiFetch<TeacherAssignmentsPayload>("/teacher/assignments")),
    optionalLoad("Attendance sessions", () => apiFetch<TeacherSessionsPayload>("/teacher/attendance/sessions")),
    optionalLoad("Results", () => apiFetch<TeacherResultsPayload>("/teacher/results")),
  ])
  const courses = coursesResult.data?.courses ?? []
  const assignments = assignmentsResult.data?.assignments ?? []
  const sessions = sessionsResult.data?.sessions ?? []
  const resultSummary = resultsResult.data?.summary ?? {}
  const assignmentCounts = countsFor(assignments, ["draft", "published", "closed", "archived"], (item) => item.status)
  const sessionCounts = countsFor(sessions, ["draft", "open", "closed", "cancelled"], (item) => item.status)
  const submissions = sum(assignments.map((item) => toNumber(item.submission_count)))
  const graded = sum(assignments.map((item) => toNumber(item.graded_count)))
  const activeCourses = courses.filter((course) => course.is_active).length
  const studentReach = sum(courses.map((course) => toNumber(course.student_count)))

  return {
    title: "Teacher Statistics",
    badge: "Assigned teaching scope",
    summary: "Course workload, assignment activity, attendance sessions, and result submission pipeline.",
    breadcrumb: roleBreadcrumb("teacher"),
    metrics: [
      metric("Assigned Courses", formatNumber(courses.length), `${formatNumber(activeCourses)} active course offerings.`, BookOpen, "text-sky-500"),
      metric("Student Reach", formatNumber(studentReach), "Students enrolled across assigned courses.", Users, "text-emerald-500"),
      metric("Submissions", formatNumber(submissions), `${formatNumber(graded)} submissions graded.`, ClipboardList, "text-amber-500"),
      metric("Results Pending", formatNumber(toNumber(resultSummary.not_started) + toNumber(resultSummary.draft)), "Course result batches not yet completed.", FileCheck2, "text-rose-500"),
    ],
    charts: [
      chart("Teaching Workload", "Course resources, students, and assignment volume", ["Courses", "Students", "Assignments", "Resources"], [courses.length, studentReach, sum(courses.map((course) => toNumber(course.assignment_count))), sum(courses.map((course) => toNumber(course.resource_count)))], "teacher-workload-gradient", "#0ea5e9", "#38bdf8", "Workload Records", "Largest Bucket"),
      chart("Assignment Lifecycle", "Assignments by publication status", ["Draft", "Published", "Closed", "Archived"], [assignmentCounts.draft, assignmentCounts.published, assignmentCounts.closed, assignmentCounts.archived], "teacher-assignment-gradient", "#f59e0b", "#fbbf24", "Assignments", "Largest Status"),
      chart("Attendance Sessions", "Attendance sessions by operational status", ["Draft", "Open", "Closed", "Cancelled"], [sessionCounts.draft, sessionCounts.open, sessionCounts.closed, sessionCounts.cancelled], "teacher-attendance-gradient", "#10b981", "#34d399", "Sessions", "Largest Status"),
      chart("Result Pipeline", "Assigned offerings by result workflow state", ["Not Started", "Draft", "Review", "Approved", "Published"], [toNumber(resultSummary.not_started), toNumber(resultSummary.draft), toNumber(resultSummary.review), toNumber(resultSummary.approved), toNumber(resultSummary.published)], "teacher-results-gradient", "#8b5cf6", "#a78bfa", "Offerings", "Largest State"),
    ],
    insights: [
      insight("Grading progress", percentage(graded, submissions), "Share of received submissions already graded.", graded >= submissions ? "healthy" : submissions ? "watch" : "healthy"),
      insight("Open attendance sessions", formatNumber(sessionCounts.open), "Attendance sessions still open.", sessionCounts.open ? "watch" : "healthy"),
      insight("Result draft load", formatNumber(toNumber(resultSummary.not_started) + toNumber(resultSummary.draft)), "Assigned offerings still before executive review.", toNumber(resultSummary.not_started) + toNumber(resultSummary.draft) ? "watch" : "healthy"),
    ],
    warnings: warningsFrom([coursesResult, assignmentsResult, sessionsResult, resultsResult]),
  }
}

async function loadLibrarianStatistics(): Promise<RoleStatisticsData> {
  const dashboard = await apiFetch<LibrarianDashboardPayload>("/librarian/dashboard")
  const summary = dashboard.summary ?? {}
  return {
    title: "Librarian Statistics",
    badge: "Library inventory and circulation",
    summary: "Available assets, active loans, pending requests, and overdue circulation risk.",
    breadcrumb: roleBreadcrumb("librarian"),
    metrics: [
      metric("Book Titles", formatNumber(toNumber(summary.book_titles)), "Active catalog titles.", Library, "text-sky-500"),
      metric("Available Copies", formatNumber(toNumber(summary.available_books)), "Book copies ready for borrowing.", BookOpen, "text-emerald-500"),
      metric("Pending Requests", formatNumber(toNumber(summary.pending_requests)), "Borrowing and acquisition requests awaiting action.", ClipboardList, "text-amber-500"),
      metric("Overdue Loans", formatNumber(toNumber(summary.overdue_loans)), "Active loans past due.", AlertCircle, "text-rose-500"),
    ],
    charts: [
      chart("Library Availability", "Assets currently available to students", ["Book Titles", "Book Copies", "Laptops", "Rooms"], [toNumber(summary.book_titles), toNumber(summary.available_books), toNumber(summary.available_laptops), toNumber(summary.available_rooms)], "librarian-assets-gradient", "#0ea5e9", "#38bdf8", "Available Assets", "Largest Asset"),
      chart("Circulation Pressure", "Requests and loan load", ["Pending", "Book Requests", "Borrow Requests", "Active Loans", "Overdue"], [toNumber(summary.pending_requests), toNumber(summary.pending_book_requests), toNumber(summary.pending_borrow_requests), toNumber(summary.active_loans), toNumber(summary.overdue_loans)], "librarian-circulation-gradient", "#10b981", "#34d399", "Circulation Records", "Largest Queue"),
    ],
    insights: [
      insight("Overdue pressure", formatNumber(toNumber(summary.overdue_loans)), "Overdue active loans requiring follow-up.", toNumber(summary.overdue_loans) ? "risk" : "healthy"),
      insight("Request queue", formatNumber(toNumber(summary.pending_requests)), "Student requests awaiting library action.", toNumber(summary.pending_requests) ? "watch" : "healthy"),
    ],
  }
}

async function loadCatererStatistics(settings: UmsPublicSettings): Promise<RoleStatisticsData> {
  const dashboard = await apiFetch<CatererDashboardPayload>("/canteen/dashboard")
  const summary = dashboard.summary ?? {}
  return {
    title: "Caterer Statistics",
    badge: "Current-month canteen allowance",
    summary: "Student allowance allocation, spending, additions, and transaction activity.",
    breadcrumb: roleBreadcrumb("caterer"),
    metrics: [
      metric("Eligible Students", formatNumber(toNumber(summary.eligible_students)), "Students initialized for this allowance month.", Users, "text-sky-500"),
      metric("Allocated", formatMoney(summary.allocated, settings), "Total student canteen allocation.", WalletCards, "text-emerald-500"),
      metric("Spent", formatMoney(summary.spent, settings), "Canteen purchases completed this month.", BriefcaseBusiness, "text-amber-500"),
      metric("Transactions", formatNumber(toNumber(summary.transactions)), "Completed checkout records.", BarChart3, "text-violet-500"),
    ],
    charts: [
      chart("Canteen Money Flow", "Monthly allocation, additions, and spending", ["Allocated", "Additions", "Spent"], [toNumber(summary.allocated), toNumber(summary.manual_additions), toNumber(summary.spent)], "caterer-money-gradient", "#10b981", "#34d399", "Money Flow", "Largest Amount"),
      chart("Canteen Activity", "Students and checkout volume for the current month", ["Students", "Transactions"], [toNumber(summary.eligible_students), toNumber(summary.transactions)], "caterer-activity-gradient", "#f59e0b", "#fbbf24", "Activity Records", "Largest Activity"),
    ],
    insights: [
      insight("Utilization", percentage(toNumber(summary.spent), toNumber(summary.allocated) + toNumber(summary.manual_additions)), "Share of available monthly canteen funds already spent.", "watch"),
      insight("Manual additions", formatMoney(summary.manual_additions, settings), "Admin-added balance in this month.", toNumber(summary.manual_additions) ? "watch" : "healthy"),
    ],
  }
}

async function loadTechnicianStatistics(): Promise<RoleStatisticsData> {
  const dashboard = await apiFetch<TechnicianDashboardPayload>("/ict-helpdesk/technician/dashboard")
  const summary = dashboard.summary ?? {}
  const tickets = dashboard.tickets ?? []
  const categoryRows = topCounts(tickets, (ticket) => ticket.category_label)
  return {
    title: "Technician Statistics",
    badge: "Service desk analytics",
    summary: "Ticket status distribution, category demand, and open support workload.",
    breadcrumb: roleBreadcrumb("technician"),
    metrics: [
      metric("Total Tickets", formatNumber(toNumber(summary.total)), "All service desk tickets.", Wrench, "text-sky-500"),
      metric("Submitted", formatNumber(toNumber(summary.submitted)), "New issues awaiting first action.", ClipboardList, "text-amber-500"),
      metric("In Progress", formatNumber(toNumber(summary.in_progress)), "Tickets actively being handled.", BarChart3, "text-violet-500"),
      metric("Solved", formatNumber(toNumber(summary.solved)), "Tickets completed by the service team.", CheckCircle2, "text-emerald-500"),
    ],
    charts: [
      chart("Ticket Status", "Service desk workload by current status", ["Submitted", "Addressed", "Progress", "Solved"], [toNumber(summary.submitted), toNumber(summary.addressed), toNumber(summary.in_progress), toNumber(summary.solved)], "technician-status-gradient", "#8b5cf6", "#a78bfa", "Tickets", "Largest Status"),
      chart("Ticket Categories", "Most common request categories", categoryRows.map(([label]) => label), categoryRows.map(([, value]) => value), "technician-category-gradient", "#0ea5e9", "#38bdf8", "Category Records", "Largest Category"),
    ],
    insights: [
      insight("Open workload", formatNumber(toNumber(summary.submitted) + toNumber(summary.addressed) + toNumber(summary.in_progress)), "Tickets not marked solved yet.", toNumber(summary.submitted) + toNumber(summary.addressed) + toNumber(summary.in_progress) ? "watch" : "healthy"),
      insight("Resolution share", percentage(toNumber(summary.solved), toNumber(summary.total)), "Share of total tickets completed.", toNumber(summary.total) && toNumber(summary.solved) < toNumber(summary.total) ? "watch" : "healthy"),
    ],
  }
}

async function loadAccountantStatistics(settings: UmsPublicSettings): Promise<RoleStatisticsData> {
  const [dashboardResult, ledgerResult, canteenResult, compensationResult] = await Promise.all([
    optionalLoad("Finance dashboard", () => apiFetch<AccountantDashboardPayload>("/finance/dashboard")),
    optionalLoad("Ledger dashboard", () => apiFetch<AccountantLedgerDashboardPayload>("/finance/ledger/dashboard")),
    optionalLoad("Canteen allowance", () => apiFetch<AccountantCanteenPayload>("/finance/canteen")),
    optionalLoad("HR compensation requests", () => apiFetch<AccountantCompensationPayload>("/finance/hr-compensation-requests")),
  ])
  const dashboard = dashboardResult.data
  const summary = dashboard?.summary ?? {}
  const plans = dashboard?.plans ?? []
  const subscriptions = dashboard?.recent_subscriptions ?? []
  const ledger = ledgerResult.data ?? {}
  const canteen = canteenResult.data?.current ?? {}
  const compensationSummary = compensationResult.data?.summary ?? {}
  const compensationRequests = compensationResult.data?.requests ?? []
  const subscriptionRows = topCounts(subscriptions, (item) => item.status)
  const activePlans = plans.filter((plan) => plan.is_active).length
  const compensationRows = topCounts(compensationRequests, (item) => item.request_type)
  return {
    title: "Accountant Statistics",
    badge: "Finance, canteen, and compensation analytics",
    summary: "Subscription state, ledger balances, canteen allowance money, and HR compensation approval activity.",
    breadcrumb: roleBreadcrumb("accountant"),
    metrics: [
      metric("Outstanding Balance", formatMoney(ledger.total_outstanding, settings), `${formatNumber(toNumber(ledger.students_with_balance))} students with balance.`, WalletCards, "text-amber-500"),
      metric("Ledger Entries", formatNumber(toNumber(ledger.total_entries ?? summary.ledger_entries)), "Finance debit, credit, waiver, and reversal entries.", ClipboardList, "text-sky-500"),
      metric("Canteen Allocated", formatMoney(canteen.allocated, settings), `${formatNumber(toNumber(canteen.eligible_students))} eligible students this month.`, Users, "text-emerald-500"),
      metric("Pending HR Requests", formatNumber(toNumber(compensationSummary.pending)), "Salary and bonus changes waiting for Accountant approval.", BriefcaseBusiness, "text-violet-500"),
    ],
    charts: [
      chart("Ledger Money Flow", "Outstanding, charges, and payments", ["Outstanding", "Charges", "Payments"], [toNumber(ledger.total_outstanding), toNumber(ledger.total_charges_amount), toNumber(ledger.total_payments)], "accountant-ledger-gradient", "#0ea5e9", "#38bdf8", "Finance Amount", "Largest Amount"),
      chart("Canteen Money Flow", "Monthly allocation, additions, and spending", ["Allocated", "Additions", "Spent"], [toNumber(canteen.allocated), toNumber(canteen.manual_additions), toNumber(canteen.spent)], "accountant-canteen-gradient", "#10b981", "#34d399", "Canteen Amount", "Largest Amount"),
      chart("HR Compensation Requests", "Salary and bonus approval status", ["Pending", "Approved", "Rejected"], [toNumber(compensationSummary.pending), toNumber(compensationSummary.approved), toNumber(compensationSummary.rejected)], "accountant-compensation-gradient", "#8b5cf6", "#a78bfa", "Requests", "Largest Status"),
      chart("Subscription Summary", "Current subscription and payment status", ["Active", "Pending", "Expired", "Paid"], [toNumber(summary.active), toNumber(summary.pending), toNumber(summary.expired), toNumber(summary.successful_payments)], "accountant-summary-gradient", "#f59e0b", "#fbbf24", "Finance Records", "Largest Status"),
      chart("Recent Subscription Status", "Latest subscription records by status", subscriptionRows.map(([label]) => labelFor(label)), subscriptionRows.map(([, value]) => value), "accountant-subscription-gradient", "#14b8a6", "#5eead4", "Recent Records", "Largest Status"),
      chart("Compensation Types", "HR requests by compensation type", compensationRows.map(([label]) => labelFor(label)), compensationRows.map(([, value]) => value), "accountant-compensation-type-gradient", "#ef4444", "#fb7185", "Requests", "Largest Type"),
    ],
    insights: [
      insight("Pending collection", formatNumber(toNumber(summary.pending)), "Subscription payments still waiting for gateway confirmation.", toNumber(summary.pending) ? "watch" : "healthy"),
      insight("Overdue charges", formatNumber(toNumber(ledger.overdue_charges)), "Posted student charges past due date.", toNumber(ledger.overdue_charges) ? "risk" : "healthy"),
      insight("Canteen utilization", percentage(toNumber(canteen.spent), toNumber(canteen.allocated) + toNumber(canteen.manual_additions)), "Share of available monthly canteen money already spent.", "watch"),
      insight("Compensation queue", formatNumber(toNumber(compensationSummary.pending)), "Salary and bonus changes that still need Accountant action.", toNumber(compensationSummary.pending) ? "watch" : "healthy"),
      insight("Plan readiness", percentage(activePlans, plans.length), "Share of subscription plans currently active.", activePlans === plans.length ? "healthy" : "watch"),
    ],
    warnings: warningsFrom([dashboardResult, ledgerResult, canteenResult, compensationResult]),
  }
}

async function loadRoleStatistics(role: StatisticsRole) {
  const settings = await loadPublicUmsSettings()
  if (role === "applicant") return loadApplicantStatistics()
  if (role === "student") return loadStudentStatistics(settings)
  if (role === "teacher") return loadTeacherStatistics()
  if (role === "librarian") return loadLibrarianStatistics()
  if (role === "caterer") return loadCatererStatistics(settings)
  if (role === "technician") return loadTechnicianStatistics()
  return loadAccountantStatistics(settings)
}

function levelBadgeClass(level: InsightDefinition["level"]) {
  if (level === "healthy") {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
  }
  if (level === "watch") {
    return "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300"
  }
  return "border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300"
}

function levelLabel(level: InsightDefinition["level"]) {
  if (level === "healthy") return "Healthy"
  if (level === "watch") return "Watch"
  return "Risk"
}

function MetricCard({ metric: item }: { metric: MetricDefinition }) {
  const Icon = item.icon
  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between gap-3 pb-2">
        <CardDescription className="text-sm font-medium">{item.title}</CardDescription>
        <span className={`rounded-lg border border-border bg-muted/50 p-2 ${item.tone}`}>
          <Icon className="size-4" />
        </span>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-2xl font-bold tracking-tight">{item.value}</p>
        <p className="text-xs leading-5 text-muted-foreground">{item.detail}</p>
      </CardContent>
    </Card>
  )
}

function defaultStatisticsErrorMessage(caught: unknown) {
  return caught instanceof Error ? caught.message : "Unable to load statistics."
}

export function StatisticsDataPage<TData>({
  breadcrumbItems,
  loadData,
  renderContent,
  getErrorMessage = defaultStatisticsErrorMessage,
  errorFallback = "The statistics payload was not available.",
}: StatisticsDataPageProps<TData>) {
  const [data, setData] = useState<TData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState("")

  const refresh = useCallback(
    async (silent = false) => {
      if (silent) setIsRefreshing(true)
      else setIsLoading(true)
      setError("")
      try {
        setData(await loadData())
      } catch (caught) {
        setError(getErrorMessage(caught))
      } finally {
        setIsLoading(false)
        setIsRefreshing(false)
      }
    },
    [getErrorMessage, loadData]
  )

  useEffect(() => {
    const timer = window.setTimeout(() => void refresh(), 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  if (isLoading) {
    return (
      <div className="flex min-h-svh flex-col bg-muted/25">
        <Header breadcrumbItems={breadcrumbItems} />
        <main className="flex-1">
          <LoadingScreen
            label="Loading Statistics..."
            className="min-h-[calc(100svh-4rem)]"
          />
        </main>
      </div>
    )
  }

  if (error || data === null) {
    return (
      <div className="flex min-h-svh flex-col bg-muted/25">
        <Header breadcrumbItems={breadcrumbItems} />
        <main className="flex-1 px-4 pb-8 pt-4 sm:px-6">
          <Card className="border-red-200 bg-red-50/60 shadow-sm dark:border-red-900/50 dark:bg-red-950/10">
            <CardHeader className="flex flex-row items-start gap-3 pb-3">
              <AlertCircle className="size-5 text-red-600 dark:text-red-400" />
              <div className="space-y-1">
                <CardTitle className="text-base text-red-950 dark:text-red-200">
                  Failed to Load Statistics
                </CardTitle>
                <CardDescription className="text-sm text-red-800 dark:text-red-300">
                  {error || errorFallback}
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <Button onClick={() => void refresh()} variant="outline">
                Try Again
              </Button>
            </CardContent>
          </Card>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={breadcrumbItems} />
      {renderContent({ data, isRefreshing, refresh })}
    </div>
  )
}

export function RoleStatisticsPage({ role }: { role: StatisticsRole }) {
  const isDark = useIsDarkMode()
  const loadStats = useCallback(() => loadRoleStatistics(role), [role])

  return (
    <StatisticsDataPage
      breadcrumbItems={roleBreadcrumb(role)}
      loadData={loadStats}
      renderContent={({ data: content, isRefreshing, refresh }) => (
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <Badge variant="outline" className="w-fit bg-background">
              {content.badge}
            </Badge>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {content.title}
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                {content.summary}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            disabled={isRefreshing}
            onClick={() => void refresh(true)}
            className="gap-2"
          >
            <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </section>

        {content.warnings?.length ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-200">
            <p className="font-medium">Some source data did not load.</p>
            <ul className="mt-2 space-y-1">
              {content.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {content.metrics.map((item) => (
            <MetricCard key={item.title} metric={item} />
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          {content.charts.map((item) => (
            <ValueBarChart
              key={item.gradientId}
              title={item.title}
              subtitle={item.subtitle}
              labels={item.labels}
              values={item.values}
              isDark={isDark}
              formatter={(value) => formatNumber(value)}
              gradientId={item.gradientId}
              startColor={item.startColor}
              endColor={item.endColor}
              totalLabel={item.totalLabel}
              peakLabel={item.peakLabel}
            />
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {content.insights.map((item) => (
            <Card key={item.title} className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="space-y-2 pb-2">
                <div className="flex items-center justify-between gap-3">
                  <CardDescription className="text-sm font-medium">{item.title}</CardDescription>
                  <Badge variant="outline" className={levelBadgeClass(item.level)}>
                    {levelLabel(item.level)}
                  </Badge>
                </div>
                <CardTitle className="text-2xl">{item.value}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-muted-foreground">{item.detail}</p>
              </CardContent>
            </Card>
          ))}
        </section>
      </main>
      )}
    />
  )
}
