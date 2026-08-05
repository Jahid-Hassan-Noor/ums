"use client"

import { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { CheckCircle2, Loader2, RefreshCw, Search, WalletCards, ChevronLeft, ChevronRight } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch } from "@/lib/auth"
import { formatUmsMoney } from "@/lib/ums-settings"

type DashboardData = {
  currency?: string
  total_students: number
  students_with_balance: number
  total_outstanding: string
  active_holds: number
  total_charges: number
  total_charges_amount: string
  total_entries: number
  total_payments: string
  overdue_charges: number
  active_plans: number
  category_breakdown: Array<{ code: string; name: string; total: string; count: number }>
}

type StudentRef = { id: number; name: string; email: string; identifier: string }
type StudentRow = { student: StudentRef; balance: string; currency?: string; active_holds: number; last_activity: string | null }

type StudentsPage = {
  students: StudentRow[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

function formatDate(value: string | null) { return value ? new Date(value).toLocaleDateString() : "—" }

function BarChart({ data }: { data: Array<{ label: string; value: number; color: string }> }) {
  const maxVal = Math.max(...data.map((d) => d.value), 1)
  return (
    <div className="space-y-2">
      {data.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span className="w-28 truncate text-xs text-muted-foreground">{item.label}</span>
          <div className="flex-1">
            <div className="h-5 rounded bg-muted/50">
              <div
                className="h-5 rounded transition-all"
                style={{ width: `${(item.value / maxVal) * 100}%`, backgroundColor: item.color, minWidth: item.value > 0 ? "2rem" : "0" }}
              />
            </div>
          </div>
          <span className="w-20 text-right text-xs font-medium">{item.value}</span>
        </div>
      ))}
    </div>
  )
}

function DonutStat({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="size-3 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="ml-auto text-sm font-semibold">{value}</span>
    </div>
  )
}

export function AccountantLedgerDashboard() {
  const router = useRouter()
  const settings = usePublicUmsSettings()
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [studentsData, setStudentsData] = useState<StudentsPage | null>(null)
  const [search, setSearch] = useState("")
  const [sortBy, setSortBy] = useState("")
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const [dashData, studentsPage] = await Promise.all([
      apiFetch<DashboardData>("/finance/ledger/dashboard"),
      apiFetch<StudentsPage>(`/finance/student-ledgers?page=${page}&page_size=20${search ? `&q=${encodeURIComponent(search)}` : ""}${sortBy ? `&sort=${sortBy}` : ""}`),
    ])
    setDashboard(dashData)
    setStudentsData(studentsPage)
  }, [page, search, sortBy])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    setSuccess("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load ledger data."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refresh()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setPage(1)
    refresh()
  }

  const categoryChartData = dashboard?.category_breakdown.slice(0, 6).map((cat, i) => ({
    label: cat.name,
    value: parseInt(cat.total.replace(/[^\d.]/g, "")) || 0,
    color: ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"][i % 6],
  })) ?? []

  const statusPieData = dashboard ? [
    { label: "Outstanding", value: parseFloat(dashboard.total_outstanding.replace(/[^\d.]/g, "")) || 0, color: "#ef4444" },
    { label: "Collected", value: parseFloat(dashboard.total_payments.replace(/[^\d.]/g, "")) || 0, color: "#10b981" },
  ] : []

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/ledger", title: "Student Ledgers" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <WalletCards className="size-6" /> Student Ledgers
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">Overview of student finances, balances, and outstanding amounts.</p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
          </Button>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {dashboard ? (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[
                { title: "Total Outstanding", value: formatUmsMoney(dashboard.total_outstanding, settings, dashboard.currency), subtitle: `${dashboard.students_with_balance} students with balance`, color: "text-red-600" },
                { title: "Active Holds", value: String(dashboard.active_holds), subtitle: "Finance holds in effect", color: "text-amber-600" },
                { title: "Total Charges", value: formatUmsMoney(dashboard.total_charges_amount, settings, dashboard.currency), subtitle: `${dashboard.total_charges} charges posted`, color: "text-blue-600" },
                { title: "Revenue Collected", value: formatUmsMoney(dashboard.total_payments, settings, dashboard.currency), subtitle: `${dashboard.total_entries} ledger entries`, color: "text-emerald-600" },
              ].map((card) => (
                <Card key={card.title}>
                  <CardHeader className="pb-2"><CardDescription>{card.title}</CardDescription><CardTitle className={`text-2xl ${card.color}`}>{card.value}</CardTitle></CardHeader>
                  <CardContent><p className="text-xs text-muted-foreground">{card.subtitle}</p></CardContent>
                </Card>
              ))}
            </section>

            <section className="grid gap-4 xl:grid-cols-3">
              <Card>
                <CardHeader><CardDescription>Revenue Overview</CardDescription></CardHeader>
                <CardContent className="space-y-3">
                  {statusPieData.map((item) => (
                    <DonutStat key={item.label} label={item.label} value={formatUmsMoney(item.value, settings)} color={item.color} />
                  ))}
                  <div className="border-t border-border pt-3">
                    <DonutStat label="Overdue Charges" value={String(dashboard.overdue_charges)} color="#f97316" />
                    <DonutStat label="Active Plans" value={String(dashboard.active_plans)} color="#8b5cf6" />
                  </div>
                </CardContent>
              </Card>

              {categoryChartData.length > 0 ? (
                <Card className="xl:col-span-2">
                  <CardHeader><CardDescription>Charges by Category</CardDescription></CardHeader>
                  <CardContent>
                    <BarChart data={categoryChartData} />
                  </CardContent>
                </Card>
              ) : (
                <Card className="xl:col-span-2">
                  <CardHeader><CardDescription>Charges by Category</CardDescription></CardHeader>
                  <CardContent>
                    <p className="py-8 text-center text-sm text-muted-foreground">No category data available.</p>
                  </CardContent>
                </Card>
              )}
            </section>
          </>
        ) : null}

        <section>
          <form onSubmit={handleSearch} className="mb-4 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search students by name, email, or ID..."
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button type="submit" variant="outline" size="sm">Search</Button>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Sort by</option>
              <option value="balance_desc">Balance (High to Low)</option>
              <option value="balance_asc">Balance (Low to High)</option>
              <option value="name">Name (A-Z)</option>
              <option value="holds">Most Holds</option>
            </select>
          </form>

          <Card>
            <CardHeader>
              <CardDescription>Students</CardDescription>
              <CardTitle>{studentsData?.total ?? 0} students</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {studentsData?.students.map((row) => (
                <button
                  key={row.student.id}
                  type="button"
                  onClick={() => router.push(`/accountant/ledger/${row.student.id}`)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-left text-sm transition-colors hover:bg-muted/60"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{row.student.name}</span>
                    <span className="text-muted-foreground">{formatUmsMoney(row.balance, settings, row.currency)}</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
                    <span>{row.student.identifier}</span>
                    <span>{row.active_holds} holds · {formatDate(row.last_activity)}</span>
                  </div>
                </button>
              ))}
              {(!studentsData || studentsData.students.length === 0) ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No students found.</p>
              ) : null}
            </CardContent>
            {studentsData && studentsData.total_pages > 1 ? (
              <div className="flex items-center justify-between border-t border-border px-4 py-3">
                <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  <ChevronLeft className="size-4" /> Previous
                </Button>
                <span className="text-xs text-muted-foreground">Page {studentsData.page} of {studentsData.total_pages}</span>
                <Button variant="ghost" size="sm" disabled={page >= studentsData.total_pages} onClick={() => setPage((p) => p + 1)}>
                  Next <ChevronRight className="size-4" />
                </Button>
              </div>
            ) : null}
          </Card>
        </section>
      </main>
    </div>
  )
}
