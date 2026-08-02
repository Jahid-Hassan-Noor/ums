"use client"

import { useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  Download,
  Edit,
  Home,
  Layers,
  Loader2,
  Phone,
  Plus,
  Save,
  Search,
  Trash2,
  Users,
  X,
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
import { apiFetch } from "@/lib/auth"
import { triggerBlobDownload } from "@/lib/fetch-utils"

type Resident = {
  id: number
  profile_id: number
  student_id: string
  name: string
  email: string
  room: string
}

type Hostel = {
  id: number
  code: string
  name: string
  hostel_type: "male" | "female"
  hostel_type_label: string
  warden_name: string
  warden_phone: string
  warden_email: string
  notes: string
  is_active: boolean
  room_count: number
  resident_count: number
}

type HostelRoom = {
  id: number
  hostel: number
  code: string
  floor: number
  number: string
  capacity: number
  is_active: boolean
  residents: Resident[]
  resident_count: number
  available_sections: string[]
}

type HostelsResponse = {
  title: string
  section: string
  hostels: Hostel[]
  rooms: HostelRoom[]
  student_life?: StudentLife
}

type HostelExportRow = Record<string, string | number>

type HostelExportResponse = {
  filename: string
  rows: HostelExportRow[]
}

type EmergencyContact = {
  label: string
  phone: string
  email: string
  available_hours: string
  notes: string
}

type WardenScheduleEntry = {
  day: string
  time_range: string
  warden_name: string
  phone: string
  location: string
  notes: string
}

type StudentLife = {
  emergency_contacts: EmergencyContact[]
  warden_schedule: WardenScheduleEntry[]
  updated_at?: string | null
  updated_by?: string
}

type StudentLifeResponse = {
  message: string
  student_life: StudentLife
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

const emptyHostelForm = {
  code: "",
  name: "",
  hostel_type: "male" as "male" | "female",
  warden_name: "",
  warden_phone: "",
  warden_email: "",
  notes: "",
  is_active: true,
}

const emptyRoomForm = {
  hostel: 0,
  floor: "1",
  number: "",
  capacity: "4",
  is_active: true,
}

const emptyEmergencyContact: EmergencyContact = {
  label: "",
  phone: "",
  email: "",
  available_hours: "",
  notes: "",
}

const emptyWardenScheduleEntry: WardenScheduleEntry = {
  day: "",
  time_range: "",
  warden_name: "",
  phone: "",
  location: "",
  notes: "",
}

const emptyStudentLife: StudentLife = {
  emergency_contacts: [],
  warden_schedule: [],
  updated_at: null,
  updated_by: "",
}

function csvCell(value: unknown) {
  const text = String(value ?? "")
  if (!/[",\n]/.test(text)) return text
  return `"${text.replace(/"/g, '""')}"`
}

function downloadCsv(filename: string, rows: HostelExportRow[]) {
  const columns = [
    "hostel_code",
    "hostel_name",
    "hostel_type",
    "warden_name",
    "warden_phone",
    "warden_email",
    "room_code",
    "floor",
    "room_number",
    "room_capacity",
    "room_section",
    "student_room",
    "student_id",
    "student_name",
    "student_email",
  ]
  const csv = [
    columns.join(","),
    ...rows.map((row) =>
      columns.map((column) => csvCell(row[column])).join(",")
    ),
  ].join("\n")
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" })
  triggerBlobDownload(blob, filename)
}

function copyStudentLife(studentLife?: StudentLife | null): StudentLife {
  return {
    emergency_contacts:
      studentLife?.emergency_contacts?.map((contact) => ({ ...contact })) ?? [],
    warden_schedule:
      studentLife?.warden_schedule?.map((entry) => ({ ...entry })) ?? [],
    updated_at: studentLife?.updated_at ?? null,
    updated_by: studentLife?.updated_by ?? "",
  }
}

function rowHasValue(row: EmergencyContact | WardenScheduleEntry) {
  return Object.values(row).some((value) => value.trim().length > 0)
}

function cleanStudentLifeForm(studentLife: StudentLife): StudentLife {
  return {
    emergency_contacts: studentLife.emergency_contacts
      .filter(rowHasValue)
      .map((contact) => ({
        label: contact.label.trim(),
        phone: contact.phone.trim(),
        email: contact.email.trim(),
        available_hours: contact.available_hours.trim(),
        notes: contact.notes.trim(),
      })),
    warden_schedule: studentLife.warden_schedule
      .filter(rowHasValue)
      .map((entry) => ({
        day: entry.day.trim(),
        time_range: entry.time_range.trim(),
        warden_name: entry.warden_name.trim(),
        phone: entry.phone.trim(),
        location: entry.location.trim(),
        notes: entry.notes.trim(),
      })),
  }
}

function formatUpdatedAt(value?: string | null) {
  if (!value) return "Not updated yet"
  return new Date(value).toLocaleString()
}

export default function AdminHostelsPage() {
  const [hostels, setHostels] = useState<Hostel[]>([])
  const [rooms, setRooms] = useState<HostelRoom[]>([])
  const [selectedHostelId, setSelectedHostelId] = useState<number | null>(null)
  const [studentLife, setStudentLife] = useState<StudentLife>(() =>
    copyStudentLife(emptyStudentLife)
  )
  const [studentLifeForm, setStudentLifeForm] = useState<StudentLife>(() =>
    copyStudentLife(emptyStudentLife)
  )
  const [isLoading, setIsLoading] = useState(true)
  const [isExporting, setIsExporting] = useState(false)
  const [isSavingStudentLife, setIsSavingStudentLife] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [isHostelModalOpen, setIsHostelModalOpen] = useState(false)
  const [editingHostel, setEditingHostel] = useState<Hostel | null>(null)
  const [hostelForm, setHostelForm] = useState(emptyHostelForm)
  const [isRoomModalOpen, setIsRoomModalOpen] = useState(false)
  const [editingRoom, setEditingRoom] = useState<HostelRoom | null>(null)
  const [roomForm, setRoomForm] = useState(emptyRoomForm)

  async function loadData() {
    setIsLoading(true)
    setError("")
    try {
      const data = await apiFetch<HostelsResponse>("/admin/hostels")
      setHostels(data.hostels ?? [])
      setRooms(data.rooms ?? [])
      const nextStudentLife = copyStudentLife(data.student_life)
      setStudentLife(nextStudentLife)
      setStudentLifeForm(copyStudentLife(nextStudentLife))
      if (data.hostels?.length) {
        setSelectedHostelId((current) => current ?? data.hostels[0].id)
      } else {
        setSelectedHostelId(null)
      }
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Failed to load hostels."
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  const filteredHostels = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()
    if (!query) return hostels
    return hostels.filter((hostel) =>
      [hostel.code, hostel.name, hostel.hostel_type_label, hostel.warden_name]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(query))
    )
  }, [hostels, searchQuery])

  const selectedHostel =
    hostels.find((hostel) => hostel.id === selectedHostelId) ?? null
  const selectedRooms = rooms.filter((room) => room.hostel === selectedHostelId)
  const totalCapacity = rooms.reduce(
    (total, room) => total + (room.capacity || 0),
    0
  )
  const totalResidents = rooms.reduce(
    (total, room) => total + (room.resident_count || 0),
    0
  )
  const maleHostels = hostels.filter(
    (hostel) => hostel.hostel_type === "male"
  ).length
  const femaleHostels = hostels.filter(
    (hostel) => hostel.hostel_type === "female"
  ).length

  function openAddHostel() {
    setEditingHostel(null)
    setHostelForm(emptyHostelForm)
    setIsHostelModalOpen(true)
  }

  function openEditHostel(hostel: Hostel) {
    setEditingHostel(hostel)
    setHostelForm({
      code: hostel.code,
      name: hostel.name,
      hostel_type: hostel.hostel_type,
      warden_name: hostel.warden_name,
      warden_phone: hostel.warden_phone,
      warden_email: hostel.warden_email,
      notes: hostel.notes,
      is_active: hostel.is_active,
    })
    setIsHostelModalOpen(true)
  }

  async function saveHostel(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")
    try {
      const payload = {
        ...hostelForm,
        code: hostelForm.code.trim().toUpperCase(),
      }
      if (editingHostel) {
        await apiFetch(`/admin/hostels/hostels/${editingHostel.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
        setSuccess("Hostel updated successfully.")
      } else {
        await apiFetch("/admin/hostels/hostels", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess("Hostel created successfully.")
      }
      setIsHostelModalOpen(false)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to save hostel."
      )
    }
  }

  async function deleteHostel(hostel: Hostel) {
    if (
      !confirm(
        `Delete ${hostel.code}? All rooms inside this hostel will be removed.`
      )
    )
      return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/admin/hostels/hostels/${hostel.id}`, {
        method: "DELETE",
      })
      setSuccess("Hostel deleted successfully.")
      if (selectedHostelId === hostel.id) setSelectedHostelId(null)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to delete hostel."
      )
    }
  }

  function openAddRoom() {
    if (!selectedHostelId) return
    setEditingRoom(null)
    setRoomForm({ ...emptyRoomForm, hostel: selectedHostelId })
    setIsRoomModalOpen(true)
  }

  function openEditRoom(room: HostelRoom) {
    setEditingRoom(room)
    setRoomForm({
      hostel: room.hostel,
      floor: String(room.floor),
      number: room.number,
      capacity: String(room.capacity),
      is_active: room.is_active,
    })
    setIsRoomModalOpen(true)
  }

  async function saveRoom(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")
    try {
      const payload = {
        ...roomForm,
        floor: Number.parseInt(roomForm.floor, 10),
        capacity: Number.parseInt(roomForm.capacity, 10),
      }
      if (editingRoom) {
        await apiFetch(`/admin/hostels/rooms/${editingRoom.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
        setSuccess("Hostel room updated successfully.")
      } else {
        await apiFetch("/admin/hostels/rooms", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess("Hostel room created successfully.")
      }
      setIsRoomModalOpen(false)
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Unable to save hostel room."
      )
    }
  }

  async function deleteRoom(room: HostelRoom) {
    if (!confirm(`Delete room ${room.code}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/admin/hostels/rooms/${room.id}`, { method: "DELETE" })
      setSuccess("Hostel room deleted successfully.")
      await loadData()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to delete hostel room."
      )
    }
  }

  function updateEmergencyContact(
    index: number,
    field: keyof EmergencyContact,
    value: string
  ) {
    setStudentLifeForm((current) => ({
      ...current,
      emergency_contacts: current.emergency_contacts.map(
        (contact, contactIndex) =>
          contactIndex === index ? { ...contact, [field]: value } : contact
      ),
    }))
  }

  function addEmergencyContact() {
    setStudentLifeForm((current) => ({
      ...current,
      emergency_contacts: [
        ...current.emergency_contacts,
        { ...emptyEmergencyContact },
      ],
    }))
  }

  function removeEmergencyContact(index: number) {
    setStudentLifeForm((current) => ({
      ...current,
      emergency_contacts: current.emergency_contacts.filter(
        (_, contactIndex) => contactIndex !== index
      ),
    }))
  }

  function updateWardenSchedule(
    index: number,
    field: keyof WardenScheduleEntry,
    value: string
  ) {
    setStudentLifeForm((current) => ({
      ...current,
      warden_schedule: current.warden_schedule.map((entry, entryIndex) =>
        entryIndex === index ? { ...entry, [field]: value } : entry
      ),
    }))
  }

  function addWardenScheduleEntry() {
    setStudentLifeForm((current) => ({
      ...current,
      warden_schedule: [
        ...current.warden_schedule,
        { ...emptyWardenScheduleEntry },
      ],
    }))
  }

  function removeWardenScheduleEntry(index: number) {
    setStudentLifeForm((current) => ({
      ...current,
      warden_schedule: current.warden_schedule.filter(
        (_, entryIndex) => entryIndex !== index
      ),
    }))
  }

  async function saveStudentLife() {
    setIsSavingStudentLife(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<StudentLifeResponse>(
        "/admin/hostels/student-life",
        {
          method: "PATCH",
          body: JSON.stringify({
            student_life: cleanStudentLifeForm(studentLifeForm),
          }),
        }
      )
      const nextStudentLife = copyStudentLife(response.student_life)
      setStudentLife(nextStudentLife)
      setStudentLifeForm(copyStudentLife(nextStudentLife))
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to update student hostel information."
      )
    } finally {
      setIsSavingStudentLife(false)
    }
  }

  async function exportHostels() {
    setIsExporting(true)
    setError("")
    setSuccess("")
    try {
      const exportData = await apiFetch<HostelExportResponse>(
        "/admin/hostels/export"
      )
      downloadCsv(
        exportData.filename || "hostel-details.csv",
        exportData.rows ?? []
      )
      setSuccess("Hostel details exported.")
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to export hostel details."
      )
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/hostels", title: "Hostels" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <span className="inline-flex h-6 w-fit items-center rounded-full border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground">
              Admin Zone
            </span>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Hostels
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Manage male and female hostel blocks, room capacities, wardens,
                and student room assignments.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={exportHostels}
              disabled={isExporting}
            >
              {isExporting ? (
                <Loader2 className="mr-1.5 size-4 animate-spin" />
              ) : (
                <Download className="mr-1.5 size-4" />
              )}
              Export Details
            </Button>
            <Button onClick={openAddHostel}>
              <Plus className="mr-1.5 size-4" />
              Add Hostel
            </Button>
          </div>
        </section>

        {error && (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}
        {success && (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{success}</p>
          </div>
        )}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Hostels
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-primary">
                <Home className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">
                {hostels.length}
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Male / Female
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                <Users className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">
                {maleHostels} / {femaleHostels}
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Rooms
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="text-success rounded-lg border border-border bg-muted/50 p-2">
                <Layers className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">
                {rooms.length}
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Residents / Capacity
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="text-warning rounded-lg border border-border bg-muted/50 p-2">
                <Users className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">
                {totalResidents} / {totalCapacity}
              </p>
            </CardContent>
          </Card>
        </section>

        {!isLoading && (
          <section className="grid gap-4 xl:grid-cols-2">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between gap-3 pb-3">
                <div className="min-w-0">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Phone className="size-5" />
                    Emergency Contacts
                  </CardTitle>
                  <CardDescription>
                    Last updated: {formatUpdatedAt(studentLife.updated_at)}
                  </CardDescription>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={addEmergencyContact}
                >
                  <Plus className="size-3.5" />
                  Add
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                {studentLifeForm.emergency_contacts.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                    No emergency contacts configured.
                  </div>
                ) : (
                  studentLifeForm.emergency_contacts.map((contact, index) => (
                    <div
                      key={index}
                      className="space-y-3 rounded-lg border border-border bg-background p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-foreground">
                          Contact {index + 1}
                        </p>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="size-8 text-destructive hover:bg-destructive/10"
                          onClick={() => removeEmergencyContact(index)}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="grid gap-2">
                          <Label htmlFor={`contact-label-${index}`}>Name</Label>
                          <Input
                            id={`contact-label-${index}`}
                            value={contact.label}
                            onChange={(event) =>
                              updateEmergencyContact(
                                index,
                                "label",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor={`contact-hours-${index}`}>
                            Available Hours
                          </Label>
                          <Input
                            id={`contact-hours-${index}`}
                            value={contact.available_hours}
                            onChange={(event) =>
                              updateEmergencyContact(
                                index,
                                "available_hours",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor={`contact-phone-${index}`}>
                            Phone
                          </Label>
                          <Input
                            id={`contact-phone-${index}`}
                            value={contact.phone}
                            onChange={(event) =>
                              updateEmergencyContact(
                                index,
                                "phone",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor={`contact-email-${index}`}>
                            Email
                          </Label>
                          <Input
                            id={`contact-email-${index}`}
                            type="email"
                            value={contact.email}
                            onChange={(event) =>
                              updateEmergencyContact(
                                index,
                                "email",
                                event.target.value
                              )
                            }
                          />
                        </div>
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor={`contact-notes-${index}`}>Notes</Label>
                        <textarea
                          id={`contact-notes-${index}`}
                          className="min-h-16 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs transition outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                          value={contact.notes}
                          onChange={(event) =>
                            updateEmergencyContact(
                              index,
                              "notes",
                              event.target.value
                            )
                          }
                        />
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between gap-3 pb-3">
                <div className="min-w-0">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <CalendarClock className="size-5" />
                    Warden Schedule
                  </CardTitle>
                  <CardDescription>
                    Students see {studentLifeForm.warden_schedule.length}{" "}
                    schedule row
                    {studentLifeForm.warden_schedule.length === 1 ? "" : "s"}.
                  </CardDescription>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={addWardenScheduleEntry}
                >
                  <Plus className="size-3.5" />
                  Add
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                {studentLifeForm.warden_schedule.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                    No warden schedule configured.
                  </div>
                ) : (
                  studentLifeForm.warden_schedule.map((entry, index) => (
                    <div
                      key={index}
                      className="space-y-3 rounded-lg border border-border bg-background p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-foreground">
                          Schedule {index + 1}
                        </p>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="size-8 text-destructive hover:bg-destructive/10"
                          onClick={() => removeWardenScheduleEntry(index)}
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="grid gap-2">
                          <Label htmlFor={`schedule-day-${index}`}>
                            Day or Date
                          </Label>
                          <Input
                            id={`schedule-day-${index}`}
                            value={entry.day}
                            onChange={(event) =>
                              updateWardenSchedule(
                                index,
                                "day",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor={`schedule-time-${index}`}>Time</Label>
                          <Input
                            id={`schedule-time-${index}`}
                            value={entry.time_range}
                            onChange={(event) =>
                              updateWardenSchedule(
                                index,
                                "time_range",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor={`schedule-warden-${index}`}>
                            Warden
                          </Label>
                          <Input
                            id={`schedule-warden-${index}`}
                            value={entry.warden_name}
                            onChange={(event) =>
                              updateWardenSchedule(
                                index,
                                "warden_name",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor={`schedule-phone-${index}`}>
                            Phone
                          </Label>
                          <Input
                            id={`schedule-phone-${index}`}
                            value={entry.phone}
                            onChange={(event) =>
                              updateWardenSchedule(
                                index,
                                "phone",
                                event.target.value
                              )
                            }
                          />
                        </div>
                        <div className="grid gap-2 sm:col-span-2">
                          <Label htmlFor={`schedule-location-${index}`}>
                            Location
                          </Label>
                          <Input
                            id={`schedule-location-${index}`}
                            value={entry.location}
                            onChange={(event) =>
                              updateWardenSchedule(
                                index,
                                "location",
                                event.target.value
                              )
                            }
                          />
                        </div>
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor={`schedule-notes-${index}`}>Notes</Label>
                        <textarea
                          id={`schedule-notes-${index}`}
                          className="min-h-16 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs transition outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                          value={entry.notes}
                          onChange={(event) =>
                            updateWardenSchedule(
                              index,
                              "notes",
                              event.target.value
                            )
                          }
                        />
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <div className="flex flex-wrap items-center justify-between gap-3 xl:col-span-2">
              <p className="text-sm text-muted-foreground">
                Updated by {studentLife.updated_by || "admin record"}.
              </p>
              <Button onClick={saveStudentLife} disabled={isSavingStudentLife}>
                {isSavingStudentLife ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Save className="size-4" />
                )}
                Save Student Info
              </Button>
            </div>
          </section>
        )}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-6 lg:grid-cols-[22rem_minmax(0,1fr)]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Hostel Blocks</CardTitle>
                <CardDescription>
                  Select a hostel to manage its rooms.
                </CardDescription>
                <div className="relative mt-2">
                  <Search className="absolute top-2.5 left-3 size-4 text-muted-foreground" />
                  <Input
                    placeholder="Search hostels..."
                    className="pl-9"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {filteredHostels.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">
                    No hostels found.
                  </p>
                ) : (
                  filteredHostels.map((hostel) => (
                    <div
                      key={hostel.id}
                      onClick={() => setSelectedHostelId(hostel.id)}
                      className={`cursor-pointer rounded-lg border p-4 transition-colors ${
                        selectedHostelId === hostel.id
                          ? "border-primary bg-primary/5"
                          : "border-border bg-background hover:bg-muted/50"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-foreground">
                              {hostel.code}
                            </span>
                            <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                              {hostel.hostel_type_label}
                            </span>
                          </div>
                          <p className="truncate text-sm text-muted-foreground">
                            {hostel.name || "Untitled hostel"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {hostel.room_count} rooms · {hostel.resident_count}{" "}
                            residents
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7 text-muted-foreground"
                            onClick={(event) => {
                              event.stopPropagation()
                              openEditHostel(hostel)
                            }}
                          >
                            <Edit className="size-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7 text-destructive hover:bg-destructive/10"
                            onClick={(event) => {
                              event.stopPropagation()
                              void deleteHostel(hostel)
                            }}
                          >
                            <Trash2 className="size-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between gap-3 pb-3">
                <div className="min-w-0">
                  <CardTitle className="truncate text-lg">
                    {selectedHostel
                      ? `${selectedHostel.code} Rooms`
                      : "Hostel Rooms"}
                  </CardTitle>
                  <CardDescription>
                    {selectedHostel
                      ? `${selectedHostel.hostel_type_label} hostel · Warden: ${selectedHostel.warden_name || "Not assigned"}`
                      : "Select a hostel to view room details."}
                  </CardDescription>
                </div>
                {selectedHostelId && (
                  <Button size="sm" onClick={openAddRoom}>
                    <Plus className="mr-1.5 size-3.5" />
                    Add Room
                  </Button>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {!selectedHostelId ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    Select a hostel from the list.
                  </p>
                ) : selectedRooms.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-8 text-center">
                    <p className="text-sm text-muted-foreground">
                      No rooms defined inside this hostel yet.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-3"
                      onClick={openAddRoom}
                    >
                      Create First Room
                    </Button>
                  </div>
                ) : (
                  <div className="grid gap-3 xl:grid-cols-2">
                    {selectedRooms.map((room) => (
                      <div
                        key={room.id}
                        className="rounded-lg border border-border bg-background p-4 shadow-sm"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-semibold text-foreground">
                              {room.code}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Floor {room.floor} · Room {room.number} ·{" "}
                              {room.resident_count}/{room.capacity} occupied
                            </p>
                          </div>
                          <div className="flex shrink-0 items-center gap-1">
                            <Button
                              variant="outline"
                              size="icon"
                              className="size-8"
                              onClick={() => openEditRoom(room)}
                            >
                              <Edit className="size-3.5" />
                            </Button>
                            <Button
                              variant="outline"
                              size="icon"
                              className="size-8 text-destructive hover:bg-destructive/10"
                              onClick={() => void deleteRoom(room)}
                            >
                              <Trash2 className="size-3.5" />
                            </Button>
                          </div>
                        </div>
                        <div className="mt-3 space-y-2 border-t pt-3">
                          {room.residents.length === 0 ? (
                            <p className="text-xs text-muted-foreground">
                              No assigned students.
                            </p>
                          ) : (
                            room.residents.map((resident) => (
                              <div
                                key={resident.id}
                                className="flex items-center justify-between gap-2 text-xs"
                              >
                                <span className="truncate text-foreground">
                                  {resident.name}
                                </span>
                                <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-muted-foreground">
                                  {resident.room}
                                </span>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </main>

      {isHostelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
          <Card className="max-h-[92svh] w-full max-w-lg overflow-y-auto border-border bg-card shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle>
                {editingHostel ? "Edit Hostel" : "Add Hostel"}
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => setIsHostelModalOpen(false)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <form onSubmit={saveHostel}>
              <CardContent className="space-y-4">
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="grid gap-2">
                    <Label htmlFor="hostel-code">Hostel Title</Label>
                    <Input
                      id="hostel-code"
                      required
                      placeholder="25A"
                      value={hostelForm.code}
                      onChange={(event) =>
                        setHostelForm({
                          ...hostelForm,
                          code: event.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="hostel-type">Type</Label>
                    <select
                      id="hostel-type"
                      className={selectClass}
                      value={hostelForm.hostel_type}
                      onChange={(event) =>
                        setHostelForm({
                          ...hostelForm,
                          hostel_type: event.target.value as "male" | "female",
                        })
                      }
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="hostel-name">Hostel Name</Label>
                  <Input
                    id="hostel-name"
                    placeholder="Optional display name"
                    value={hostelForm.name}
                    onChange={(event) =>
                      setHostelForm({ ...hostelForm, name: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="grid gap-2">
                    <Label htmlFor="warden-name">Warden Name</Label>
                    <Input
                      id="warden-name"
                      value={hostelForm.warden_name}
                      onChange={(event) =>
                        setHostelForm({
                          ...hostelForm,
                          warden_name: event.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="warden-phone">Warden Phone</Label>
                    <Input
                      id="warden-phone"
                      value={hostelForm.warden_phone}
                      onChange={(event) =>
                        setHostelForm({
                          ...hostelForm,
                          warden_phone: event.target.value,
                        })
                      }
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="warden-email">Warden Email</Label>
                  <Input
                    id="warden-email"
                    type="email"
                    value={hostelForm.warden_email}
                    onChange={(event) =>
                      setHostelForm({
                        ...hostelForm,
                        warden_email: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="hostel-notes">Notes</Label>
                  <textarea
                    id="hostel-notes"
                    className="min-h-20 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs transition outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                    value={hostelForm.notes}
                    onChange={(event) =>
                      setHostelForm({
                        ...hostelForm,
                        notes: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="hostel-active"
                    checked={hostelForm.is_active}
                    onChange={(event) =>
                      setHostelForm({
                        ...hostelForm,
                        is_active: event.target.checked,
                      })
                    }
                    className="size-4 rounded border-border"
                  />
                  <Label htmlFor="hostel-active" className="cursor-pointer">
                    Active Hostel
                  </Label>
                </div>
              </CardContent>
              <div className="flex justify-end gap-2 border-t p-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsHostelModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  {editingHostel ? "Save Changes" : "Create Hostel"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {isRoomModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-md border-border bg-card shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle>{editingRoom ? "Edit Room" : "Add Room"}</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => setIsRoomModalOpen(false)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <form onSubmit={saveRoom}>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="room-hostel">Hostel</Label>
                  <select
                    id="room-hostel"
                    className={selectClass}
                    value={roomForm.hostel}
                    onChange={(event) =>
                      setRoomForm({
                        ...roomForm,
                        hostel: Number.parseInt(event.target.value, 10),
                      })
                    }
                  >
                    {hostels.map((hostel) => (
                      <option key={hostel.id} value={hostel.id}>
                        {hostel.code} ({hostel.hostel_type_label})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-2 sm:grid-cols-3">
                  <div className="grid gap-2">
                    <Label htmlFor="room-floor">Floor</Label>
                    <Input
                      id="room-floor"
                      type="number"
                      min="0"
                      required
                      value={roomForm.floor}
                      onChange={(event) =>
                        setRoomForm({ ...roomForm, floor: event.target.value })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="room-number">Room No.</Label>
                    <Input
                      id="room-number"
                      required
                      placeholder="13"
                      value={roomForm.number}
                      onChange={(event) =>
                        setRoomForm({ ...roomForm, number: event.target.value })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="room-capacity">Capacity</Label>
                    <Input
                      id="room-capacity"
                      type="number"
                      min="1"
                      max="26"
                      required
                      value={roomForm.capacity}
                      onChange={(event) =>
                        setRoomForm({
                          ...roomForm,
                          capacity: event.target.value,
                        })
                      }
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="room-active"
                    checked={roomForm.is_active}
                    onChange={(event) =>
                      setRoomForm({
                        ...roomForm,
                        is_active: event.target.checked,
                      })
                    }
                    className="size-4 rounded border-border"
                  />
                  <Label htmlFor="room-active" className="cursor-pointer">
                    Active Room
                  </Label>
                </div>
              </CardContent>
              <div className="flex justify-end gap-2 border-t p-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsRoomModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  {editingRoom ? "Save Changes" : "Create Room"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
