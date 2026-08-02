"use client"

import { useEffect, useMemo, useState } from "react"
import { AlertCircle, CheckCircle2, Download, Loader2, Search, X } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  generateCatalogReport,
  loadReportCatalog,
  type AdminReportDefinition,
} from "@/lib/admin-reports"

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

export function AdminReportCategoryPage({
  group,
}: {
  group: "academic" | "operations"
}) {
  const [reports, setReports] = useState<AdminReportDefinition[]>([])
  const [selectedKey, setSelectedKey] = useState("")
  const [filters, setFilters] = useState({ q: "", status: "", date_from: "", date_to: "" })
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const title = group === "academic" ? "Academic Reports" : "Operations Reports"

  useEffect(() => {
    void loadReportCatalog()
      .then((data) => {
        const matching = data.reports.filter((report) => report.group === group)
        setReports(matching)
        setSelectedKey(matching[0]?.key ?? "")
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load reports."))
      .finally(() => setIsLoading(false))
  }, [group])

  const selected = useMemo(
    () => reports.find((report) => report.key === selectedKey) ?? null,
    [reports, selectedKey]
  )
  const appliedCount = Object.values(filters).filter(Boolean).length

  async function generate() {
    if (!selected) return
    setIsGenerating(true)
    setError("")
    setSuccess("")
    try {
      await generateCatalogReport(selected.key, filters)
      setSuccess(`${selected.name} generated and added to Export History.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to generate report.")
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/reports", title: "Reports" },
          { href: `/admin/reports/${group}`, title: group === "academic" ? "Academic" : "Operations" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Choose one related dataset, apply useful filters, and generate a stored XLSX workbook.
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

        {isLoading ? (
          <Loader2 className="size-7 animate-spin text-muted-foreground" />
        ) : (
          <section className="grid gap-4 xl:grid-cols-[20rem_minmax(0,1fr)]">
            <div className="space-y-3">
              {reports.map((report) => (
                <button
                  key={report.key}
                  type="button"
                  className="block w-full text-left"
                  onClick={() => {
                    setSelectedKey(report.key)
                    setFilters({ q: "", status: "", date_from: "", date_to: "" })
                    setSuccess("")
                  }}
                >
                  <Card className={`transition ${selectedKey === report.key ? "border-primary/60 bg-primary/5" : "hover:border-primary/30"}`}>
                    <CardHeader className="p-4">
                      <CardTitle className="text-sm">{report.name}</CardTitle>
                      <CardDescription className="leading-5">{report.description}</CardDescription>
                    </CardHeader>
                  </Card>
                </button>
              ))}
            </div>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <CardTitle>{selected?.name}</CardTitle>
                    <CardDescription className="mt-1">{selected?.description}</CardDescription>
                  </div>
                  {appliedCount ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setFilters({ q: "", status: "", date_from: "", date_to: "" })}
                    >
                      <X className="size-4" />
                      Clear {appliedCount}
                    </Button>
                  ) : null}
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2 sm:col-span-2">
                    <Label htmlFor="report-search">Search within report</Label>
                    <div className="relative">
                      <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
                      <Input
                        id="report-search"
                        className="pl-9"
                        placeholder="Name, code, course, venue, or other report text"
                        value={filters.q}
                        onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="report-date-from">From date</Label>
                    <Input
                      id="report-date-from"
                      type="date"
                      value={filters.date_from}
                      onChange={(event) => setFilters((current) => ({ ...current, date_from: event.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="report-date-to">To date</Label>
                    <Input
                      id="report-date-to"
                      type="date"
                      value={filters.date_to}
                      onChange={(event) => setFilters((current) => ({ ...current, date_to: event.target.value }))}
                    />
                  </div>
                  {selected?.statuses.length ? (
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="report-status">Status</Label>
                      <select
                        id="report-status"
                        className={selectClass}
                        value={filters.status}
                        onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
                      >
                        <option value="">All statuses</option>
                        {selected.statuses.map((status) => (
                          <option key={status} value={status}>
                            {status.replaceAll("_", " ")}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : null}
                </div>
                <div className="flex flex-col gap-3 rounded-lg border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-muted-foreground">
                    {appliedCount ? `${appliedCount} filters will be applied.` : "The full dataset will be exported."}
                  </p>
                  <Button onClick={() => void generate()} disabled={!selected || isGenerating}>
                    {isGenerating ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
                    Generate XLSX
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}
