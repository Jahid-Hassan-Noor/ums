"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  CircleDollarSign,
  FileText,
  Gift,
  History,
  Loader2,
  RefreshCw,
  Save,
  Search,
  TrendingDown,
  TrendingUp,
  UserCog,
  Users,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { HrDashboard } from "@/components/role-zone/role-dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import LoadingScreen from "@/components/ui/loading-screen"
import { Textarea } from "@/components/ui/textarea"
import { formatCurrency, formatDateOnly } from "@/components/utils/format"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch } from "@/lib/auth"
import { zoneForUmsRole } from "@/lib/ums-settings"
import { parseUmsRole } from "@/lib/ums-roles"

type View = "dashboard" | "statistics" | "employees" | "positions" | "my-profile"

type Position = {
  id: number
  code: string
  title: string
  employment_type: string
  employment_type_label: string
  grade: string
  department: string
  unit: string
  is_active: boolean
}

type Employee = {
  id: number
  profile_id: number
  employee_no: string
  name: string
  email: string
  role: string
  identifier: string
  employment_status: string
  employment_status_label: string
  joining_date: string | null
  work_email: string
  salary_currency: string
  base_salary: string
  current_salary: string
  current_bonus: string
  vacation_days_total: number
  vacation_days_used: number
  vacation_days_remaining: number
  leave_days_total: number
  leave_days_used: number
  leave_days_remaining: number
  position: Position | null
  reporting_manager: { id: number; name: string; employee_no: string } | null
  notes: string
  updated_at: string
}

type EmploymentRecord = {
  id: number
  status: string
  status_label: string
  position: Position | null
  start_date: string | null
  end_date: string | null
  notes: string
  recorded_by: string
  created_at: string
}

type SalaryAdjustment = {
  id: number
  employee_id: number
  employee_name: string
  employee_no: string
  change_type: "increase" | "decrease"
  change_type_label: string
  amount: string
  previous_salary: string
  new_salary: string
  effective_date: string | null
  reason: string
  recorded_by: string
  created_at: string
}

type CompensationRequest = {
  id: number
  employee: {
    id: number
    name: string
    employee_no: string
    role: string
    position: string
    currency: string
  }
  request_type: "salary" | "bonus"
  request_type_label: string
  change_type: "increase" | "decrease" | "set"
  change_type_label: string
  amount: string
  previous_amount: string
  requested_amount: string
  effective_date: string | null
  reason: string
  status: "pending" | "approved" | "rejected"
  status_label: string
  requested_by: { name: string } | null
  reviewed_by: { name: string } | null
  reviewed_at: string | null
  review_note: string
  created_at: string
}

type EmployeeDocument = {
  id: number
  document_type: string
  document_type_label: string
  title: string
  expires_on: string | null
  uploaded_by: string
  uploaded_at: string
}

type EmployeeDetail = Employee & {
  employment_records: EmploymentRecord[]
  salary_adjustments: SalaryAdjustment[]
  compensation_requests: CompensationRequest[]
  documents: EmployeeDocument[]
  direct_reports: { id: number; name: string; employee_no: string; position: string }[]
}

type ProfileOption = {
  id: number
  name: string
  email: string
  role: string
  identifier: string
  has_employee_record: boolean
}

type DashboardResponse = {
  summary: {
    employees: number
    active: number
    probation: number
    suspended: number
    positions: number
    employees_without_position: number
    documents_expiring_soon: number
    monthly_payroll: string
    average_salary: string
    total_bonus: string
    average_bonus: string
    pending_compensation_requests: number
    vacation_days_available: number
  }
  statistics: {
    status_counts: ChartRow[]
    role_counts: { role: string; count: number }[]
    position_counts: { title: string; code: string; count: number }[]
    recent_records: EmploymentRecord[]
    recent_salary_adjustments: SalaryAdjustment[]
    recent_compensation_requests: CompensationRequest[]
  }
  employees: Employee[]
  positions: Position[]
}

type ChartRow = {
  label: string
  count: number
  status?: string
  role?: string
  title?: string
  code?: string
}

type HrStatisticsResponse = {
  summary: DashboardResponse["summary"] & {
    vacation_days_total: number
    vacation_days_used: number
    vacation_days_remaining: number
    leave_placeholder: boolean
  }
  charts: {
    status_counts: ChartRow[]
    role_counts: { role: string; count: number }[]
    position_counts: { title: string; code: string; count: number }[]
    salary_bands: ChartRow[]
    bonus_bands: ChartRow[]
    compensation_request_status: ChartRow[]
    compensation_request_types: Array<{ type: string; label: string; count: number }>
    leave_placeholder: ChartRow[]
  }
  recent_compensation_requests: CompensationRequest[]
}

const emptyPosition = {
  code: "",
  title: "",
  employment_type: "full_time",
  grade: "",
}

const emptyEmployee = {
  profile_id: "",
  employee_no: "",
  employment_status: "active",
  position_id: "",
  joining_date: "",
  work_email: "",
  salary_currency: "USD",
  base_salary: "",
  current_bonus: "",
  notes: "",
}

const emptyCompensationRequest = {
  request_type: "salary" as "salary" | "bonus",
  change_type: "increase" as "increase" | "decrease" | "set",
  amount: "",
  effective_date: "",
  reason: "",
}

function viewTitle(view: View) {
  if (view === "employees") return "Employees"
  if (view === "positions") return "Positions"
  if (view === "statistics") return "HR Statistics"
  if (view === "my-profile") return "My HR Profile"
  return "HR Dashboard"
}

function statusLabel(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value: string | null, locale: string) {
  if (!value) return "Not recorded"
  const formatted = formatDateOnly(value, { locale, formatOptions: { dateStyle: "medium" } })
  return formatted === "N/A" ? "Not recorded" : formatted
}

function formatMoney(value: string | number | null | undefined, currency: string, locale: string) {
  const amount = Number(value ?? 0)
  if (Number.isNaN(amount)) return `${currency} ${value ?? "0.00"}`
  try {
    return formatCurrency(amount, { currency, locale })
  } catch {
    return `${currency} ${amount.toFixed(2)}`
  }
}

export function HrWorkspacePage({ view }: { view: View }) {
  const umsSettings = usePublicUmsSettings()
  const locale = umsSettings.localization.locale
  const defaultCurrency = umsSettings.localization.currency_code
  const roleLabel = useCallback(
    (value: string) => {
      const role = parseUmsRole(value)
      return role ? zoneForUmsRole(role, umsSettings).label : statusLabel(value)
    },
    [umsSettings]
  )
  const [summary, setSummary] = useState<DashboardResponse["summary"] | null>(null)
  const [statistics, setStatistics] = useState<DashboardResponse["statistics"] | null>(null)
  const [hrStatistics, setHrStatistics] = useState<HrStatisticsResponse | null>(null)
  const [employees, setEmployees] = useState<Employee[]>([])
  const [positions, setPositions] = useState<Position[]>([])
  const [profiles, setProfiles] = useState<ProfileOption[]>([])
  const [myEmployee, setMyEmployee] = useState<Employee | null>(null)
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null)
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeDetail | null>(null)
  const [employeeFilters, setEmployeeFilters] = useState({ q: "", status: "", role: "", position_id: "" })
  const [positionForm, setPositionForm] = useState(emptyPosition)
  const [employeeForm, setEmployeeForm] = useState(emptyEmployee)
  const [compensationForm, setCompensationForm] = useState(emptyCompensationRequest)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const availableProfiles = useMemo(
    () => profiles.filter((profile) => !profile.has_employee_record),
    [profiles]
  )

  const filteredEmployees = useMemo(() => {
    const query = employeeFilters.q.trim().toLowerCase()
    return employees.filter((employee) => {
      const matchesQuery = query
        ? [
            employee.name,
            employee.employee_no,
            employee.email,
            employee.work_email,
            employee.position?.title ?? "",
            employee.role,
          ].some((value) => value.toLowerCase().includes(query))
        : true
      const matchesStatus = employeeFilters.status ? employee.employment_status === employeeFilters.status : true
      const matchesRole = employeeFilters.role ? employee.role === employeeFilters.role : true
      const matchesPosition = employeeFilters.position_id ? employee.position?.id === Number(employeeFilters.position_id) : true
      return matchesQuery && matchesStatus && matchesRole && matchesPosition
    })
  }, [employeeFilters, employees])

  const roleOptions = useMemo(
    () => Array.from(new Set(employees.map((employee) => employee.role))).sort(),
    [employees]
  )

  const loadEmployeeDetail = useCallback(async (employeeId: number) => {
    setDetailLoading(true)
    try {
      const data = await apiFetch<{ employee: EmployeeDetail }>(`/hr/employees/${employeeId}`)
      setSelectedEmployee(data.employee)
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const selectEmployee = useCallback((employeeId: number) => {
    setSelectedEmployeeId(employeeId)
    void loadEmployeeDetail(employeeId).catch((caught) =>
      setError(caught instanceof Error ? caught.message : "Unable to load employee details.")
    )
  }, [loadEmployeeDetail])

  const loadData = useCallback(async () => {
    const dashboard = await apiFetch<DashboardResponse>("/hr/dashboard")
    setSummary(dashboard.summary)
    setStatistics(dashboard.statistics)
    setEmployees(dashboard.employees ?? [])
    setPositions(dashboard.positions ?? [])

    if (view === "statistics") {
      setHrStatistics(await apiFetch<HrStatisticsResponse>("/hr/statistics"))
    } else {
      setHrStatistics(null)
    }

    if (view === "employees") {
      const [employeeData, profileData] = await Promise.all([
        apiFetch<{ employees: Employee[] }>("/hr/employees"),
        apiFetch<{ profiles: ProfileOption[] }>("/hr/profiles"),
      ])
      const nextEmployees = employeeData.employees ?? []
      setEmployees(nextEmployees)
      setProfiles(profileData.profiles ?? [])
      const nextSelectedId = selectedEmployeeId && nextEmployees.some((employee) => employee.id === selectedEmployeeId)
        ? selectedEmployeeId
        : nextEmployees[0]?.id ?? null
      setSelectedEmployeeId(nextSelectedId)
      if (nextSelectedId) {
        await loadEmployeeDetail(nextSelectedId)
      } else {
        setSelectedEmployee(null)
      }
    }

    if (view === "positions") {
      const positionData = await apiFetch<{ positions: Position[] }>("/hr/positions")
      setPositions(positionData.positions ?? [])
    }

    if (view === "my-profile") {
      const profileData = await apiFetch<{ employee: Employee | null }>("/hr/my-profile")
      setMyEmployee(profileData.employee)
    }
  }, [loadEmployeeDetail, selectedEmployeeId, view])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load HR data."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  async function savePosition(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/hr/positions", {
        method: "POST",
        body: JSON.stringify(positionForm),
      })
      setSuccess("Position saved.")
      setPositionForm(emptyPosition)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save position.")
    } finally {
      setSaving(false)
    }
  }

  async function saveEmployee(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/hr/employees", {
        method: "POST",
        body: JSON.stringify({
          ...employeeForm,
          profile_id: Number(employeeForm.profile_id),
          position_id: employeeForm.position_id ? Number(employeeForm.position_id) : null,
          base_salary: employeeForm.base_salary || "0.00",
          current_salary: employeeForm.base_salary || "0.00",
          current_bonus: employeeForm.current_bonus || "0.00",
        }),
      })
      setSuccess("Employee record saved.")
      setEmployeeForm(emptyEmployee)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save employee record.")
    } finally {
      setSaving(false)
    }
  }

  async function submitCompensationRequest(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedEmployeeId) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const result = await apiFetch<{ employee: EmployeeDetail; message: string }>(`/hr/employees/${selectedEmployeeId}/compensation-requests`, {
        method: "POST",
        body: JSON.stringify(compensationForm),
      })
      setSelectedEmployee(result.employee)
      setSuccess(result.message)
      setCompensationForm(emptyCompensationRequest)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit compensation request.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/hr", title: "HR" }, { href: `/hr/${view === "dashboard" ? "dashboard" : view}`, title: viewTitle(view) }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              {view === "positions" ? <UserCog className="size-6" /> : view === "statistics" ? <BarChart3 className="size-6" /> : <Users className="size-6" />}
              {viewTitle(view)}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">Manage employee records, position structure, salary and bonus requests, and HR lifecycle activity.</p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
          </Button>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {view === "dashboard" ? (
          <>
            <HrDashboard />
            {summary ? (
              <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Employees" value={summary.employees} icon={<Users className="size-4" />} />
                <StatCard label="Monthly Payroll" value={formatMoney(summary.monthly_payroll, defaultCurrency, locale)} icon={<CircleDollarSign className="size-4" />} />
                <StatCard label="Total Bonus" value={formatMoney(summary.total_bonus, defaultCurrency, locale)} icon={<Gift className="size-4" />} />
                <StatCard label="Pending Requests" value={summary.pending_compensation_requests} icon={<History className="size-4" />} />
                <StatCard label="Average Salary" value={formatMoney(summary.average_salary, defaultCurrency, locale)} icon={<BarChart3 className="size-4" />} />
                <StatCard label="Average Bonus" value={formatMoney(summary.average_bonus, defaultCurrency, locale)} icon={<Gift className="size-4" />} />
                <StatCard label="Active Positions" value={summary.positions} icon={<BriefcaseBusiness className="size-4" />} />
                <StatCard label="Vacation Days Placeholder" value={summary.vacation_days_available} icon={<FileText className="size-4" />} />
              </section>
            ) : null}

            {statistics ? (
              <section className="grid gap-4 xl:grid-cols-2">
                <ChartCard title="Employment Status" subtitle="Status distribution" rows={statistics.status_counts} total={summary?.employees ?? 0} />
                <ChartCard title="Roles and Positions" subtitle="Workforce coverage" rows={[...statistics.role_counts.map((role) => ({ label: roleLabel(role.role), count: role.count })), ...statistics.position_counts.map((position) => ({ label: position.code ? `${position.title} (${position.code})` : position.title, count: position.count }))]} total={summary?.employees ?? 0} />
                <RecentRequests requests={statistics.recent_compensation_requests} defaultCurrency={defaultCurrency} locale={locale} />
                <RecentSalaryAdjustments adjustments={statistics.recent_salary_adjustments} defaultCurrency={defaultCurrency} locale={locale} />
              </section>
            ) : null}
          </>
        ) : null}

        {view === "statistics" ? (
          <HrStatisticsView data={hrStatistics} defaultCurrency={defaultCurrency} locale={locale} roleLabel={roleLabel} />
        ) : null}

        {view === "positions" ? (
          <section className="grid gap-4 lg:grid-cols-[24rem_minmax(0,1fr)]">
            <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={savePosition}>
              <h2 className="text-base font-semibold">New Position</h2>
              <div className="mt-4 grid gap-3">
                <div className="space-y-2"><Label htmlFor="position_code">Code</Label><Input id="position_code" value={positionForm.code} onChange={(event) => setPositionForm((current) => ({ ...current, code: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="position_title">Title</Label><Input id="position_title" value={positionForm.title} onChange={(event) => setPositionForm((current) => ({ ...current, title: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="employment_type">Employment Type</Label><select id="employment_type" value={positionForm.employment_type} onChange={(event) => setPositionForm((current) => ({ ...current, employment_type: event.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"><option value="full_time">Full-time</option><option value="part_time">Part-time</option><option value="contract">Contract</option><option value="adjunct">Adjunct</option></select></div>
                <div className="space-y-2"><Label htmlFor="grade">Grade</Label><Input id="grade" value={positionForm.grade} onChange={(event) => setPositionForm((current) => ({ ...current, grade: event.target.value }))} /></div>
                <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Save Position</Button>
              </div>
            </form>
            <section className="grid content-start gap-3">
              {positions.map((position) => (
                <Card key={position.id}>
                  <CardContent className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-medium">{position.title}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{position.code} - {position.employment_type_label || statusLabel(position.employment_type)} - {position.grade || "No grade"}</p>
                    </div>
                    <span className="w-fit rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">{position.is_active ? "Active" : "Inactive"}</span>
                  </CardContent>
                </Card>
              ))}
            </section>
          </section>
        ) : null}

        {view === "employees" ? (
          <section className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
            <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={saveEmployee}>
              <h2 className="text-base font-semibold">New Employee Record</h2>
              <div className="mt-4 grid gap-3">
                <div className="space-y-2"><Label htmlFor="profile_id">Portal Profile</Label><select id="profile_id" value={employeeForm.profile_id} onChange={(event) => setEmployeeForm((current) => ({ ...current, profile_id: event.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required><option value="">Select staff profile</option>{availableProfiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.name} - {profile.role} - {profile.identifier}</option>)}</select></div>
                <div className="space-y-2"><Label htmlFor="employee_no">Employee No.</Label><Input id="employee_no" value={employeeForm.employee_no} onChange={(event) => setEmployeeForm((current) => ({ ...current, employee_no: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="position_id">Position</Label><select id="position_id" value={employeeForm.position_id} onChange={(event) => setEmployeeForm((current) => ({ ...current, position_id: event.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"><option value="">No position</option>{positions.map((position) => <option key={position.id} value={position.id}>{position.title} - {position.code}</option>)}</select></div>
                <div className="space-y-2"><Label htmlFor="employment_status">Status</Label><select id="employment_status" value={employeeForm.employment_status} onChange={(event) => setEmployeeForm((current) => ({ ...current, employment_status: event.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"><option value="draft">Draft</option><option value="active">Active</option><option value="probation">Probation</option><option value="suspended">Suspended</option><option value="resigned">Resigned</option><option value="terminated">Terminated</option><option value="retired">Retired</option></select></div>
                <div className="grid gap-3 sm:grid-cols-[1fr_6rem]">
                  <div className="space-y-2"><Label htmlFor="base_salary">Initial Salary</Label><Input id="base_salary" type="number" min="0" step="0.01" value={employeeForm.base_salary} onChange={(event) => setEmployeeForm((current) => ({ ...current, base_salary: event.target.value }))} /></div>
                  <div className="space-y-2"><Label htmlFor="salary_currency">Currency</Label><Input id="salary_currency" maxLength={3} value={employeeForm.salary_currency} onChange={(event) => setEmployeeForm((current) => ({ ...current, salary_currency: event.target.value.toUpperCase() }))} /></div>
                </div>
                <div className="space-y-2"><Label htmlFor="current_bonus">Initial Bonus</Label><Input id="current_bonus" type="number" min="0" step="0.01" value={employeeForm.current_bonus} onChange={(event) => setEmployeeForm((current) => ({ ...current, current_bonus: event.target.value }))} /></div>
                <div className="space-y-2"><Label htmlFor="joining_date">Joining Date</Label><Input id="joining_date" type="date" value={employeeForm.joining_date} onChange={(event) => setEmployeeForm((current) => ({ ...current, joining_date: event.target.value }))} /></div>
                <div className="space-y-2"><Label htmlFor="work_email">Work Email</Label><Input id="work_email" type="email" value={employeeForm.work_email} onChange={(event) => setEmployeeForm((current) => ({ ...current, work_email: event.target.value }))} /></div>
                <div className="space-y-2"><Label htmlFor="notes">Notes</Label><Textarea id="notes" value={employeeForm.notes} onChange={(event) => setEmployeeForm((current) => ({ ...current, notes: event.target.value }))} /></div>
                <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Save Employee</Button>
              </div>
            </form>

            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_25rem]">
              <div className="space-y-4">
                <Card>
                  <CardContent className="grid gap-3 p-4 md:grid-cols-[minmax(0,1.6fr)_repeat(3,minmax(0,1fr))]">
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                      <Input className="pl-9" placeholder="Search employees" value={employeeFilters.q} onChange={(event) => setEmployeeFilters((current) => ({ ...current, q: event.target.value }))} />
                    </div>
                    <select value={employeeFilters.status} onChange={(event) => setEmployeeFilters((current) => ({ ...current, status: event.target.value }))} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option value="">All statuses</option>
                      <option value="draft">Draft</option>
                      <option value="active">Active</option>
                      <option value="probation">Probation</option>
                      <option value="suspended">Suspended</option>
                      <option value="resigned">Resigned</option>
                      <option value="terminated">Terminated</option>
                      <option value="retired">Retired</option>
                    </select>
                    <select value={employeeFilters.role} onChange={(event) => setEmployeeFilters((current) => ({ ...current, role: event.target.value }))} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option value="">All roles</option>
                      {roleOptions.map((role) => <option key={role} value={role}>{roleLabel(role)}</option>)}
                    </select>
                    <select value={employeeFilters.position_id} onChange={(event) => setEmployeeFilters((current) => ({ ...current, position_id: event.target.value }))} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option value="">All positions</option>
                      {positions.map((position) => <option key={position.id} value={position.id}>{position.title}</option>)}
                    </select>
                  </CardContent>
                </Card>

                <section className="grid gap-3">
                  {filteredEmployees.map((employee) => (
                    <button
                      key={employee.id}
                      type="button"
                      onClick={() => selectEmployee(employee.id)}
                      className={`rounded-lg border bg-background p-4 text-left shadow-sm transition hover:border-primary/60 ${selectedEmployeeId === employee.id ? "border-primary ring-1 ring-primary/20" : "border-border"}`}
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="font-medium">{employee.name}</p>
                          <p className="mt-1 text-sm text-muted-foreground">{employee.employee_no} - {roleLabel(employee.role)} - {employee.position?.title ?? "No position"}</p>
                        </div>
                        <span className="w-fit rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">{employee.employment_status_label || statusLabel(employee.employment_status)}</span>
                      </div>
                      <div className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2 xl:grid-cols-4">
                        <span>{employee.work_email || employee.email}</span>
                        <span>Salary {formatMoney(employee.current_salary, employee.salary_currency || defaultCurrency, locale)}</span>
                        <span>Bonus {formatMoney(employee.current_bonus, employee.salary_currency || defaultCurrency, locale)}</span>
                        <span>Vacation {employee.vacation_days_remaining}/{employee.vacation_days_total} days</span>
                      </div>
                    </button>
                  ))}
                  {filteredEmployees.length === 0 ? <p className="rounded-lg border border-border bg-background p-4 text-sm text-muted-foreground">No employees match the current filters.</p> : null}
                </section>
              </div>

              <EmployeeDetailPanel
                employee={selectedEmployee}
                loading={detailLoading}
                compensationForm={compensationForm}
                saving={saving}
                onCompensationFormChange={setCompensationForm}
                onCompensationSubmit={submitCompensationRequest}
                defaultCurrency={defaultCurrency}
                locale={locale}
                roleLabel={roleLabel}
              />
            </section>
          </section>
        ) : null}

        {view === "my-profile" ? (
          <Card>
            <CardHeader>
              <CardDescription>Employee master record</CardDescription>
              <CardTitle>{myEmployee?.name ?? "No employee record"}</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {myEmployee ? (
                <>
                  <InfoItem label="Employee No." value={myEmployee.employee_no} />
                  <InfoItem label="Status" value={myEmployee.employment_status_label || statusLabel(myEmployee.employment_status)} />
                  <InfoItem label="Position" value={myEmployee.position?.title ?? "Not assigned"} />
                  <InfoItem label="Current Salary" value={formatMoney(myEmployee.current_salary, myEmployee.salary_currency || defaultCurrency, locale)} />
                  <InfoItem label="Current Bonus" value={formatMoney(myEmployee.current_bonus, myEmployee.salary_currency || defaultCurrency, locale)} />
                  <InfoItem label="Vacation Placeholder" value={`${myEmployee.vacation_days_remaining}/${myEmployee.vacation_days_total} days`} />
                  <InfoItem label="Joining Date" value={formatDate(myEmployee.joining_date, locale)} />
                  <InfoItem label="Manager" value={myEmployee.reporting_manager?.name ?? "Not assigned"} />
                  <InfoItem label="Work Email" value={myEmployee.work_email || myEmployee.email || "Not recorded"} />
                </>
              ) : (
                <p className="text-sm text-muted-foreground">HR has not created your employee master record yet.</p>
              )}
            </CardContent>
          </Card>
        ) : null}
      </main>
    </div>
  )
}

function HrStatisticsView({
  data,
  defaultCurrency,
  locale,
  roleLabel,
}: {
  data: HrStatisticsResponse | null
  defaultCurrency: string
  locale: string
  roleLabel: (value: string) => string
}) {
  if (!data) {
    return (
      <LoadingScreen
        label="Loading Statistics..."
        className="min-h-[24rem]"
      />
    )
  }

  return (
    <section className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Employees" value={data.summary.employees} icon={<Users className="size-4" />} />
        <StatCard label="Payroll" value={formatMoney(data.summary.monthly_payroll, defaultCurrency, locale)} icon={<CircleDollarSign className="size-4" />} />
        <StatCard label="Bonus Pool" value={formatMoney(data.summary.total_bonus, defaultCurrency, locale)} icon={<Gift className="size-4" />} />
        <StatCard label="Pending Requests" value={data.summary.pending_compensation_requests} icon={<History className="size-4" />} />
      </section>
      <section className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="Employment Status" subtitle="All employee statuses" rows={data.charts.status_counts} total={data.summary.employees} />
        <ChartCard title="Role Distribution" subtitle="Employees by portal role" rows={data.charts.role_counts.map((row) => ({ label: roleLabel(row.role), count: row.count }))} total={data.summary.employees} />
        <ChartCard title="Salary Bands" subtitle="Current salary spread" rows={data.charts.salary_bands} total={data.summary.employees} />
        <ChartCard title="Bonus Bands" subtitle="Current bonus spread" rows={data.charts.bonus_bands} total={data.summary.employees} />
        <ChartCard title="Compensation Requests" subtitle="Approval queue status" rows={data.charts.compensation_request_status} total={Math.max(data.charts.compensation_request_status.reduce((sum, row) => sum + row.count, 0), 1)} />
        <ChartCard title="Vacation And Leave Placeholder" subtitle="Temporary stats until leave workflow is built" rows={data.charts.leave_placeholder} total={Math.max(data.summary.vacation_days_total, 1)} />
      </section>
      <RecentRequests requests={data.recent_compensation_requests} defaultCurrency={defaultCurrency} locale={locale} />
    </section>
  )
}

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription className="flex items-center gap-2">{icon}{label}</CardDescription>
        <CardTitle>{value}</CardTitle>
      </CardHeader>
    </Card>
  )
}

function ChartCard({ title, subtitle, rows, total }: { title: string; subtitle: string; rows: ChartRow[]; total: number }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{subtitle}</CardDescription>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map((row) => <ProgressRow key={`${row.label}-${row.count}`} label={row.label || row.title || ""} count={row.count} total={total} />)}
      </CardContent>
    </Card>
  )
}

function ProgressRow({ label, count, total }: { label: string; count: number; total: number }) {
  const percentage = total > 0 ? Math.min(100, Math.round((count / total) * 100)) : 0
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="truncate">{label}</span>
        <span className="text-muted-foreground">{count}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary transition-all duration-700 ease-out" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  )
}

function HistoryRow({ icon, title, meta }: { icon: React.ReactNode; title: string; meta: string }) {
  return (
    <div className="flex gap-3 rounded-md border border-border p-3">
      <span className="mt-0.5 text-muted-foreground">{icon}</span>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{meta}</p>
      </div>
    </div>
  )
}

function InfoItem({ label, value }: { label: string; value: string | number }) {
  return (
    <p className="text-sm">
      <span className="text-muted-foreground">{label}</span>
      <br />
      {value}
    </p>
  )
}

function RecentRequests({
  requests,
  defaultCurrency,
  locale,
}: {
  requests: CompensationRequest[]
  defaultCurrency: string
  locale: string
}) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>Salary and bonus approval queue</CardDescription>
        <CardTitle>Compensation Requests</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {requests.length ? requests.map((item) => (
          <HistoryRow
            key={item.id}
            icon={item.change_type === "decrease" ? <TrendingDown className="size-4" /> : <TrendingUp className="size-4" />}
            title={`${item.employee.name} - ${item.request_type_label} ${item.change_type_label} - ${item.status_label}`}
            meta={`${formatMoney(item.previous_amount, item.employee.currency || defaultCurrency, locale)} to ${formatMoney(item.requested_amount, item.employee.currency || defaultCurrency, locale)} - ${formatDate(item.effective_date, locale)}`}
          />
        )) : <p className="text-sm text-muted-foreground">No compensation requests yet.</p>}
      </CardContent>
    </Card>
  )
}

function RecentSalaryAdjustments({
  adjustments,
  defaultCurrency,
  locale,
}: {
  adjustments: SalaryAdjustment[]
  defaultCurrency: string
  locale: string
}) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>Approved salary changes</CardDescription>
        <CardTitle>Salary History</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {adjustments.length ? adjustments.map((adjustment) => (
          <HistoryRow
            key={adjustment.id}
            icon={adjustment.change_type === "increase" ? <TrendingUp className="size-4" /> : <TrendingDown className="size-4" />}
            title={`${adjustment.employee_name} - ${adjustment.change_type_label}`}
            meta={`${formatMoney(adjustment.previous_salary, defaultCurrency, locale)} to ${formatMoney(adjustment.new_salary, defaultCurrency, locale)} on ${formatDate(adjustment.effective_date, locale)}`}
          />
        )) : <p className="text-sm text-muted-foreground">No approved salary adjustments recorded yet.</p>}
      </CardContent>
    </Card>
  )
}

function EmployeeDetailPanel({
  employee,
  loading,
  compensationForm,
  saving,
  onCompensationFormChange,
  onCompensationSubmit,
  defaultCurrency,
  locale,
  roleLabel,
}: {
  employee: EmployeeDetail | null
  loading: boolean
  compensationForm: typeof emptyCompensationRequest
  saving: boolean
  onCompensationFormChange: React.Dispatch<React.SetStateAction<typeof emptyCompensationRequest>>
  onCompensationSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  defaultCurrency: string
  locale: string
  roleLabel: (value: string) => string
}) {
  if (loading && !employee) {
    return (
      <Card>
        <CardContent className="flex min-h-48 items-center justify-center p-6 text-sm text-muted-foreground">
          <Loader2 className="mr-2 size-4 animate-spin" /> Loading details
        </CardContent>
      </Card>
    )
  }

  if (!employee) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">Select an employee to view their full record.</CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardDescription>{employee.employee_no} - {employee.employment_status_label || statusLabel(employee.employment_status)}</CardDescription>
        <CardTitle>{employee.name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <section className="grid gap-3 sm:grid-cols-2">
          <InfoItem label="Role" value={roleLabel(employee.role)} />
          <InfoItem label="Position" value={employee.position?.title ?? "Not assigned"} />
          <InfoItem label="Current Salary" value={formatMoney(employee.current_salary, employee.salary_currency || defaultCurrency, locale)} />
          <InfoItem label="Current Bonus" value={formatMoney(employee.current_bonus, employee.salary_currency || defaultCurrency, locale)} />
          <InfoItem label="Vacation Placeholder" value={`${employee.vacation_days_remaining}/${employee.vacation_days_total} days`} />
          <InfoItem label="Leave Placeholder" value={`${employee.leave_days_remaining}/${employee.leave_days_total} days`} />
          <InfoItem label="Joining Date" value={formatDate(employee.joining_date, locale)} />
          <InfoItem label="Manager" value={employee.reporting_manager?.name ?? "Not assigned"} />
          <InfoItem label="Direct Reports" value={employee.direct_reports.length} />
        </section>

        <form className="space-y-3 rounded-lg border border-border p-4" onSubmit={onCompensationSubmit}>
          <div>
            <h3 className="text-sm font-semibold">Salary Or Bonus Request</h3>
            <p className="mt-1 text-xs text-muted-foreground">Requests are sent to Accountant for approval before employee compensation changes.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="request_type">Compensation</Label>
              <select id="request_type" value={compensationForm.request_type} onChange={(event) => onCompensationFormChange((current) => ({ ...current, request_type: event.target.value as "salary" | "bonus" }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="salary">Salary</option>
                <option value="bonus">Bonus</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="change_type">Type</Label>
              <select id="change_type" value={compensationForm.change_type} onChange={(event) => onCompensationFormChange((current) => ({ ...current, change_type: event.target.value as "increase" | "decrease" | "set" }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="increase">Increase</option>
                <option value="decrease">Decrease</option>
                <option value="set">Set Amount</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="compensation_amount">Amount</Label>
              <Input id="compensation_amount" type="number" min="0.01" step="0.01" value={compensationForm.amount} onChange={(event) => onCompensationFormChange((current) => ({ ...current, amount: event.target.value }))} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="effective_date">Effective Date</Label>
              <Input id="effective_date" type="date" value={compensationForm.effective_date} onChange={(event) => onCompensationFormChange((current) => ({ ...current, effective_date: event.target.value }))} />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="compensation_reason">Reason</Label>
              <Textarea id="compensation_reason" value={compensationForm.reason} onChange={(event) => onCompensationFormChange((current) => ({ ...current, reason: event.target.value }))} />
            </div>
          </div>
          <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Submit For Approval</Button>
        </form>

        <section className="space-y-3">
          <h3 className="text-sm font-semibold">Compensation Requests</h3>
          {employee.compensation_requests.length ? employee.compensation_requests.map((item) => (
            <HistoryRow
              key={item.id}
              icon={item.change_type === "decrease" ? <TrendingDown className="size-4" /> : <TrendingUp className="size-4" />}
              title={`${item.request_type_label} ${item.change_type_label} - ${item.status_label}`}
              meta={`${formatMoney(item.previous_amount, employee.salary_currency || defaultCurrency, locale)} to ${formatMoney(item.requested_amount, employee.salary_currency || defaultCurrency, locale)} on ${formatDate(item.effective_date, locale)}`}
            />
          )) : <p className="text-sm text-muted-foreground">No compensation requests recorded yet.</p>}
        </section>

        <section className="space-y-3">
          <h3 className="text-sm font-semibold">Approved Salary History</h3>
          {employee.salary_adjustments.length ? employee.salary_adjustments.map((adjustment) => (
            <HistoryRow
              key={adjustment.id}
              icon={adjustment.change_type === "increase" ? <TrendingUp className="size-4" /> : <TrendingDown className="size-4" />}
              title={`${adjustment.change_type_label} ${formatMoney(adjustment.amount, employee.salary_currency || defaultCurrency, locale)}`}
              meta={`${formatMoney(adjustment.previous_salary, employee.salary_currency || defaultCurrency, locale)} to ${formatMoney(adjustment.new_salary, employee.salary_currency || defaultCurrency, locale)} on ${formatDate(adjustment.effective_date, locale)}`}
            />
          )) : <p className="text-sm text-muted-foreground">No approved salary adjustments recorded yet.</p>}
        </section>

        <section className="space-y-3">
          <h3 className="text-sm font-semibold">Employment History</h3>
          {employee.employment_records.length ? employee.employment_records.map((record) => (
            <HistoryRow
              key={record.id}
              icon={<History className="size-4" />}
              title={`${record.status_label} - ${record.position?.title ?? "No position"}`}
              meta={`${record.recorded_by || "HR"} on ${formatDate(record.start_date, locale)}`}
            />
          )) : <p className="text-sm text-muted-foreground">No employment history recorded yet.</p>}
        </section>

        <section className="space-y-3">
          <h3 className="text-sm font-semibold">Documents</h3>
          {employee.documents.length ? employee.documents.map((document) => (
            <HistoryRow
              key={document.id}
              icon={<FileText className="size-4" />}
              title={`${document.title} - ${document.document_type_label}`}
              meta={`Expires ${formatDate(document.expires_on, locale)}`}
            />
          )) : <p className="text-sm text-muted-foreground">No documents recorded yet.</p>}
        </section>
      </CardContent>
    </Card>
  )
}
