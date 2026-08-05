"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Loader2, Zap } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch } from "@/lib/auth"
import { LedgerNav } from "@/components/accountant/ledger/ledger-nav"

type Category = { id: number; code: string; name: string; is_active: boolean }
type StudentRef = { id: number; name: string; email: string; identifier: string }
type BulkResult = { posted_count: number; error_count: number; charges: Array<unknown>; errors: Array<{ student_id: number; error: string }> }

export function AccountantLedgerBulkPage() {
  const settings = usePublicUmsSettings()
  const currencyCode = settings.localization.currency_code || "USD"
  const [categories, setCategories] = useState<Category[]>([])
  const [studentOptions, setStudentOptions] = useState<StudentRef[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [form, setForm] = useState({ category_id: "", description: "", amount: "", due_date: "" })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [result, setResult] = useState<BulkResult | null>(null)
  const [studentSearch, setStudentSearch] = useState("")

  const loadData = useCallback(async () => {
    const [catData, studData] = await Promise.all([
      apiFetch<{ categories: Category[] }>("/finance/fee-categories"),
      apiFetch<{ students: StudentRef[] }>("/finance/students"),
    ])
    setCategories(catData.categories ?? [])
    setStudentOptions(studData.students ?? [])
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
        .catch(() => {})
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  function toggleStudent(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    const filtered = studentOptions.filter((s) => !studentSearch || s.name.toLowerCase().includes(studentSearch.toLowerCase()) || s.identifier.toLowerCase().includes(studentSearch.toLowerCase()))
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filtered.map((s) => s.id)))
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (selectedIds.size === 0) { setError("Select at least one student."); return }
    setSaving(true)
    setError("")
    setSuccess("")
    setResult(null)
    try {
      const data = await apiFetch<BulkResult>("/finance/ledger/bulk-charge", {
        method: "POST",
        body: JSON.stringify({ ...form, category_id: Number(form.category_id), student_ids: Array.from(selectedIds) }),
      })
      setResult(data)
      setSuccess(`${data.posted_count} charges posted successfully.`)
      setSelectedIds(new Set())
      setForm({ category_id: "", description: "", amount: "", due_date: "" })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to post bulk charges.")
    } finally {
      setSaving(false)
    }
  }

  const filteredStudents = studentOptions.filter((s) => !studentSearch || s.name.toLowerCase().includes(studentSearch.toLowerCase()) || s.identifier.toLowerCase().includes(studentSearch.toLowerCase()))
  const activeCategories = categories.filter((c) => c.is_active)

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: "/accountant/ledger/bulk-charge", title: "Bulk Charge" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <LedgerNav />
        <section className="border-b border-border/70 pb-5">
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
            <Zap className="size-6" /> Bulk Charge
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">Post the same charge to multiple students at once.</p>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {loading ? (
          <div className="flex items-center justify-center py-12"><Loader2 className="size-6 animate-spin text-muted-foreground" /></div>
        ) : (
        <form onSubmit={(e) => void handleSubmit(e)} className="grid gap-6 xl:grid-cols-[1fr_22rem]">
          <Card>
            <CardHeader><CardDescription>Select Students</CardDescription><CardTitle>{selectedIds.size} of {filteredStudents.length} selected</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                <Input placeholder="Search students..." value={studentSearch} onChange={(e) => setStudentSearch(e.target.value)} className="flex-1" />
                <Button type="button" variant="outline" size="sm" onClick={toggleAll}>{selectedIds.size === filteredStudents.length ? "Deselect All" : "Select All"}</Button>
              </div>
              <div className="max-h-96 space-y-1 overflow-y-auto">
                {filteredStudents.map((s) => (
                  <label key={s.id} className={`flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2 text-sm transition-colors ${selectedIds.has(s.id) ? "border-primary bg-primary/5" : "border-border hover:bg-muted/60"}`}>
                    <input type="checkbox" checked={selectedIds.has(s.id)} onChange={() => toggleStudent(s.id)} className="size-4" />
                    <div className="flex-1">
                      <span className="font-medium">{s.name}</span>
                      <span className="ml-2 text-muted-foreground">{s.identifier}</span>
                    </div>
                  </label>
                ))}
                {filteredStudents.length === 0 ? <p className="py-4 text-center text-sm text-muted-foreground">No students found.</p> : null}
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader><CardDescription>Charge Details</CardDescription></CardHeader>
              <CardContent className="grid gap-3">
                <div className="space-y-2">
                  <Label>Category</Label>
                  <select value={form.category_id} onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" required>
                    <option value="">Select category</option>
                    {activeCategories.map((c) => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
                  </select>
                </div>
                <div className="space-y-2"><Label>Description</Label><Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} required /></div>
                <div className="space-y-2"><Label>Amount ({currencyCode})</Label><Input type="number" min="0" step="0.01" value={form.amount} onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))} required /></div>
                <div className="space-y-2"><Label>Due Date</Label><Input type="date" value={form.due_date} onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))} /></div>
                <Button type="submit" disabled={saving || selectedIds.size === 0}>
                  {saving ? <Loader2 className="size-4 animate-spin" /> : <Zap className="size-4" />}
                  Post to {selectedIds.size} Student{selectedIds.size !== 1 ? "s" : ""}
                </Button>
              </CardContent>
            </Card>

            {result ? (
              <Card>
                <CardHeader><CardDescription>Result</CardDescription></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p className="text-emerald-700">{result.posted_count} charges posted</p>
                  {result.error_count > 0 ? (
                    <div>
                      <p className="text-red-700">{result.error_count} errors:</p>
                      {result.errors.map((err, i) => <p key={i} className="text-red-600">Student #{err.student_id}: {err.error}</p>)}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            ) : null}
          </div>
        </form>
        )}
      </main>
    </div>
  )
}
