"use client"

import { useEffect, useMemo, useState } from "react"
import { CheckCircle2, Loader2, RefreshCw, Save, Search } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type Option = { value: string; label: string }
type Ticket = {
  id: number
  reference: string
  category_label: string
  subject: string
  description: string
  location: string
  status: string
  status_label: string
  assigned_to: { name: string } | null
  student: { name: string; student_id: string; email: string; phone: string }
  created_at: string
  updates: Array<{ id: number; status_label: string; note: string; author_name: string; created_at: string }>
}
type Summary = { total: number; submitted: number; addressed: number; in_progress: number; solved: number }

export function TechnicianHelpdeskPage() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [statuses, setStatuses] = useState<Option[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [filter, setFilter] = useState("all")
  const [query, setQuery] = useState("")
  const [drafts, setDrafts] = useState<Record<number, { status: string; note: string }>>({})
  const [saving, setSaving] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadData() {
    const response = await apiFetch<{ tickets: Ticket[]; statuses: Option[]; summary: Summary }>("/ict-helpdesk/technician/dashboard")
    setTickets(response.tickets ?? [])
    setStatuses(response.statuses ?? [])
    setSummary(response.summary)
    setDrafts(Object.fromEntries((response.tickets ?? []).map((ticket) => [ticket.id, { status: ticket.status, note: "" }])))
  }

  useEffect(() => {
    const timer = window.setTimeout(() => void loadData().catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load ICT Helpdesk.")), 0)
    return () => window.clearTimeout(timer)
  }, [])

  const visibleTickets = useMemo(() => tickets.filter((ticket) => {
    const matchesStatus = filter === "all" || ticket.status === filter
    const text = `${ticket.reference} ${ticket.subject} ${ticket.student.name} ${ticket.student.student_id} ${ticket.category_label}`.toLowerCase()
    return matchesStatus && text.includes(query.trim().toLowerCase())
  }), [filter, query, tickets])

  function updateDraft(id: number, field: "status" | "note", value: string) {
    setDrafts((current) => ({ ...current, [id]: { status: current[id]?.status ?? "submitted", note: current[id]?.note ?? "", [field]: value } }))
  }

  async function save(ticket: Ticket) {
    setSaving(ticket.id)
    setError("")
    setSuccess("")
    try {
      const draft = drafts[ticket.id]
      await apiFetch(`/ict-helpdesk/technician/tickets/${ticket.id}`, { method: "PATCH", body: JSON.stringify(draft) })
      setSuccess(`${ticket.reference} updated successfully.`)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update ICT ticket.")
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/technician", title: "Technician" }, { href: "/technician/helpdesk", title: "ICT Helpdesk" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5"><div><h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">ICT Helpdesk</h1><p className="mt-2 text-sm text-muted-foreground">Review student issues, record progress, and notify students when work advances.</p></div><Button variant="outline" onClick={() => void loadData()}><RefreshCw className="size-4" /> Refresh</Button></section>
        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">{summary ? [["Total", summary.total], ["Submitted", summary.submitted], ["Addressed", summary.addressed], ["In progress", summary.in_progress], ["Solved", summary.solved]].map(([label, value]) => <Card key={label}><CardHeader><CardDescription>{label}</CardDescription><CardTitle className="text-3xl">{value}</CardTitle></CardHeader></Card>) : <Loader2 className="size-6 animate-spin" />}</section>
        <section className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search className="absolute left-3 top-3 size-4 text-muted-foreground" /><Input className="pl-9" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search ticket, student, or category" /></div><select className="h-10 rounded-lg border bg-background px-3 text-sm" value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">All statuses</option>{statuses.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></section>
        <section className="grid gap-4 xl:grid-cols-2">{visibleTickets.map((ticket) => <Card key={ticket.id}><CardHeader><div className="flex flex-wrap items-start justify-between gap-3"><div><CardDescription>{ticket.reference} · {ticket.category_label}</CardDescription><CardTitle>{ticket.subject}</CardTitle></div><Badge variant={ticket.status === "solved" ? "default" : "secondary"}>{ticket.status_label}</Badge></div></CardHeader><CardContent className="space-y-4"><p className="text-sm leading-6">{ticket.description}</p><div className="grid gap-2 rounded-lg border bg-muted/25 p-3 text-sm sm:grid-cols-2"><p><strong>Student:</strong> {ticket.student.name}</p><p><strong>Student ID:</strong> {ticket.student.student_id}</p><p><strong>Email:</strong> {ticket.student.email || "Not provided"}</p><p><strong>Phone:</strong> {ticket.student.phone || "Not provided"}</p><p><strong>Location:</strong> {ticket.location || "Not provided"}</p><p><strong>Assigned:</strong> {ticket.assigned_to?.name ?? "Unassigned"}</p></div><div className="grid gap-3 sm:grid-cols-[12rem_minmax(0,1fr)]"><select className="h-10 rounded-lg border bg-background px-3 text-sm" value={drafts[ticket.id]?.status ?? ticket.status} onChange={(event) => updateDraft(ticket.id, "status", event.target.value)}>{statuses.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><Textarea value={drafts[ticket.id]?.note ?? ""} onChange={(event) => updateDraft(ticket.id, "note", event.target.value)} placeholder="Progress or resolution note for the student" /></div><Button onClick={() => void save(ticket)} disabled={saving === ticket.id}>{saving === ticket.id ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Update Ticket</Button>{ticket.updates.length ? <div className="space-y-2 border-t pt-4">{ticket.updates.slice().reverse().map((update) => <div key={update.id} className="text-sm"><strong>{update.status_label}</strong><span className="text-muted-foreground"> · {update.note || update.author_name} · {new Date(update.created_at).toLocaleString()}</span></div>)}</div> : null}</CardContent></Card>)}</section>
      </main>
    </div>
  )
}
