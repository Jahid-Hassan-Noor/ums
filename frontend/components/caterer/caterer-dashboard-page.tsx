"use client"

import { FormEvent, useState } from "react"
import { CheckCircle2, Loader2, Search, WalletCards } from "lucide-react"

import { Header } from "@/components/layout/header"
import { CatererDashboard } from "@/components/role-zone/role-dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch } from "@/lib/auth"
import { formatUmsMoney } from "@/lib/ums-settings"

type Account = {
  student: {
    student_id: string
    name: string
    email: string
    enrollment_status: string
  }
  month: string
  allowance_amount: string
  adjustment_amount: string
  spent_amount: string
  balance: string
  transactions: Array<{
    id: number
    amount: string
    description: string
    caterer_name: string
    created_at: string
  }>
}

export function CatererDashboardPage() {
  const settings = usePublicUmsSettings()
  const diningLabel = settings.module_labels.canteen || settings.policies.dining.label || "Dining"
  const diningLabelLower = diningLabel.toLowerCase()
  const currencyCode = settings.localization.currency_code || "USD"
  const [studentId, setStudentId] = useState("")
  const [account, setAccount] = useState<Account | null>(null)
  const [amount, setAmount] = useState("")
  const [description, setDescription] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function searchStudent(event?: FormEvent) {
    event?.preventDefault()
    setBusy(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ account: Account }>(`/canteen/student?student_id=${encodeURIComponent(studentId.trim())}`)
      setAccount(response.account)
    } catch (caught) {
      setAccount(null)
      setError(caught instanceof Error ? caught.message : `Unable to find student for ${diningLabelLower} checkout.`)
    } finally {
      setBusy(false)
    }
  }

  async function completeTransaction(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ account: Account; message: string }>("/canteen/transactions", {
        method: "POST",
        body: JSON.stringify({ student_id: studentId.trim(), amount, description }),
      })
      setAccount(response.account)
      setAmount("")
      setDescription("")
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : `Unable to complete ${diningLabelLower} transaction.`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/caterer", title: "Caterer" }, { href: "/caterer/dashboard", title: "Dashboard" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <CatererDashboard />
        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}
        <Card id="student-card-checkout" className="scroll-mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Search className="size-5" /> Student Card Search</CardTitle>
            <CardDescription>Enter the student ID printed on the student card.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-3 sm:flex-row" onSubmit={searchStudent}>
              <Input autoFocus placeholder="Student ID" value={studentId} onChange={(event) => setStudentId(event.target.value)} required />
              <Button disabled={busy} type="submit">{busy ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />} Search</Button>
            </form>
          </CardContent>
        </Card>
        {account ? (
          <section className="grid gap-4 xl:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardDescription>{account.student.student_id} · {account.student.enrollment_status || "Active"}</CardDescription>
                  <CardTitle>{account.student.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="rounded-lg border bg-emerald-50 p-4 text-emerald-900">
                    <p className="text-sm">Current balance</p>
                    <p className="mt-1 text-4xl font-semibold">{formatUmsMoney(account.balance, settings)}</p>
                  </div>
                  <div className="flex justify-between text-sm"><span>Monthly allocation</span><strong>{formatUmsMoney(account.allowance_amount, settings)}</strong></div>
                  <div className="flex justify-between text-sm"><span>Admin-added balance</span><strong>{formatUmsMoney(account.adjustment_amount, settings)}</strong></div>
                  <div className="flex justify-between text-sm"><span>Spent this month</span><strong>{formatUmsMoney(account.spent_amount, settings)}</strong></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><WalletCards className="size-5" /> Complete Bill</CardTitle></CardHeader>
                <CardContent>
                  <form className="space-y-4" onSubmit={completeTransaction}>
                    <div className="space-y-2"><Label htmlFor="amount">Bill amount ({currencyCode})</Label><Input id="amount" type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required /></div>
                    <div className="space-y-2"><Label htmlFor="description">Description</Label><Input id="description" placeholder="Lunch" value={description} onChange={(event) => setDescription(event.target.value)} /></div>
                    <Button className="w-full" disabled={busy} type="submit">Deduct Bill</Button>
                  </form>
                </CardContent>
              </Card>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Transactions This Month</CardTitle>
                <CardDescription>Only transactions from {account.month.slice(0, 7)} are shown.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {account.transactions.length ? account.transactions.map((transaction) => (
                  <div key={transaction.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3">
                    <div><p className="font-medium">{transaction.description || `${diningLabel} purchase`}</p><p className="text-xs text-muted-foreground">{new Date(transaction.created_at).toLocaleString()} · {transaction.caterer_name}</p></div>
                    <strong>{formatUmsMoney(transaction.amount, settings)}</strong>
                  </div>
                )) : <p className="text-sm text-muted-foreground">No {diningLabelLower} transactions for this student in the current month.</p>}
              </CardContent>
            </Card>
          </section>
        ) : null}
      </main>
    </div>
  )
}
