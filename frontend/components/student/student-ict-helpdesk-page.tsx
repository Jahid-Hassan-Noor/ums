"use client"

import { FormEvent, useEffect, useState } from "react"
import { CheckCircle2, Clock3, Loader2, Send, Wrench } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type Option = { value: string; label: string }
type TicketUpdate = { id: number; status_label: string; note: string; author_name: string; created_at: string }
type Ticket = {
  id: number
  reference: string
  category_label: string
  subject: string
  description: string
  location: string
  status: string
  status_label: string
  resolution_notes: string
  assigned_to: { name: string } | null
  created_at: string
  updates: TicketUpdate[]
}
type TicketsResponse = {
  title: string
  categories: Option[]
  tickets: Ticket[]
}

function badgeVariant(status: string) {
  if (status === "solved") return "default" as const
  if (status === "submitted") return "outline" as const
  return "secondary" as const
}

export function StudentICTHelpdeskPage() {
  const [title, setTitle] = useState("Service Desk")
  const [categories, setCategories] = useState<Option[]>([])
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [category, setCategory] = useState("")
  const [subject, setSubject] = useState("")
  const [description, setDescription] = useState("")
  const [location, setLocation] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  async function loadTickets() {
    const response = await apiFetch<TicketsResponse>("/ict-helpdesk/student/tickets")
    const nextCategories = response.categories ?? []
    setTitle(response.title || "Service Desk")
    setCategories(nextCategories)
    setTickets(response.tickets ?? [])
    setCategory((current) => current || nextCategories[0]?.value || "")
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadTickets().catch((caught) =>
        setError(caught instanceof Error ? caught.message : "Unable to load service desk tickets.")
      )
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  async function submitTicket(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ message: string }>("/ict-helpdesk/student/tickets", {
        method: "POST",
        body: JSON.stringify({ category, subject, description, location }),
      })
      setSuccess(response.message)
      setSubject("")
      setDescription("")
      setLocation("")
      await loadTickets()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit service desk ticket.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/student", title: "Student" }, { href: "/student/ict-helpdesk", title }]} />
      <main className="flex-1 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Submit support requests and follow every progress update here.
          </p>
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

          <section className="grid gap-5 xl:grid-cols-[minmax(0,24rem)_minmax(0,1fr)]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="size-5" />
                  Submit a Request
                </CardTitle>
                <CardDescription>Create one tracked request for the service team.</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="flex flex-col gap-4" onSubmit={submitTicket}>
                  <FieldGroup>
                    <Field>
                      <FieldLabel htmlFor="category">Request category</FieldLabel>
                      <select
                        id="category"
                        className="h-10 w-full rounded-lg border bg-background px-3 text-sm"
                        value={category}
                        onChange={(event) => setCategory(event.target.value)}
                        required
                      >
                        {categories.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="subject">Subject</FieldLabel>
                      <Input
                        id="subject"
                        value={subject}
                        onChange={(event) => setSubject(event.target.value)}
                        placeholder="Briefly describe the request"
                        required
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="description">Details</FieldLabel>
                      <Textarea
                        id="description"
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        placeholder="Include relevant details, errors, and what you already tried."
                        required
                      />
                    </Field>
                    <Field>
                      <FieldLabel htmlFor="location">Location (optional)</FieldLabel>
                      <Input
                        id="location"
                        value={location}
                        onChange={(event) => setLocation(event.target.value)}
                        placeholder="Hostel, lab, classroom, or office"
                      />
                    </Field>
                  </FieldGroup>
                  <Button type="submit" className="w-full" disabled={busy || !category}>
                    {busy ? (
                      <Loader2 data-icon="inline-start" className="animate-spin" />
                    ) : (
                      <Send data-icon="inline-start" />
                    )}
                    Submit to {title}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <div className="flex flex-col gap-4">
              {tickets.length ? (
                tickets.map((ticket) => (
                  <Card key={ticket.id}>
                    <CardHeader>
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <CardDescription>
                            {ticket.reference} - {ticket.category_label}
                          </CardDescription>
                          <CardTitle>{ticket.subject}</CardTitle>
                        </div>
                        <Badge variant={badgeVariant(ticket.status)}>{ticket.status_label}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-4">
                      <p className="text-sm leading-6">{ticket.description}</p>
                      <div className="grid gap-2 text-sm sm:grid-cols-2">
                        <p>
                          <strong>Assigned technician:</strong>{" "}
                          {ticket.assigned_to?.name ?? "Awaiting assignment"}
                        </p>
                        <p>
                          <strong>Submitted:</strong> {new Date(ticket.created_at).toLocaleString()}
                        </p>
                        {ticket.location ? (
                          <p>
                            <strong>Location:</strong> {ticket.location}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex flex-col gap-2 border-t pt-4">
                        <p className="flex items-center gap-2 text-sm font-medium">
                          <Clock3 className="size-4" />
                          Progress history
                        </p>
                        {ticket.updates.map((update) => (
                          <div key={update.id} className="rounded-lg border p-3 text-sm">
                            <div className="flex flex-wrap justify-between gap-2">
                              <strong>{update.status_label}</strong>
                              <span className="text-xs text-muted-foreground">
                                {new Date(update.created_at).toLocaleString()}
                              </span>
                            </div>
                            <p className="mt-1 text-muted-foreground">
                              {update.note || `Updated by ${update.author_name}`}
                            </p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                    <Wrench className="size-8 text-muted-foreground" />
                    <p className="font-medium">No service desk requests submitted</p>
                    <p className="text-sm text-muted-foreground">
                      Your submitted requests and progress updates will appear here.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
