"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, CheckCircle2, Download, Loader2, RefreshCw, Search, X } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import {
  downloadBlob,
  fetchAdminDirectoryExport,
  type AdminDirectoryKind,
  type AdminDirectoryOption,
} from "@/lib/admin-directory"

type FilterDefinition = {
  key: string
  label: string
  optionKey?: string
  placeholder?: string
}

const reportConfig: Record<
  AdminDirectoryKind,
  { label: string; description: string; filters: FilterDefinition[] }
> = {
  students: {
    label: "Students XLSX",
    description: "Filter students by identity, intake, session, status, school, and programme.",
    filters: [
      { key: "q", label: "Search", placeholder: "Name, student ID, email" },
      { key: "country", label: "Country / nationality", optionKey: "countries" },
      { key: "intake", label: "Intake", optionKey: "intakes" },
      { key: "session", label: "Session", optionKey: "sessions" },
      { key: "status", label: "Student status", optionKey: "statuses" },
      { key: "school", label: "School", optionKey: "schools" },
      { key: "program", label: "Programme", optionKey: "programs" },
    ],
  },
  teachers: {
    label: "Teachers XLSX",
    description: "Filter teachers by organisation placement and designation.",
    filters: [
      { key: "q", label: "Search", placeholder: "Name, staff ID, email" },
      { key: "school", label: "School", optionKey: "schools" },
      { key: "center", label: "Centre", optionKey: "centers" },
      { key: "unit", label: "Unit", optionKey: "units" },
      { key: "department", label: "Department", optionKey: "departments" },
      { key: "designation", label: "Designation", optionKey: "designations" },
    ],
  },
  executives: {
    label: "Executives XLSX",
    description: "Filter executives by assigned organisation and designation.",
    filters: [
      { key: "q", label: "Search", placeholder: "Name, staff ID, email" },
      { key: "school", label: "School", optionKey: "schools" },
      { key: "center", label: "Centre", optionKey: "centers" },
      { key: "unit", label: "Unit", optionKey: "units" },
      { key: "department", label: "Department", optionKey: "departments" },
      { key: "designation", label: "Designation", optionKey: "designations" },
    ],
  },
  applicants: {
    label: "Applicants XLSX",
    description: "Filter applicants by origin, account state, intake, and application status.",
    filters: [
      { key: "q", label: "Search", placeholder: "Name, email, application number" },
      { key: "nationality", label: "Nationality", optionKey: "nationalities" },
      { key: "country", label: "Country of residence", optionKey: "countries" },
      { key: "account_status", label: "Account status", optionKey: "account_statuses" },
      { key: "intake", label: "Latest intake", optionKey: "intakes" },
      {
        key: "application_status",
        label: "Application status",
        optionKey: "application_statuses",
      },
    ],
  },
}

type PeopleResponse = {
  summary?: { total?: number; active?: number }
  filters?: Record<string, AdminDirectoryOption[]>
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

export function AdminPeopleReportsPage() {
  const [kind, setKind] = useState<AdminDirectoryKind>("students")
  const [options, setOptions] = useState<Record<string, AdminDirectoryOption[]>>({})
  const [summary, setSummary] = useState({ total: 0, active: 0 })
  const [filters, setFilters] = useState<Record<string, string>>({ sort: "asc" })
  const [isLoading, setIsLoading] = useState(true)
  const [isExporting, setIsExporting] = useState<"all" | "filtered" | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const config = reportConfig[kind]

  const loadOptions = useCallback(async (selectedKind: AdminDirectoryKind) => {
    setIsLoading(true)
    setError("")
    try {
      const data = await apiFetch<PeopleResponse>(`/admin/manage/${selectedKind}`)
      setOptions(data.filters ?? {})
      setSummary({
        total: data.summary?.total ?? 0,
        active: data.summary?.active ?? 0,
      })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load report options.")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadOptions(kind)
    }, 0)
    return () => window.clearTimeout(timer)
  }, [kind, loadOptions])

  const appliedCount = useMemo(
    () => Object.entries(filters).filter(([key, value]) => key !== "sort" && value).length,
    [filters]
  )

  function selectReport(nextKind: AdminDirectoryKind) {
    setKind(nextKind)
    setFilters({ sort: "asc" })
    setSuccess("")
  }

  async function exportReport(scope: "all" | "filtered") {
    setIsExporting(scope)
    setError("")
    setSuccess("")
    try {
      const exportFilters = scope === "filtered" ? filters : { sort: filters.sort }
      const { blob, filename } = await fetchAdminDirectoryExport(kind, exportFilters)
      downloadBlob(blob, filename)
      setSuccess(`${config.label} generated and added to Export History.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to generate report.")
    } finally {
      setIsExporting(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/reports", title: "Reports" },
          { href: "/admin/reports/people", title: "People" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">People Reports</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Generate filtered XLSX directories for portal people and applicant accounts.
          </p>
        </section>

        {error ? (
          <p className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </p>
        ) : null}
        {success ? (
          <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="size-4 shrink-0" /> {success}
          </p>
        ) : null}

        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {(Object.keys(reportConfig) as AdminDirectoryKind[]).map((item) => (
            <button key={item} type="button" className="text-left" onClick={() => selectReport(item)}>
              <Card className={`h-full transition ${kind === item ? "border-primary/60 bg-primary/5" : "hover:border-primary/30"}`}>
                <CardHeader>
                  <CardTitle className="text-base">{reportConfig[item].label}</CardTitle>
                  <CardDescription className="leading-5">{reportConfig[item].description}</CardDescription>
                </CardHeader>
              </Card>
            </button>
          ))}
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <CardTitle>{config.label}</CardTitle>
                <CardDescription className="mt-1">{config.description}</CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" onClick={() => void loadOptions(kind)} disabled={isLoading}>
                  <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
                {appliedCount ? (
                  <Button variant="outline" onClick={() => setFilters({ sort: "asc" })}>
                    <X className="size-4" />
                    Clear {appliedCount}
                  </Button>
                ) : null}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            {isLoading ? (
              <div className="flex h-32 items-center justify-center">
                <Loader2 className="size-7 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  {config.filters.map((filter) => (
                    <div key={filter.key} className="space-y-2">
                      <Label htmlFor={`people-${filter.key}`}>{filter.label}</Label>
                      {filter.optionKey ? (
                        <select
                          id={`people-${filter.key}`}
                          className={selectClass}
                          value={filters[filter.key] ?? ""}
                          onChange={(event) =>
                            setFilters((current) => ({
                              ...current,
                              [filter.key]: event.target.value,
                            }))
                          }
                        >
                          <option value="">All</option>
                          {(options[filter.optionKey] ?? []).map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <div className="relative">
                          <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
                          <Input
                            id={`people-${filter.key}`}
                            className="pl-9"
                            placeholder={filter.placeholder}
                            value={filters[filter.key] ?? ""}
                            onChange={(event) =>
                              setFilters((current) => ({
                                ...current,
                                [filter.key]: event.target.value,
                              }))
                            }
                          />
                        </div>
                      )}
                    </div>
                  ))}
                  <div className="space-y-2">
                    <Label htmlFor="people-sort">Name order</Label>
                    <select
                      id="people-sort"
                      className={selectClass}
                      value={filters.sort ?? "asc"}
                      onChange={(event) =>
                        setFilters((current) => ({ ...current, sort: event.target.value }))
                      }
                    >
                      <option value="asc">A to Z</option>
                      <option value="desc">Z to A</option>
                    </select>
                  </div>
                </div>
                <div className="flex flex-col gap-3 rounded-lg border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-sm">
                    <p className="font-medium">{summary.total} available records</p>
                    <p className="text-xs text-muted-foreground">
                      {appliedCount ? `${appliedCount} filters will be applied.` : "No filters applied."}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={() => void exportReport("all")}
                      disabled={isExporting !== null}
                    >
                      {isExporting === "all" ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
                      Export All
                    </Button>
                    <Button
                      onClick={() => void exportReport("filtered")}
                      disabled={isExporting !== null}
                    >
                      {isExporting === "filtered" ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
                      Export Filtered XLSX
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
