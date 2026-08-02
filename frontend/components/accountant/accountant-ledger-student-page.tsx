"use client"

import { useCallback, useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, CheckCircle2, Loader2, RefreshCw, Save, WalletCards, ShieldAlert, CreditCard } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import { LedgerEntryBadge, ChargeStatusBadge, HoldStatusBadge } from "@/components/accountant/ledger/ledger-badges"
import { ExportMenu } from "@/components/accountant/ledger/export-menu"
import { RecordPaymentModal } from "@/components/accountant/ledger/record-payment-modal"

type StudentRef = { id: number; name: string; email: string; identifier: string }
type Category = { id: number; code: string; name: string; description: string; is_active: boolean }
type Charge = { id: number; category: Category; description: string; amount: string; due_date: string | null; status: string; created_at: string }
type LedgerEntry = { id: number; entry_type: string; amount: string; description: string; balance_after: string; posted_at: string; posted_by: string }
type Hold = { id: number; reason: string; notes: string; is_active: boolean; placed_at: string; released_at: string | null }
type StudentSummary = { student: StudentRef; balance: string; currency: string; active_holds: Hold[]; charges: Charge[]; ledger_entries: LedgerEntry[] }

type PaginatedEntries = { entries: LedgerEntry[]; total: number; page: number; page_size: number; total_pages: number }
type PaginatedCharges = { charges: Charge[]; total: number; page: number; page_size: number; total_pages: number }

function money(value: string) { return `RM ${Number(value || 0).toFixed(2)}` }
function formatDate(value: string | null) { return value ? new Date(value).toLocaleDateString() : "—" }
function label(value: string) { return value.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()) }

type Tab = "charges" | "entries" | "holds"

export function AccountantLedgerStudentPage() {
  const params = useParams()
  const router = useRouter()
  const studentId = params.studentId as string

  const [summary, setSummary] = useState<StudentSummary | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [tab, setTab] = useState<Tab>("charges")
  const [entriesData, setEntriesData] = useState<PaginatedEntries | null>(null)
  const [chargesData, setChargesData] = useState<PaginatedCharges | null>(null)
  const [entriesPage, setEntriesPage] = useState(1)
  const [chargesPage, setChargesPage] = useState(1)
  const [chargeFilter, setChargeFilter] = useState("")
  const [entryFilter, setEntryFilter] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showPayment, setShowPayment] = useState(false)

  const [chargeForm, setChargeForm] = useState({ category_id: "", description: "", amount: "", due_date: "" })
  const [holdForm, setHoldForm] = useState({ reason: "", notes: "" })

  const loadSummary = useCallback(async () => {
    const data = await apiFetch<StudentSummary>(`/finance/student-ledgers?student_id=${studentId}`)
    setSummary(data)
  }, [studentId])

  const loadEntries = useCallback(async () => {
    const params = new URLSearchParams({ page: String(entriesPage), page_size: "15" })
    if (entryFilter) params.set("entry_type", entryFilter)
    const data = await apiFetch<PaginatedEntries>(`/finance/students/${studentId}/entries?${params.toString()}`)
    setEntriesData(data)
  }, [studentId, entriesPage, entryFilter])

  const loadCharges = useCallback(async () => {
    const params = new URLSearchParams({ page: String(chargesPage), page_size: "15" })
    if (chargeFilter) params.set("status", chargeFilter)
    const data = await apiFetch<PaginatedCharges>(`/finance/students/${studentId}/charges?${params.toString()}`)
    setChargesData(data)
  }, [studentId, chargesPage, chargeFilter])

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const catData = await apiFetch<{ categories: Category[] }>("/finance/fee-categories")
      setCategories(catData.categories ?? [])
      await loadSummary()
      await loadEntries()
      await loadCharges()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load student ledger.")
    } finally {
      setLoading(false)
    }
  }, [loadSummary, loadEntries, loadCharges])

  useEffect(() => { void loadAll() }, [loadAll])

  const loadEntriesFiltered = useCallback(async () => {
    if (loading) return
    const params = new URLSearchParams({ page: String(entriesPage), page_size: "15" })
    if (entryFilter) params.set("entry_type", entryFilter)
    const data = await apiFetch<PaginatedEntries>(`/finance/students/${studentId}/entries?${params.toString()}`)
    setEntriesData(data)
  }, [studentId, entriesPage, entryFilter, loading])

  const loadChargesFiltered = useCallback(async () => {
    if (loading) return
    const params = new URLSearchParams({ page: String(chargesPage), page_size: "15" })
    if (chargeFilter) params.set("status", chargeFilter)
    const data = await apiFetch<PaginatedCharges>(`/finance/students/${studentId}/charges?${params.toString()}`)
    setChargesData(data)
  }, [studentId, chargesPage, chargeFilter, loading])

  useEffect(() => { void loadEntriesFiltered() }, [loadEntriesFiltered])
  useEffect(() => { void loadChargesFiltered() }, [loadChargesFiltered])

  async function saveCharge(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/student-ledgers", {
        method: "POST",
        body: JSON.stringify({ ...chargeForm, student_id: Number(studentId), category_id: Number(chargeForm.category_id) }),
      })
      setChargeForm({ category_id: "", description: "", amount: "", due_date: "" })
      setSuccess("Charge posted.")
      await loadSummary()
      await loadCharges()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to post charge.")
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
        body: JSON.stringify({ student_id: Number(studentId), ...holdForm }),
      })
      setHoldForm({ reason: "", notes: "" })
      setSuccess("Finance hold placed.")
      await loadSummary()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to place hold.")
    } finally {
      setSaving(false)
    }
  }

  async function releaseHold(holdId: number) {
    setSaving(true)
    setError("")
    try {
      await apiFetch("/finance/holds", { method: "PATCH", body: JSON.stringify({ hold_id: holdId }) })
      setSuccess("Hold released.")
      await loadSummary()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to release hold.")
    } finally {
      setSaving(false)
    }
  }

  const activeCategories = categories.filter((c) => c.is_active)

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[
        { href: "/accountant", title: "Accountant" },
        { href: "/accountant/ledger", title: "Student Ledgers" },
        { href: `/accountant/ledger/${studentId}`, title: summary?.student.name ?? "Student" },
      ]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-5">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => router.push("/accountant/ledger")}>
              <ArrowLeft className="size-4" />
            </Button>
            <div>
              <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
                <WalletCards className="size-6" /> {summary?.student.name ?? "Loading..."}
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">{summary?.student.identifier} · {summary?.student.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ExportMenu studentId={Number(studentId)} />
            <Button variant="outline" size="sm" disabled={loading} onClick={() => void loadAll()}>
              {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
            </Button>
          </div>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {summary ? (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Card><CardHeader className="pb-2"><CardDescription>Current Balance</CardDescription><CardTitle className="text-2xl">{money(summary.balance)}</CardTitle></CardHeader></Card>
              <Card><CardHeader className="pb-2"><CardDescription>Active Holds</CardDescription><CardTitle className="text-2xl">{summary.active_holds.length}</CardTitle></CardHeader></Card>
              <Card><CardHeader className="pb-2"><CardDescription>Total Charges</CardDescription><CardTitle className="text-2xl">{summary.charges.length}</CardTitle></CardHeader></Card>
              <Card><CardHeader className="pb-2"><CardDescription>Ledger Entries</CardDescription><CardTitle className="text-2xl">{summary.ledger_entries.length}</CardTitle></CardHeader></Card>
            </section>

            <div className="flex gap-1 border-b border-border/70 pb-px">
              {(["charges", "entries", "holds"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                    tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t === "charges" && <CreditCard className="size-4" />}
                  {t === "entries" && <WalletCards className="size-4" />}
                  {t === "holds" && <ShieldAlert className="size-4" />}
                  {label(t)}
                </button>
              ))}
            </div>

            {tab === "charges" && (
              <div className="grid gap-4 xl:grid-cols-[1fr_22rem]">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div><CardDescription>Charges</CardDescription><CardTitle>{chargesData?.total ?? 0} total</CardTitle></div>
                    <select value={chargeFilter} onChange={(e) => { setChargeFilter(e.target.value); setChargesPage(1) }} className="rounded-md border border-input bg-background px-2 py-1 text-xs">
                      <option value="">All Status</option>
                      <option value="posted">Posted</option>
                      <option value="draft">Draft</option>
                      <option value="waived">Waived</option>
                      <option value="reversed">Reversed</option>
                    </select>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {chargesData?.charges.map((charge) => (
                      <div key={charge.id} className="rounded-md border border-border p-3 text-sm">
                        <div className="flex items-start justify-between">
                          <p className="font-medium">{charge.description}</p>
                          <ChargeStatusBadge status={charge.status} />
                        </div>
                        <p className="mt-1 text-muted-foreground">
                          {charge.category.code} · {money(charge.amount)} · Due: {formatDate(charge.due_date)}
                        </p>
                      </div>
                    ))}
                    {(!chargesData || chargesData.charges.length === 0) ? <p className="py-4 text-center text-sm text-muted-foreground">No charges found.</p> : null}
                  </CardContent>
                  {chargesData && chargesData.total_pages > 1 ? (
                    <div className="flex items-center justify-between border-t border-border px-4 py-3">
                      <Button variant="ghost" size="sm" disabled={chargesPage <= 1} onClick={() => setChargesPage((p) => p - 1)}>Previous</Button>
                      <span className="text-xs text-muted-foreground">Page {chargesData.page} of {chargesData.total_pages}</span>
                      <Button variant="ghost" size="sm" disabled={chargesPage >= chargesData.total_pages} onClick={() => setChargesPage((p) => p + 1)}>Next</Button>
                    </div>
                  ) : null}
                </Card>

                <div className="space-y-4">
                  <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={saveCharge}>
                    <h3 className="text-sm font-semibold">Post Charge</h3>
                    <div className="mt-3 grid gap-3">
                      <div className="space-y-2">
                        <Label>Category</Label>
                        <select value={chargeForm.category_id} onChange={(e) => setChargeForm((c) => ({ ...c, category_id: e.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required>
                          <option value="">Select</option>
                          {activeCategories.map((c) => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
                        </select>
                      </div>
                      <div className="space-y-2"><Label>Description</Label><Input value={chargeForm.description} onChange={(e) => setChargeForm((c) => ({ ...c, description: e.target.value }))} required /></div>
                      <div className="space-y-2"><Label>Amount (RM)</Label><Input type="number" min="0" step="0.01" value={chargeForm.amount} onChange={(e) => setChargeForm((c) => ({ ...c, amount: e.target.value }))} required /></div>
                      <div className="space-y-2"><Label>Due Date</Label><Input type="date" value={chargeForm.due_date} onChange={(e) => setChargeForm((c) => ({ ...c, due_date: e.target.value }))} /></div>
                      <Button type="submit" disabled={saving} size="sm">{saving ? <Loader2 className="size-3 animate-spin" /> : <Save className="size-3" />} Post</Button>
                    </div>
                  </form>
                  <Button variant="outline" className="w-full" onClick={() => setShowPayment(true)}>
                    <CreditCard className="size-4" /> Record Payment
                  </Button>
                </div>
              </div>
            )}

            {tab === "entries" && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div><CardDescription>Ledger Entries</CardDescription><CardTitle>{entriesData?.total ?? 0} total</CardTitle></div>
                  <select value={entryFilter} onChange={(e) => { setEntryFilter(e.target.value); setEntriesPage(1) }} className="rounded-md border border-input bg-background px-2 py-1 text-xs">
                    <option value="">All Types</option>
                    <option value="debit">Debit</option>
                    <option value="payment">Payment</option>
                    <option value="waiver">Waiver</option>
                    <option value="refund">Refund</option>
                    <option value="reversal">Reversal</option>
                    <option value="adjustment">Adjustment</option>
                  </select>
                </CardHeader>
                <CardContent className="space-y-2">
                  {entriesData?.entries.map((entry) => (
                    <div key={entry.id} className="rounded-md border border-border p-3 text-sm">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <LedgerEntryBadge type={entry.entry_type} />
                          <span className="font-medium">{money(entry.amount)}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">{formatDate(entry.posted_at)}</span>
                      </div>
                      <p className="mt-1 text-muted-foreground">{entry.description}</p>
                      <p className="mt-1 text-xs text-muted-foreground">Balance after: {money(entry.balance_after)} · Posted by: {entry.posted_by || "—"}</p>
                    </div>
                  ))}
                  {(!entriesData || entriesData.entries.length === 0) ? <p className="py-4 text-center text-sm text-muted-foreground">No entries found.</p> : null}
                </CardContent>
                {entriesData && entriesData.total_pages > 1 ? (
                  <div className="flex items-center justify-between border-t border-border px-4 py-3">
                    <Button variant="ghost" size="sm" disabled={entriesPage <= 1} onClick={() => setEntriesPage((p) => p - 1)}>Previous</Button>
                    <span className="text-xs text-muted-foreground">Page {entriesData.page} of {entriesData.total_pages}</span>
                    <Button variant="ghost" size="sm" disabled={entriesPage >= entriesData.total_pages} onClick={() => setEntriesPage((p) => p + 1)}>Next</Button>
                  </div>
                ) : null}
              </Card>
            )}

            {tab === "holds" && (
              <div className="grid gap-4 xl:grid-cols-[1fr_22rem]">
                <Card>
                  <CardHeader><CardDescription>Finance Holds</CardDescription><CardTitle>{summary.active_holds.length} active</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {summary.active_holds.map((hold) => (
                      <div key={hold.id} className="rounded-md border border-border p-3 text-sm">
                        <div className="flex items-start justify-between">
                          <p className="font-medium">{hold.reason}</p>
                          <HoldStatusBadge isActive={hold.is_active} />
                        </div>
                        {hold.notes ? <p className="mt-1 text-muted-foreground">{hold.notes}</p> : null}
                        <p className="mt-1 text-xs text-muted-foreground">Placed: {formatDate(hold.placed_at)}</p>
                        {hold.is_active ? (
                          <Button variant="destructive" size="sm" className="mt-2" disabled={saving} onClick={() => void releaseHold(hold.id)}>
                            Release Hold
                          </Button>
                        ) : null}
                      </div>
                    ))}
                    {summary.active_holds.length === 0 ? <p className="py-4 text-center text-sm text-muted-foreground">No active holds.</p> : null}
                  </CardContent>
                </Card>

                <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={saveHold}>
                  <h3 className="text-sm font-semibold">Place Hold</h3>
                  <div className="mt-3 grid gap-3">
                    <div className="space-y-2"><Label>Reason</Label><Input value={holdForm.reason} onChange={(e) => setHoldForm((h) => ({ ...h, reason: e.target.value }))} required /></div>
                    <div className="space-y-2"><Label>Notes</Label><Input value={holdForm.notes} onChange={(e) => setHoldForm((h) => ({ ...h, notes: e.target.value }))} /></div>
                    <Button type="submit" disabled={saving} size="sm">{saving ? <Loader2 className="size-3 animate-spin" /> : <ShieldAlert className="size-3" />} Place Hold</Button>
                  </div>
                </form>
              </div>
            )}
          </>
        ) : loading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="size-6 animate-spin text-muted-foreground" /></div>
        ) : null}
      </main>

      {summary ? (
        <RecordPaymentModal
          studentId={Number(studentId)}
          studentName={summary.student.name}
          open={showPayment}
          onClose={() => setShowPayment(false)}
          onSuccess={() => { void loadSummary(); void loadEntries() }}
        />
      ) : null}
    </div>
  )
}
