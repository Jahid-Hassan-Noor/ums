"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Loader2, Plus, RefreshCw, Save, Search, ShieldAlert, ChevronLeft, ChevronRight } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import { HoldStatusBadge } from "@/components/accountant/ledger/ledger-badges"
import { LedgerNav } from "@/components/accountant/ledger/ledger-nav"

type Hold = { id: number; student: { id: number; name: string; email: string; identifier: string }; reason: string; notes: string; is_active: boolean; placed_at: string; released_at: string | null }
type HoldsPage = { holds: Hold[]; total: number; page: number; page_size: number; total_pages: number }
type StudentRef = { id: number; name: string; email: string; identifier: string }

function formatDate(value: string | null) { return value ? new Date(value).toLocaleDateString() : "—" }

export function AccountantLedgerHoldsPage() {
  const [holdsData, setHoldsData] = useState<HoldsPage | null>(null)
  const [studentOptions, setStudentOptions] = useState<StudentRef[]>([])
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState<string>("active")
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [holdForm, setHoldForm] = useState({ student_id: "", reason: "", notes: "" })

  const loadData = useCallback(async () => {
    const params = new URLSearchParams({ page: String(page), page_size: "20" })
    if (filter) params.set("active", filter === "active" ? "true" : filter === "released" ? "false" : "true")
    if (search) params.set("q", search)
    const [holdsResult, studsResult] = await Promise.all([
      apiFetch<HoldsPage>(`/finance/holds?${params.toString()}`),
      apiFetch<{ students: StudentRef[] }>("/finance/students"),
    ])
    setHoldsData(holdsResult)
    setStudentOptions(studsResult.students ?? [])
  }, [page, filter, search])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load holds."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => { void refresh() }, [refresh])

  async function releaseHold(holdId: number) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/holds", { method: "PATCH", body: JSON.stringify({ hold_id: holdId }) })
      setSuccess("Hold released.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to release hold.")
    } finally {
      setSaving(false)
    }
  }

  async function saveHold(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/holds", {
        method: "POST",
        body: JSON.stringify({ ...holdForm, student_id: Number(holdForm.student_id) }),
      })
      setHoldForm({ student_id: "", reason: "", notes: "" })
      setSuccess("Finance hold placed.")
      setShowForm(false)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to place hold.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/ledger/holds", title: "Finance Holds" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <LedgerNav />
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <ShieldAlert className="size-6" /> Finance Holds
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">View and manage finance holds on student accounts.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" disabled={loading} onClick={refresh}>
              {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
            </Button>
            <Button onClick={() => setShowForm(!showForm)}>
              <Plus className="size-4" /> Place Hold
            </Button>
          </div>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {showForm ? (
          <Card>
            <CardHeader><CardTitle>Place Finance Hold</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={(e) => void saveHold(e)} className="grid gap-3 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label>Student</Label>
                  <select value={holdForm.student_id} onChange={(e) => setHoldForm((f) => ({ ...f, student_id: e.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required>
                    <option value="">Select student</option>
                    {studentOptions.map((s) => <option key={s.id} value={s.id}>{s.name} - {s.identifier}</option>)}
                  </select>
                </div>
                <div className="space-y-2"><Label>Reason</Label><Input value={holdForm.reason} onChange={(e) => setHoldForm((f) => ({ ...f, reason: e.target.value }))} required /></div>
                <div className="space-y-2"><Label>Notes</Label><Input value={holdForm.notes} onChange={(e) => setHoldForm((f) => ({ ...f, notes: e.target.value }))} /></div>
                <div className="sm:col-span-3 flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
                  <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Place Hold</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <form onSubmit={(e) => { e.preventDefault(); setPage(1); refresh() }} className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search by student or reason..." className="pl-9 w-72" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <Button type="submit" variant="outline" size="sm">Search</Button>
          </form>
          <select value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1) }} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
            <option value="">All Holds</option>
            <option value="active">Active Only</option>
            <option value="released">Released Only</option>
          </select>
        </div>

        <Card>
          <CardHeader>
            <CardDescription>Holds</CardDescription>
            <CardTitle>{holdsData?.total ?? 0} holds</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {holdsData?.holds.map((hold) => (
              <div key={hold.id} className="rounded-md border border-border p-3 text-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{hold.student.name}</p>
                    <p className="text-xs text-muted-foreground">{hold.student.identifier} · {hold.student.email}</p>
                  </div>
                  <HoldStatusBadge isActive={hold.is_active} />
                </div>
                <p className="mt-2 font-medium">{hold.reason}</p>
                {hold.notes ? <p className="mt-1 text-muted-foreground">{hold.notes}</p> : null}
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Placed: {formatDate(hold.placed_at)}</span>
                  {hold.released_at ? <span>Released: {formatDate(hold.released_at)}</span> : null}
                </div>
                {hold.is_active ? (
                  <Button variant="destructive" size="sm" className="mt-2" disabled={saving} onClick={() => void releaseHold(hold.id)}>
                    Release Hold
                  </Button>
                ) : null}
              </div>
            ))}
            {(!holdsData || holdsData.holds.length === 0) ? <p className="py-8 text-center text-sm text-muted-foreground">No holds found.</p> : null}
          </CardContent>
          {holdsData && holdsData.total_pages > 1 ? (
            <div className="flex items-center justify-between border-t border-border px-4 py-3">
              <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft className="size-4" /> Previous</Button>
              <span className="text-xs text-muted-foreground">Page {holdsData.page} of {holdsData.total_pages}</span>
              <Button variant="ghost" size="sm" disabled={page >= holdsData.total_pages} onClick={() => setPage((p) => p + 1)}>Next <ChevronRight className="size-4" /></Button>
            </div>
          ) : null}
        </Card>
      </main>
    </div>
  )
}
