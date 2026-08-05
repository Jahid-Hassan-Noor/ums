"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { CheckCircle2, Loader2, RefreshCw, Save, XCircle } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch } from "@/lib/auth"
import { DEFAULT_UMS_PUBLIC_SETTINGS, formatUmsMoney, type UmsPublicSettings } from "@/lib/ums-settings"

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
  requested_by: { name: string; role: string } | null
  reviewed_by: { name: string; role: string } | null
  reviewed_at: string | null
  review_note: string
  created_at: string
}

type ResponseData = {
  requests: CompensationRequest[]
  summary: {
    pending: number
    approved: number
    rejected: number
  }
}

function statusLabel(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function money(value: string, settings: UmsPublicSettings, currency?: string) {
  return formatUmsMoney(value, settings, currency)
}

function formatDate(value: string | null, locale = DEFAULT_UMS_PUBLIC_SETTINGS.localization.locale) {
  if (!value) return "Not set"
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(value))
}

export function AccountantCompensationRequestsPage() {
  const settings = usePublicUmsSettings()
  const [data, setData] = useState<ResponseData | null>(null)
  const [filter, setFilter] = useState("")
  const [notes, setNotes] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const response = await apiFetch<ResponseData>("/finance/hr-compensation-requests")
    setData(response)
  }, [])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load compensation requests."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  const requests = useMemo(() => {
    const rows = data?.requests ?? []
    return filter ? rows.filter((item) => item.status === filter) : rows
  }, [data, filter])

  async function reviewRequest(item: CompensationRequest, status: "approved" | "rejected") {
    setSavingId(item.id)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string }>("/finance/hr-compensation-requests", {
        method: "PATCH",
        body: JSON.stringify({
          request_id: item.id,
          status,
          review_note: notes[item.id] ?? "",
        }),
      })
      setSuccess(response.message)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to review compensation request.")
    } finally {
      setSavingId(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/compensation-requests", title: "Compensation Requests" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Compensation Requests</h1>
            <p className="mt-2 text-sm text-muted-foreground">Approve or reject HR-submitted salary and bonus changes before they affect employee records.</p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>{loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh</Button>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {loading ? <Loader2 className="size-6 animate-spin text-muted-foreground" /> : null}
        {data ? (
          <>
            <section className="grid gap-4 md:grid-cols-3">
              <StatCard label="Pending" value={data.summary.pending} />
              <StatCard label="Approved" value={data.summary.approved} />
              <StatCard label="Rejected" value={data.summary.rejected} />
            </section>

            <Card>
              <CardContent className="flex flex-wrap gap-2 p-4">
                {[
                  ["", "All"],
                  ["pending", "Pending"],
                  ["approved", "Approved"],
                  ["rejected", "Rejected"],
                ].map(([value, label]) => (
                  <Button key={value || "all"} type="button" variant={filter === value ? "default" : "outline"} onClick={() => setFilter(value)}>
                    {label}
                  </Button>
                ))}
              </CardContent>
            </Card>

            <section className="grid gap-4">
              {requests.map((item) => (
                <Card key={item.id}>
                  <CardContent className="space-y-4 p-4">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">{item.request_type_label}</span>
                          <span className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">{item.change_type_label}</span>
                          <span className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">{item.status_label}</span>
                        </div>
                        <h2 className="mt-3 text-base font-semibold">{item.employee.name}</h2>
                        <p className="mt-1 text-sm text-muted-foreground">{item.employee.employee_no} - {statusLabel(item.employee.role)} - {item.employee.position || "No position"}</p>
                      </div>
                      <div className="text-left lg:text-right">
                        <p className="text-lg font-semibold">{money(item.previous_amount, settings, item.employee.currency)} to {money(item.requested_amount, settings, item.employee.currency)}</p>
                        <p className="text-xs text-muted-foreground">Effective {formatDate(item.effective_date, settings.localization.locale)}</p>
                      </div>
                    </div>
                    <div className="grid gap-3 text-sm md:grid-cols-3">
                      <InfoItem label="Amount" value={money(item.amount, settings, item.employee.currency)} />
                      <InfoItem label="Requested By" value={item.requested_by?.name ?? "HR"} />
                      <InfoItem label="Submitted" value={formatDate(item.created_at, settings.localization.locale)} />
                    </div>
                    {item.reason ? <p className="rounded-md bg-muted/60 p-3 text-sm text-muted-foreground">{item.reason}</p> : null}
                    {item.status === "pending" ? (
                      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
                        <Textarea placeholder="Review note" value={notes[item.id] ?? ""} onChange={(event) => setNotes((current) => ({ ...current, [item.id]: event.target.value }))} />
                        <div className="flex flex-wrap gap-2">
                          <Button disabled={savingId === item.id} onClick={() => void reviewRequest(item, "approved")}>{savingId === item.id ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Approve</Button>
                          <Button variant="destructive" disabled={savingId === item.id} onClick={() => void reviewRequest(item, "rejected")}><XCircle className="size-4" /> Reject</Button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">Reviewed by {item.reviewed_by?.name ?? "Accountant"} on {formatDate(item.reviewed_at, settings.localization.locale)}{item.review_note ? ` - ${item.review_note}` : ""}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
              {requests.length === 0 ? <p className="rounded-lg border border-border bg-background p-4 text-sm text-muted-foreground">No compensation requests match this filter.</p> : null}
            </section>
          </>
        ) : null}
      </main>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  )
}

function InfoItem({ label, value }: { label: string; value: string | number }) {
  return (
    <p>
      <span className="text-muted-foreground">{label}</span>
      <br />
      {value}
    </p>
  )
}
