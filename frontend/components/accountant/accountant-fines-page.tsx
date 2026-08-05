"use client"

import { useCallback, useEffect, useState } from "react"
import { AlertCircle, CheckCircle2, Loader2, Plus, RefreshCw, Search, ShieldAlert, User, Wallet } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch } from "@/lib/auth"
import { LedgerNav } from "@/components/accountant/ledger/ledger-nav"
import { formatUmsMoney } from "@/lib/ums-settings"
import {
  fetchAccountantFines,
  createFine,
  deductFine,
  fineStatusColor,
  fineStatusLabel,
  type Fine,
} from "@/lib/fines"

type SearchStudent = {
  id: number
  name: string
  email: string
  identifier: string
}

export function AccountantFinesPage() {
  const settings = usePublicUmsSettings()
  const currencyCode = settings.localization.currency_code || "USD"
  const [fines, setFines] = useState<Fine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>("")
  const [searchStudentId, setSearchStudentId] = useState<string>("")

  // Issue fine modal state
  const [showIssueModal, setShowIssueModal] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<SearchStudent | null>(null)
  const [studentQuery, setStudentQuery] = useState("")
  const [foundStudents, setFoundStudents] = useState<SearchStudent[]>([])
  const [searchingStudents, setSearchingStudents] = useState(false)
  
  // Fine form values
  const [reason, setReason] = useState("")
  const [description, setDescription] = useState("")
  const [amount, setAmount] = useState("")
  const [dueDate, setDueDate] = useState("")
  const [submittingFine, setSubmittingFine] = useState(false)

  // Deduct modal state
  const [deductingFine, setDeductingFine] = useState<Fine | null>(null)
  const [deductionNote, setDeductionNote] = useState("")
  const [submittingDeduction, setSubmittingDeduction] = useState(false)

  const loadFines = useCallback(async () => {
    setError("")
    try {
      const data = await fetchAccountantFines({
        status: filterStatus || undefined,
        student_id: searchStudentId ? Number(searchStudentId) : undefined,
      })
      setFines(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load fines.")
    }
  }, [filterStatus, searchStudentId])

  const refresh = useCallback(() => {
    setLoading(true)
    void loadFines().finally(() => setLoading(false))
  }, [loadFines])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  // Search students for autocomplete
  useEffect(() => {
    if (!studentQuery.trim()) {
      const timer = window.setTimeout(() => {
        setFoundStudents([])
      }, 0)
      return () => window.clearTimeout(timer)
    }
    const timer = setTimeout(async () => {
      setSearchingStudents(true)
      try {
        const res = await apiFetch<{ students: SearchStudent[] }>(`/finance/students?q=${encodeURIComponent(studentQuery)}`)
        setFoundStudents(res.students ?? [])
      } catch (err) {
        console.error("Student search failed", err)
      } finally {
        setSearchingStudents(false)
      }
    }, 400)

    return () => clearTimeout(timer)
  }, [studentQuery])

  async function handleCreateFine(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedStudent) {
      setError("Please select a student first.")
      return
    }
    if (!reason || !amount) {
      setError("Reason and amount are required.")
      return
    }

    setSubmittingFine(true)
    setError("")
    setSuccess("")
    try {
      await createFine({
        student_id: selectedStudent.id,
        reason,
        amount,
        description,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
      })
      setSuccess(`Fine successfully issued to ${selectedStudent.name}.`)
      setShowIssueModal(false)
      // reset form
      setSelectedStudent(null)
      setStudentQuery("")
      setReason("")
      setDescription("")
      setAmount("")
      setDueDate("")
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to issue fine.")
    } finally {
      setSubmittingFine(false)
    }
  }

  async function handleDeductFine() {
    if (!deductingFine) return
    setSubmittingDeduction(true)
    setError("")
    setSuccess("")
    try {
      await deductFine(deductingFine.id, deductionNote)
      setSuccess(`Fine successfully marked as deducted from ${deductingFine.student.name}'s meal allowance.`)
      setDeductingFine(null)
      setDeductionNote("")
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process manual deduction.")
    } finally {
      setSubmittingDeduction(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/ledger/fines", title: "Fines & Charges" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <LedgerNav />
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <ShieldAlert className="size-8 text-amber-500" /> Fines & Charges
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Issue fines to students, set payment deadlines, and manually deduct unpaid fines from their meal allowance.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" disabled={loading} onClick={refresh}>
              {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
            </Button>
            <Button className="bg-amber-600 hover:bg-amber-700 text-white" onClick={() => setShowIssueModal(true)}>
              <Plus className="size-4 mr-1" /> Issue Fine
            </Button>
          </div>
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

        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center bg-card p-4 rounded-xl border border-border shadow-xs">
          <div className="flex-1 min-w-[200px]">
            <Label className="text-xs text-muted-foreground mb-1 block">Filter by Status</Label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
            >
              <option value="">All Fines & Charges</option>
              <option value="pending">Pending Payment</option>
              <option value="paid">Paid Online</option>
              <option value="overdue">Overdue</option>
              <option value="deducted">Deducted from Allowance</option>
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <Label className="text-xs text-muted-foreground mb-1 block">Student Database ID</Label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by Profile ID..."
                value={searchStudentId}
                onChange={(e) => setSearchStudentId(e.target.value)}
                className="pl-9 h-9"
              />
            </div>
          </div>
        </div>

        {/* Fines Table */}
        <Card className="overflow-hidden border border-border/80 shadow-xs">
          <CardHeader className="bg-muted/50 border-b border-border/60">
            <CardTitle className="text-lg">Issued Fines History</CardTitle>
            <CardDescription>A list of all fine records, online payments, and meal allowance deductions.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                <Loader2 className="size-8 animate-spin mb-2 text-primary" />
                <p>Loading fines registry...</p>
              </div>
            ) : fines.length === 0 ? (
              <div className="text-center p-12 text-muted-foreground bg-muted/20">
                <ShieldAlert className="size-12 mx-auto text-muted-foreground/30 mb-3" />
                <p className="font-medium text-foreground">No Fines or Charges Found</p>
                <p className="text-sm mt-1">Adjust filters or create a new fine for a student.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border/60 bg-muted/50 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      <th className="p-4">Fine ID</th>
                      <th className="p-4">Student</th>
                      <th className="p-4">Reason / Description</th>
                      <th className="p-4 text-right">Amount</th>
                      <th className="p-4">Deadline</th>
                      <th className="p-4">Status</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {fines.map((fine) => (
                      <tr key={fine.id} className="hover:bg-muted/30 transition">
                        <td className="p-4 font-mono text-xs">#{fine.id}</td>
                        <td className="p-4">
                          <div className="font-medium text-foreground">{fine.student.name}</div>
                          <div className="text-xs text-muted-foreground font-mono">{fine.student.identifier || fine.student.email}</div>
                        </td>
                        <td className="p-4 max-w-[280px]">
                          <div className="font-medium text-foreground">{fine.reason}</div>
                          {fine.description && <div className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{fine.description}</div>}
                          {fine.deduction_note && (
                            <div className="text-xs text-primary bg-primary/10 p-1.5 rounded-md mt-1.5 border border-primary/20">
                              <span className="font-semibold">Deduction Note:</span> {fine.deduction_note}
                            </div>
                          )}
                        </td>
                        <td className="p-4 text-right font-semibold text-foreground">
                          {formatUmsMoney(fine.amount, settings, fine.currency)}
                        </td>
                        <td className="p-4 text-muted-foreground">
                          {fine.due_date ? new Date(fine.due_date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "None"}
                        </td>
                        <td className="p-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${fineStatusColor(fine.status)}`}>
                            {fineStatusLabel(fine.status)}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          {(fine.status === "pending" || fine.status === "overdue") ? (
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-blue-200 hover:bg-blue-50 text-blue-700 font-semibold"
                              onClick={() => setDeductingFine(fine)}
                            >
                              <Wallet className="size-3.5 mr-1" /> Deduct manual
                            </Button>
                          ) : (
                            <span className="text-xs text-muted-foreground font-medium italic">Settled</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Modal: Issue Fine */}
        {showIssueModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
            <div className="w-full max-w-lg bg-card rounded-2xl shadow-xl border border-border overflow-hidden animate-in fade-in zoom-in-95 duration-150">
              <div className="bg-amber-500/10 border-b border-amber-200/50 dark:border-amber-800/50 p-5">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <ShieldAlert className="size-5 text-amber-500" /> Issue Student Fine / Charge
                </h3>
                <p className="text-xs text-muted-foreground mt-1">This will send an in-app and email alert immediately to the student.</p>
              </div>
              <form onSubmit={handleCreateFine}>
                <div className="p-5 space-y-4">
                  {/* Student Search box */}
                  <div className="space-y-2 relative">
                    <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Select Student Profile</Label>
                    {selectedStudent ? (
                      <div className="flex items-center justify-between bg-muted p-3 rounded-lg border border-border">
                        <div className="flex items-center gap-2">
                          <User className="size-4 text-muted-foreground" />
                          <div>
                            <span className="font-semibold text-foreground">{selectedStudent.name}</span>
                            <span className="text-xs text-muted-foreground ml-2">({selectedStudent.identifier})</span>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" className="h-7 text-xs text-red-500 hover:text-red-700" onClick={() => setSelectedStudent(null)}>Change</Button>
                      </div>
                    ) : (
                      <>
                        <div className="relative">
                          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder="Type student name or ID..."
                            value={studentQuery}
                            onChange={(e) => setStudentQuery(e.target.value)}
                            className="pl-9 h-10"
                          />
                        </div>
                        {searchingStudents && <div className="text-xs text-muted-foreground p-1">Searching profiles...</div>}
                        {foundStudents.length > 0 && (
                          <div className="absolute left-0 right-0 z-55 max-h-40 overflow-y-auto bg-card border border-border shadow-lg rounded-md mt-1 divide-y divide-border">
                            {foundStudents.map((stud) => (
                              <div
                                key={stud.id}
                                className="p-2.5 text-sm hover:bg-muted cursor-pointer flex justify-between items-center"
                                onClick={() => {
                                  setSelectedStudent(stud)
                                  setFoundStudents([])
                                  setStudentQuery("")
                                }}
                              >
                                <div>
                                  <span className="font-semibold text-foreground">{stud.name}</span>
                                  <span className="text-xs text-muted-foreground block font-mono">{stud.identifier || stud.email}</span>
                                </div>
                                <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Select</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="reason" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reason / Title</Label>
                    <Input
                      id="reason"
                      placeholder="e.g. Broken room desk, Lost library card..."
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="amount" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Amount ({currencyCode})</Label>
                    <Input
                      id="amount"
                      type="number"
                      min="0.01"
                      step="0.01"
                      placeholder="e.g. 50.00"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="due_date" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Payment Deadline (Optional)</Label>
                    <Input
                      id="due_date"
                      type="datetime-local"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Detailed Description (Optional)</Label>
                    <textarea
                      id="description"
                      rows={3}
                      placeholder="Additional information about the fine..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                    />
                  </div>
                </div>
                <div className="bg-muted border-t border-border p-4 flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowIssueModal(false)}>Cancel</Button>
                  <Button type="submit" className="bg-amber-600 hover:bg-amber-700 text-white font-semibold" disabled={submittingFine}>
                    {submittingFine ? <Loader2 className="size-4 animate-spin mr-1" /> : null} Issue Fine
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Deduct Manual */}
        {deductingFine && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
            <div className="w-full max-w-md bg-card rounded-2xl shadow-xl border border-border overflow-hidden animate-in fade-in zoom-in-95 duration-150">
              <div className="bg-blue-500/10 border-b border-blue-200/50 dark:border-blue-800/50 p-5">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <Wallet className="size-5 text-blue-600" /> Manual Allowance Deduction
                </h3>
                <p className="text-xs text-muted-foreground mt-1">Deduct fine manually from the student&apos;s physical bank allowance account.</p>
              </div>
              <div className="p-5 space-y-4">
                <div className="text-sm space-y-1.5 bg-muted p-3 rounded-lg border border-border">
                  <div className="flex justify-between"><span className="text-muted-foreground">Student:</span> <span className="font-semibold text-foreground">{deductingFine.student.name}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Reason:</span> <span className="font-medium text-foreground">{deductingFine.reason}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Amount:</span> <span className="font-bold text-red-600">{formatUmsMoney(deductingFine.amount, settings, deductingFine.currency)}</span></div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="deduction_note" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Deduction Note</Label>
                  <textarea
                    id="deduction_note"
                    rows={3}
                    placeholder="e.g. Deducted from July 2026 Allowance bank credit..."
                    value={deductionNote}
                    onChange={(e) => setDeductionNote(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  />
                  <p className="text-[11px] text-muted-foreground italic">Note: Ensure deduction is done manually on bank records before marking this.</p>
                </div>
              </div>
              <div className="bg-muted border-t border-border p-4 flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setDeductingFine(null)}>Cancel</Button>
                <Button type="button" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold" onClick={handleDeductFine} disabled={submittingDeduction}>
                  {submittingDeduction ? <Loader2 className="size-4 animate-spin mr-1" /> : null} Mark Deducted
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
