"use client"

import { useCallback, useEffect, useState } from "react"
import { AlertCircle, Download, Loader2, RefreshCw, Trash2 } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { formatDateTime } from "@/components/utils/format"
import {
  deleteStoredReport,
  downloadStoredReport,
  loadReportExports,
  type ReportExportsResponse,
} from "@/lib/admin-reports"

export function AdminReportExportsPage() {
  const [data, setData] = useState<ReportExportsResponse | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError("")
    try {
      setData(await loadReportExports())
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load export history.")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  async function download(id: number, filename: string) {
    setBusyId(id)
    setError("")
    try {
      await downloadStoredReport(id, filename)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to download export.")
    } finally {
      setBusyId(null)
    }
  }

  async function remove(id: number) {
    setBusyId(id)
    setError("")
    try {
      await deleteStoredReport(id)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete export.")
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/reports", title: "Reports" },
          { href: "/admin/reports/exports", title: "Export History" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Export History</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Review statuses, redownload completed workbooks, and remove old exports.
            </p>
          </div>
          <Button variant="outline" onClick={() => void loadData()} disabled={isLoading}>
            <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </section>

        {error ? (
          <p className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </p>
        ) : null}

        <section className="grid gap-3 sm:grid-cols-4">
          {[
            ["Total exports", data?.summary.total ?? 0],
            ["Processing", data?.summary.processing ?? 0],
            ["Completed", data?.summary.completed ?? 0],
            ["Failed", data?.summary.failed ?? 0],
          ].map(([label, value]) => (
            <Card key={label}>
              <CardHeader className="pb-2">
                <CardDescription>{label}</CardDescription>
                <CardTitle className="text-2xl">{value}</CardTitle>
              </CardHeader>
            </Card>
          ))}
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle>Generated Files</CardTitle>
            <CardDescription>Up to the latest 250 exports are shown.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex h-48 items-center justify-center">
                <Loader2 className="size-7 animate-spin text-muted-foreground" />
              </div>
            ) : data?.exports.length ? (
              <div className="overflow-x-auto rounded-lg border">
                <table className="w-full min-w-[850px] text-left text-sm">
                  <thead className="bg-muted/50 text-xs text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Report</th>
                      <th className="px-4 py-3 font-medium">Requested by</th>
                      <th className="px-4 py-3 font-medium">Filters</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Created</th>
                      <th className="px-4 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.exports.map((item) => (
                      <tr key={item.id} className="border-t">
                        <td className="px-4 py-3">
                          <p className="font-medium">{item.name}</p>
                          <p className="text-xs text-muted-foreground">{item.filename || item.export_type}</p>
                        </td>
                        <td className="px-4 py-3">{item.requested_by || "Unknown"}</td>
                        <td className="max-w-xs px-4 py-3 text-xs text-muted-foreground">
                          {Object.entries(item.filters)
                            .filter(([key]) => key !== "row_count")
                            .map(([key, value]) => `${key}: ${value}`)
                            .join(", ") || "None"}
                          <p>{item.filters.row_count ?? 0} rows</p>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={item.status === "completed" ? "default" : "outline"}>
                            {item.status}
                          </Badge>
                          {item.error_message ? <p className="mt-1 text-xs text-red-600">{item.error_message}</p> : null}
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">
                          {formatDateTime(item.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busyId === item.id || item.status !== "completed"}
                              onClick={() => void download(item.id, item.filename)}
                            >
                              {busyId === item.id ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
                              Download
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busyId === item.id}
                              onClick={() => void remove(item.id)}
                            >
                              <Trash2 className="size-4" />
                              Remove
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                No exports have been generated yet.
              </p>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
