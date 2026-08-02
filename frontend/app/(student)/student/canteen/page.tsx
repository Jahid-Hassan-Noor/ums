"use client"

import { useCallback, useEffect, useState } from "react"
import { Loader2, RefreshCw, Utensils, WalletCards } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"

type CanteenAccount = {
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

type StudentDashboardResponse = {
  canteen_account: CanteenAccount | null
  canteen_message: string
}

function money(value: string) {
  return `RM ${Number(value || 0).toFixed(2)}`
}

export default function StudentCanteenPage() {
  const [account, setAccount] = useState<CanteenAccount | null>(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)

  const loadCanteenAccount = useCallback(async () => {
    setError("")
    const response = await apiFetch<StudentDashboardResponse>("/student/dashboard")
    setAccount(response.canteen_account)
    setMessage(response.canteen_message)
  }, [])

  const refreshCanteenAccount = useCallback(() => {
    setLoading(true)
    void loadCanteenAccount()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load canteen balance."))
      .finally(() => setLoading(false))
  }, [loadCanteenAccount])

  useEffect(() => {
    const timer = window.setTimeout(refreshCanteenAccount, 0)
    return () => window.clearTimeout(timer)
  }, [refreshCanteenAccount])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/canteen", title: "Canteen" },
        ]}
      />
      <main className="flex-1 px-4 pb-8 pt-4 sm:px-6">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
          <section className="space-y-4">
            <div className="flex flex-wrap items-end justify-between gap-3 border-b border-border/70 pb-4">
              <div>
                <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
                  <Utensils className="size-6" /> Canteen
                </h1>
                <p className="mt-2 text-sm text-muted-foreground">
                  Check your current monthly meal allowance and canteen purchases.
                </p>
              </div>
              <Button variant="outline" disabled={loading} onClick={refreshCanteenAccount}>
                {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
              </Button>
            </div>

            {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
            {message ? <p className="rounded-lg border bg-muted/50 p-3 text-sm text-muted-foreground">{message}</p> : null}

            {account ? (
              <div className="grid gap-4 xl:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
                <Card>
                  <CardHeader>
                    <CardDescription>Allowance month {account.month.slice(0, 7)}</CardDescription>
                    <CardTitle className="flex items-center gap-2">
                      <WalletCards className="size-5" /> Available Balance
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="rounded-lg border bg-emerald-50 p-4 text-emerald-900">
                      <p className="text-sm">Current balance</p>
                      <p className="mt-1 text-4xl font-semibold">{money(account.balance)}</p>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Monthly allowance</span>
                      <strong>{money(account.allowance_amount)}</strong>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Admin additions</span>
                      <strong>{money(account.adjustment_amount)}</strong>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Spent this month</span>
                      <strong>{money(account.spent_amount)}</strong>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Transactions This Month</CardTitle>
                    <CardDescription>Your canteen purchases for the current allowance month.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {account.transactions.length ? (
                      account.transactions.map((transaction) => (
                        <div
                          key={transaction.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3"
                        >
                          <div>
                            <p className="font-medium">{transaction.description || "Canteen purchase"}</p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(transaction.created_at).toLocaleString()} · {transaction.caterer_name}
                            </p>
                          </div>
                          <strong>{money(transaction.amount)}</strong>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No canteen transactions this month.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : loading ? (
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            ) : null}
          </section>
        </div>
      </main>
    </div>
  )
}
