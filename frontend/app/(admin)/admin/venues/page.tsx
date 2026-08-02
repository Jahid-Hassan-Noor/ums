"use client"

import { useEffect, useState } from "react"
import {
  AlertCircle,
  Armchair,
  Building2,
  CheckCircle2,
  Edit,
  Layers,
  Loader2,
  MapPin,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type Building = {
  id: number
  code: string
  name: string
  description: string
  address: string
  is_active: boolean
}

type Venue = {
  id: number
  building: number
  building_detail?: Building
  code: string
  name: string
  floor: string
  capacity: number | null
  is_active: boolean
}

type VenuesResponse = {
  title: string
  section: string
  buildings: Building[]
  venues: Venue[]
}

export default function AdminVenuesPage() {
  const [buildings, setBuildings] = useState<Building[]>([])
  const [venues, setVenues] = useState<Venue[]>([])
  const [selectedBuildingId, setSelectedBuildingId] = useState<number | null>(null)
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("")
  
  // Building Modal State
  const [isBuildingModalOpen, setIsBuildingModalOpen] = useState(false)
  const [editingBuilding, setEditingBuilding] = useState<Building | null>(null)
  const [buildingForm, setBuildingForm] = useState({
    code: "",
    name: "",
    description: "",
    address: "",
    is_active: true,
  })

  // Venue Modal State
  const [isVenueModalOpen, setIsVenueModalOpen] = useState(false)
  const [editingVenue, setEditingVenue] = useState<Venue | null>(null)
  const [venueForm, setVenueForm] = useState({
    building: 0,
    code: "",
    name: "",
    floor: "",
    capacity: "",
    is_active: true,
  })

  const loadData = async () => {
    try {
      setIsLoading(true)
      const data = await apiFetch<VenuesResponse>("/admin/venues")
      setBuildings(data.buildings || [])
      setVenues(data.venues || [])
      if (data.buildings && data.buildings.length > 0 && selectedBuildingId === null) {
        setSelectedBuildingId(data.buildings[0].id)
      }
      setError("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load venues and infrastructure.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          setIsLoading(true)
          const data = await apiFetch<VenuesResponse>("/admin/venues")
          setBuildings(data.buildings || [])
          setVenues(data.venues || [])
          if (data.buildings && data.buildings.length > 0) {
            setSelectedBuildingId((current) => current ?? data.buildings[0].id)
          }
          setError("")
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to load venues and infrastructure.")
        } finally {
          setIsLoading(false)
        }
      })()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [])

  // Building Actions
  const handleOpenAddBuilding = () => {
    setEditingBuilding(null)
    setBuildingForm({
      code: "",
      name: "",
      description: "",
      address: "",
      is_active: true,
    })
    setIsBuildingModalOpen(true)
  }

  const handleOpenEditBuilding = (b: Building) => {
    setEditingBuilding(b)
    setBuildingForm({
      code: b.code,
      name: b.name,
      description: b.description,
      address: b.address,
      is_active: b.is_active,
    })
    setIsBuildingModalOpen(true)
  }

  const handleSaveBuilding = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    try {
      if (editingBuilding) {
        await apiFetch(`/admin/venues/buildings/${editingBuilding.id}`, {
          method: "PUT",
          body: JSON.stringify(buildingForm),
        })
        setSuccess("Building updated successfully.")
      } else {
        await apiFetch("/admin/venues/buildings", {
          method: "POST",
          body: JSON.stringify(buildingForm),
        })
        setSuccess("Building added successfully.")
      }
      setIsBuildingModalOpen(false)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving building.")
    }
  }

  const handleDeleteBuilding = async (id: number) => {
    if (!confirm("Are you sure you want to delete this building? All nested venues will be deleted.")) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/admin/venues/buildings/${id}`, {
        method: "DELETE",
      })
      setSuccess("Building deleted successfully.")
      if (selectedBuildingId === id) {
        setSelectedBuildingId(null)
      }
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error deleting building.")
    }
  }

  // Venue Actions
  const handleOpenAddVenue = () => {
    if (!selectedBuildingId) return
    setEditingVenue(null)
    setVenueForm({
      building: selectedBuildingId,
      code: "",
      name: "",
      floor: "",
      capacity: "",
      is_active: true,
    })
    setIsVenueModalOpen(true)
  }

  const handleOpenEditVenue = (v: Venue) => {
    setEditingVenue(v)
    setVenueForm({
      building: v.building,
      code: v.code,
      name: v.name,
      floor: v.floor,
      capacity: v.capacity !== null ? String(v.capacity) : "",
      is_active: v.is_active,
    })
    setIsVenueModalOpen(true)
  }

  const handleSaveVenue = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    try {
      const payload = {
        ...venueForm,
        capacity: venueForm.capacity ? parseInt(venueForm.capacity) : null,
      }
      if (editingVenue) {
        await apiFetch(`/admin/venues/venues/${editingVenue.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
        setSuccess("Venue updated successfully.")
      } else {
        await apiFetch("/admin/venues/venues", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess("Venue added successfully.")
      }
      setIsVenueModalOpen(false)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving venue.")
    }
  }

  const handleDeleteVenue = async (id: number) => {
    if (!confirm("Are you sure you want to delete this venue?")) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/admin/venues/venues/${id}`, {
        method: "DELETE",
      })
      setSuccess("Venue deleted successfully.")
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error deleting venue.")
    }
  }

  // Filters
  const filteredBuildings = buildings.filter((b) =>
    b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    b.code.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedBuilding = buildings.find((b) => b.id === selectedBuildingId)
  const nestedVenues = venues.filter((v) => v.building === selectedBuildingId)

  // Metrics
  const totalCapacity = venues.reduce((acc, curr) => acc + (curr.capacity || 0), 0)

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/venues", title: "Venues" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <span className="inline-flex h-6 w-fit items-center rounded-full border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground">
              Admin Zone
            </span>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Venues & Infrastructure
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Manage campus buildings, physical lecture rooms, laboratories, and seating capacities.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleOpenAddBuilding}>
              <Plus className="mr-1.5 size-4" />
              Add Building
            </Button>
          </div>
        </section>

        {/* Feedback Messages */}
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

        {/* Dashboard Metrics */}
        <section className="grid gap-4 sm:grid-cols-3">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">Total Buildings</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-primary">
                <Building2 className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{buildings.length}</p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">Total Venues (Rooms)</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-success">
                <Layers className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{venues.length}</p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">Total Capacity</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-warning">
                <Armchair className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{totalCapacity} seats</p>
            </CardContent>
          </Card>
        </section>

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
            {/* Buildings List Column */}
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Buildings</CardTitle>
                <CardDescription>Select a building to view or add its venues.</CardDescription>
                <div className="relative mt-2">
                  <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                  <Input
                    placeholder="Search buildings..."
                    className="pl-9"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {filteredBuildings.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">No buildings found.</p>
                ) : (
                  filteredBuildings.map((b) => (
                    <div
                      key={b.id}
                      onClick={() => setSelectedBuildingId(b.id)}
                      className={`flex cursor-pointer items-start justify-between rounded-lg border p-4 transition-colors ${
                        selectedBuildingId === b.id
                          ? "border-primary bg-primary/5"
                          : "border-border bg-background hover:bg-muted/50"
                      }`}
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground">{b.name}</span>
                          <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                            {b.code}
                          </span>
                        </div>
                        {b.description && (
                          <p className="truncate text-xs text-muted-foreground">{b.description}</p>
                        )}
                        {b.address && (
                          <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                            <MapPin className="size-3" />
                            <span>{b.address}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 ml-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-muted-foreground"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenEditBuilding(b)
                          }}
                        >
                          <Edit className="size-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-destructive hover:bg-destructive/10"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteBuilding(b.id)
                          }}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Venues (Rooms) Column */}
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle className="text-lg">
                    Venues inside {selectedBuilding ? selectedBuilding.name : "Selected Building"}
                  </CardTitle>
                  <CardDescription>
                    {selectedBuilding ? `Infrastructure rooms inside ${selectedBuilding.code}.` : "Please select a building."}
                  </CardDescription>
                </div>
                {selectedBuildingId && (
                  <Button size="sm" onClick={handleOpenAddVenue}>
                    <Plus className="mr-1.5 size-3.5" />
                    Add Venue
                  </Button>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {!selectedBuildingId ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    Please select a building from the left list.
                  </p>
                ) : nestedVenues.length === 0 ? (
                  <div className="rounded-lg border border-dashed p-8 text-center">
                    <p className="text-sm text-muted-foreground">No venues defined inside this building yet.</p>
                    <Button variant="outline" size="sm" className="mt-3" onClick={handleOpenAddVenue}>
                      Create First Venue
                    </Button>
                  </div>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {nestedVenues.map((v) => (
                      <div
                        key={v.id}
                        className="flex flex-col justify-between rounded-lg border border-border bg-background p-4 shadow-sm"
                      >
                        <div className="space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-semibold text-foreground">{v.name}</span>
                            <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary font-mono">
                              {v.code}
                            </span>
                          </div>
                          <div className="space-y-1 text-xs text-muted-foreground">
                            {v.floor && (
                              <div className="flex items-center gap-1.5">
                                <Layers className="size-3.5 shrink-0" />
                                <span>{v.floor}</span>
                              </div>
                            )}
                            {v.capacity && (
                              <div className="flex items-center gap-1.5">
                                <Armchair className="size-3.5 shrink-0" />
                                <span>{v.capacity} seats</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="mt-4 flex items-center justify-end gap-1.5 border-t pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-2"
                            onClick={() => handleOpenEditVenue(v)}
                          >
                            <Edit className="size-3 mr-1" />
                            Edit
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-2 text-destructive hover:bg-destructive/10"
                            onClick={() => handleDeleteVenue(v.id)}
                          >
                            <Trash2 className="size-3 mr-1" />
                            Delete
                          </Button>
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

      {/* Building Dialog Modal */}
      {isBuildingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md border-border bg-card shadow-lg animate-in fade-in zoom-in-95 duration-150">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle>{editingBuilding ? "Edit Building" : "Add Building"}</CardTitle>
              <Button variant="ghost" size="icon" className="size-8" onClick={() => setIsBuildingModalOpen(false)}>
                <X className="size-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleSaveBuilding}>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="b-code">Building Code</Label>
                  <Input
                    id="b-code"
                    placeholder="e.g. ACAD-A"
                    required
                    value={buildingForm.code}
                    onChange={(e) => setBuildingForm({ ...buildingForm, code: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="b-name">Building Name</Label>
                  <Input
                    id="b-name"
                    placeholder="e.g. Academic Block A"
                    required
                    value={buildingForm.name}
                    onChange={(e) => setBuildingForm({ ...buildingForm, name: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="b-desc">Description</Label>
                  <Input
                    id="b-desc"
                    placeholder="Brief details about the building usage..."
                    value={buildingForm.description}
                    onChange={(e) => setBuildingForm({ ...buildingForm, description: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="b-addr">Address / Location</Label>
                  <Input
                    id="b-addr"
                    placeholder="Campus street or sector details..."
                    value={buildingForm.address}
                    onChange={(e) => setBuildingForm({ ...buildingForm, address: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="b-active"
                    checked={buildingForm.is_active}
                    onChange={(e) => setBuildingForm({ ...buildingForm, is_active: e.target.checked })}
                    className="size-4 rounded border-border"
                  />
                  <Label htmlFor="b-active" className="cursor-pointer">Active Building</Label>
                </div>
              </CardContent>
              <div className="flex justify-end gap-2 border-t p-4">
                <Button type="button" variant="outline" onClick={() => setIsBuildingModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingBuilding ? "Save Changes" : "Create Building"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Venue Dialog Modal */}
      {isVenueModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md border-border bg-card shadow-lg animate-in fade-in zoom-in-95 duration-150">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle>{editingVenue ? "Edit Venue" : "Add Venue Room"}</CardTitle>
              <Button variant="ghost" size="icon" className="size-8" onClick={() => setIsVenueModalOpen(false)}>
                <X className="size-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleSaveVenue}>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="v-building">Parent Building</Label>
                  <select
                    id="v-building"
                    value={venueForm.building}
                    onChange={(e) =>
                      setVenueForm({
                        ...venueForm,
                        building: parseInt(e.target.value),
                      })
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm ring-offset-background"
                  >
                    {buildings.map((building) => (
                      <option key={building.id} value={building.id}>
                        {building.name} ({building.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="v-code">Venue Code (Room ID)</Label>
                  <Input
                    id="v-code"
                    placeholder="e.g. CR-101"
                    required
                    value={venueForm.code}
                    onChange={(e) => setVenueForm({ ...venueForm, code: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="v-name">Venue / Room Name</Label>
                  <Input
                    id="v-name"
                    placeholder="e.g. Seminar Classroom 1"
                    required
                    value={venueForm.name}
                    onChange={(e) => setVenueForm({ ...venueForm, name: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="v-floor">Floor</Label>
                  <Input
                    id="v-floor"
                    placeholder="e.g. Ground Floor, First Floor"
                    value={venueForm.floor}
                    onChange={(e) => setVenueForm({ ...venueForm, floor: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="v-cap">Seating Capacity</Label>
                  <Input
                    id="v-cap"
                    type="number"
                    min="1"
                    placeholder="Maximum number of students..."
                    value={venueForm.capacity}
                    onChange={(e) => setVenueForm({ ...venueForm, capacity: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="v-active"
                    checked={venueForm.is_active}
                    onChange={(e) => setVenueForm({ ...venueForm, is_active: e.target.checked })}
                    className="size-4 rounded border-border"
                  />
                  <Label htmlFor="v-active" className="cursor-pointer">Active Venue</Label>
                </div>
              </CardContent>
              <div className="flex justify-end gap-2 border-t p-4">
                <Button type="button" variant="outline" onClick={() => setIsVenueModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingVenue ? "Save Changes" : "Create Venue"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
