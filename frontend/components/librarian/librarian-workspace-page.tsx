"use client"

import { useEffect, useMemo, useState } from "react"
import { CheckCircle2, DoorOpen, Loader2, Plus, RefreshCw, RotateCcw } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type Shelf = { id: number; code: string; name: string; location: string }
type Book = { id: number; title: string; author: string; isbn: string; category: string; total_copies: number; available_copies: number; is_active: boolean }
type Copy = { id: number; book: number; accession_number: string; status: string; shelf: number | null; shelf_position: string; shelf_detail?: Shelf | null }
type Laptop = { id: number; asset_tag: string; brand: string; model: string; specifications: string; storage_location: string; status: string }
type LibraryRoom = { id: number; code: string; name: string; location: string; capacity: number; facilities: string; key_reference: string; default_duration_minutes: number; status: string; availability_status: string }
type Student = { id: number; name: string; username: string; student_id: string; email: string }
type Request = { id: number; asset_type: "book" | "laptop" | "room"; status: string; student: number; student_detail: Student; book: number | null; laptop: number | null; room: number | null; book_detail?: Book | null; laptop_detail?: Laptop | null; room_detail?: LibraryRoom | null; notes: string }
type BookAcquisitionRequest = { id: number; title: string; author: string; isbn: string; notes: string; status: string; review_note: string; student_detail: Student; added_book_detail?: Book | null }
type Loan = { id: number; student: number; student_detail: Student; book_copy: number | null; laptop: number | null; room: number | null; book_copy_detail?: Copy & { book?: number }; laptop_detail?: Laptop | null; room_detail?: LibraryRoom | null; due_at: string; status: string; is_overdue: boolean }
type BorrowingLimit = { id: number; student: number | null; student_detail: Student | null; max_borrow_at_a_time: number; max_keep_at_a_time: number; is_default: boolean }

const inputClass = "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"

export function LibrarianWorkspacePage({ mode }: { mode: "books" | "laptops" | "rooms" | "circulation" | "settings" }) {
  const [books, setBooks] = useState<Book[]>([])
  const [copies, setCopies] = useState<Copy[]>([])
  const [shelves, setShelves] = useState<Shelf[]>([])
  const [laptops, setLaptops] = useState<Laptop[]>([])
  const [rooms, setRooms] = useState<LibraryRoom[]>([])
  const [students, setStudents] = useState<Student[]>([])
  const [requests, setRequests] = useState<Request[]>([])
  const [bookRequests, setBookRequests] = useState<BookAcquisitionRequest[]>([])
  const [loans, setLoans] = useState<Loan[]>([])
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [bookForm, setBookForm] = useState({ title: "", author: "", isbn: "", category: "" })
  const [shelfForm, setShelfForm] = useState({ code: "", name: "", location: "" })
  const [copyForm, setCopyForm] = useState({ book_id: "", accession_number: "", shelf: "", shelf_position: "" })
  const [laptopForm, setLaptopForm] = useState({ asset_tag: "", brand: "", model: "", specifications: "", storage_location: "" })
  const [roomForm, setRoomForm] = useState({ code: "", name: "", location: "", capacity: "4", facilities: "", key_reference: "", default_duration_minutes: "120" })
  const [loanForm, setLoanForm] = useState({ request_id: "", student_id: "", asset_type: "book", book_copy_id: "", laptop_id: "", room_id: "", due_at: "", notes: "" })
  const [borrowingLimits, setBorrowingLimits] = useState<BorrowingLimit[]>([])
  const [limitForm, setLimitForm] = useState({ student_id: "", max_borrow_at_a_time: "3", max_keep_at_a_time: "5", is_default: false })
  const [librarySettings, setLibrarySettings] = useState({ books_enabled: true, laptops_enabled: true, rooms_enabled: true })
  const [bookRequestNotes, setBookRequestNotes] = useState<Record<number, string>>({})
  const [bookRequestCatalogIds, setBookRequestCatalogIds] = useState<Record<number, string>>({})

  async function loadData() {
    setError("")
    const [bookData, copyData, shelfData, laptopData, roomData, studentData, requestData, bookRequestData, loanData, limitData, settingsData] = await Promise.all([
      apiFetch<{ books: Book[] }>("/librarian/books"),
      apiFetch<{ copies: Copy[] }>("/librarian/copies"),
      apiFetch<{ shelves: Shelf[] }>("/librarian/shelves"),
      apiFetch<{ laptops: Laptop[] }>("/librarian/laptops"),
      apiFetch<{ rooms: LibraryRoom[] }>("/librarian/rooms"),
      apiFetch<{ students: Student[] }>("/librarian/students"),
      apiFetch<{ requests: Request[] }>("/librarian/requests"),
      apiFetch<{ requests: BookAcquisitionRequest[] }>("/librarian/book-requests"),
      apiFetch<{ loans: Loan[] }>("/librarian/loans"),
      apiFetch<{ limits: BorrowingLimit[] }>("/librarian/borrowing-limits"),
      apiFetch<{ books_enabled: boolean; laptops_enabled: boolean; rooms_enabled: boolean }>("/librarian/library-settings"),
    ])
    setBooks(bookData.books ?? [])
    setCopies(copyData.copies ?? [])
    setShelves(shelfData.shelves ?? [])
    setLaptops(laptopData.laptops ?? [])
    setRooms(roomData.rooms ?? [])
    setStudents(studentData.students ?? [])
    setRequests(requestData.requests ?? [])
    setBookRequests(bookRequestData.requests ?? [])
    setLoans(loanData.loans ?? [])
    setBorrowingLimits(limitData.limits ?? [])
    setLibrarySettings(settingsData ?? { books_enabled: true, laptops_enabled: true, rooms_enabled: true })
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadData()
        .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load library data."))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  const availableCopies = copies.filter((copy) => copy.status === "available")
  const availableLaptops = laptops.filter((laptop) => laptop.status === "available")
  const availableRooms = rooms.filter((room) => room.availability_status === "available")
  const activeLoans = loans.filter((loan) => loan.status === "active")
  const pendingRequests = requests.filter((request) => request.status === "pending")
  const pendingBookRequests = bookRequests.filter((request) => request.status === "pending")
  const bookMap = useMemo(() => new Map(books.map((book) => [book.id, book])), [books])
  const defaultLimit = borrowingLimits.find((l) => l.is_default)
  const studentLimits = borrowingLimits.filter((l) => !l.is_default && l.student_detail)

  function activeBookLoansForStudent(studentId: number): number {
    return activeLoans.filter((loan) => loan.student === studentId && loan.book_copy !== null).length
  }

  function getLimitForStudent(studentId: number) {
    const personal = studentLimits.find((l) => l.student === studentId)
    return personal ?? defaultLimit ?? { max_borrow_at_a_time: 3, max_keep_at_a_time: 5 }
  }

  async function perform(action: () => Promise<unknown>, message: string) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await action()
      setSuccess(message)
      await loadData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save changes.")
    } finally {
      setSaving(false)
    }
  }

  function fulfilRequest(request: Request) {
    setLoanForm({
      request_id: String(request.id),
      student_id: String(request.student),
      asset_type: request.asset_type,
      book_copy_id: "",
      laptop_id: request.laptop ? String(request.laptop) : "",
      room_id: request.room ? String(request.room) : "",
      due_at: "",
      notes: request.notes ?? "",
    })
  }

  const title =
    mode === "books"
      ? "Book Inventory"
      : mode === "laptops"
        ? "Laptop Inventory"
        : mode === "rooms"
          ? "Discussion Rooms"
          : mode === "settings"
            ? "Library Settings"
            : "Circulation"
  const description =
    mode === "books"
      ? "Maintain titles, copies, shelves, and precise shelf positions."
      : mode === "laptops"
        ? "Maintain university laptops available for student borrowing."
        : mode === "rooms"
          ? "Maintain reservable rooms, capacity, facilities, keys, and standard time limits."
          : mode === "settings"
            ? "Control which library services are available to students."
            : "Fulfil student requests, allocate room keys or assets for a time limit, and record returns."

  function requestAssetLabel(request: Request) {
    if (request.asset_type === "book") return request.book_detail?.title
    if (request.asset_type === "laptop") {
      return `${request.laptop_detail?.brand ?? ""} ${request.laptop_detail?.model ?? ""}`.trim()
    }
    return request.room_detail
      ? `${request.room_detail.name} (${request.room_detail.code})`
      : "Discussion room"
  }

  function loanAssetLabel(loan: Loan) {
    if (loan.book_copy) {
      return `${bookMap.get(loan.book_copy_detail?.book ?? 0)?.title ?? "Book"} / ${loan.book_copy_detail?.accession_number}`
    }
    if (loan.laptop_detail) {
      return `${loan.laptop_detail.asset_tag} / ${loan.laptop_detail.brand} ${loan.laptop_detail.model}`
    }
    return loan.room_detail
      ? `${loan.room_detail.name} (${loan.room_detail.code}) · Key ${loan.room_detail.key_reference || "not labelled"}`
      : "Discussion room"
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/librarian", title: "Librarian" }, { href: `/librarian/${mode}`, title }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </div>
          <Button variant="outline" onClick={() => void loadData()} disabled={loading || saving}>
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </section>
        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}
        {loading ? <Loader2 className="size-6 animate-spin text-muted-foreground" /> : null}

        {mode === "books" && !loading ? (
          <>
            <section className="grid gap-4 xl:grid-cols-3">
              <Card>
                <CardHeader><CardTitle>Add Book Title</CardTitle><CardDescription>Create one catalog title, then add physical copies.</CardDescription></CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={(event) => {
                    event.preventDefault()
                    void perform(() => apiFetch("/librarian/books", { method: "POST", body: JSON.stringify(bookForm) }), "Book title added.")
                    setBookForm({ title: "", author: "", isbn: "", category: "" })
                  }}>
                    <Input placeholder="Title" value={bookForm.title} onChange={(e) => setBookForm({ ...bookForm, title: e.target.value })} required />
                    <Input placeholder="Author" value={bookForm.author} onChange={(e) => setBookForm({ ...bookForm, author: e.target.value })} required />
                    <Input placeholder="ISBN" value={bookForm.isbn} onChange={(e) => setBookForm({ ...bookForm, isbn: e.target.value })} />
                    <Input placeholder="Category" value={bookForm.category} onChange={(e) => setBookForm({ ...bookForm, category: e.target.value })} />
                    <Button type="submit" disabled={saving}><Plus className="size-4" /> Add Book</Button>
                  </form>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Add Shelf</CardTitle><CardDescription>Define the shelf and its physical location.</CardDescription></CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={(event) => {
                    event.preventDefault()
                    void perform(() => apiFetch("/librarian/shelves", { method: "POST", body: JSON.stringify(shelfForm) }), "Shelf added.")
                    setShelfForm({ code: "", name: "", location: "" })
                  }}>
                    <Input placeholder="Shelf code" value={shelfForm.code} onChange={(e) => setShelfForm({ ...shelfForm, code: e.target.value })} required />
                    <Input placeholder="Shelf name" value={shelfForm.name} onChange={(e) => setShelfForm({ ...shelfForm, name: e.target.value })} required />
                    <Input placeholder="Location, e.g. Level 1 East" value={shelfForm.location} onChange={(e) => setShelfForm({ ...shelfForm, location: e.target.value })} required />
                    <Button type="submit" disabled={saving}><Plus className="size-4" /> Add Shelf</Button>
                  </form>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Add Physical Copy</CardTitle><CardDescription>Give each copy its own accession number and shelf position.</CardDescription></CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={(event) => {
                    event.preventDefault()
                    void perform(
                      () => apiFetch(`/librarian/books/${copyForm.book_id}/copies`, { method: "POST", body: JSON.stringify({ accession_number: copyForm.accession_number, shelf: Number(copyForm.shelf), shelf_position: copyForm.shelf_position }) }),
                      "Book copy added."
                    )
                    setCopyForm({ book_id: "", accession_number: "", shelf: "", shelf_position: "" })
                  }}>
                    <select className={inputClass} value={copyForm.book_id} onChange={(e) => setCopyForm({ ...copyForm, book_id: e.target.value })} required>
                      <option value="">Select book</option>{books.filter((book) => book.is_active).map((book) => <option key={book.id} value={book.id}>{book.title}</option>)}
                    </select>
                    <Input placeholder="Accession number" value={copyForm.accession_number} onChange={(e) => setCopyForm({ ...copyForm, accession_number: e.target.value })} required />
                    <select className={inputClass} value={copyForm.shelf} onChange={(e) => setCopyForm({ ...copyForm, shelf: e.target.value })} required>
                      <option value="">Select shelf</option>{shelves.map((shelf) => <option key={shelf.id} value={shelf.id}>{shelf.code} - {shelf.location}</option>)}
                    </select>
                    <Input placeholder="Position, e.g. Bay 3 / Row 2" value={copyForm.shelf_position} onChange={(e) => setCopyForm({ ...copyForm, shelf_position: e.target.value })} />
                    <Button type="submit" disabled={saving}><Plus className="size-4" /> Add Copy</Button>
                  </form>
                </CardContent>
              </Card>
            </section>
            <Card>
              <CardHeader>
                <CardTitle>Student Book Addition Requests</CardTitle>
                <CardDescription>{pendingBookRequests.length} requests are waiting for a library decision.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {bookRequests.map((request) => (
                  <div key={request.id} className="rounded-lg border p-4">
                    <div className="flex flex-wrap justify-between gap-3">
                      <div>
                        <p className="font-semibold">{request.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {request.author}{request.isbn ? ` · ISBN ${request.isbn}` : ""} · requested by {request.student_detail.name}
                        </p>
                        {request.notes ? <p className="mt-2 text-sm">{request.notes}</p> : null}
                      </div>
                      <span className="text-sm font-medium capitalize">{request.status}</span>
                    </div>
                    {request.status === "pending" ? (
                      <div className="mt-4 grid gap-2 lg:grid-cols-[minmax(12rem,0.8fr)_minmax(15rem,1fr)_auto_auto]">
                        <select
                          className={inputClass}
                          value={bookRequestCatalogIds[request.id] ?? ""}
                          onChange={(event) => setBookRequestCatalogIds({ ...bookRequestCatalogIds, [request.id]: event.target.value })}
                        >
                          <option value="">Select added catalog title</option>
                          {books.filter((book) => book.is_active).map((book) => <option key={book.id} value={book.id}>{book.title} — {book.author}</option>)}
                        </select>
                        <Input
                          placeholder="Response to student"
                          value={bookRequestNotes[request.id] ?? ""}
                          onChange={(event) => setBookRequestNotes({ ...bookRequestNotes, [request.id]: event.target.value })}
                        />
                        <Button
                          size="sm"
                          disabled={saving || !bookRequestCatalogIds[request.id]}
                          onClick={() => void perform(
                            () => apiFetch(`/librarian/book-requests/${request.id}`, {
                              method: "PATCH",
                              body: JSON.stringify({
                                status: "added",
                                book_id: Number(bookRequestCatalogIds[request.id]),
                                review_note: bookRequestNotes[request.id] ?? "",
                              }),
                            }),
                            "Book request marked as added."
                          )}
                        >
                          Mark Added
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={saving}
                          onClick={() => void perform(
                            () => apiFetch(`/librarian/book-requests/${request.id}`, {
                              method: "PATCH",
                              body: JSON.stringify({
                                status: "unavailable",
                                review_note: bookRequestNotes[request.id] ?? "",
                              }),
                            }),
                            "Student notified that the book cannot be added."
                          )}
                        >
                          Not Available
                        </Button>
                      </div>
                    ) : (
                      <div className="mt-3 text-sm">
                        {request.review_note ? <p>{request.review_note}</p> : null}
                        {request.added_book_detail ? <p className="text-emerald-700">Catalog title: {request.added_book_detail.title}</p> : null}
                      </div>
                    )}
                  </div>
                ))}
                {!bookRequests.length ? <p className="text-sm text-muted-foreground">No student book addition requests yet.</p> : null}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Book List</CardTitle><CardDescription>{books.length} titles and {copies.length} physical copies.</CardDescription></CardHeader>
              <CardContent className="space-y-3">
                {books.map((book) => (
                  <div key={book.id} className="rounded-lg border p-4">
                    <div className="flex flex-wrap justify-between gap-3">
                      <div><p className="font-semibold">{book.title}</p><p className="text-sm text-muted-foreground">{book.author} {book.isbn ? `/ ${book.isbn}` : ""}</p></div>
                      <div className="text-sm"><span className="font-medium">{book.available_copies}</span> available / {book.total_copies} copies</div>
                    </div>
                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      {copies.filter((copy) => copy.book === book.id).map((copy) => (
                        <div key={copy.id} className="rounded-md bg-muted/50 p-3 text-sm">
                          <p className="font-medium">{copy.accession_number} · {copy.status}</p>
                          <p className="text-muted-foreground">{copy.shelf_detail ? `${copy.shelf_detail.code}, ${copy.shelf_detail.location}` : "Shelf not assigned"} {copy.shelf_position ? `/ ${copy.shelf_position}` : ""}</p>
                          <div className="mt-3 grid gap-2 sm:grid-cols-3">
                            <select className={inputClass} value={copy.shelf ?? ""} onChange={(event) => void perform(() => apiFetch(`/librarian/copies/${copy.id}`, { method: "PATCH", body: JSON.stringify({ shelf: event.target.value ? Number(event.target.value) : null }) }), "Copy shelf updated.")}>
                              <option value="">No shelf</option>{shelves.map((shelf) => <option key={shelf.id} value={shelf.id}>{shelf.code}</option>)}
                            </select>
                            <Input
                              defaultValue={copy.shelf_position}
                              placeholder="Shelf position"
                              onBlur={(event) => {
                                if (event.target.value !== copy.shelf_position) {
                                  void perform(() => apiFetch(`/librarian/copies/${copy.id}`, { method: "PATCH", body: JSON.stringify({ shelf_position: event.target.value }) }), "Copy position updated.")
                                }
                              }}
                            />
                            <select className={inputClass} value={copy.status} onChange={(event) => void perform(() => apiFetch(`/librarian/copies/${copy.id}`, { method: "PATCH", body: JSON.stringify({ status: event.target.value }) }), "Copy status updated.")}>
                              {["available", "loaned", "maintenance", "lost"].map((value) => <option key={value} value={value}>{value}</option>)}
                            </select>
                          </div>
                        </div>
                      ))}
                    </div>
                    {book.is_active ? <Button className="mt-3" size="sm" variant="outline" onClick={() => void perform(() => apiFetch(`/librarian/books/${book.id}`, { method: "DELETE" }), "Book title deactivated.")}>Deactivate title</Button> : null}
                  </div>
                ))}
              </CardContent>
            </Card>
          </>
        ) : null}

        {mode === "laptops" && !loading ? (
          <section className="grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)]">
            <Card>
              <CardHeader><CardTitle>Add Laptop</CardTitle><CardDescription>Register a university laptop for borrowing.</CardDescription></CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={(event) => {
                  event.preventDefault()
                  void perform(() => apiFetch("/librarian/laptops", { method: "POST", body: JSON.stringify(laptopForm) }), "Laptop added.")
                  setLaptopForm({ asset_tag: "", brand: "", model: "", specifications: "", storage_location: "" })
                }}>
                  <Input placeholder="Asset tag" value={laptopForm.asset_tag} onChange={(e) => setLaptopForm({ ...laptopForm, asset_tag: e.target.value })} required />
                  <Input placeholder="Brand" value={laptopForm.brand} onChange={(e) => setLaptopForm({ ...laptopForm, brand: e.target.value })} required />
                  <Input placeholder="Model" value={laptopForm.model} onChange={(e) => setLaptopForm({ ...laptopForm, model: e.target.value })} required />
                  <Input placeholder="Specifications" value={laptopForm.specifications} onChange={(e) => setLaptopForm({ ...laptopForm, specifications: e.target.value })} />
                  <Input placeholder="Storage location" value={laptopForm.storage_location} onChange={(e) => setLaptopForm({ ...laptopForm, storage_location: e.target.value })} />
                  <Button type="submit" disabled={saving}><Plus className="size-4" /> Add Laptop</Button>
                </form>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Laptop Assets</CardTitle><CardDescription>{availableLaptops.length} of {laptops.length} laptops available.</CardDescription></CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                {laptops.map((laptop) => (
                  <div key={laptop.id} className="rounded-lg border p-4">
                    <p className="font-semibold">{laptop.asset_tag}</p>
                    <p className="text-sm text-muted-foreground">{laptop.brand} {laptop.model}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{laptop.specifications || "No specifications"} · {laptop.storage_location || "No storage location"}</p>
                    <Label className="mt-3 block">Status</Label>
                    <select className={inputClass} value={laptop.status} onChange={(e) => void perform(() => apiFetch(`/librarian/laptops/${laptop.id}`, { method: "PATCH", body: JSON.stringify({ status: e.target.value }) }), "Laptop status updated.")}>
                      {["available", "loaned", "maintenance", "retired", "lost"].map((value) => <option key={value} value={value}>{value}</option>)}
                    </select>
                  </div>
                ))}
              </CardContent>
            </Card>
          </section>
        ) : null}

        {mode === "rooms" && !loading ? (
          <section className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)]">
            <Card>
              <CardHeader>
                <CardTitle className="flex gap-2"><DoorOpen className="size-5" /> Add Discussion Room</CardTitle>
                <CardDescription>Register the room, reception key, and normal allocation period.</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={(event) => {
                  event.preventDefault()
                  void perform(
                    () => apiFetch("/librarian/rooms", {
                      method: "POST",
                      body: JSON.stringify({
                        ...roomForm,
                        capacity: Number(roomForm.capacity),
                        default_duration_minutes: Number(roomForm.default_duration_minutes),
                      }),
                    }),
                    "Discussion room added."
                  )
                  setRoomForm({ code: "", name: "", location: "", capacity: "4", facilities: "", key_reference: "", default_duration_minutes: "120" })
                }}>
                  <Input placeholder="Room code" value={roomForm.code} onChange={(e) => setRoomForm({ ...roomForm, code: e.target.value })} required />
                  <Input placeholder="Room name" value={roomForm.name} onChange={(e) => setRoomForm({ ...roomForm, name: e.target.value })} required />
                  <Input placeholder="Location" value={roomForm.location} onChange={(e) => setRoomForm({ ...roomForm, location: e.target.value })} required />
                  <div><Label>Capacity</Label><Input type="number" min="1" value={roomForm.capacity} onChange={(e) => setRoomForm({ ...roomForm, capacity: e.target.value })} required /></div>
                  <Input placeholder="Facilities, e.g. display, whiteboard" value={roomForm.facilities} onChange={(e) => setRoomForm({ ...roomForm, facilities: e.target.value })} />
                  <Input placeholder="Reception key reference" value={roomForm.key_reference} onChange={(e) => setRoomForm({ ...roomForm, key_reference: e.target.value })} />
                  <div><Label>Standard allocation (minutes)</Label><Input type="number" min="15" value={roomForm.default_duration_minutes} onChange={(e) => setRoomForm({ ...roomForm, default_duration_minutes: e.target.value })} required /></div>
                  <Button type="submit" disabled={saving}><Plus className="size-4" /> Add Room</Button>
                </form>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Room Inventory</CardTitle><CardDescription>{availableRooms.length} of {rooms.length} rooms open for new reservations.</CardDescription></CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                {rooms.map((room) => (
                  <div key={room.id} className="rounded-lg border p-4">
                    <p className="font-semibold">{room.name} · {room.code}</p>
                    <p className="text-sm text-muted-foreground">{room.location} · Capacity {room.capacity}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{room.facilities || "No facilities listed"} · Key {room.key_reference || "not labelled"} · {room.default_duration_minutes} minutes</p>
                    <Label className="mt-3 block">Status</Label>
                    <select className={inputClass} value={room.status} onChange={(event) => void perform(() => apiFetch(`/librarian/rooms/${room.id}`, { method: "PATCH", body: JSON.stringify({ status: event.target.value }) }), "Room status updated.")}>
                      {["available", "in_use", "maintenance", "inactive"].map((value) => <option key={value} value={value}>{value === "available" && room.availability_status === "reserved" ? "reserved" : value.replace("_", " ")}</option>)}
                    </select>
                  </div>
                ))}
                {!rooms.length ? <p className="text-sm text-muted-foreground">No discussion rooms have been registered.</p> : null}
              </CardContent>
            </Card>
          </section>
        ) : null}

        {mode === "circulation" && !loading ? (
          <>
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
              <Card>
                <CardHeader><CardTitle>Pending Student Requests</CardTitle><CardDescription>{pendingRequests.length} requests awaiting action.</CardDescription></CardHeader>
                <CardContent className="space-y-3">
                  {pendingRequests.map((request) => (
                    <div key={request.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4">
                      <div>
                        <p className="font-semibold">{request.student_detail.name}</p>
                        <p className="text-sm text-muted-foreground">{requestAssetLabel(request)}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => fulfilRequest(request)}>Fulfil</Button>
                        <Button size="sm" variant="outline" onClick={() => void perform(() => apiFetch(`/librarian/requests/${request.id}`, { method: "PATCH", body: JSON.stringify({ status: "rejected" }) }), "Request rejected.")}>Reject</Button>
                      </div>
                    </div>
                  ))}
                  {!pendingRequests.length ? <p className="text-sm text-muted-foreground">No pending requests.</p> : null}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Assign Timed Loan or Room</CardTitle><CardDescription>Issue an asset or room key directly, or fulfil a selected request.</CardDescription></CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={(event) => {
                    event.preventDefault()
                    void perform(() => apiFetch("/librarian/loans", {
                      method: "POST",
                      body: JSON.stringify({
                        request_id: loanForm.request_id ? Number(loanForm.request_id) : null,
                        student_id: Number(loanForm.student_id),
                        book_copy_id: loanForm.asset_type === "book" ? Number(loanForm.book_copy_id) : null,
                        laptop_id: loanForm.asset_type === "laptop" ? Number(loanForm.laptop_id) : null,
                        room_id: loanForm.asset_type === "room" ? Number(loanForm.room_id) : null,
                        due_at: new Date(loanForm.due_at).toISOString(),
                        notes: loanForm.notes,
                      }),
                    }), loanForm.asset_type === "room" ? "Room key allocated." : "Loan assigned.")
                    setLoanForm({ request_id: "", student_id: "", asset_type: "book", book_copy_id: "", laptop_id: "", room_id: "", due_at: "", notes: "" })
                  }}>
                    <select className={inputClass} value={loanForm.student_id} onChange={(e) => setLoanForm({ ...loanForm, student_id: e.target.value })} required>
                      <option value="">Select student</option>{students.map((student) => <option key={student.id} value={student.id}>{student.name} ({student.student_id || student.username})</option>)}
                    </select>
                    <select className={inputClass} value={loanForm.asset_type} onChange={(e) => setLoanForm({ ...loanForm, asset_type: e.target.value, book_copy_id: "", laptop_id: "", room_id: "" })}>
                      <option value="book">Book</option><option value="laptop">Laptop</option><option value="room">Discussion room</option>
                    </select>
                    {loanForm.asset_type === "book" ? (
                      <select className={inputClass} value={loanForm.book_copy_id} onChange={(e) => setLoanForm({ ...loanForm, book_copy_id: e.target.value })} required>
                        <option value="">Select available copy</option>{availableCopies.filter((copy) => {
                          const request = pendingRequests.find((row) => String(row.id) === loanForm.request_id)
                          return !request?.book || copy.book === request.book
                        }).map((copy) => <option key={copy.id} value={copy.id}>{bookMap.get(copy.book)?.title} / {copy.accession_number}</option>)}
                      </select>
                    ) : loanForm.asset_type === "laptop" ? (
                      <select className={inputClass} value={loanForm.laptop_id} onChange={(e) => setLoanForm({ ...loanForm, laptop_id: e.target.value })} required>
                        <option value="">Select available laptop</option>{availableLaptops.map((laptop) => <option key={laptop.id} value={laptop.id}>{laptop.asset_tag} / {laptop.brand} {laptop.model}</option>)}
                      </select>
                    ) : (
                      <select className={inputClass} value={loanForm.room_id} onChange={(e) => setLoanForm({ ...loanForm, room_id: e.target.value })} required>
                        <option value="">Select reserved or available room</option>{rooms.filter((room) => {
                          const request = pendingRequests.find((row) => String(row.id) === loanForm.request_id)
                          return room.status === "available" && (room.availability_status === "available" || room.id === request?.room)
                        }).map((room) => <option key={room.id} value={room.id}>{room.code} / {room.name} / Key {room.key_reference || "not labelled"}</option>)}
                      </select>
                    )}
                    <div><Label>Due date and time</Label><Input type="datetime-local" value={loanForm.due_at} onChange={(e) => setLoanForm({ ...loanForm, due_at: e.target.value })} required /></div>
                    <Input placeholder="Loan notes" value={loanForm.notes} onChange={(e) => setLoanForm({ ...loanForm, notes: e.target.value })} />
                    <Button type="submit" disabled={saving}><RotateCcw className="size-4" /> Assign Loan</Button>
                  </form>
                </CardContent>
              </Card>
            </section>
            <Card>
              <CardHeader><CardTitle>Active Loans and Room Allocations</CardTitle><CardDescription>{activeLoans.length} assets or rooms currently assigned.</CardDescription></CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {activeLoans.map((loan) => (
                  <div key={loan.id} className={`rounded-lg border p-4 ${loan.is_overdue ? "border-red-300 bg-red-50/50" : ""}`}>
                    <p className="font-semibold">{loan.student_detail.name}</p>
                    <p className="text-sm text-muted-foreground">{loanAssetLabel(loan)}</p>
                    <p className="mt-2 text-xs text-muted-foreground">Due {new Date(loan.due_at).toLocaleString()}{loan.is_overdue ? " · Overdue" : ""}</p>
                    <Button className="mt-3" size="sm" onClick={() => void perform(() => apiFetch(`/librarian/loans/${loan.id}/return`, { method: "POST", body: JSON.stringify({}) }), loan.room ? "Room key returned and room released." : "Return confirmed.")}>{loan.room ? "Confirm Key Return" : "Confirm Return"}</Button>
                  </div>
                ))}
              </CardContent>
            </Card>
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
              <Card>
                <CardHeader><CardTitle>Borrowing Limits</CardTitle><CardDescription>Default and per-student limits for books. Laptops and rooms are always limited to 1.</CardDescription></CardHeader>
                <CardContent className="space-y-3">
                  {defaultLimit ? (
                    <div className="rounded-lg border p-4">
                      <p className="font-semibold">Default Limit</p>
                      <p className="text-sm text-muted-foreground">Borrow: {defaultLimit.max_borrow_at_a_time} at a time · Keep: {defaultLimit.max_keep_at_a_time} max</p>
                    </div>
                  ) : (
                    <div className="rounded-lg border p-4">
                      <p className="font-semibold">Default Limit</p>
                      <p className="text-sm text-muted-foreground">Borrow: 3 at a time · Keep: 5 max</p>
                    </div>
                  )}
                  {studentLimits.map((limit) => (
                    <div key={limit.id} className="rounded-lg border p-4">
                      <div className="flex flex-wrap justify-between gap-3">
                        <div>
                          <p className="font-semibold">{limit.student_detail?.name}</p>
                          <p className="text-sm text-muted-foreground">Borrow: {limit.max_borrow_at_a_time} at a time · Keep: {limit.max_keep_at_a_time} max</p>
                        </div>
                        <Button size="sm" variant="outline" onClick={() => void perform(() => apiFetch(`/librarian/borrowing-limits/${limit.id}`, { method: "DELETE" }), "Student limit removed. Reverted to default.")}>Remove</Button>
                      </div>
                    </div>
                  ))}
                  {activeLoans.filter((loan) => loan.book_copy !== null).length > 0 ? (
                    <div className="rounded-lg border p-4">
                      <p className="font-semibold text-sm mb-2">Current Book Holdings</p>
                      {students.filter((s) => activeBookLoansForStudent(s.id) > 0).map((student) => {
                        const limit = getLimitForStudent(student.id)
                        const held = activeBookLoansForStudent(student.id)
                        return (
                          <p key={student.id} className="text-sm text-muted-foreground">
                            {student.name}: {held}/{limit.max_keep_at_a_time} books held
                          </p>
                        )
                      })}
                    </div>
                  ) : null}
                  <Card className="border-dashed">
                    <CardHeader><CardTitle className="text-base">Set Per-Student Limit</CardTitle><CardDescription>Override the default for a specific student.</CardDescription></CardHeader>
                    <CardContent>
                      <form className="space-y-3" onSubmit={(event) => {
                        event.preventDefault()
                        void perform(() => apiFetch("/librarian/borrowing-limits", {
                          method: "POST",
                          body: JSON.stringify({
                            student_id: Number(limitForm.student_id),
                            max_borrow_at_a_time: Number(limitForm.max_borrow_at_a_time),
                            max_keep_at_a_time: Number(limitForm.max_keep_at_a_time),
                            is_default: false,
                          }),
                        }), "Student borrowing limit set.")
                        setLimitForm({ student_id: "", max_borrow_at_a_time: "3", max_keep_at_a_time: "5", is_default: false })
                      }}>
                        <select className={inputClass} value={limitForm.student_id} onChange={(e) => setLimitForm({ ...limitForm, student_id: e.target.value })} required>
                          <option value="">Select student</option>{students.map((student) => <option key={student.id} value={student.id}>{student.name} ({student.student_id || student.username})</option>)}
                        </select>
                        <div className="grid grid-cols-2 gap-3">
                          <div><Label>Max borrow at a time</Label><Input type="number" min="1" value={limitForm.max_borrow_at_a_time} onChange={(e) => setLimitForm({ ...limitForm, max_borrow_at_a_time: e.target.value })} required /></div>
                          <div><Label>Max keep at a time</Label><Input type="number" min="1" value={limitForm.max_keep_at_a_time} onChange={(e) => setLimitForm({ ...limitForm, max_keep_at_a_time: e.target.value })} required /></div>
                        </div>
                        <Button type="submit" disabled={saving}>Set Limit</Button>
                      </form>
                    </CardContent>
                  </Card>
                </CardContent>
              </Card>
            </section>
          </>
        ) : null}

        {mode === "settings" && !loading ? (
          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <Card>
              <CardHeader>
                <CardTitle>Book Borrowing</CardTitle>
                <CardDescription>Control whether students can borrow books. When disabled, the books page stays visible but students cannot submit borrow requests.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <p className="font-semibold">Book Borrowing Service</p>
                    <p className="text-sm text-muted-foreground">
                      Currently <span className={librarySettings.books_enabled ? "text-emerald-600" : "text-red-600"}>{librarySettings.books_enabled ? "enabled" : "disabled"}</span>
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant={librarySettings.books_enabled ? "outline" : "default"}
                    disabled={saving}
                    onClick={() => void perform(
                      () => apiFetch("/librarian/library-settings", {
                        method: "PATCH",
                        body: JSON.stringify({ books_enabled: !librarySettings.books_enabled }),
                      }).then(() => setLibrarySettings(prev => ({ ...prev, books_enabled: !prev.books_enabled }))),
                      librarySettings.books_enabled ? "Book borrowing disabled." : "Book borrowing enabled."
                    )}
                  >
                    {librarySettings.books_enabled ? "Disable" : "Enable"}
                  </Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Laptop Borrowing</CardTitle>
                <CardDescription>Control whether students can borrow laptops. When disabled, the laptops option disappears from student and librarian sidebars.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <p className="font-semibold">Laptop Borrowing Service</p>
                    <p className="text-sm text-muted-foreground">
                      Currently <span className={librarySettings.laptops_enabled ? "text-emerald-600" : "text-red-600"}>{librarySettings.laptops_enabled ? "enabled" : "disabled"}</span>
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant={librarySettings.laptops_enabled ? "outline" : "default"}
                    disabled={saving}
                    onClick={() => void perform(
                      () => apiFetch("/librarian/library-settings", {
                        method: "PATCH",
                        body: JSON.stringify({ laptops_enabled: !librarySettings.laptops_enabled }),
                      }).then(() => setLibrarySettings(prev => ({ ...prev, laptops_enabled: !prev.laptops_enabled }))),
                      librarySettings.laptops_enabled ? "Laptop borrowing disabled." : "Laptop borrowing enabled."
                    )}
                  >
                    {librarySettings.laptops_enabled ? "Disable" : "Enable"}
                  </Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Discussion Room Booking</CardTitle>
                <CardDescription>Control whether students can reserve discussion rooms. When disabled, the rooms option disappears from student and librarian sidebars.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <p className="font-semibold">Discussion Room Booking Service</p>
                    <p className="text-sm text-muted-foreground">
                      Currently <span className={librarySettings.rooms_enabled ? "text-emerald-600" : "text-red-600"}>{librarySettings.rooms_enabled ? "enabled" : "disabled"}</span>
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant={librarySettings.rooms_enabled ? "outline" : "default"}
                    disabled={saving}
                    onClick={() => void perform(
                      () => apiFetch("/librarian/library-settings", {
                        method: "PATCH",
                        body: JSON.stringify({ rooms_enabled: !librarySettings.rooms_enabled }),
                      }).then(() => setLibrarySettings(prev => ({ ...prev, rooms_enabled: !prev.rooms_enabled }))),
                      librarySettings.rooms_enabled ? "Room booking disabled." : "Room booking enabled."
                    )}
                  >
                    {librarySettings.rooms_enabled ? "Disable" : "Enable"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </section>
        ) : null}
      </main>
    </div>
  )
}
