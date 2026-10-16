"use client"

import Link from "next/link"
import { useCallback, useEffect, useState, type FormEvent } from "react"
import {
  BookOpen,
  BookPlus,
  CheckCircle2,
  DoorOpen,
  Laptop,
  Loader2,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react"

import { Header } from "@/components/layout/header"
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
import {
  DEFAULT_LIBRARY_POLICY,
  libraryDurationLabel,
  libraryServiceEnabled,
  normalizeLibraryPolicy,
  type LibraryPolicy,
  type LibraryServices,
} from "@/lib/library-policy"

type Book = {
  id: number
  title: string
  author: string
  isbn: string
  category: string
  available_copies: number
  total_copies: number
}

type LaptopAsset = {
  id: number
  asset_tag: string
  brand: string
  model: string
  specifications: string
}

type LibraryRoom = {
  id: number
  code: string
  name: string
  location: string
  capacity: number
  facilities: string
  default_duration_minutes: number
}

type BorrowRequest = {
  id: number
  asset_type: "book" | "laptop" | "room"
  status: string
  review_note: string
  book_detail?: Book | null
  laptop_detail?: LaptopAsset | null
  room_detail?: LibraryRoom | null
  created_at: string
}

type AcquisitionRequest = {
  id: number
  title: string
  author: string
  isbn: string
  status: string
  review_note: string
  added_book_detail?: Book | null
  created_at: string
}

type Loan = {
  id: number
  status: string
  due_at: string
  returned_at?: string | null
  is_overdue: boolean
  book_copy_detail?: { accession_number: string; book_title: string } | null
  laptop_detail?: LaptopAsset | null
  room_detail?: LibraryRoom | null
}

type LibraryData = {
  books: Book[]
  laptops: LaptopAsset[]
  rooms: LibraryRoom[]
  requests: BorrowRequest[]
  acquisition_requests: AcquisitionRequest[]
  loans: Loan[]
  borrowing_limit: { max_borrow_at_a_time: number; max_keep_at_a_time: number }
  active_book_loans: number
  active_laptop_loans: number
  active_room_loans: number
  pending_book_requests: number
  pending_laptop_requests: number
  pending_room_requests: number
  library_services: LibraryServices
  library_policy: LibraryPolicy
}

const emptyData: LibraryData = {
  books: [],
  laptops: [],
  rooms: [],
  requests: [],
  acquisition_requests: [],
  loans: [],
  borrowing_limit: { max_borrow_at_a_time: 3, max_keep_at_a_time: 5 },
  active_book_loans: 0,
  active_laptop_loans: 0,
  active_room_loans: 0,
  pending_book_requests: 0,
  pending_laptop_requests: 0,
  pending_room_requests: 0,
  library_services: DEFAULT_LIBRARY_POLICY,
  library_policy: DEFAULT_LIBRARY_POLICY,
}

export function StudentLibraryPage({
  mode,
}: {
  mode: "books" | "laptops" | "rooms"
}) {
  const [data, setData] = useState<LibraryData>(emptyData)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [searchInput, setSearchInput] = useState("")
  const [appliedQuery, setAppliedQuery] = useState("")
  const [hasSearched, setHasSearched] = useState(false)
  const [requestForm, setRequestForm] = useState({
    title: "",
    author: "",
    isbn: "",
    notes: "",
  })

  const loadData = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const params = new URLSearchParams({ section: mode })
      if (mode === "books" && appliedQuery) params.set("q", appliedQuery)
      const response = await apiFetch<LibraryData>(
        `/student/library?${params.toString()}`
      )
      const policy = normalizeLibraryPolicy(response.library_policy ?? response.library_services)
      setData({
        ...response,
        library_services: policy,
        library_policy: policy,
      })
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to load library."
      )
    } finally {
      setLoading(false)
    }
  }, [appliedQuery, mode])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  async function requestAsset(
    assetType: "book" | "laptop" | "room",
    id: number
  ) {
    const savingKey = `${assetType}-${id}`
    setSaving(savingKey)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/student/library", {
        method: "POST",
        body: JSON.stringify(
          assetType === "book"
            ? { asset_type: assetType, book_id: id }
            : assetType === "laptop"
              ? { asset_type: assetType, laptop_id: id }
              : { asset_type: assetType, room_id: id }
        ),
      })
      setSuccess(
        assetType === "room"
          ? "Room reservation request submitted to the library."
          : "Borrowing request submitted to the library."
      )
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to submit request."
      )
    } finally {
      setSaving(null)
    }
  }

  async function cancelRoomReservation(requestId: number) {
    setSaving(`cancel-room-${requestId}`)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/student/library/room-reservations/${requestId}/cancel`, {
        method: "POST",
      })
      setSuccess("Room reservation cancelled.")
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to cancel room reservation."
      )
    } finally {
      setSaving(null)
    }
  }

  async function submitAcquisitionRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving("acquisition")
    setError("")
    setSuccess("")
    try {
      await apiFetch("/student/library/book-requests", {
        method: "POST",
        body: JSON.stringify(requestForm),
      })
      setRequestForm({ title: "", author: "", isbn: "", notes: "" })
      setSuccess("Your request to add this book was sent to the librarian.")
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to submit the book request."
      )
    } finally {
      setSaving(null)
    }
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextQuery = searchInput.trim()
    setHasSearched(true)
    if (nextQuery === appliedQuery) {
      void loadData()
    } else {
      setAppliedQuery(nextQuery)
    }
  }

  const title =
    mode === "books"
      ? "Library Books"
      : mode === "laptops"
        ? "Library Laptops"
        : "Discussion Rooms"
  const description =
    mode === "books"
      ? "Search the catalog by title or author, request an available copy, or suggest a new book."
      : mode === "laptops"
        ? "View and request only laptops that are currently available to borrow."
        : "Check rooms currently open for reservation, then collect the allocated key from the library reception."

  function requestLabel(request: BorrowRequest) {
    if (request.asset_type === "book") return request.book_detail?.title
    if (request.asset_type === "laptop") {
      return `${request.laptop_detail?.brand ?? ""} ${request.laptop_detail?.model ?? ""}`.trim()
    }
    return request.room_detail
      ? `${request.room_detail.name} (${request.room_detail.code})`
      : "Discussion room"
  }

  function loanLabel(loan: Loan) {
    if (loan.book_copy_detail) {
      return `${loan.book_copy_detail.book_title} / ${loan.book_copy_detail.accession_number}`
    }
    if (loan.laptop_detail) {
      return `${loan.laptop_detail.brand} ${loan.laptop_detail.model}`
    }
    return loan.room_detail
      ? `${loan.room_detail.name} (${loan.room_detail.code})`
      : "Discussion room"
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: `/student/library/${mode}`, title },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {title}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </div>
          <Button
            variant="outline"
            onClick={() => void loadData()}
            disabled={loading}
          >
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />{" "}
            Refresh
          </Button>
        </section>

        <nav
          className="grid gap-3 sm:grid-cols-3"
          aria-label="Library sections"
        >
          {libraryServiceEnabled(data.library_policy, "book") ? (
            <Button
              render={<Link href="/student/library/books" />}
              variant={mode === "books" ? "default" : "outline"}
              className="justify-start"
            >
              <BookOpen className="size-4" /> Books
            </Button>
          ) : null}
          {libraryServiceEnabled(data.library_policy, "laptop") ? (
            <Button
              render={<Link href="/student/library/laptops" />}
              variant={mode === "laptops" ? "default" : "outline"}
              className="justify-start"
            >
              <Laptop className="size-4" /> Laptops
            </Button>
          ) : null}
          {libraryServiceEnabled(data.library_policy, "room") ? (
            <Button
              render={<Link href="/student/library/rooms" />}
              variant={mode === "rooms" ? "default" : "outline"}
              className="justify-start"
            >
              <DoorOpen className="size-4" /> Discussion Rooms
            </Button>
          ) : null}
        </nav>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="size-4" /> {success}
          </p>
        ) : null}
        {loading ? (
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        ) : null}

        {mode === "books" && !loading ? (
          <>
            {!data.library_services.books_enabled ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
                <p className="font-semibold text-amber-800">Book Borrowing Temporarily Unavailable</p>
                <p className="mt-1 text-amber-700">The librarian has temporarily paused book borrowing. You can still browse the catalog but cannot submit borrow requests.</p>
              </div>
            ) : null}
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm">
              <p className="font-semibold text-blue-800">Your Borrowing Status</p>
              <p className="mt-1 text-blue-700">
                Books on loan: <span className="font-medium">{data.active_book_loans}</span>
                {" · "}
                Pending requests: <span className="font-medium">{data.pending_book_requests}</span>
                {" · "}
                Limit used (including pending): <span className="font-medium">{data.active_book_loans + data.pending_book_requests}</span> / {data.library_policy.limits.book.max_keep_at_a_time}
                {" · "}
                Can borrow: <span className="font-medium">{Math.max(0, data.library_policy.limits.book.max_borrow_at_a_time - data.active_book_loans - data.pending_book_requests)}</span> more at a time
                {" - "}
                Loan period: <span className="font-medium">{libraryDurationLabel(data.library_policy.loan_periods.book)}</span>
              </p>
            </div>
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(20rem,0.6fr)]">
              <Card>
                <CardHeader>
                  <CardTitle className="flex gap-2">
                    <Search className="size-5" /> Search Books
                  </CardTitle>
                  <CardDescription>
                    The catalog stays hidden until you search by book title or
                    author name.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <form
                    className="flex flex-col gap-2 sm:flex-row"
                    onSubmit={submitSearch}
                  >
                    <Input
                      value={searchInput}
                      onChange={(event) => setSearchInput(event.target.value)}
                      placeholder="Enter a book title or author"
                      aria-label="Book title or author"
                      required
                    />
                    <Button type="submit">
                      <Search className="size-4" /> Search
                    </Button>
                  </form>

                  {!hasSearched ? (
                    <p className="text-sm text-muted-foreground">
                      Search to see matching books.
                    </p>
                  ) : data.books.length ? (
                    <div className="space-y-3">
                      {data.books.map((book) => (
                        <div
                          key={book.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4"
                        >
                          <div>
                            <p className="font-semibold">{book.title}</p>
                            <p className="text-sm text-muted-foreground">
                              {book.author}
                              {book.isbn ? ` · ISBN ${book.isbn}` : ""}
                              {` · ${book.available_copies} available`}
                            </p>
                          </div>
                          <Button
                            size="sm"
                            disabled={
                              !book.available_copies ||
                              !data.library_services.books_enabled ||
                              !data.library_policy.reservation_rules.book.enabled ||
                              saving === `book-${book.id}`
                            }
                            onClick={() => void requestAsset("book", book.id)}
                          >
                            {saving === `book-${book.id}` ? (
                              <Loader2 className="size-4 animate-spin" />
                            ) : null}
                            {book.available_copies
                              ? data.library_services.books_enabled && data.library_policy.reservation_rules.book.enabled
                                ? "Request to Borrow"
                                : "Requests Paused"
                              : "Unavailable"}
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No books matched “{appliedQuery}”. You can request that
                      the library add it.
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex gap-2">
                    <BookPlus className="size-5" /> Request a New Book
                  </CardTitle>
                  <CardDescription>
                    Suggest a title that is not currently available in the
                    library.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form
                    className="space-y-3"
                    onSubmit={submitAcquisitionRequest}
                  >
                    <div>
                      <Label>Book title</Label>
                      <Input
                        value={requestForm.title}
                        onChange={(event) =>
                          setRequestForm({
                            ...requestForm,
                            title: event.target.value,
                          })
                        }
                        required
                      />
                    </div>
                    <div>
                      <Label>Author name</Label>
                      <Input
                        value={requestForm.author}
                        onChange={(event) =>
                          setRequestForm({
                            ...requestForm,
                            author: event.target.value,
                          })
                        }
                        required
                      />
                    </div>
                    <div>
                      <Label>ISBN (optional)</Label>
                      <Input
                        value={requestForm.isbn}
                        onChange={(event) =>
                          setRequestForm({
                            ...requestForm,
                            isbn: event.target.value,
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label>Why do you need this book? (optional)</Label>
                      <Textarea
                        value={requestForm.notes}
                        onChange={(event) =>
                          setRequestForm({
                            ...requestForm,
                            notes: event.target.value,
                          })
                        }
                      />
                    </div>
                    <Button type="submit" disabled={saving === "acquisition" || !data.library_policy.reservation_rules.book.enabled}>
                      {saving === "acquisition" ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <BookPlus className="size-4" />
                      )}
                      Submit Request
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </section>

            <Card>
              <CardHeader>
                <CardTitle>My Book Addition Requests</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                {data.acquisition_requests.map((request) => (
                  <div
                    key={request.id}
                    className="rounded-lg border p-4 text-sm"
                  >
                    <p className="font-semibold">{request.title}</p>
                    <p className="text-muted-foreground">
                      {request.author} · {request.status}
                    </p>
                    {request.review_note ? (
                      <p className="mt-2">{request.review_note}</p>
                    ) : null}
                    {request.added_book_detail ? (
                      <p className="mt-2 text-emerald-700">
                        Added to catalog as {request.added_book_detail.title}.
                      </p>
                    ) : null}
                  </div>
                ))}
                {!data.acquisition_requests.length ? (
                  <p className="text-sm text-muted-foreground">
                    No book addition requests yet.
                  </p>
                ) : null}
              </CardContent>
            </Card>
          </>
        ) : null}

        {mode === "laptops" && !loading ? (
          <>
            {!data.library_services.laptops_enabled ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
                <p className="font-semibold text-amber-800">Laptop Borrowing Currently Disabled</p>
                <p className="mt-1 text-amber-700">The librarian has disabled laptop borrowing. Please check back later.</p>
              </div>
            ) : null}
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm">
              <p className="font-semibold text-blue-800">Your Laptop Status</p>
              <p className="mt-1 text-blue-700">
                Laptops on loan: <span className="font-medium">{data.active_laptop_loans}</span>
                {" · "}
                Pending requests: <span className="font-medium">{data.pending_laptop_requests}</span>
                {" · "}
                Limit used (including pending): <span className="font-medium">{data.active_laptop_loans + data.pending_laptop_requests}</span> / {data.library_policy.limits.laptop.max_keep_at_a_time}
                {" - "}
                Loan period: <span className="font-medium">{libraryDurationLabel(data.library_policy.loan_periods.laptop)}</span>
                {data.active_laptop_loans >= 1 ? " · Return your current laptop before borrowing another." : ""}
              </p>
            </div>
            <Card>
            <CardHeader>
              <CardTitle className="flex gap-2">
                <Laptop className="size-5" /> Available Laptops
              </CardTitle>
              <CardDescription>
                Borrowed, maintenance, lost, and retired laptops are not shown.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {data.laptops.map((laptop) => (
                <div
                  key={laptop.id}
                  className="flex flex-col justify-between gap-4 rounded-lg border p-4"
                >
                  <div>
                    <p className="font-semibold">
                      {laptop.brand} {laptop.model}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {laptop.asset_tag}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {laptop.specifications || "Standard configuration"}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    disabled={saving === `laptop-${laptop.id}` || !data.library_services.laptops_enabled || !data.library_policy.reservation_rules.laptop.enabled}
                    onClick={() => void requestAsset("laptop", laptop.id)}
                  >
                    {saving === `laptop-${laptop.id}` ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : null}
                    {data.library_services.laptops_enabled && data.library_policy.reservation_rules.laptop.enabled ? "Request to Borrow" : "Requests Disabled"}
                  </Button>
                </div>
              ))}
              {!data.laptops.length ? (
                <p className="text-sm text-muted-foreground">
                  No laptops are currently available.
                </p>
              ) : null}
            </CardContent>
          </Card>
          </>
        ) : null}

        {mode === "rooms" && !loading ? (
          <>
            {!data.library_services.rooms_enabled ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
                <p className="font-semibold text-amber-800">Discussion Room Booking Currently Disabled</p>
                <p className="mt-1 text-amber-700">The librarian has disabled discussion room booking. Please check back later.</p>
              </div>
            ) : null}
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm">
              <p className="font-semibold text-blue-800">Your Room Status</p>
              <p className="mt-1 text-blue-700">
                Rooms allocated: <span className="font-medium">{data.active_room_loans}</span>
                {" · "}
                Pending reservations: <span className="font-medium">{data.pending_room_requests}</span>
                {" · "}
                Limit used (including pending): <span className="font-medium">{data.active_room_loans + data.pending_room_requests}</span> / {data.library_policy.limits.room.max_keep_at_a_time}
                {" - "}
                Allocation period: <span className="font-medium">{libraryDurationLabel(data.library_policy.loan_periods.room)}</span>
                {data.active_room_loans >= 1 ? " · Return your current room before reserving another." : ""}
              </p>
            </div>
            <Card>
            <CardHeader>
              <CardTitle className="flex gap-2">
                <DoorOpen className="size-5" /> Available Discussion Rooms
              </CardTitle>
              <CardDescription>
                A reservation holds the room until a librarian allocates its key
                and confirms your return time.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {data.rooms.map((room) => (
                <div
                  key={room.id}
                  className="flex flex-col justify-between gap-4 rounded-lg border p-4"
                >
                  <div>
                    <p className="font-semibold">{room.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {room.code} · {room.location}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Capacity {room.capacity} · Standard allocation{" "}
                      {room.default_duration_minutes} minutes
                    </p>
                    {room.facilities ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        {room.facilities}
                      </p>
                    ) : null}
                  </div>
                  <Button
                    size="sm"
                    disabled={saving === `room-${room.id}` || !data.library_services.rooms_enabled || !data.library_policy.reservation_rules.room.enabled}
                    onClick={() => void requestAsset("room", room.id)}
                  >
                    {saving === `room-${room.id}` ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : null}
                    {data.library_services.rooms_enabled && data.library_policy.reservation_rules.room.enabled ? "Request Reservation" : "Reservations Disabled"}
                  </Button>
                </div>
              ))}
              {!data.rooms.length ? (
                <p className="text-sm text-muted-foreground">
                  No discussion rooms are currently available for reservation.
                </p>
              ) : null}
            </CardContent>
          </Card>
          </>
        ) : null}

        {!loading ? (
          <section className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>
                  {mode === "rooms"
                    ? "My Room Reservations"
                    : "My Borrowing Requests"}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.requests.map((request) => (
                  <div
                    key={request.id}
                    className="rounded-lg border p-3 text-sm"
                  >
                    <p className="font-medium">
                      {requestLabel(request)}
                    </p>
                    <p className="text-muted-foreground">
                      {request.status} ·{" "}
                      {new Date(request.created_at).toLocaleString()}
                    </p>
                    {request.review_note ? (
                      <p className="mt-2">{request.review_note}</p>
                    ) : null}
                    {mode === "rooms" &&
                    request.asset_type === "room" &&
                    request.status === "pending" ? (
                      <Button
                        className="mt-3"
                        size="sm"
                        variant="outline"
                        disabled={saving === `cancel-room-${request.id}`}
                        onClick={() => void cancelRoomReservation(request.id)}
                      >
                        {saving === `cancel-room-${request.id}` ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          <XCircle className="size-4" />
                        )}
                        Cancel Reservation
                      </Button>
                    ) : null}
                  </div>
                ))}
                {!data.requests.length ? (
                  <p className="text-sm text-muted-foreground">
                    {mode === "rooms"
                      ? "No room reservation requests yet."
                      : "No borrowing requests yet."}
                  </p>
                ) : null}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>
                  {mode === "rooms" ? "My Room Allocations" : "My Loans"}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.loans.map((loan) => (
                  <div
                    key={loan.id}
                    className={`rounded-lg border p-3 text-sm ${loan.is_overdue ? "border-red-300 bg-red-50/50" : ""}`}
                  >
                    <p className="font-medium">
                      {loanLabel(loan)}
                    </p>
                    <p className="text-muted-foreground">
                      {loan.status} · Due{" "}
                      {new Date(loan.due_at).toLocaleString()}
                      {loan.is_overdue ? " · Overdue" : ""}
                    </p>
                  </div>
                ))}
                {!data.loans.length ? (
                  <p className="text-sm text-muted-foreground">
                    {mode === "rooms"
                      ? "No room allocations yet."
                      : "No library loans yet."}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          </section>
        ) : null}
      </main>
    </div>
  )
}
