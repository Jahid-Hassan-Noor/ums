"use client"

import { useEffect, useState } from "react"
import { Clock3, Loader2, Mail, Phone, RefreshCw, ShieldAlert } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"

type EmergencyContact = {
  label: string
  phone: string
  email: string
  available_hours: string
  notes: string
}

type EmergencyContactsResponse = {
  contacts: EmergencyContact[]
  updated_at: string | null
}

function formatUpdatedAt(value: string | null) {
  if (!value) return "Not updated yet"
  return new Date(value).toLocaleString()
}

export function StudentEmergencyContactsPage() {
  const [contacts, setContacts] = useState<EmergencyContact[]>([])
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState("")

  async function loadContacts() {
    const response = await apiFetch<EmergencyContactsResponse>("/student/emergency-contacts")
    setContacts(response.contacts ?? [])
    setUpdatedAt(response.updated_at ?? null)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadContacts()
        .catch((caught) =>
          setError(caught instanceof Error ? caught.message : "Unable to load emergency contacts.")
        )
        .finally(() => setLoading(false))
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  async function refreshContacts() {
    setRefreshing(true)
    setError("")
    try {
      await loadContacts()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to refresh emergency contacts.")
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/emergency-contacts", title: "Emergency Contacts" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Emergency Contacts</h1>
            <p className="text-sm text-muted-foreground">Last updated: {formatUpdatedAt(updatedAt)}</p>
          </div>
          <Button variant="outline" onClick={refreshContacts} disabled={refreshing}>
            {refreshing ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </Button>
        </section>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>
        ) : null}

        {loading ? (
          <div className="flex h-52 items-center justify-center">
            <Loader2 className="size-7 animate-spin text-muted-foreground" />
          </div>
        ) : contacts.length ? (
          <section className="grid gap-4 lg:grid-cols-2">
            {contacts.map((contact, index) => (
              <Card key={`${contact.label}-${index}`} className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardDescription>Contact {index + 1}</CardDescription>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <ShieldAlert className="size-5" />
                    {contact.label}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  {contact.available_hours ? (
                    <p className="flex items-center gap-2 text-muted-foreground">
                      <Clock3 className="size-4" />
                      {contact.available_hours}
                    </p>
                  ) : null}
                  {contact.phone ? (
                    <p className="flex items-center gap-2">
                      <Phone className="size-4 text-muted-foreground" />
                      <a className="font-medium text-primary" href={`tel:${contact.phone}`}>
                        {contact.phone}
                      </a>
                    </p>
                  ) : null}
                  {contact.email ? (
                    <p className="flex items-center gap-2">
                      <Mail className="size-4 text-muted-foreground" />
                      <a className="font-medium text-primary" href={`mailto:${contact.email}`}>
                        {contact.email}
                      </a>
                    </p>
                  ) : null}
                  {contact.notes ? (
                    <p className="border-t border-border/70 pt-3 leading-6 text-muted-foreground">
                      {contact.notes}
                    </p>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </section>
        ) : (
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <ShieldAlert className="size-8 text-muted-foreground" />
              <p className="font-medium">No emergency contacts are available.</p>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
