"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileSpreadsheet,
  GraduationCap,
  ListChecks,
  Upload,
  UserPlus,
  Users,
  UserCog,
  WalletCards,
  type LucideIcon,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

export type AdminCreateAccountRole =
  | "student"
  | "teacher"
  | "executive"
  | "librarian"
  | "caterer"
  | "technician"
  | "accountant"
  | "hr"
const MAX_PASSWORD_LENGTH = 20

type RoleConfig = {
  title: string
  label: string
  description: string
  idLabel: string
  idPlaceholder: string
  icon: LucideIcon
}

type AccountForm = {
  username: string
  first_name: string
  last_name: string
  email: string
  password: string
  ums_id: string
  phone_number: string
  room: string
  assignment_type: "" | "school" | "center"
  school_id: string
  center_id: string
  unit_id: string
  department_id: string
  program_id: string
  designation: string
}

type TeacherAssignmentForm = {
  assignment_type: "" | "school" | "center"
  school_id: string
  center_id: string
}

type CreateAccountResponse = {
  message?: string
  user?: {
    username?: string
    email?: string
    role?: string
  }
}

type ImportAccountResult = {
  row: number
  status: "created" | "error"
  username?: string
  email?: string
  detail?: string
}

type ImportAccountResponse = {
  message?: string
  created_count: number
  failed_count: number
  total_rows: number
  results: ImportAccountResult[]
}

type AcademicUnit = {
  id: number
  code: string
  name: string
  school?: number | null
  center?: number | null
}

type ProgramOption = {
  id: number
  code: string
  name: string
  school: number | null
  center: number | null
}

type ScopedAccountConfigResponse = {
  schools?: AcademicUnit[]
  centers?: AcademicUnit[]
  units?: AcademicUnit[]
  departments?: AcademicUnit[]
}

type StudentAccountConfigResponse = {
  schools?: AcademicUnit[]
  centers?: AcademicUnit[]
  programs?: ProgramOption[]
}

const roleConfig: Record<AdminCreateAccountRole, RoleConfig> = {
  student: {
    title: "Create Student",
    label: "Student",
    description: "Create a student portal account with a student ID.",
    idLabel: "Student ID",
    idPlaceholder: "Student ID",
    icon: GraduationCap,
  },
  teacher: {
    title: "Create Teacher",
    label: "Teacher",
    description:
      "Create a teacher account assigned to one or more schools or centres.",
    idLabel: "Staff ID",
    idPlaceholder: "Teacher staff ID",
    icon: BookOpen,
  },
  executive: {
    title: "Create Executive",
    label: "Executive",
    description: "Create an executive account assigned to one specific unit.",
    idLabel: "Staff ID",
    idPlaceholder: "Executive staff ID",
    icon: Users,
  },
  librarian: {
    title: "Create Librarian",
    label: "Librarian",
    description:
      "Create a librarian account assigned to a configured library owner.",
    idLabel: "Staff ID",
    idPlaceholder: "Librarian staff ID",
    icon: BookOpen,
  },
  caterer: {
    title: "Create Caterer",
    label: "Caterer",
    description:
      "Create a dining or canteen worker account assigned to a configured owner.",
    idLabel: "Staff ID",
    idPlaceholder: "Caterer staff ID",
    icon: Users,
  },
  technician: {
    title: "Create Technician",
    label: "Technician",
    description:
      "Create a service desk technician account assigned to a configured department or unit.",
    idLabel: "Staff ID",
    idPlaceholder: "Technician staff ID",
    icon: Users,
  },
  accountant: {
    title: "Create Accountant",
    label: "Accountant",
    description:
      "Create a finance department account for managing subscriptions and payment settings.",
    idLabel: "Staff ID",
    idPlaceholder: "Accountant staff ID",
    icon: WalletCards,
  },
  hr: {
    title: "Create HR",
    label: "Human Resources",
    description:
      "Create a human resources account for managing university employee records.",
    idLabel: "Staff ID",
    idPlaceholder: "HR staff ID",
    icon: UserCog,
  },
}

const commonImportColumns = [
  "username",
  "email",
  "first_name",
  "last_name",
  "ums_id",
]
const optionalImportColumns = ["phone_number", "password"]

const roleImportColumns: Record<AdminCreateAccountRole, string[]> = {
  student: [
    "school_id",
    "school_code",
    "center_id",
    "center_code",
    "program_id",
    "program_code",
    "room",
  ],
  teacher: [
    "school_id",
    "school_code",
    "center_id",
    "center_code",
    "teacher_assignments",
    "designation",
  ],
  executive: [
    "unit_id",
    "unit_code",
    "school_id",
    "school_code",
    "center_id",
    "center_code",
  ],
  librarian: [
    "school_id",
    "school_code",
    "center_id",
    "center_code",
    "unit_id",
    "unit_code",
    "designation",
  ],
  caterer: [
    "school_id",
    "school_code",
    "center_id",
    "center_code",
    "unit_id",
    "unit_code",
    "designation",
  ],
  technician: [
    "department_id",
    "department_code",
    "unit_id",
    "unit_code",
    "school_id",
    "school_code",
    "center_id",
    "center_code",
    "designation",
  ],
  accountant: [],
  hr: [],
}

const roleImportNotes: Record<AdminCreateAccountRole, string[]> = {
  student: [
    "Use either school or centre columns. Program columns are optional.",
    "student_id is accepted instead of ums_id.",
  ],
  teacher: [
    "Use teacher_assignments for multiple scopes, such as school:SAS;center:ACE.",
    "staff_id is accepted instead of ums_id.",
  ],
  executive: [
    "unit_id or unit_code is required. Add school or centre columns when the unit needs scope context.",
    "staff_id is accepted instead of ums_id.",
  ],
  librarian: [
    "staff_id is accepted instead of ums_id.",
    "Owner columns are optional when role ownership defaults are configured in admin settings.",
  ],
  caterer: [
    "staff_id is accepted instead of ums_id.",
    "Owner columns are optional when role ownership defaults are configured in admin settings.",
  ],
  technician: [
    "staff_id is accepted instead of ums_id.",
    "Use department or unit columns, or configure role ownership defaults in admin settings.",
  ],
  accountant: ["staff_id is accepted instead of ums_id."],
  hr: ["staff_id is accepted instead of ums_id."],
}

const emptyForm: AccountForm = {
  username: "",
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  ums_id: "",
  phone_number: "",
  room: "",
  assignment_type: "",
  school_id: "",
  center_id: "",
  unit_id: "",
  department_id: "",
  program_id: "",
  designation: "",
}

const emptyTeacherAssignment: TeacherAssignmentForm = {
  assignment_type: "",
  school_id: "",
  center_id: "",
}

const ownerScopedRoles = new Set<AdminCreateAccountRole>([
  "librarian",
  "caterer",
  "technician",
])

function breadcrumbs(accountRole?: AdminCreateAccountRole) {
  const items = [
    { href: "/admin", title: "Admin" },
    { href: "/admin/create-account", title: "Create Account" },
  ]

  if (accountRole) {
    items.push({
      href: `/admin/create-account/${accountRole}`,
      title: roleConfig[accountRole].title,
    })
  }

  return items
}

function ColumnList({ columns }: { columns: string[] }) {
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {columns.map((column) => (
        <code
          key={column}
          className="rounded-md border border-border bg-muted px-1.5 py-1 text-[0.72rem] text-muted-foreground"
        >
          {column}
        </code>
      ))}
    </div>
  )
}

function RolePicker() {
  return (
    <section className="grid gap-4 md:grid-cols-3">
      {(Object.keys(roleConfig) as AdminCreateAccountRole[]).map((role) => {
        const config = roleConfig[role]
        const Icon = config.icon

        return (
          <Link
            key={role}
            href={`/admin/create-account/${role}`}
            className="group rounded-lg border border-border bg-background p-5 shadow-sm transition-colors hover:bg-muted/60"
          >
            <div className="flex items-start justify-between gap-4">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                <Icon className="size-5" />
              </span>
              <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </div>
            <h2 className="mt-4 text-base font-semibold">{config.title}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {config.description}
            </p>
          </Link>
        )
      })}
    </section>
  )
}

type UnitScopeFieldsProps = {
  assignmentType: AccountForm["assignment_type"]
  schoolId: string
  centerId: string
  schools: AcademicUnit[]
  centers: AcademicUnit[]
  schoolLabel?: string
  centerLabel?: string
  onAssignmentTypeChange: (value: AccountForm["assignment_type"]) => void
  onSchoolChange: (value: string) => void
  onCenterChange: (value: string) => void
}

function UnitScopeFields({
  assignmentType,
  schoolId,
  centerId,
  schools,
  centers,
  schoolLabel = "School",
  centerLabel = "Centre",
  onAssignmentTypeChange,
  onSchoolChange,
  onCenterChange,
}: UnitScopeFieldsProps) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="assignment_type">Assigned Unit Type</Label>
        <select
          id="assignment_type"
          value={assignmentType}
          onChange={(event) =>
            onAssignmentTypeChange(
              event.target.value as AccountForm["assignment_type"]
            )
          }
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          required
        >
          <option value="">Select assignment</option>
          <option value="school">School</option>
          <option value="center">Centre</option>
        </select>
      </div>
      {assignmentType === "school" ? (
        <div className="space-y-2">
          <Label htmlFor="school_id">{schoolLabel}</Label>
          <select
            id="school_id"
            value={schoolId}
            onChange={(event) => onSchoolChange(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            required
          >
            <option value="">Select school</option>
            {schools.map((school) => (
              <option key={school.id} value={school.id}>
                {school.code} - {school.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {assignmentType === "center" ? (
        <div className="space-y-2">
          <Label htmlFor="center_id">{centerLabel}</Label>
          <select
            id="center_id"
            value={centerId}
            onChange={(event) => onCenterChange(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            required
          >
            <option value="">Select centre</option>
            {centers.map((center) => (
              <option key={center.id} value={center.id}>
                {center.code} - {center.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
    </>
  )
}

type SpecialOwnerFieldsProps = {
  role: AdminCreateAccountRole
  assignmentType: AccountForm["assignment_type"]
  schoolId: string
  centerId: string
  unitId: string
  departmentId: string
  schools: AcademicUnit[]
  centers: AcademicUnit[]
  units: AcademicUnit[]
  departments: AcademicUnit[]
  onAssignmentTypeChange: (value: AccountForm["assignment_type"]) => void
  onSchoolChange: (value: string) => void
  onCenterChange: (value: string) => void
  onUnitChange: (value: string) => void
  onDepartmentChange: (value: string) => void
}

function SpecialOwnerFields({
  role,
  assignmentType,
  schoolId,
  centerId,
  unitId,
  departmentId,
  schools,
  centers,
  units,
  departments,
  onAssignmentTypeChange,
  onSchoolChange,
  onCenterChange,
  onUnitChange,
  onDepartmentChange,
}: SpecialOwnerFieldsProps) {
  const scopedUnits = units.filter((unit) =>
    assignmentType === "school"
      ? String(unit.school ?? "") === schoolId
      : assignmentType === "center"
        ? String(unit.center ?? "") === centerId
        : false
  )

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="owner_assignment_type">Owner Scope</Label>
        <select
          id="owner_assignment_type"
          value={assignmentType}
          onChange={(event) =>
            onAssignmentTypeChange(
              event.target.value as AccountForm["assignment_type"]
            )
          }
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">Use configured default</option>
          <option value="school">School</option>
          <option value="center">Center</option>
        </select>
      </div>
      {assignmentType === "school" ? (
        <div className="space-y-2">
          <Label htmlFor="owner_school_id">Owner School</Label>
          <select
            id="owner_school_id"
            value={schoolId}
            onChange={(event) => onSchoolChange(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select school</option>
            {schools.map((school) => (
              <option key={school.id} value={school.id}>
                {school.code} - {school.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {assignmentType === "center" ? (
        <div className="space-y-2">
          <Label htmlFor="owner_center_id">Owner Center</Label>
          <select
            id="owner_center_id"
            value={centerId}
            onChange={(event) => onCenterChange(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Select center</option>
            {centers.map((center) => (
              <option key={center.id} value={center.id}>
                {center.code} - {center.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {assignmentType ? (
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="owner_unit_id">Owner Unit</Label>
          <select
            id="owner_unit_id"
            value={unitId}
            onChange={(event) => onUnitChange(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">No specific unit</option>
            {scopedUnits.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.code} - {unit.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {role === "technician" ? (
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="department_id">Service Department</Label>
          <select
            id="department_id"
            value={departmentId}
            onChange={(event) => onDepartmentChange(event.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Use owner unit or configured default</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.code} - {department.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}
    </>
  )
}

export function AdminCreateAccountPage({
  accountRole,
}: {
  accountRole?: AdminCreateAccountRole
}) {
  const [form, setForm] = useState<AccountForm>(emptyForm)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const importInputRef = useRef<HTMLInputElement>(null)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importError, setImportError] = useState("")
  const [importSuccess, setImportSuccess] = useState("")
  const [importResults, setImportResults] = useState<ImportAccountResult[]>([])
  const [isImporting, setIsImporting] = useState(false)
  const [schools, setSchools] = useState<AcademicUnit[]>([])
  const [centers, setCenters] = useState<AcademicUnit[]>([])
  const [units, setUnits] = useState<AcademicUnit[]>([])
  const [departments, setDepartments] = useState<AcademicUnit[]>([])
  const [programs, setPrograms] = useState<ProgramOption[]>([])
  const [teacherAssignments, setTeacherAssignments] = useState<
    TeacherAssignmentForm[]
  >([{ ...emptyTeacherAssignment }])
  const config = accountRole ? roleConfig[accountRole] : null
  const visibleImportResults = importResults.slice(0, 8)
  const activeRoleImportColumns = accountRole
    ? roleImportColumns[accountRole]
    : []
  const activeRoleImportNotes = accountRole ? roleImportNotes[accountRole] : []

  useEffect(() => {
    if (accountRole === "executive") {
      async function loadExecutiveUnits() {
        try {
          const response = await apiFetch<ScopedAccountConfigResponse>(
            "/admin/create-account/executive"
          )
          setSchools(response.schools ?? [])
          setCenters(response.centers ?? [])
          setUnits(response.units ?? [])
        } catch (caught) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load executive assignments."
          )
        }
      }

      loadExecutiveUnits()
    }

    if (accountRole === "student") {
      async function loadStudentConfig() {
        try {
          const response = await apiFetch<StudentAccountConfigResponse>(
            "/admin/create-account/student"
          )
          setSchools(response.schools ?? [])
          setCenters(response.centers ?? [])
          setPrograms(response.programs ?? [])
        } catch (caught) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load school and program data."
          )
        }
      }

      loadStudentConfig()
    }

    if (accountRole === "teacher") {
      async function loadTeacherConfig() {
        try {
          const response = await apiFetch<ScopedAccountConfigResponse>(
            "/admin/create-account/teacher"
          )
          setSchools(response.schools ?? [])
          setCenters(response.centers ?? [])
        } catch (caught) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load teacher assignments."
          )
        }
      }

      loadTeacherConfig()
    }

    if (accountRole && ownerScopedRoles.has(accountRole)) {
      async function loadOwnerConfig() {
        try {
          const response = await apiFetch<ScopedAccountConfigResponse>(
            `/admin/create-account/${accountRole}`
          )
          setSchools(response.schools ?? [])
          setCenters(response.centers ?? [])
          setUnits(response.units ?? [])
          setDepartments(response.departments ?? [])
        } catch (caught) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Unable to load role ownership options."
          )
        }
      }

      loadOwnerConfig()
    }
  }, [accountRole])

  function updateField(field: keyof AccountForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function updateTeacherAssignment(
    index: number,
    field: keyof TeacherAssignmentForm,
    value: string
  ) {
    setTeacherAssignments((current) =>
      current.map((assignment, assignmentIndex) => {
        if (assignmentIndex !== index) return assignment
        if (field === "assignment_type") {
          return {
            assignment_type: value as TeacherAssignmentForm["assignment_type"],
            school_id: value === "school" ? assignment.school_id : "",
            center_id: value === "center" ? assignment.center_id : "",
          }
        }
        return { ...assignment, [field]: value }
      })
    )
  }

  async function handleImportSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!accountRole) return

    setImportError("")
    setImportSuccess("")
    setImportResults([])
    if (!importFile) {
      setImportError("Choose a .csv or .xlsx file first.")
      return
    }
    setIsImporting(true)

    try {
      const body = new FormData()
      body.append("file", importFile)
      const response = await apiFetch<ImportAccountResponse>(
        `/admin/create-account/${accountRole}/import`,
        {
          method: "POST",
          body,
        }
      )
      setImportSuccess(
        response.message ??
          `Imported ${response.created_count} ${roleConfig[accountRole].label.toLowerCase()} accounts.`
      )
      setImportResults(response.results ?? [])
      setImportFile(null)
      if (importInputRef.current) {
        importInputRef.current.value = ""
      }
    } catch (caught) {
      setImportError(
        caught instanceof Error ? caught.message : "Unable to import accounts."
      )
    } finally {
      setIsImporting(false)
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!accountRole) return

    setError("")
    setSuccess("")
    if (form.password && form.password.length > MAX_PASSWORD_LENGTH) {
      setError(
        `Temporary password must be ${MAX_PASSWORD_LENGTH} characters or fewer.`
      )
      return
    }
    setIsSubmitting(true)

    try {
      const {
        assignment_type,
        school_id,
        center_id,
        unit_id,
        department_id,
        program_id,
        ...accountPayload
      } = form
      const usesScopedOwner =
        accountRole === "executive" ||
        accountRole === "student" ||
        ownerScopedRoles.has(accountRole)
      const response = await apiFetch<CreateAccountResponse>(
        `/admin/create-account/${accountRole}`,
        {
          method: "POST",
          body: JSON.stringify({
            ...accountPayload,
            school_id:
              usesScopedOwner && assignment_type === "school"
                ? Number(school_id)
                : null,
            center_id:
              usesScopedOwner && assignment_type === "center"
                ? Number(center_id)
                : null,
            unit_id:
              (accountRole === "executive" || ownerScopedRoles.has(accountRole)) && unit_id
                ? Number(unit_id)
                : null,
            department_id:
              accountRole === "technician" && department_id
                ? Number(department_id)
                : null,
            program_id:
              accountRole === "student" && program_id
                ? Number(program_id)
                : null,
            teacher_assignments:
              accountRole === "teacher"
                ? teacherAssignments.map((assignment) => ({
                    school_id:
                      assignment.assignment_type === "school"
                        ? Number(assignment.school_id)
                        : null,
                    center_id:
                      assignment.assignment_type === "center"
                        ? Number(assignment.center_id)
                        : null,
                  }))
                : undefined,
          }),
        }
      )
      setSuccess(
        response.message ??
          `${roleConfig[accountRole].label} account created successfully.`
      )
      setForm(emptyForm)
      setTeacherAssignments([{ ...emptyTeacherAssignment }])
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to create account."
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={breadcrumbs(accountRole)} />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <span className="inline-flex h-6 w-fit items-center rounded-full border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground">
              Admin Zone
            </span>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {config?.title ?? "Create Account"}
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                {config?.description ??
                  "Choose the account type before entering role-specific account details."}
              </p>
            </div>
          </div>
          {accountRole ? (
            <Button
              variant="outline"
              render={<Link href="/admin/create-account" />}
            >
              <ArrowLeft className="size-4" />
              Account Types
            </Button>
          ) : null}
        </section>

        {!accountRole ? <RolePicker /> : null}

        {config ? (
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
            <div className="space-y-4">
              <form
                className="rounded-lg border border-border bg-background p-5 shadow-sm"
                onSubmit={handleImportSubmit}
              >
                <div className="flex items-start gap-3">
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <FileSpreadsheet className="size-5" />
                  </span>
                  <div>
                    <h2 className="text-base font-semibold">
                      Import {config.label} Accounts
                    </h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Upload a .csv or .xlsx sheet to create multiple{" "}
                      {config.label.toLowerCase()} accounts.
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
                  <div className="space-y-2">
                    <Label htmlFor="account-import-file">Sheet File</Label>
                    <Input
                      ref={importInputRef}
                      id="account-import-file"
                      type="file"
                      accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                      onChange={(event) => {
                        setImportFile(event.target.files?.[0] ?? null)
                        setImportError("")
                        setImportSuccess("")
                        setImportResults([])
                      }}
                    />
                  </div>
                  <Button type="submit" disabled={isImporting}>
                    <Upload className="size-4" />
                    {isImporting ? "Importing..." : "Import"}
                  </Button>
                </div>

                {importError ? (
                  <div className="mt-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
                    <AlertCircle className="mt-0.5 size-4 shrink-0" />
                    <p>{importError}</p>
                  </div>
                ) : null}
                {importSuccess ? (
                  <div className="mt-4 flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
                    <p>{importSuccess}</p>
                  </div>
                ) : null}

                {importResults.length ? (
                  <div className="mt-4 rounded-lg border border-border bg-muted/20 p-3">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <ListChecks className="size-4 text-muted-foreground" />
                      Import Results
                    </div>
                    <div className="mt-3 space-y-2">
                      {visibleImportResults.map((result) => (
                        <div
                          key={`${result.row}-${result.status}-${result.username ?? result.detail ?? ""}`}
                          className="flex flex-col gap-1 rounded-md border border-border bg-background px-3 py-2 text-sm sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="min-w-0">
                            <span className="font-medium">
                              Row {result.row}
                            </span>
                            <span className="ml-2 text-muted-foreground">
                              {result.status === "created"
                                ? `${result.username ?? "Account"} created`
                                : (result.detail ?? "Needs attention")}
                            </span>
                          </div>
                          <span
                            className={
                              result.status === "created"
                                ? "w-fit rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700"
                                : "w-fit rounded-md bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
                            }
                          >
                            {result.status === "created" ? "Created" : "Error"}
                          </span>
                        </div>
                      ))}
                    </div>
                    {importResults.length > visibleImportResults.length ? (
                      <p className="mt-3 text-xs text-muted-foreground">
                        Showing {visibleImportResults.length} of{" "}
                        {importResults.length} rows.
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </form>

              <form
                className="rounded-lg border border-border bg-background p-5 shadow-sm"
                onSubmit={handleSubmit}
              >
                <div className="flex items-start gap-3">
                  <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                    <UserPlus className="size-5" />
                  </span>
                  <div>
                    <h2 className="text-base font-semibold">{config.title}</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      The created account will be assigned the{" "}
                      {config.label.toLowerCase()} role.
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      autoComplete="username"
                      value={form.username}
                      onChange={(event) =>
                        updateField("username", event.target.value)
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      value={form.email}
                      onChange={(event) =>
                        updateField("email", event.target.value)
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name</Label>
                    <Input
                      id="first_name"
                      autoComplete="given-name"
                      value={form.first_name}
                      onChange={(event) =>
                        updateField("first_name", event.target.value)
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name</Label>
                    <Input
                      id="last_name"
                      autoComplete="family-name"
                      value={form.last_name}
                      onChange={(event) =>
                        updateField("last_name", event.target.value)
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ums_id">{config.idLabel}</Label>
                    <Input
                      id="ums_id"
                      value={form.ums_id}
                      placeholder={config.idPlaceholder}
                      onChange={(event) =>
                        updateField("ums_id", event.target.value)
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone_number">Phone</Label>
                    <Input
                      id="phone_number"
                      autoComplete="tel"
                      value={form.phone_number}
                      onChange={(event) =>
                        updateField("phone_number", event.target.value)
                      }
                    />
                  </div>
                  {accountRole === "student" ? (
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="room">Hostel Room</Label>
                      <Input
                        id="room"
                        value={form.room}
                        placeholder="25D-02-14-C"
                        onChange={(event) =>
                          updateField("room", event.target.value)
                        }
                      />
                    </div>
                  ) : null}
                  {accountRole === "student" ? (
                    <>
                      <UnitScopeFields
                        assignmentType={form.assignment_type}
                        schoolId={form.school_id}
                        centerId={form.center_id}
                        schools={schools}
                        centers={centers}
                        onAssignmentTypeChange={(value) =>
                          setForm((current) => ({
                            ...current,
                            assignment_type: value,
                            school_id:
                              value === "school" ? current.school_id : "",
                            center_id:
                              value === "center" ? current.center_id : "",
                            program_id: "",
                          }))
                        }
                        onSchoolChange={(schoolId) =>
                          setForm((current) => ({
                            ...current,
                            school_id: schoolId,
                            program_id: "",
                          }))
                        }
                        onCenterChange={(centerId) =>
                          setForm((current) => ({
                            ...current,
                            center_id: centerId,
                            program_id: "",
                          }))
                        }
                      />
                      {form.assignment_type ? (
                        <div className="space-y-2 sm:col-span-2">
                          <Label htmlFor="program_id">Program</Label>
                          <select
                            id="program_id"
                            value={form.program_id}
                            onChange={(event) =>
                              updateField("program_id", event.target.value)
                            }
                            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          >
                            <option value="">Select program</option>
                            {programs
                              .filter((prog) =>
                                form.assignment_type === "school"
                                  ? prog.school === Number(form.school_id)
                                  : prog.center === Number(form.center_id)
                              )
                              .map((prog) => (
                                <option key={prog.id} value={prog.id}>
                                  {prog.code} - {prog.name}
                                </option>
                              ))}
                          </select>
                        </div>
                      ) : null}
                    </>
                  ) : null}
                  {accountRole === "teacher" ? (
                    <>
                      <div className="space-y-2 sm:col-span-2">
                        <Label htmlFor="designation">Designation</Label>
                        <Input
                          id="designation"
                          value={form.designation}
                          placeholder="Lecturer or Part-time Teacher"
                          onChange={(event) =>
                            updateField("designation", event.target.value)
                          }
                          list="teacher-designations"
                        />
                        <datalist id="teacher-designations">
                          <option value="Lecturer" />
                          <option value="Part-time Teacher" />
                        </datalist>
                      </div>
                      <div className="space-y-3 sm:col-span-2">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <Label>School or Centre Assignments</Label>
                            <p className="mt-1 text-xs text-muted-foreground">
                              The first assignment is the teacher&apos;s primary
                              scope.
                            </p>
                          </div>
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() =>
                              setTeacherAssignments((current) => [
                                ...current,
                                { ...emptyTeacherAssignment },
                              ])
                            }
                          >
                            Add Assignment
                          </Button>
                        </div>
                        {teacherAssignments.map((assignment, index) => (
                          <div
                            key={index}
                            className="grid gap-3 rounded-lg border border-border bg-muted/20 p-3 sm:grid-cols-[12rem_minmax(0,1fr)_auto]"
                          >
                            <select
                              value={assignment.assignment_type}
                              onChange={(event) =>
                                updateTeacherAssignment(
                                  index,
                                  "assignment_type",
                                  event.target.value
                                )
                              }
                              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                              required
                            >
                              <option value="">Select type</option>
                              <option value="school">School</option>
                              <option value="center">Centre</option>
                            </select>
                            {assignment.assignment_type === "school" ? (
                              <select
                                value={assignment.school_id}
                                onChange={(event) =>
                                  updateTeacherAssignment(
                                    index,
                                    "school_id",
                                    event.target.value
                                  )
                                }
                                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                required
                              >
                                <option value="">Select school</option>
                                {schools.map((school) => (
                                  <option key={school.id} value={school.id}>
                                    {school.code} - {school.name}
                                  </option>
                                ))}
                              </select>
                            ) : assignment.assignment_type === "center" ? (
                              <select
                                value={assignment.center_id}
                                onChange={(event) =>
                                  updateTeacherAssignment(
                                    index,
                                    "center_id",
                                    event.target.value
                                  )
                                }
                                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                required
                              >
                                <option value="">Select centre</option>
                                {centers.map((center) => (
                                  <option key={center.id} value={center.id}>
                                    {center.code} - {center.name}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <div />
                            )}
                            <Button
                              type="button"
                              variant="outline"
                              disabled={teacherAssignments.length === 1}
                              onClick={() =>
                                setTeacherAssignments((current) =>
                                  current.filter(
                                    (_, assignmentIndex) =>
                                      assignmentIndex !== index
                                  )
                                )
                              }
                            >
                              Remove
                            </Button>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : null}
                  {accountRole === "executive" ? (
                    <>
                      <UnitScopeFields
                        assignmentType={form.assignment_type}
                        schoolId={form.school_id}
                        centerId={form.center_id}
                        schools={schools}
                        centers={centers}
                        schoolLabel="Assigned School"
                        centerLabel="Assigned Centre"
                        onAssignmentTypeChange={(value) =>
                          setForm((current) => ({
                            ...current,
                            assignment_type: value,
                            school_id:
                              value === "school" ? current.school_id : "",
                            center_id:
                              value === "center" ? current.center_id : "",
                            unit_id: "",
                          }))
                        }
                        onSchoolChange={(schoolId) =>
                          updateField("school_id", schoolId)
                        }
                        onCenterChange={(centerId) =>
                          updateField("center_id", centerId)
                        }
                      />
                      {form.assignment_type ? (
                        <div className="space-y-2 sm:col-span-2">
                          <Label htmlFor="unit_id">Administrative Unit</Label>
                          <select
                            id="unit_id"
                            value={form.unit_id}
                            onChange={(event) =>
                              updateField("unit_id", event.target.value)
                            }
                            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            required
                          >
                            <option value="">Select unit</option>
                            {units
                              .filter((unit) =>
                                form.assignment_type === "school"
                                  ? String(unit.school ?? "") === form.school_id
                                  : String(unit.center ?? "") === form.center_id
                              )
                              .map((unit) => (
                                <option key={unit.id} value={unit.id}>
                                  {unit.code} - {unit.name}
                                </option>
                              ))}
                          </select>
                        </div>
                      ) : null}
                    </>
                  ) : null}
                  {accountRole && ownerScopedRoles.has(accountRole) ? (
                    <>
                      <div className="space-y-2 sm:col-span-2">
                        <Label htmlFor="designation">Designation</Label>
                        <Input
                          id="designation"
                          value={form.designation}
                          placeholder="Role title or position"
                          onChange={(event) =>
                            updateField("designation", event.target.value)
                          }
                        />
                      </div>
                      <SpecialOwnerFields
                        role={accountRole}
                        assignmentType={form.assignment_type}
                        schoolId={form.school_id}
                        centerId={form.center_id}
                        unitId={form.unit_id}
                        departmentId={form.department_id}
                        schools={schools}
                        centers={centers}
                        units={units}
                        departments={departments}
                        onAssignmentTypeChange={(value) =>
                          setForm((current) => ({
                            ...current,
                            assignment_type: value,
                            school_id:
                              value === "school" ? current.school_id : "",
                            center_id:
                              value === "center" ? current.center_id : "",
                            unit_id: "",
                          }))
                        }
                        onSchoolChange={(schoolId) =>
                          setForm((current) => ({
                            ...current,
                            school_id: schoolId,
                            unit_id: "",
                          }))
                        }
                        onCenterChange={(centerId) =>
                          setForm((current) => ({
                            ...current,
                            center_id: centerId,
                            unit_id: "",
                          }))
                        }
                        onUnitChange={(unitId) =>
                          updateField("unit_id", unitId)
                        }
                        onDepartmentChange={(departmentId) =>
                          updateField("department_id", departmentId)
                        }
                      />
                    </>
                  ) : null}
                  <div className="space-y-2 sm:col-span-2">
                    <Label htmlFor="password">Temporary Password</Label>
                    <Input
                      id="password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Optional"
                      value={form.password}
                      onChange={(event) =>
                        updateField("password", event.target.value)
                      }
                      maxLength={MAX_PASSWORD_LENGTH}
                    />
                    <p className="text-xs leading-5 text-muted-foreground">
                      Leave the temporary password blank to generate a random
                      8-character password.
                    </p>
                  </div>
                </div>

                {error ? (
                  <div className="mt-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
                    <AlertCircle className="mt-0.5 size-4 shrink-0" />
                    <p>{error}</p>
                  </div>
                ) : null}
                {success ? (
                  <div className="mt-4 flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
                    <p>{success}</p>
                  </div>
                ) : null}

                <div className="mt-5 flex justify-end">
                  <Button type="submit" disabled={isSubmitting}>
                    <UserPlus className="size-4" />
                    {isSubmitting ? "Creating..." : config.title}
                  </Button>
                </div>
              </form>
            </div>

            <aside className="space-y-4 text-sm">
              <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
                <h2 className="text-base font-semibold">Account Role</h2>
                <div className="mt-4 flex gap-3 text-muted-foreground">
                  <span className="rounded-lg border border-border bg-muted/50 p-2">
                    <config.icon className="size-5" />
                  </span>
                  <div>
                    <p className="font-medium text-foreground">
                      {config.label}
                    </p>
                    <p className="mt-1 leading-6">{config.description}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="size-4 text-muted-foreground" />
                  <h2 className="text-base font-semibold">
                    Sheet Import Guide
                  </h2>
                </div>

                <div className="mt-4 space-y-4">
                  <div>
                    <p className="font-medium">Accepted Files</p>
                    <ColumnList columns={[".csv", ".xlsx"]} />
                  </div>

                  <div>
                    <p className="font-medium">Required Columns</p>
                    <ColumnList columns={commonImportColumns} />
                  </div>

                  <div>
                    <p className="font-medium">Optional Columns</p>
                    <ColumnList columns={optionalImportColumns} />
                  </div>

                  {activeRoleImportColumns.length ? (
                    <div>
                      <p className="font-medium">{config.label} Columns</p>
                      <ColumnList columns={activeRoleImportColumns} />
                    </div>
                  ) : null}

                  <div className="space-y-2 text-xs leading-5 text-muted-foreground">
                    {activeRoleImportNotes.map((note) => (
                      <p key={note}>{note}</p>
                    ))}
                    <p>
                      Leave password blank to generate and email an 8-character
                      password.
                    </p>
                  </div>
                </div>
              </div>
            </aside>
          </section>
        ) : null}
      </main>
    </div>
  )
}
