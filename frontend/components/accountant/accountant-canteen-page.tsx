"use client"

import { FormEvent, useEffect, useState } from "react"
import { CheckCircle2, Loader2, Save, Search, WalletCards } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type Bonus = {
  month: string
  extra_amount: string
  occasion: string
}

type ResponseData = {
  current: {
    month: string
    eligible_students: number
    allocated: string
    spent: string
    manual_additions: string
    transactions: number
  }
  settings: {
    monthly_allowance: string
    current_allocation: string
    eligible_students: number
  }
  bonuses: Bonus[]
}

type StudentAccount = {
  student: {
    student_id: string
    name: string
    enrollment_status: string
  }
  allowance_amount: string
  adjustment_amount: string
  spent_amount: string
  balance: string
  adjustments: Array<{
    id: number
    amount: string
    reason: string
    added_by_name: string
    created_at: string
  }>
}

function money(value: string) {
  return `RM ${Number(value || 0).toFixed(2)}`
}

export function AccountantCanteenPage() {
  const [data, setData] = useState<ResponseData | null>(null)
  const [monthlyAllowance, setMonthlyAllowance] = useState("50.00")
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7))
  const [extraAmount, setExtraAmount] = useState("0.00")
  const [occasion, setOccasion] = useState("")
  const [studentId, setStudentId] = useState("")
  const [studentAccount, setStudentAccount] = useState<StudentAccount | null>(null)
  const [manualAmount, setManualAmount] = useState("")
  const [manualReason, setManualReason] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    const response = await apiFetch<ResponseData>("/finance/canteen")
    setData(response)
    setMonthlyAllowance(response.settings.monthly_allowance)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData().catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load canteen settings."))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  async function save(payload: Record<string, string>) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/canteen", { method: "PATCH", body: JSON.stringify(payload) })
      setSuccess("Canteen allowance settings updated successfully.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update canteen settings.")
    } finally {
      setSaving(false)
    }
  }

  async function searchStudent(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ account: StudentAccount }>(`/finance/canteen?student_id=${encodeURIComponent(studentId.trim())}`)
      setStudentAccount(response.account)
    } catch (caught) {
      setStudentAccount(null)
      setError(caught instanceof Error ? caught.message : "Unable to find student.")
    } finally {
      setSaving(false)
    }
  }

  async function addStudentBalance(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ account: StudentAccount; message: string }>("/finance/canteen", {
        method: "POST",
        body: JSON.stringify({ student_id: studentId.trim(), amount: manualAmount, reason: manualReason }),
      })
      setStudentAccount(response.account)
      setManualAmount("")
      setManualReason("")
      setSuccess(response.message)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to add student balance.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/canteen", title: "Canteen Allowance" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Canteen Allowance</h1>
          <p className="mt-2 text-sm text-muted-foreground">Manage monthly student allowance, monthly extras, and audited manual balance additions.</p>
        </section>
        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}
        {!data ? <Loader2 className="size-6 animate-spin text-muted-foreground" /> : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["Eligible Students", String(data.current.eligible_students)],
                ["Current Allocation", money(data.settings.current_allocation)],
                ["Current Month Spent", money(data.current.spent)],
                ["Manual Additions", money(data.current.manual_additions)],
              ].map(([label, value]) => (
                <Card key={label}>
                  <CardHeader>
                    <CardDescription>{label}</CardDescription>
                    <CardTitle className="text-3xl">{value}</CardTitle>
                  </CardHeader>
                </Card>
              ))}
            </section>
            <section className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><WalletCards className="size-5" /> Standard Monthly Amount</CardTitle>
                  <CardDescription>Applied to every eligible active student. Existing balances for the current month are synchronized.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="monthly_allowance">Amount (RM)</Label>
                    <Input id="monthly_allowance" type="number" min="0" step="0.01" value={monthlyAllowance} onChange={(event) => setMonthlyAllowance(event.target.value)} />
                  </div>
                  <Button disabled={saving} onClick={() => void save({ monthly_allowance: monthlyAllowance })}><Save className="size-4" /> Save Monthly Amount</Button>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Monthly Extra Money</CardTitle>
                  <CardDescription>Add an extra allocation for Eid or another occasion in one selected month.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-2"><Label htmlFor="month">Month</Label><Input id="month" type="month" value={month} onChange={(event) => setMonth(event.target.value)} /></div>
                    <div className="space-y-2"><Label htmlFor="extra">Extra amount (RM)</Label><Input id="extra" type="number" min="0" step="0.01" value={extraAmount} onChange={(event) => setExtraAmount(event.target.value)} /></div>
                  </div>
                  <div className="space-y-2"><Label htmlFor="occasion">Occasion</Label><Input id="occasion" placeholder="Eid allowance" value={occasion} onChange={(event) => setOccasion(event.target.value)} /></div>
                  <Button disabled={saving} onClick={() => void save({ month: `${month}-01`, extra_amount: extraAmount, occasion })}><Save className="size-4" /> Save Monthly Extra</Button>
                </CardContent>
              </Card>
            </section>
            <Card>
              <CardHeader>
                <CardTitle>Manual Student Balance Addition</CardTitle>
                <CardDescription>Search an eligible student and add audited balance for the current month.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form className="flex flex-col gap-3 sm:flex-row" onSubmit={searchStudent}>
                  <Input placeholder="Student ID" value={studentId} onChange={(event) => setStudentId(event.target.value)} required />
                  <Button type="submit" variant="outline" disabled={saving}><Search className="size-4" /> Search Student</Button>
                </form>
                {studentAccount ? (
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="space-y-3 rounded-lg border p-4">
                      <div><p className="font-semibold">{studentAccount.student.name}</p><p className="text-sm text-muted-foreground">{studentAccount.student.student_id} - {studentAccount.student.enrollment_status || "Active"}</p></div>
                      <div className="flex justify-between text-sm"><span>Monthly allocation</span><strong>{money(studentAccount.allowance_amount)}</strong></div>
                      <div className="flex justify-between text-sm"><span>Accountant additions</span><strong>{money(studentAccount.adjustment_amount)}</strong></div>
                      <div className="flex justify-between text-sm"><span>Spent</span><strong>{money(studentAccount.spent_amount)}</strong></div>
                      <div className="flex justify-between border-t pt-3"><span>Current balance</span><strong>{money(studentAccount.balance)}</strong></div>
                    </div>
                    <form className="space-y-3 rounded-lg border p-4" onSubmit={addStudentBalance}>
                      <div className="space-y-2"><Label htmlFor="manual_amount">Amount to add (RM)</Label><Input id="manual_amount" type="number" min="0.01" step="0.01" value={manualAmount} onChange={(event) => setManualAmount(event.target.value)} required /></div>
                      <div className="space-y-2"><Label htmlFor="manual_reason">Reason</Label><Input id="manual_reason" placeholder="Emergency meal support" value={manualReason} onChange={(event) => setManualReason(event.target.value)} required /></div>
                      <Button type="submit" disabled={saving}><Save className="size-4" /> Add Student Balance</Button>
                    </form>
                  </div>
                ) : null}
                {studentAccount?.adjustments.length ? (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Manual addition history this month</p>
                    {studentAccount.adjustments.map((adjustment) => (
                      <div key={adjustment.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm">
                        <span>{adjustment.reason} - {adjustment.added_by_name} - {new Date(adjustment.created_at).toLocaleString()}</span>
                        <strong>{money(adjustment.amount)}</strong>
                      </div>
                    ))}
                  </div>
                ) : null}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Recent Monthly Extras</CardTitle><CardDescription>Latest configured occasion-specific allocations.</CardDescription></CardHeader>
              <CardContent className="space-y-2">
                {data.bonuses.length ? data.bonuses.map((bonus) => (
                  <div key={bonus.month} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm">
                    <span className="font-medium">{bonus.month.slice(0, 7)} - {bonus.occasion || "Monthly extra"}</span>
                    <span>{money(bonus.extra_amount)}</span>
                  </div>
                )) : <p className="text-sm text-muted-foreground">No monthly extras configured.</p>}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  )
}
