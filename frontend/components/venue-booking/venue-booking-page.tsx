"use client"

import { useCallback, useEffect, useState, type FormEvent } from "react"
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Loader2,
  MapPin,
  XCircle,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"
import { statusBadgeVariant } from "@/lib/status-utils"

type BookingRole = "student" | "teacher" | "technician"

type Venue = {
  id: number
  code: string
  name: string
  building: string
  capacity: number | null
}

type BookingRequest = {
  id: number
  requester: {
    id: number
    name: string
    role: string
    student_id: string
    staff_id: string
  }
  venue: Venue
  booking_type: "event" | "personal"
  purpose: string
  explanation: string
  booking_date: string
  start_time: string
  end_time: string
  status: "pending" | "approved" | "rejected" | "cancelled"
  reviewed_by: string
  rejection_reason: string
  created_at: string
}

type BookingResponse = {
  role: BookingRole
  venues: Venue[]
  requests: BookingRequest[]
}

const emptyForm = {
  venue_id: "",
  booking_type: "event",
  purpose: "",
  explanation: "",
  booking_date: "",
  start_time: "",
  end_time: "",
}

function roleLabel(role: BookingRole) {
  if (role === "technician") return "Technician"
  if (role === "teacher") return "Teacher"
  return "Student"
}

function localDateInputValue() {
  const now = new Date()
  const localTime = new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
  return localTime.toISOString().slice(0, 10)
}

export function VenueBookingPage({ role }: { role: BookingRole }) {
  const isReviewer = role === "technician"
  const [data, setData] = useState<BookingResponse | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [rejectionReasons, setRejectionReasons] = useState<
    Record<number, string>
  >({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const endpoint = isReviewer
    ? "/ict-helpdesk/technician/venue-bookings"
    : `/${role}/venue-bookings`

  const loadData = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await apiFetch<BookingResponse>(endpoint)
      setData(response)
      setError("")
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load venue bookings."
      )
    } finally {
      setIsLoading(false)
    }
  }, [endpoint])

  useEffect(() => {
    const timer = window.setTimeout(() => void loadData(), 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  async function submitRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({ ...form, venue_id: Number(form.venue_id) }),
      })
      setForm(emptyForm)
      setSuccess("Venue booking request submitted for technician review.")
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to submit venue booking request."
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function decide(requestId: number, decision: "approved" | "rejected") {
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(
        `/ict-helpdesk/technician/venue-bookings/${requestId}/decision`,
        {
          method: "POST",
          body: JSON.stringify({
            decision,
            rejection_reason: rejectionReasons[requestId] || "",
          }),
        }
      )
      setSuccess(`Venue booking request ${decision}.`)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to review venue booking request."
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function cancelBooking(request: BookingRequest) {
    setIsSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`${endpoint}/${request.id}/cancel`, {
        method: "POST",
      })
      setSuccess(
        request.status === "approved"
          ? "Venue booking cancelled."
          : "Venue booking request cancelled."
      )
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to cancel venue booking."
      )
    } finally {
      setIsSaving(false)
    }
  }

  const requests = data?.requests || []
  const pendingCount = requests.filter(
    (request) => request.status === "pending"
  ).length
  const approvedCount = requests.filter(
    (request) => request.status === "approved"
  ).length
  const rejectedCount = requests.filter(
    (request) => request.status === "rejected"
  ).length
  const cancelledCount = requests.filter(
    (request) => request.status === "cancelled"
  ).length

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: `/${role}`, title: roleLabel(role) },
          { href: `/${role}/venue-bookings`, title: "Venue Bookings" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {isReviewer ? "Venue Booking Requests" : "Book a Venue"}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {isReviewer
              ? "Review requests and approve only bookings that remain free from class and venue conflicts."
              : "Request an active university venue for an event or personal use. Class schedules and approved bookings are checked automatically."}
          </p>
        </section>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            {success}
          </p>
        ) : null}

        <section className="grid gap-4 sm:grid-cols-4">
          {[
            ["Pending", pendingCount],
            ["Approved", approvedCount],
            ["Rejected", rejectedCount],
            ["Cancelled", cancelledCount],
          ].map(([label, value]) => (
            <Card key={label}>
              <CardHeader>
                <CardDescription>{label}</CardDescription>
                <CardTitle className="text-3xl">{value}</CardTitle>
              </CardHeader>
            </Card>
          ))}
        </section>

        {!isReviewer ? (
          <Card>
            <CardHeader>
              <CardTitle>New Venue Request</CardTitle>
              <CardDescription>
                Provide the exact date, time, and a clear explanation of how the
                venue will be used.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                className="grid gap-4 lg:grid-cols-2"
                onSubmit={submitRequest}
              >
                <div className="space-y-2">
                  <Label htmlFor="venue">Venue</Label>
                  <select
                    id="venue"
                    className="h-9 w-full rounded-lg border border-input bg-transparent px-3 text-sm"
                    required
                    value={form.venue_id}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        venue_id: event.target.value,
                      }))
                    }
                  >
                    <option value="">Select an available venue</option>
                    {(data?.venues || []).map((venue) => (
                      <option key={venue.id} value={venue.id}>
                        {venue.building} - {venue.name}
                        {venue.capacity ? ` (${venue.capacity} people)` : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="booking_type">Use type</Label>
                  <select
                    id="booking_type"
                    className="h-9 w-full rounded-lg border border-input bg-transparent px-3 text-sm"
                    value={form.booking_type}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        booking_type: event.target.value,
                      }))
                    }
                  >
                    <option value="event">Event</option>
                    <option value="personal">Personal use</option>
                  </select>
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label htmlFor="purpose">Purpose</Label>
                  <Input
                    id="purpose"
                    required
                    placeholder="Student society workshop"
                    value={form.purpose}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        purpose: event.target.value,
                      }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="booking_date">Date</Label>
                  <Input
                    id="booking_date"
                    type="date"
                    min={localDateInputValue()}
                    required
                    value={form.booking_date}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        booking_date: event.target.value,
                      }))
                    }
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="start_time">Start time</Label>
                    <Input
                      id="start_time"
                      type="time"
                      required
                      value={form.start_time}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          start_time: event.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="end_time">End time</Label>
                    <Input
                      id="end_time"
                      type="time"
                      required
                      value={form.end_time}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          end_time: event.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label htmlFor="explanation">Detailed explanation</Label>
                  <Textarea
                    id="explanation"
                    minLength={20}
                    required
                    placeholder="Explain the activity, expected attendees, setup, and why this venue is suitable."
                    value={form.explanation}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        explanation: event.target.value,
                      }))
                    }
                  />
                </div>
                <div className="lg:col-span-2">
                  <Button disabled={isSaving || isLoading} type="submit">
                    {isSaving ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <CalendarDays className="size-4" />
                    )}
                    Submit Venue Request
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>{isReviewer ? "All Requests" : "My Requests"}</CardTitle>
            <CardDescription>
              Booking decisions and rejection reasons appear here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            ) : null}
            {!isLoading && !requests.length ? (
              <p className="text-sm text-muted-foreground">
                No venue booking requests yet.
              </p>
            ) : null}
            {requests.map((request) => (
              <article
                key={request.id}
                className="space-y-4 rounded-xl border p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{request.purpose}</h3>
                      <Badge variant={statusBadgeVariant(request.status)}>
                        {request.status}
                      </Badge>
                      <Badge variant="outline">
                        {request.booking_type === "event"
                          ? "Event"
                          : "Personal use"}
                      </Badge>
                    </div>
                    {isReviewer ? (
                      <p className="mt-1 text-sm text-muted-foreground">
                        Requested by {request.requester.name} (
                        {request.requester.role})
                      </p>
                    ) : null}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Requested {new Date(request.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <p className="flex items-center gap-2">
                    <MapPin className="size-4 text-muted-foreground" />
                    {request.venue.building} - {request.venue.name}
                  </p>
                  <p className="flex items-center gap-2">
                    <Clock3 className="size-4 text-muted-foreground" />
                    {request.booking_date} · {request.start_time}-
                    {request.end_time}
                  </p>
                </div>
                <p className="rounded-lg bg-muted/60 p-3 text-sm">
                  {request.explanation}
                </p>
                {request.rejection_reason ? (
                  <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    Rejection reason: {request.rejection_reason}
                  </p>
                ) : null}
                {!isReviewer &&
                (request.status === "pending" ||
                  request.status === "approved") ? (
                  <div className="border-t pt-4">
                    <Button
                      disabled={isSaving}
                      variant="outline"
                      onClick={() => void cancelBooking(request)}
                    >
                      <XCircle className="size-4" />
                      {request.status === "approved"
                        ? "Cancel Booking"
                        : "Cancel Request"}
                    </Button>
                  </div>
                ) : null}
                {isReviewer && request.status === "pending" ? (
                  <div className="space-y-3 border-t pt-4">
                    <div className="space-y-2">
                      <Label htmlFor={`reason-${request.id}`}>
                        Rejection reason
                      </Label>
                      <Input
                        id={`reason-${request.id}`}
                        placeholder="Required only when rejecting"
                        value={rejectionReasons[request.id] || ""}
                        onChange={(event) =>
                          setRejectionReasons((current) => ({
                            ...current,
                            [request.id]: event.target.value,
                          }))
                        }
                      />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        disabled={isSaving}
                        onClick={() => void decide(request.id, "approved")}
                      >
                        <CheckCircle2 className="size-4" /> Approve
                      </Button>
                      <Button
                        disabled={
                          isSaving ||
                          !(rejectionReasons[request.id] || "").trim()
                        }
                        variant="destructive"
                        onClick={() => void decide(request.id, "rejected")}
                      >
                        <XCircle className="size-4" /> Reject
                      </Button>
                    </div>
                  </div>
                ) : null}
              </article>
            ))}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
