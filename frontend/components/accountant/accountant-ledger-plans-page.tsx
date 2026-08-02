"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, CreditCard, Loader2, Plus, RefreshCw } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"
import { PlanStatusBadge, InstallmentStatusBadge } from "@/components/accountant/ledger/ledger-badges"
import { LedgerNav } from "@/components/accountant/ledger/ledger-nav"

type StudentRef = { id: number; name: string; email: string; identifier: string }
type Installment = { id: number; installment_number: number; amount: string; due_date: string; status: string; paid_at: string | null; notes: string }
type PaymentPlan = { id: number; student: StudentRef; description: string; total_amount: string; currency: string; installment_count: number; frequency: string; status: string; paid_installments: number; remaining_installments: number; created_at: string; installments: Installment[] }

function formatDate(value: string | null) { return value ? new Date(value).toLocaleDateString() : "—" }

export function AccountantLedgerPlansPage() {
  const [plans, setPlans] = useState<PaymentPlan[]>([])
  const [studentOptions, setStudentOptions] = useState<StudentRef[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showCreate, setShowCreate] = useState(false)
  const [expandedPlan, setExpandedPlan] = useState<number | null>(null)
  const [statusFilter, setStatusFilter] = useState("")

  const [form, setForm] = useState({ student_id: "", total_amount: "", installment_count: "3", frequency: "monthly", description: "" })

  const loadData = useCallback(async () => {
    const params = new URLSearchParams()
    if (statusFilter) params.set("status", statusFilter)
    const [plansData, studData] = await Promise.all([
      apiFetch<{ plans: PaymentPlan[] }>(`/finance/ledger/payment-plans?${params.toString()}`),
      apiFetch<{ students: StudentRef[] }>("/finance/students"),
    ])
    setPlans(plansData.plans ?? [])
    setStudentOptions(studData.students ?? [])
  }, [statusFilter])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load payment plans."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => { void refresh() }, [refresh])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/finance/ledger/payment-plans", {
        method: "POST",
        body: JSON.stringify({ ...form, student_id: Number(form.student_id), total_amount: Number(form.total_amount), installment_count: Number(form.installment_count) }),
      })
      setForm({ student_id: "", total_amount: "", installment_count: "3", frequency: "monthly", description: "" })
      setSuccess("Payment plan created.")
      setShowCreate(false)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create plan.")
    } finally {
      setSaving(false)
    }
  }

  async function recordPayment(planId: number, installmentId: number) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/finance/ledger/payment-plans/${planId}/pay`, {
        method: "POST",
        body: JSON.stringify({ installment_id: installmentId }),
      })
      setSuccess("Installment payment recorded.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to record payment.")
    } finally {
      setSaving(false)
    }
  }

  async function cancelPlan(planId: number) {
    setSaving(true)
    setError("")
    try {
      await apiFetch(`/finance/ledger/payment-plans/${planId}`, { method: "DELETE" })
      setSuccess("Plan cancelled.")
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to cancel plan.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/ledger/payment-plans", title: "Payment Plans" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <LedgerNav />
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <CreditCard className="size-6" /> Payment Plans
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">Create and manage installment payment plans for students.</p>
          </div>
          <div className="flex gap-2">
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded-md border border-input bg-background px-3 py-2 text-sm">
              <option value="">All Plans</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <Button variant="outline" disabled={loading} onClick={refresh}>
              {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
            </Button>
            <Button onClick={() => setShowCreate(!showCreate)}>
              <Plus className="size-4" /> New Plan
            </Button>
          </div>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {showCreate ? (
          <Card>
            <CardHeader><CardTitle>Create Payment Plan</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={(e) => void handleCreate(e)} className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Student</Label>
                  <select value={form.student_id} onChange={(e) => setForm((f) => ({ ...f, student_id: e.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required>
                    <option value="">Select student</option>
                    {studentOptions.map((s) => <option key={s.id} value={s.id}>{s.name} - {s.identifier}</option>)}
                  </select>
                </div>
                <div className="space-y-2"><Label>Total Amount (RM)</Label><Input type="number" min="0.01" step="0.01" value={form.total_amount} onChange={(e) => setForm((f) => ({ ...f, total_amount: e.target.value }))} required /></div>
                <div className="space-y-2"><Label>Installments</Label><Input type="number" min="2" max="24" value={form.installment_count} onChange={(e) => setForm((f) => ({ ...f, installment_count: e.target.value }))} required /></div>
                <div className="space-y-2">
                  <Label>Frequency</Label>
                  <select value={form.frequency} onChange={(e) => setForm((f) => ({ ...f, frequency: e.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="monthly">Monthly</option>
                    <option value="biweekly">Biweekly</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
                <div className="space-y-2 sm:col-span-2"><Label>Description</Label><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Optional description" /></div>
                <div className="sm:col-span-2 flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                  <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />} Create Plan</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        ) : null}

        <div className="space-y-3">
          {plans.map((plan) => (
            <Card key={plan.id}>
              <CardHeader className="cursor-pointer" onClick={() => setExpandedPlan(expandedPlan === plan.id ? null : plan.id)}>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">{plan.student.name}</CardTitle>
                    <CardDescription>{plan.description || "Payment plan"} · {plan.installment_count} installments · {plan.frequency}</CardDescription>
                  </div>
                  <div className="flex items-center gap-3">
                    <PlanStatusBadge status={plan.status} />
                    <span className="text-sm font-medium">{plan.total_amount}</span>
                  </div>
                </div>
              </CardHeader>
              {expandedPlan === plan.id ? (
                <CardContent className="border-t border-border pt-4">
                  <div className="mb-3 flex items-center justify-between text-sm text-muted-foreground">
                    <span>Paid: {plan.paid_installments} of {plan.installment_count}</span>
                    <span>Remaining: {plan.remaining_installments}</span>
                  </div>
                  <div className="space-y-2">
                    {plan.installments.map((inst) => (
                      <div key={inst.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                        <div className="flex items-center gap-3">
                          <span className="font-medium">#{inst.installment_number}</span>
                          <span>{inst.amount}</span>
                          <span className="text-muted-foreground">Due: {formatDate(inst.due_date)}</span>
                          {inst.paid_at ? <span className="text-muted-foreground">Paid: {formatDate(inst.paid_at)}</span> : null}
                        </div>
                        <div className="flex items-center gap-2">
                          <InstallmentStatusBadge status={inst.status} />
                          {inst.status === "pending" && plan.status === "active" ? (
                            <Button size="sm" variant="outline" disabled={saving} onClick={() => void recordPayment(plan.id, inst.id)}>
                              Record Payment
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                  {plan.status === "active" ? (
                    <div className="mt-3 flex justify-end">
                      <Button variant="destructive" size="sm" disabled={saving} onClick={() => void cancelPlan(plan.id)}>Cancel Plan</Button>
                    </div>
                  ) : null}
                </CardContent>
              ) : null}
            </Card>
          ))}
          {plans.length === 0 ? (
            <Card><CardContent className="py-8 text-center text-sm text-muted-foreground">No payment plans found.</CardContent></Card>
          ) : null}
        </div>
      </main>
    </div>
  )
}
