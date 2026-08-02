"use client"

import Link from "next/link"
import type { LucideIcon } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  Clock,
  GraduationCap,
  Loader2,
  MinusCircle,
  Plus,
  RefreshCw,
  Search,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import { statusClassName } from "@/lib/status-utils"

type CoursesView = "register" | "current" | "completed"
type CoursesNavigation = "courses" | "registration"

type SemesterSummary = {
  id: number | string
  name: string
  academic_session?: string
  semester_type?: string
  max_credit_hours?: number
}

type RegistrationPhase = {
  id: number
  title: string
  phase: string
  opens_at: string
  closes_at: string
}

type LabGroup = {
  id: number
  code: string
  capacity: number
  used: number
  remaining: number
}

type TutorialGroup = {
  id: number
  code: string
  capacity: number
  used: number
  remaining: number
  lab_groups: LabGroup[]
}

type RegistrationOffering = {
  id: number
  course: {
    id: number
    code: string
    title: string
    credits: number
    has_lab: boolean
    prerequisites?: Array<{ id: number; code: string; title: string }>
  }
  semester: SemesterSummary
  section: string
  capacity: number
  used: number
  remaining: number
  groups: TutorialGroup[]
}

type RegistrationRecord = {
  id: number
  offering: number
  status: string
  is_manual?: boolean
  created_at: string
  offering_detail?: {
    id: number
    section: string
    course_detail?: {
      code: string
      title: string
      credits: number
      has_lab: boolean
    }
    semester_detail?: SemesterSummary
  }
  tutorial_group_detail?: { id: number; code: string } | null
  lab_group_detail?: { id: number; code: string } | null
}

type RegistrationResponse = {
  title: string
  semester: SemesterSummary | null
  current_phase: RegistrationPhase | null
  can_add: boolean
  can_drop: boolean
  evaluation_gate?: {
    blocked: boolean
    pending_count: number
    message: string
    surveys: Array<{
      id: number
      title: string
      course_code: string
      course_title: string
      semester: string
      state: string
      url: string
    }>
  }
  credit_hours?: {
    registered: number
    maximum: number
  }
  offerings: RegistrationOffering[]
  registrations: RegistrationRecord[]
}

type CurrentCourse = {
  id: number
  offering_id: number
  course: {
    id: number
    code: string
    title: string
    credits: number
    has_lab: boolean
  }
  semester: SemesterSummary
  section: string
  instructor: string
  tutorial_group: string
  lab_group: string
  enrolled_at: string | null
  attendance_percentage: number
  attendance_summary: {
    attended: number
    total_classes: number
    attendance_percentage: number
  }
}

type CurrentCoursesResponse = {
  title: string
  semester: SemesterSummary | null
  summary: {
    course_count: number
    registered_credit_hours: number
    max_credit_hours: number
  }
  courses: CurrentCourse[]
}

type CompletedCourse = {
  id: string
  source: "transcript" | "enrollment"
  offering_id: number | null
  course_code: string
  course_title: string
  credit_hours: string
  semester: SemesterSummary
  score: string
  grade: string
  grade_points: string
  gpa: string
  cgpa: string
  completed_at: string | null
  status: string
}

type CompletedCoursesResponse = {
  title: string
  summary: {
    course_count: number
    completed_credit_hours: number
  }
  courses: CompletedCourse[]
}

type GroupSelection = {
  tutorialGroupId: string
  labGroupId: string
}

function endpointForView(view: CoursesView) {
  if (view === "register") return "/student/courses/register"
  if (view === "current") return "/student/courses/current"
  return "/student/courses/completed"
}

function titleForView(
  view: CoursesView,
  navigation: CoursesNavigation = "courses"
) {
  if (navigation === "registration" && view === "register")
    return "Offered Courses"
  if (view === "register") return "Course Registration"
  if (view === "current") return "Current Courses"
  return "Completed Courses"
}

function descriptionForView(
  view: CoursesView,
  navigation: CoursesNavigation = "courses"
) {
  if (navigation === "registration" && view === "register") {
    return "Browse eligible course offerings, choose groups, and manage registration changes while the period is open."
  }
  if (view === "register") {
    return "Register for eligible courses, choose tutorial and lab groups, and manage drops during the open period."
  }
  if (view === "current") {
    return "Track active enrollments, teaching groups, credit load, and attendance progress for the running semester."
  }
  return "Review courses completed in previous semesters, including published grades where available."
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "Not set"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Not set"
  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "0"
  const parsed = Number(value)
  if (Number.isNaN(parsed)) return String(value)
  return Number.isInteger(parsed) ? String(parsed) : parsed.toFixed(2)
}

function statusLabel(status: string) {
  return status
    .replace(/[-_]/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

function groupLabel(tutorial?: string, lab?: string) {
  if (tutorial && lab) return `${tutorial} / ${lab}`
  if (tutorial) return tutorial
  if (lab) return lab
  return "Unassigned"
}

function firstAvailableTutorial(offering: RegistrationOffering) {
  return (
    offering.groups.find((group) => group.remaining > 0) ?? offering.groups[0]
  )
}

function firstAvailableLab(tutorial: TutorialGroup | undefined) {
  return (
    tutorial?.lab_groups.find((group) => group.remaining > 0) ??
    tutorial?.lab_groups[0]
  )
}

function SelectBox({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: Array<{ value: string; label: string; disabled?: boolean }>
  disabled?: boolean
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm transition-colors outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

function SummaryTile({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string
  value: string
  subtitle: string
  icon: LucideIcon
}) {
  return (
    <Card className="border-border/70 shadow-sm">
      <CardContent className="flex items-center justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-1 truncate text-2xl font-semibold">{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <Icon className="size-5 shrink-0 text-muted-foreground" />
      </CardContent>
    </Card>
  )
}

function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-background p-8 text-center">
      <BookOpen className="mx-auto size-8 text-muted-foreground" />
      <p className="mt-3 font-medium">{title}</p>
      <p className="mx-auto mt-1 max-w-md text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </div>
  )
}

export function StudentCoursesPage({
  view,
  navigation = "courses",
}: {
  view: CoursesView
  navigation?: CoursesNavigation
}) {
  const [registrationData, setRegistrationData] =
    useState<RegistrationResponse | null>(null)
  const [currentData, setCurrentData] = useState<CurrentCoursesResponse | null>(
    null
  )
  const [completedData, setCompletedData] =
    useState<CompletedCoursesResponse | null>(null)
  const [query, setQuery] = useState("")
  const [groupSelections, setGroupSelections] = useState<
    Record<number, GroupSelection>
  >({})
  const [busyAction, setBusyAction] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const endpoint = endpointForView(view)
    if (view === "register") {
      const data = await apiFetch<RegistrationResponse>(endpoint)
      setRegistrationData(data)
      setCurrentData(null)
      setCompletedData(null)
      return
    }
    if (view === "current") {
      const data = await apiFetch<CurrentCoursesResponse>(endpoint)
      setCurrentData(data)
      setRegistrationData(null)
      setCompletedData(null)
      return
    }
    const data = await apiFetch<CompletedCoursesResponse>(endpoint)
    setCompletedData(data)
    setRegistrationData(null)
    setCurrentData(null)
  }, [view])

  useEffect(() => {
    let active = true

    async function hydrate() {
      try {
        await loadData()
      } catch (caught) {
        if (!active) return
        setError(
          caught instanceof Error ? caught.message : "Unable to load courses."
        )
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void hydrate()

    return () => {
      active = false
    }
  }, [loadData])

  async function refreshData() {
    setIsLoading(true)
    setError("")
    setSuccess("")
    try {
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load courses."
      )
    } finally {
      setIsLoading(false)
    }
  }

  const activeRegistrations = useMemo(() => {
    const records = registrationData?.registrations ?? []
    return new Map(
      records
        .filter((record) => ["approved", "pending"].includes(record.status))
        .map((record) => [record.offering, record])
    )
  }, [registrationData?.registrations])

  const filteredOfferings = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    const offerings = registrationData?.offerings ?? []
    if (!normalized) return offerings
    return offerings.filter((offering) =>
      [
        offering.course.code,
        offering.course.title,
        offering.section,
        offering.semester.name,
        offering.course.prerequisites?.map((item) => item.code).join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [query, registrationData?.offerings])

  const filteredCurrentCourses = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    const courses = currentData?.courses ?? []
    if (!normalized) return courses
    return courses.filter((course) =>
      [
        course.course.code,
        course.course.title,
        course.section,
        course.instructor,
        course.semester.name,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [currentData?.courses, query])

  const filteredCompletedCourses = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    const courses = completedData?.courses ?? []
    if (!normalized) return courses
    return courses.filter((course) =>
      [
        course.course_code,
        course.course_title,
        course.semester.name,
        course.grade,
        course.status,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [completedData?.courses, query])

  function selectionFor(offering: RegistrationOffering): GroupSelection {
    const existing = groupSelections[offering.id]
    const firstTutorial = firstAvailableTutorial(offering)
    const tutorialGroupId =
      existing?.tutorialGroupId ||
      (firstTutorial ? String(firstTutorial.id) : "")
    const tutorial =
      offering.groups.find((group) => String(group.id) === tutorialGroupId) ??
      firstTutorial
    const firstLab = firstAvailableLab(tutorial)
    const labGroupId =
      existing?.labGroupId || (firstLab ? String(firstLab.id) : "")
    return { tutorialGroupId, labGroupId }
  }

  function setTutorialGroup(
    offering: RegistrationOffering,
    tutorialGroupId: string
  ) {
    const tutorial = offering.groups.find(
      (group) => String(group.id) === tutorialGroupId
    )
    const labGroup = firstAvailableLab(tutorial)
    setGroupSelections((current) => ({
      ...current,
      [offering.id]: {
        tutorialGroupId,
        labGroupId: labGroup ? String(labGroup.id) : "",
      },
    }))
  }

  function setLabGroup(offeringId: number, labGroupId: string) {
    setGroupSelections((current) => ({
      ...current,
      [offeringId]: {
        tutorialGroupId: current[offeringId]?.tutorialGroupId ?? "",
        labGroupId,
      },
    }))
  }

  async function mutateRegistration(
    action: "register" | "drop",
    offering: RegistrationOffering
  ) {
    setError("")
    setSuccess("")
    setBusyAction(`${action}-${offering.id}`)

    const selection = selectionFor(offering)

    try {
      const payload =
        action === "drop"
          ? {
              action,
              offering_id: offering.id,
            }
          : {
              action,
              offering_id: offering.id,
              tutorial_group_id: selection.tutorialGroupId
                ? Number(selection.tutorialGroupId)
                : null,
              lab_group_id: selection.labGroupId
                ? Number(selection.labGroupId)
                : null,
            }
      const response = await apiFetch<{ message: string }>(
        "/student/courses/register",
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      )
      setSuccess(response.message)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to update registration."
      )
    } finally {
      setBusyAction("")
    }
  }

  const pageTitle = titleForView(view, navigation)
  const pageDescription = descriptionForView(view, navigation)
  const parentCrumb =
    navigation === "registration"
      ? { href: "/student/registration", title: "Registration" }
      : { href: "/student/courses", title: "Courses" }
  const currentHref =
    navigation === "registration" && view === "register"
      ? "/student/registration/offered-courses"
      : `/student/courses/${view}`

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          parentCrumb,
          { href: currentHref, title: pageTitle },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold sm:text-3xl">{pageTitle}</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {pageDescription}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => void refreshData()}
            disabled={isLoading}
          >
            <RefreshCw
              className={isLoading ? "size-4 animate-spin" : "size-4"}
            />
            Refresh
          </Button>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{success}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : view === "register" && registrationData ? (
          <RegistrationView
            data={registrationData}
            query={query}
            setQuery={setQuery}
            offerings={filteredOfferings}
            activeRegistrations={activeRegistrations}
            selectionFor={selectionFor}
            setTutorialGroup={setTutorialGroup}
            setLabGroup={setLabGroup}
            mutateRegistration={mutateRegistration}
            busyAction={busyAction}
          />
        ) : view === "current" && currentData ? (
          <CurrentCoursesView
            data={currentData}
            query={query}
            setQuery={setQuery}
            courses={filteredCurrentCourses}
          />
        ) : view === "completed" && completedData ? (
          <CompletedCoursesView
            data={completedData}
            query={query}
            setQuery={setQuery}
            courses={filteredCompletedCourses}
          />
        ) : null}
      </main>
    </div>
  )
}

function RegistrationView({
  data,
  query,
  setQuery,
  offerings,
  activeRegistrations,
  selectionFor,
  setTutorialGroup,
  setLabGroup,
  mutateRegistration,
  busyAction,
}: {
  data: RegistrationResponse
  query: string
  setQuery: (value: string) => void
  offerings: RegistrationOffering[]
  activeRegistrations: Map<number, RegistrationRecord>
  selectionFor: (offering: RegistrationOffering) => GroupSelection
  setTutorialGroup: (
    offering: RegistrationOffering,
    tutorialGroupId: string
  ) => void
  setLabGroup: (offeringId: number, labGroupId: string) => void
  mutateRegistration: (
    action: "register" | "drop",
    offering: RegistrationOffering
  ) => Promise<void>
  busyAction: string
}) {
  const registeredCredits = data.credit_hours?.registered ?? 0
  const maxCredits =
    data.credit_hours?.maximum ?? data.semester?.max_credit_hours ?? 0

  return (
    <div className="space-y-6">
      {data.evaluation_gate?.blocked ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
          <div className="flex gap-3">
            <AlertCircle className="mt-0.5 size-5 shrink-0" />
            <div className="min-w-0">
              <p className="font-semibold">Course registration is on hold</p>
              <p className="mt-1 text-sm leading-6">
                {data.evaluation_gate.message}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {data.evaluation_gate.surveys.map((survey) => (
                  <Button
                    key={survey.id}
                    size="sm"
                    variant="outline"
                    render={<Link href={survey.url} />}
                  >
                    Complete {survey.course_code}
                    <ArrowRight className="size-4" />
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
      <section className="grid gap-3 md:grid-cols-3">
        <SummaryTile
          title="Semester"
          value={data.semester?.name ?? "No active semester"}
          subtitle={
            data.semester?.academic_session ||
            "Registration depends on admin setup."
          }
          icon={CalendarDays}
        />
        <SummaryTile
          title="Registration Phase"
          value={data.current_phase?.title ?? "Closed"}
          subtitle={
            data.current_phase
              ? `${formatDateTime(data.current_phase.opens_at)} - ${formatDateTime(data.current_phase.closes_at)}`
              : "No open phase right now."
          }
          icon={Clock}
        />
        <SummaryTile
          title="Credit Load"
          value={`${registeredCredits}/${maxCredits}`}
          subtitle="Registered credit hours against the semester limit."
          icon={BookOpen}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_25rem]">
        <Card className="border-border/70 shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>Eligible Offered Courses</CardTitle>
                <CardDescription>
                  {data.can_add
                    ? "Select a group and register."
                    : "Adding courses is not open in the current phase."}
                </CardDescription>
              </div>
              <div className="relative md:w-72">
                <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  className="pl-9"
                  placeholder="Search course code or title"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {offerings.map((offering) => {
              const registration = activeRegistrations.get(offering.id)
              const selection = selectionFor(offering)
              const selectedTutorial = offering.groups.find(
                (group) => String(group.id) === selection.tutorialGroupId
              )
              const selectedLab = selectedTutorial?.lab_groups.find(
                (group) => String(group.id) === selection.labGroupId
              )
              const isBusy = busyAction.endsWith(`-${offering.id}`)
              const isFull =
                offering.groups.length === 0
                  ? offering.remaining <= 0
                  : selectedTutorial?.remaining === 0
              const labUnavailable =
                offering.course.has_lab && selectedTutorial?.lab_groups.length
                  ? selectedLab?.remaining === 0
                  : false

              return (
                <div
                  key={offering.id}
                  className="rounded-lg border border-border bg-background p-4"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold">{offering.course.code}</p>
                        <Badge variant="outline">
                          {offering.section || "Main"}
                        </Badge>
                        <Badge variant="secondary">
                          {offering.course.credits} credits
                        </Badge>
                        {offering.course.has_lab ? (
                          <Badge variant="outline">Lab</Badge>
                        ) : null}
                        {registration ? (
                          <span
                            className={`rounded-full border px-2 py-0.5 text-xs font-medium ${statusClassName(registration.status)}`}
                          >
                            {statusLabel(registration.status)}
                          </span>
                        ) : null}
                      </div>
                      <div>
                        <p className="text-sm font-medium">
                          {offering.course.title}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {offering.semester.name} / {offering.used} enrolled /{" "}
                          {offering.remaining} remaining
                        </p>
                      </div>
                      {offering.course.prerequisites?.length ? (
                        <p className="text-xs text-muted-foreground">
                          Prerequisites:{" "}
                          {offering.course.prerequisites
                            .map((item) => item.code)
                            .join(", ")}
                        </p>
                      ) : null}
                    </div>

                    <div className="grid min-w-0 gap-3 sm:grid-cols-2 lg:w-80">
                      {offering.groups.length ? (
                        <SelectBox
                          label="Tutorial"
                          value={selection.tutorialGroupId}
                          disabled={!!registration || !data.can_add}
                          onChange={(value) =>
                            setTutorialGroup(offering, value)
                          }
                          options={offering.groups.map((group) => ({
                            value: String(group.id),
                            label: `${group.code} (${group.remaining}/${group.capacity})`,
                            disabled: group.remaining <= 0,
                          }))}
                        />
                      ) : null}
                      {offering.course.has_lab &&
                      selectedTutorial?.lab_groups.length ? (
                        <SelectBox
                          label="Lab"
                          value={selection.labGroupId}
                          disabled={!!registration || !data.can_add}
                          onChange={(value) => setLabGroup(offering.id, value)}
                          options={selectedTutorial.lab_groups.map((group) => ({
                            value: String(group.id),
                            label: `${group.code} (${group.remaining}/${group.capacity})`,
                            disabled: group.remaining <= 0,
                          }))}
                        />
                      ) : null}
                      <div className="flex items-end gap-2 sm:col-span-2">
                        {registration ? (
                          <Button
                            variant="outline"
                            className="w-full"
                            disabled={!data.can_drop || isBusy}
                            onClick={() =>
                              void mutateRegistration("drop", offering)
                            }
                          >
                            {isBusy ? (
                              <Loader2 className="size-4 animate-spin" />
                            ) : (
                              <MinusCircle className="size-4" />
                            )}
                            Drop
                          </Button>
                        ) : (
                          <Button
                            className="w-full"
                            disabled={
                              !data.can_add ||
                              isBusy ||
                              isFull ||
                              labUnavailable
                            }
                            onClick={() =>
                              void mutateRegistration("register", offering)
                            }
                          >
                            {isBusy ? (
                              <Loader2 className="size-4 animate-spin" />
                            ) : (
                              <Plus className="size-4" />
                            )}
                            Register
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
            {offerings.length === 0 ? (
              <EmptyState
                title="No eligible courses found"
                description="Try a different search, or check again when the registration phase opens."
              />
            ) : null}
          </CardContent>
        </Card>

        <Card className="h-fit border-border/70 shadow-sm">
          <CardHeader>
            <CardTitle>My Registration</CardTitle>
            <CardDescription>
              Submitted and approved course registration records.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.registrations.map((record) => (
              <div
                key={record.id}
                className="rounded-lg border border-border bg-background p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {record.offering_detail?.course_detail?.code ?? "Course"}{" "}
                      / {record.offering_detail?.section ?? "Section"}
                    </p>
                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                      {record.offering_detail?.course_detail?.title ??
                        "Registered course"}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full border px-2 py-0.5 text-xs font-medium ${statusClassName(record.status)}`}
                  >
                    {statusLabel(record.status)}
                  </span>
                </div>
                <div className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                  <p>
                    <span className="block font-medium text-foreground">
                      Group
                    </span>
                    {groupLabel(
                      record.tutorial_group_detail?.code,
                      record.lab_group_detail?.code
                    )}
                  </p>
                  <p>
                    <span className="block font-medium text-foreground">
                      Credits
                    </span>
                    {record.offering_detail?.course_detail?.credits ?? 0}
                  </p>
                </div>
              </div>
            ))}
            {data.registrations.length === 0 ? (
              <EmptyState
                title="No registrations yet"
                description="Registered courses will appear here."
              />
            ) : null}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

function CurrentCoursesView({
  data,
  query,
  setQuery,
  courses,
}: {
  data: CurrentCoursesResponse
  query: string
  setQuery: (value: string) => void
  courses: CurrentCourse[]
}) {
  return (
    <div className="space-y-6">
      <section className="grid gap-3 md:grid-cols-3">
        <SummaryTile
          title="Active Courses"
          value={String(data.summary.course_count)}
          subtitle={data.semester?.name ?? "No active semester"}
          icon={BookOpen}
        />
        <SummaryTile
          title="Credit Hours"
          value={`${data.summary.registered_credit_hours}/${data.summary.max_credit_hours}`}
          subtitle="Current registered credit load."
          icon={GraduationCap}
        />
        <SummaryTile
          title="Semester"
          value={data.semester?.academic_session || "Not set"}
          subtitle={data.semester?.name ?? "Current enrollment view"}
          icon={CalendarDays}
        />
      </section>

      <Card className="border-border/70 shadow-sm">
        <CardHeader>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Enrolled Courses</CardTitle>
              <CardDescription>
                Active courses for the selected semester.
              </CardDescription>
            </div>
            <div className="relative md:w-72">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="pl-9"
                placeholder="Search current courses"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 xl:grid-cols-2">
          {courses.map((course) => (
            <div
              key={course.id}
              className="rounded-lg border border-border bg-background p-4"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold">{course.course.code}</p>
                    <Badge variant="outline">{course.section || "Main"}</Badge>
                    <Badge variant="secondary">
                      {course.course.credits} credits
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm font-medium">
                    {course.course.title}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {course.instructor || "Instructor pending"} /{" "}
                    {groupLabel(course.tutorial_group, course.lab_group)}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  render={
                    <Link href={`/student/courses/${course.offering_id}`} />
                  }
                >
                  Open
                  <ArrowRight className="size-4" />
                </Button>
              </div>
              <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                <div>
                  <p className="text-muted-foreground">Attendance</p>
                  <p className="mt-1 font-semibold">
                    {formatNumber(course.attendance_percentage)}%
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Classes</p>
                  <p className="mt-1 font-semibold">
                    {course.attendance_summary.attended}/
                    {course.attendance_summary.total_classes}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Enrolled</p>
                  <p className="mt-1 font-semibold">
                    {formatDateTime(course.enrolled_at)}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {courses.length === 0 ? (
            <div className="xl:col-span-2">
              <EmptyState
                title="No current courses"
                description="Approved enrollments for the running semester will appear here."
              />
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}

function CompletedCoursesView({
  data,
  query,
  setQuery,
  courses,
}: {
  data: CompletedCoursesResponse
  query: string
  setQuery: (value: string) => void
  courses: CompletedCourse[]
}) {
  return (
    <div className="space-y-6">
      <section className="grid gap-3 md:grid-cols-2">
        <SummaryTile
          title="Completed Courses"
          value={String(data.summary.course_count)}
          subtitle="Courses marked completed or published in transcript records."
          icon={CheckCircle2}
        />
        <SummaryTile
          title="Completed Credits"
          value={formatNumber(data.summary.completed_credit_hours)}
          subtitle="Credit hours from completed course records."
          icon={GraduationCap}
        />
      </section>

      <Card className="border-border/70 shadow-sm">
        <CardHeader>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Course History</CardTitle>
              <CardDescription>
                Completed courses by semester and publication status.
              </CardDescription>
            </div>
            <div className="relative md:w-72">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="pl-9"
                placeholder="Search completed courses"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {courses.map((course) => (
            <div
              key={course.id}
              className="rounded-lg border border-border bg-background p-4"
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold">{course.course_code}</p>
                    <Badge variant="secondary">
                      {formatNumber(course.credit_hours)} credits
                    </Badge>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-xs font-medium ${statusClassName(course.status)}`}
                    >
                      {course.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm font-medium">
                    {course.course_title}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {course.semester.name} /{" "}
                    {course.semester.academic_session ||
                      "Academic session not set"}
                  </p>
                </div>
                <div className="grid gap-3 text-sm sm:grid-cols-4 lg:w-[28rem]">
                  <div>
                    <p className="text-muted-foreground">Score</p>
                    <p className="mt-1 font-semibold">
                      {course.score || "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Grade</p>
                    <p className="mt-1 font-semibold">
                      {course.grade || "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Points</p>
                    <p className="mt-1 font-semibold">
                      {course.grade_points || "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Completed</p>
                    <p className="mt-1 font-semibold">
                      {formatDateTime(course.completed_at)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {courses.length === 0 ? (
            <EmptyState
              title="No completed courses"
              description="Completed enrollments and published transcript courses will appear here."
            />
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
