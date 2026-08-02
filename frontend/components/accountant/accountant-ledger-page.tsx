"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { CheckCircle2, Loader2, RefreshCw, Save, ShieldAlert, WalletCards } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type StudentRef = {
  id: number
  name: string
  email: string
  identifier: string
}

type StudentRow = {
  student: StudentRef
  balance: string
  active_holds: number
}

type Category = {
  id: number
  code: string
  name: string
  description: string
  is_active: boolean
}

type Charge = {
  id: number
  category: Category
  description: string
  amount: string
  due_date: string | null
  status: string
  created_at: string
}

type LedgerEntry = {
  id: number
  entry_type: string
  amount: string
  description: string
  balance_after: string
  posted_at: string
  posted_by: string
}

type Hold = {
  id: number
  reason: string
  notes: string
  is_active: boolean
  placed_at: string
}

type StudentSummary = {
  student: StudentRef
  balance: string
  currency: string
  active_holds: Hold[]
  charges: Charge[]
  ledger_entries: LedgerEntry[]
}

type StudentOption = {
  id: number
  name: string
  email: string
  identifier: string
}

const emptyCharge = {
  student_id: "",
  category_id: "",
  description: "",
  amount: "",
  due_date: "",
}

const emptyCategory = {
  code: "",
  name: "",
}

const emptyHold = {
  student_id: "",
  reason: "",
  notes: "",
}

function money(value: string) {
  return `RM ${Number(value || 0).toFixed(2)}`
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : "Not set"
}

function label(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function AccountantLedgerPage() {
  const [students, setStudents] = useState<StudentRow[]>([])
  const [studentOptions, setStudentOptions] = useState<StudentOption[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState("")
  const [summary, setSummary] = useState<StudentSummary | null>(null)
  const [chargeForm, setChargeForm] = useState(emptyCharge)
  const [categoryForm, setCategoryForm] = useState(emptyCategory)
  const [holdForm, setHoldForm] = useState(emptyHold)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const activeCategories = useMemo(
    () => categories.filter((category) => category.is_active),
    [categories]
  )

  const loadSummary = useCallback(async (studentId: string) => {
    if (!studentId) {
      setSummary(null)
      return
    }
    const data = await apiFetch<StudentSummary>(`/finance/student-ledgers?student_id=${studentId}`)
    setSummary(data)
  }, [])

  const loadData = useCallback(async () => {
    const [ledgerData, categoryData, studentData] = await Promise.all([
      apiFetch<{ students: StudentRow[] }>("/finance/student-ledgers"),
      apiFetch<{ categories: Category[] }>("/finance/fee-categories"),
      apiFetch<{ students: StudentOption[] }>("/finance/students"),
    ])
    setStudents(ledgerData.students ?? [])
    setCategories(categoryData.categories ?? [])
    setStudentOptions(studentData.students ?? [])
    if (selectedStudentId) {
      await loadSummary(selectedStudentId)
    }
  }, [loadSummary, selectedStudentId])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load student ledgers."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  async function selectStudent(studentId: string) {
    setSelectedStudentId(studentId)
    setChargeForm((current) => ({ ...current, student_id: studentId }))
    setHoldForm((current) => ({ ...current, student_id: studentId }))
    setError("")
    try {
      await loadSummary(studentId)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load selected student ledger.")
    }
  }

  async function saveCategory(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/fee-categories", {
        method: "POST",
        body: JSON.stringify(categoryForm),
      })
      setCategoryForm(emptyCategory)
      setSuccess("Fee category saved.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save category.")
    } finally {
      setSaving(false)
    }
  }

  async function saveCharge(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/student-ledgers", {
        method: "POST",
        body: JSON.stringify({
          ...chargeForm,
          student_id: Number(chargeForm.student_id),
          category_id: Number(chargeForm.category_id),
        }),
      })
      setChargeForm({ ...emptyCharge, student_id: selectedStudentId })
      setSuccess("Student charge posted.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to post student charge.")
    } finally {
      setSaving(false)
    }
  }

  async function saveHold(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/holds", {
        method: "POST",
        body: JSON.stringify({
          ...holdForm,
          student_id: Number(holdForm.student_id),
        }),
      })
      setHoldForm({ ...emptyHold, student_id: selectedStudentId })
      setSuccess("Finance hold placed.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to place finance hold.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/ledger", title: "Student Ledgers" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <WalletCards className="size-6" /> Student Ledgers
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">Post student charges, review outstanding balances, and place finance holds.</p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
          </Button>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        <section className="grid gap-4 xl:grid-cols-[22rem_22rem_minmax(0,1fr)]">
          <div className="space-y-4">
            <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={saveCategory}>
              <h2 className="text-base font-semibold">Fee Category</h2>
              <div className="mt-4 grid gap-3">
                <div className="space-y-2"><Label htmlFor="category_code">Code</Label><Input id="category_code" value={categoryForm.code} onChange={(event) => setCategoryForm((current) => ({ ...current, code: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="category_name">Name</Label><Input id="category_name" value={categoryForm.name} onChange={(event) => setCategoryForm((current) => ({ ...current, name: event.target.value }))} required /></div>
                <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Save Category</Button>
              </div>
            </form>
            <Card>
              <CardHeader>
                <CardDescription>Balances</CardDescription>
                <CardTitle>{students.length} students</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {students.slice(0, 12).map((row) => (
                  <button key={row.student.id} type="button" onClick={() => void selectStudent(String(row.student.id))} className="w-full rounded-md border border-border bg-background px-3 py-2 text-left text-sm transition-colors hover:bg-muted/60">
                    <span className="font-medium">{row.student.name}</span>
                    <span className="mt-1 block text-muted-foreground">{row.student.identifier} - {money(row.balance)} - {row.active_holds} holds</span>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={saveCharge}>
              <h2 className="text-base font-semibold">Post Charge</h2>
              <div className="mt-4 grid gap-3">
                <div className="space-y-2"><Label htmlFor="charge_student">Student</Label><select id="charge_student" value={chargeForm.student_id} onChange={(event) => void selectStudent(event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required><option value="">Select student</option>{studentOptions.map((student) => <option key={student.id} value={student.id}>{student.name} - {student.identifier}</option>)}</select></div>
                <div className="space-y-2"><Label htmlFor="charge_category">Category</Label><select id="charge_category" value={chargeForm.category_id} onChange={(event) => setChargeForm((current) => ({ ...current, category_id: event.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required><option value="">Select category</option>{activeCategories.map((category) => <option key={category.id} value={category.id}>{category.code} - {category.name}</option>)}</select></div>
                <div className="space-y-2"><Label htmlFor="description">Description</Label><Input id="description" value={chargeForm.description} onChange={(event) => setChargeForm((current) => ({ ...current, description: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="amount">Amount</Label><Input id="amount" type="number" min="0" step="0.01" value={chargeForm.amount} onChange={(event) => setChargeForm((current) => ({ ...current, amount: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="due_date">Due Date</Label><Input id="due_date" type="date" value={chargeForm.due_date} onChange={(event) => setChargeForm((current) => ({ ...current, due_date: event.target.value }))} /></div>
                <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Post Charge</Button>
              </div>
            </form>

            <form className="rounded-lg border border-border bg-background p-5 shadow-sm" onSubmit={saveHold}>
              <h2 className="flex items-center gap-2 text-base font-semibold"><ShieldAlert className="size-4" /> Finance Hold</h2>
              <div className="mt-4 grid gap-3">
                <div className="space-y-2"><Label htmlFor="hold_student">Student</Label><select id="hold_student" value={holdForm.student_id} onChange={(event) => void selectStudent(event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required><option value="">Select student</option>{studentOptions.map((student) => <option key={student.id} value={student.id}>{student.name} - {student.identifier}</option>)}</select></div>
                <div className="space-y-2"><Label htmlFor="hold_reason">Reason</Label><Input id="hold_reason" value={holdForm.reason} onChange={(event) => setHoldForm((current) => ({ ...current, reason: event.target.value }))} required /></div>
                <div className="space-y-2"><Label htmlFor="hold_notes">Notes</Label><Input id="hold_notes" value={holdForm.notes} onChange={(event) => setHoldForm((current) => ({ ...current, notes: event.target.value }))} /></div>
                <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <ShieldAlert className="size-4" />} Place Hold</Button>
              </div>
            </form>
          </div>

          <section className="space-y-4">
            <Card>
              <CardHeader>
                <CardDescription>Selected Student</CardDescription>
                <CardTitle>{summary?.student.name ?? "Choose a student"}</CardTitle>
              </CardHeader>
              <CardContent>
                {summary ? (
                  <div className="grid gap-3 sm:grid-cols-3">
                    <p className="text-sm"><span className="text-muted-foreground">Identifier</span><br />{summary.student.identifier}</p>
                    <p className="text-sm"><span className="text-muted-foreground">Balance</span><br />{money(summary.balance)}</p>
                    <p className="text-sm"><span className="text-muted-foreground">Active Holds</span><br />{summary.active_holds.length}</p>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Select a student to review charges and ledger entries.</p>
                )}
              </CardContent>
            </Card>

            {summary ? (
              <>
                <Card>
                  <CardHeader><CardDescription>Recent Charges</CardDescription><CardTitle>{summary.charges.length}</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {summary.charges.slice(0, 8).map((charge) => (
                      <div key={charge.id} className="rounded-md border border-border p-3 text-sm">
                        <p className="font-medium">{charge.description}</p>
                        <p className="mt-1 text-muted-foreground">{charge.category.code} - {money(charge.amount)} - {formatDate(charge.due_date)} - {label(charge.status)}</p>
                      </div>
                    ))}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardDescription>Ledger Entries</CardDescription><CardTitle>{summary.ledger_entries.length}</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {summary.ledger_entries.slice(-10).reverse().map((entry) => (
                      <div key={entry.id} className="rounded-md border border-border p-3 text-sm">
                        <p className="font-medium">{label(entry.entry_type)} - {money(entry.amount)}</p>
                        <p className="mt-1 text-muted-foreground">{entry.description} - Balance {money(entry.balance_after)}</p>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </>
            ) : null}
          </section>
        </section>
      </main>
    </div>
  )
}
