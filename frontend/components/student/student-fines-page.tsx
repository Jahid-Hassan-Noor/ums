"use client"

import { useCallback, useEffect, useState } from "react"
import { AlertCircle, CheckCircle2, CreditCard, ExternalLink, Loader2, RefreshCw, ShieldAlert, Wallet } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  fetchStudentFines,
  initiateFinePay,
  fineStatusColor,
  fineStatusLabel,
  type Fine,
} from "@/lib/fines"

export function StudentFinesPage() {
  const [fines, setFines] = useState<Fine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [payingFineId, setPayingFineId] = useState<number | null>(null)

  const loadFines = useCallback(async () => {
    setError("")
    try {
      const data = await fetchStudentFines()
      setFines(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load your fines.")
    }
  }, [])

  const refresh = useCallback(() => {
    setLoading(true)
    void loadFines().finally(() => setLoading(false))
  }, [loadFines])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function handlePayFine(fine: Fine) {
    setPayingFineId(fine.id)
    setError("")
    try {
      const res = await initiateFinePay(fine.id)
      if (res.checkout_url) {
        window.location.href = res.checkout_url
      } else {
        setError("Could not generate payment link. Please contact the Finance Office.")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout process.")
    } finally {
      setPayingFineId(null)
    }
  }

  // Calculate outstanding fines
  const outstandingFines = fines.filter(f => f.status === "pending" || f.status === "overdue")
  const totalOutstanding = outstandingFines.reduce((sum, f) => sum + Number(f.amount), 0)

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/student", title: "Student" }, { href: "/student/fines", title: "My Fines & Charges" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <ShieldAlert className="size-8 text-amber-500" /> My Fines & Charges
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Review and pay your outstanding university charges or fines online.
            </p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
          </Button>
        </section>

        {error && (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertCircle className="size-5 shrink-0" />
            <div>{error}</div>
          </div>
        )}
        {success && (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
            <CheckCircle2 className="size-5 shrink-0" />
            <div>{success}</div>
          </div>
        )}

        {/* Overview Summary */}
        <section className="grid gap-4 md:grid-cols-3">
          <Card className="border-amber-200 bg-amber-50/20">
            <CardHeader className="pb-2">
              <CardDescription className="text-amber-800 font-semibold">Outstanding Balance</CardDescription>
              <CardTitle className="text-3xl text-amber-950">RM {totalOutstanding.toFixed(2)}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-amber-800/80">Total pending or overdue fees requiring settlement.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Overdue Fines</CardDescription>
              <CardTitle>{outstandingFines.filter(f => f.status === "overdue").length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Fines past due date. These are subject to manual meal allowance deduction.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Settled Charges</CardDescription>
              <CardTitle>{fines.filter(f => f.status === "paid" || f.status === "deducted").length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Charges successfully settled online or deducted from allowance.</p>
            </CardContent>
          </Card>
        </section>

        {/* Fines List */}
        <Card className="border border-border/80 shadow-xs">
          <CardHeader className="bg-slate-50/30 border-b border-border/60">
            <CardTitle className="text-lg">Fines Registry</CardTitle>
            <CardDescription>Track all fines, replacement fees, or other charges associated with your account.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                <Loader2 className="size-8 animate-spin mb-2 text-primary" />
                <p>Loading fines...</p>
              </div>
            ) : fines.length === 0 ? (
              <div className="text-center p-12 text-muted-foreground">
                <ShieldAlert className="size-12 mx-auto text-muted-foreground/30 mb-3" />
                <p className="font-semibold text-slate-700 text-base">Your Registry is Clear!</p>
                <p className="text-sm mt-1">You have no issued fines or outstanding charges.</p>
              </div>
            ) : (
              <div className="divide-y divide-border/40">
                {fines.map((fine) => (
                  <div key={fine.id} className="p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:bg-slate-50/20 transition">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900 text-base">{fine.reason}</span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${fineStatusColor(fine.status)}`}>
                          {fineStatusLabel(fine.status)}
                        </span>
                      </div>
                      {fine.description && <p className="text-sm text-slate-600 max-w-2xl">{fine.description}</p>}
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        <span>Issued on: {new Date(fine.created_at).toLocaleDateString("en-GB")}</span>
                        {fine.due_date && (
                          <span className={fine.status === "overdue" ? "text-red-600 font-medium" : ""}>
                            Deadline: {new Date(fine.due_date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                          </span>
                        )}
                        {fine.paid_at && <span>Paid on: {new Date(fine.paid_at).toLocaleDateString("en-GB")}</span>}
                        {fine.deducted_at && <span>Deducted on: {new Date(fine.deducted_at).toLocaleDateString("en-GB")}</span>}
                      </div>
                      {fine.deduction_note && (
                        <div className="text-xs text-blue-700 bg-blue-50/60 p-2 rounded-md border border-blue-100 max-w-xl mt-1.5">
                          <span className="font-semibold">Allowance Deduction Note:</span> {fine.deduction_note}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-4 self-stretch md:self-auto justify-between border-t md:border-0 border-border/40 pt-3 md:pt-0">
                      <div className="text-right">
                        <div className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">Amount Due</div>
                        <div className="text-xl font-bold text-slate-900">{fine.currency} {Number(fine.amount).toFixed(2)}</div>
                      </div>
                      {(fine.status === "pending" || fine.status === "overdue") ? (
                        <Button
                          className="bg-amber-600 hover:bg-amber-700 text-white font-semibold flex items-center shadow-sm"
                          onClick={() => handlePayFine(fine)}
                          disabled={payingFineId !== null}
                        >
                          {payingFineId === fine.id ? (
                            <Loader2 className="size-4 animate-spin mr-1.5" />
                          ) : (
                            <CreditCard className="size-4 mr-1.5" />
                          )}
                          Pay Online
                        </Button>
                      ) : fine.status === "deducted" ? (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-100 px-3 py-1.5 rounded-lg">
                          <Wallet className="size-3.5" /> Deducted from Allowance
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-lg">
                          <CheckCircle2 className="size-3.5" /> Settled Online
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
