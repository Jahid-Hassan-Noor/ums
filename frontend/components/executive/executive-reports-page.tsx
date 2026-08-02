"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { AlertCircle, CheckCircle2, Download, FileSpreadsheet, Loader2, Search, X } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  exportExecutiveReport,
  loadExecutiveReports,
  type ExecutiveReportKind,
  type ExecutiveReportsResponse,
} from "@/lib/executive-reports"

type FilterDefinition = {
  key: string
  label: string
  optionKey?: string
  placeholder?: string
  type?: "number"
}

const reportConfig: Record<
  ExecutiveReportKind,
  {
    title: string
    description: string
    dataKey: "students" | "teachers" | "results"
    filters: FilterDefinition[]
  }
> = {
  students: {
    title: "Students",
    description: "Export students belonging to your assigned school or centre.",
    dataKey: "students",
    filters: [
      { key: "q", label: "Search", placeholder: "Name, student ID, email" },
      { key: "program", label: "Programme", optionKey: "programs" },
      { key: "status", label: "Enrollment status", optionKey: "statuses" },
      { key: "current_year", label: "Current year", optionKey: "current_years" },
      { key: "intake", label: "Intake", optionKey: "intakes" },
      { key: "cohort", label: "Cohort", optionKey: "cohorts" },
    ],
  },
  teachers: {
    title: "Teachers",
    description: "Export teachers belonging to your assigned school or centre.",
    dataKey: "teachers",
    filters: [
      { key: "q", label: "Search", placeholder: "Name, staff ID, email" },
      { key: "designation", label: "Designation", optionKey: "designations" },
      { key: "academic_rank", label: "Academic rank", optionKey: "academic_ranks" },
      { key: "department", label: "Department", optionKey: "departments" },
      { key: "unit", label: "Unit", optionKey: "units" },
    ],
  },
  "final-results": {
    title: "Final Results",
    description: "Export published final results with GPA and CGPA filters.",
    dataKey: "results",
    filters: [
      { key: "q", label: "Search", placeholder: "Student, ID, course code" },
      { key: "program", label: "Programme", optionKey: "programs" },
      { key: "semester", label: "Semester", optionKey: "semesters" },
      { key: "intake", label: "Intake", optionKey: "intakes" },
      { key: "cohort", label: "Cohort", optionKey: "cohorts" },
      { key: "minimum_cgpa", label: "Minimum CGPA", type: "number" },
      { key: "maximum_cgpa", label: "Maximum CGPA", type: "number" },
    ],
  },
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

export function ExecutiveReportsPage() {
  const [data, setData] = useState<ExecutiveReportsResponse | null>(null)
  const [kind, setKind] = useState<ExecutiveReportKind>("students")
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const config = reportConfig[kind]

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError("")
    try {
      setData(await loadExecutiveReports())
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load executive reports.")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadData(), 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  const selectedData = data?.[config.dataKey]
  const appliedCount = useMemo(
    () => Object.values(filters).filter((value) => value !== "").length,
    [filters]
  )

  function selectReport(nextKind: ExecutiveReportKind) {
    setKind(nextKind)
    setFilters({})
    setSuccess("")
    setError("")
  }

  async function exportReport() {
    setIsExporting(true)
    setError("")
    setSuccess("")
    try {
      await exportExecutiveReport(kind, filters)
      setSuccess(`${config.title} report generated successfully.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to export report.")
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/reports", title: "Reports" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Reports</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              Export people and published final-result records within your assigned scope.
            </p>
          </div>
          {data?.scope ? (
            <div className="rounded-lg border bg-card px-4 py-3 text-sm shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Assigned {data.scope.kind}
              </p>
              <p className="mt-1 font-semibold">{data.scope.code} - {data.scope.name}</p>
            </div>
          ) : null}
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

        <section className="grid gap-3 md:grid-cols-3">
          {(Object.keys(reportConfig) as ExecutiveReportKind[]).map((reportKind) => {
            const report = reportConfig[reportKind]
            return (
              <button
                key={reportKind}
                type="button"
                className="text-left"
                onClick={() => selectReport(reportKind)}
              >
                <Card className={`h-full transition ${kind === reportKind ? "border-primary/60 bg-primary/5" : "hover:border-primary/30"}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <FileSpreadsheet className="size-5 text-primary" />
                      <span className="text-xs text-muted-foreground">
                        {data?.[report.dataKey].count ?? 0} records
                      </span>
                    </div>
                    <CardTitle className="pt-2 text-base">{report.title}</CardTitle>
                    <CardDescription className="leading-5">{report.description}</CardDescription>
                  </CardHeader>
                </Card>
              </button>
            )
          })}
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <CardTitle>{config.title} Export</CardTitle>
                <CardDescription className="mt-1">{config.description}</CardDescription>
              </div>
              {appliedCount ? (
                <Button variant="outline" size="sm" onClick={() => setFilters({})}>
                  <X className="size-4" />
                  Clear {appliedCount}
                </Button>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            {isLoading ? (
              <div className="flex h-40 items-center justify-center">
                <Loader2 className="size-7 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  {config.filters.map((filter) => (
                    <div key={filter.key} className="space-y-2">
                      <Label htmlFor={`executive-report-${filter.key}`}>{filter.label}</Label>
                      {filter.optionKey ? (
                        <select
                          id={`executive-report-${filter.key}`}
                          className={selectClass}
                          value={filters[filter.key] ?? ""}
                          onChange={(event) =>
                            setFilters((current) => ({ ...current, [filter.key]: event.target.value }))
                          }
                        >
                          <option value="">All</option>
                          {(selectedData?.filters[filter.optionKey] ?? []).map((option) => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                          ))}
                        </select>
                      ) : (
                        <div className="relative">
                          {filter.key === "q" ? (
                            <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
                          ) : null}
                          <Input
                            id={`executive-report-${filter.key}`}
                            className={filter.key === "q" ? "pl-9" : ""}
                            type={filter.type ?? "text"}
                            min={filter.type === "number" ? "0" : undefined}
                            max={filter.type === "number" ? "4" : undefined}
                            step={filter.type === "number" ? "0.01" : undefined}
                            placeholder={filter.placeholder}
                            value={filters[filter.key] ?? ""}
                            onChange={(event) =>
                              setFilters((current) => ({ ...current, [filter.key]: event.target.value }))
                            }
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="flex flex-col gap-3 rounded-lg border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-sm">
                    <p className="font-medium">{selectedData?.count ?? 0} scoped records available</p>
                    <p className="text-xs text-muted-foreground">
                      {appliedCount ? `${appliedCount} filters will be applied.` : "The complete scoped report will be exported."}
                    </p>
                  </div>
                  <Button onClick={() => void exportReport()} disabled={isExporting || isLoading}>
                    {isExporting ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
                    Export Filtered XLSX
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
