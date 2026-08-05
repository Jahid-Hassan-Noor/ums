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
type Summary = { total: number } & Record<string, number>
type DashboardResponse = {
  title: string
  tickets: Ticket[]
  statuses: Option[]
  summary: Summary
}

export function TechnicianHelpdeskPage() {
  const [title, setTitle] = useState("Service Desk")
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
    const response = await apiFetch<DashboardResponse>("/ict-helpdesk/technician/dashboard")
    const nextTickets = response.tickets ?? []
    setTitle(response.title || "Service Desk")
    setTickets(nextTickets)
    setStatuses(response.statuses ?? [])
    setSummary(response.summary)
    setDrafts(Object.fromEntries(nextTickets.map((ticket) => [ticket.id, { status: ticket.status, note: "" }])))
  }

  useEffect(() => {
    const timer = window.setTimeout(
      () =>
        void loadData().catch((caught) =>
          setError(caught instanceof Error ? caught.message : "Unable to load service desk tickets.")
        ),
      0
    )
    return () => window.clearTimeout(timer)
  }, [])

  const visibleTickets = useMemo(
    () =>
      tickets.filter((ticket) => {
        const matchesStatus = filter === "all" || ticket.status === filter
        const text = `${ticket.reference} ${ticket.subject} ${ticket.student.name} ${ticket.student.student_id} ${ticket.category_label}`.toLowerCase()
        return matchesStatus && text.includes(query.trim().toLowerCase())
      }),
    [filter, query, tickets]
  )

  const summaryCards = useMemo(() => {
    if (!summary) return []
    return [
      { label: "Total", value: summary.total ?? 0 },
      ...statuses.map((status) => ({
        label: status.label,
        value: summary[status.value] ?? 0,
      })),
    ]
  }, [statuses, summary])

  function updateDraft(id: number, field: "status" | "note", value: string) {
    setDrafts((current) => ({
      ...current,
      [id]: {
        status: current[id]?.status ?? statuses[0]?.value ?? "submitted",
        note: current[id]?.note ?? "",
        [field]: value,
      },
    }))
  }

  async function save(ticket: Ticket) {
    setSaving(ticket.id)
    setError("")
    setSuccess("")
    try {
      const draft = drafts[ticket.id] ?? { status: ticket.status, note: "" }
      await apiFetch(`/ict-helpdesk/technician/tickets/${ticket.id}`, {
        method: "PATCH",
        body: JSON.stringify(draft),
      })
      setSuccess(`${ticket.reference} updated successfully.`)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update service desk ticket.")
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/technician", title: "Technician" }, { href: "/technician/helpdesk", title }]} />
      <main className="flex-1 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Review student requests, record progress, and keep submitters informed.
            </p>
          </div>
          <Button variant="outline" onClick={() => void loadData()}>
            <RefreshCw data-icon="inline-start" />
            Refresh
          </Button>
        </section>

        <div className="mt-6 flex flex-col gap-6">
          {error ? (
            <p className="rounded-lg border border-destructive/30 bg-background p-3 text-sm text-destructive">
              {error}
            </p>
          ) : null}
          {success ? (
            <p className="flex items-center gap-2 rounded-lg border bg-background p-3 text-sm text-foreground">
              <CheckCircle2 className="size-4 text-primary" />
              {success}
            </p>
          ) : null}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {summaryCards.length ? (
              summaryCards.map((card) => (
                <Card key={card.label}>
                  <CardHeader>
                    <CardDescription>{card.label}</CardDescription>
                    <CardTitle className="text-3xl">{card.value}</CardTitle>
                  </CardHeader>
                </Card>
              ))
            ) : (
              <Loader2 className="size-6 animate-spin" />
            )}
          </section>

          <section className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 size-4 text-muted-foreground" />
              <Input
                className="pl-9"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search ticket, student, or category"
              />
            </div>
            <select
              className="h-10 rounded-lg border bg-background px-3 text-sm"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="all">All statuses</option>
              {statuses.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            {visibleTickets.map((ticket) => (
              <Card key={ticket.id}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardDescription>
                        {ticket.reference} - {ticket.category_label}
                      </CardDescription>
                      <CardTitle>{ticket.subject}</CardTitle>
                    </div>
                    <Badge variant={ticket.status === "solved" ? "default" : "secondary"}>
                      {ticket.status_label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                  <p className="text-sm leading-6">{ticket.description}</p>
                  <div className="grid gap-2 rounded-lg border bg-muted/25 p-3 text-sm sm:grid-cols-2">
                    <p>
                      <strong>Student:</strong> {ticket.student.name}
                    </p>
                    <p>
                      <strong>Student ID:</strong> {ticket.student.student_id}
                    </p>
                    <p>
                      <strong>Email:</strong> {ticket.student.email || "Not provided"}
                    </p>
                    <p>
                      <strong>Phone:</strong> {ticket.student.phone || "Not provided"}
                    </p>
                    <p>
                      <strong>Location:</strong> {ticket.location || "Not provided"}
                    </p>
                    <p>
                      <strong>Assigned:</strong> {ticket.assigned_to?.name ?? "Unassigned"}
                    </p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-[12rem_minmax(0,1fr)]">
                    <select
                      className="h-10 rounded-lg border bg-background px-3 text-sm"
                      value={drafts[ticket.id]?.status ?? ticket.status}
                      onChange={(event) => updateDraft(ticket.id, "status", event.target.value)}
                    >
                      {statuses.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <Textarea
                      value={drafts[ticket.id]?.note ?? ""}
                      onChange={(event) => updateDraft(ticket.id, "note", event.target.value)}
                      placeholder="Progress or resolution note for the student"
                    />
                  </div>
                  <Button onClick={() => void save(ticket)} disabled={saving === ticket.id}>
                    {saving === ticket.id ? (
                      <Loader2 data-icon="inline-start" className="animate-spin" />
                    ) : (
                      <Save data-icon="inline-start" />
                    )}
                    Update Ticket
                  </Button>
                  {ticket.updates.length ? (
                    <div className="flex flex-col gap-2 border-t pt-4">
                      {ticket.updates
                        .slice()
                        .reverse()
                        .map((update) => (
                          <div key={update.id} className="text-sm">
                            <strong>{update.status_label}</strong>
                            <span className="text-muted-foreground">
                              {" "}
                              - {update.note || update.author_name} -{" "}
                              {new Date(update.created_at).toLocaleString()}
                            </span>
                          </div>
                        ))}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </section>
        </div>
      </main>
    </div>
  )
}
