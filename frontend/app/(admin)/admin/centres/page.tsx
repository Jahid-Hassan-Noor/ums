"use client"

import { type FormEvent, useEffect, useState } from "react"
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Edit,
  Loader2,
  Plus,
  Search,
  Trash2,
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
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type Centre = {
  id: number
  code: string
  slug: string | null
  name: string
  description: string
  about: string
  offerings: string[]
  image_url: string
  is_active: boolean
}

type CentresResponse = {
  title: string
  section: string
  centres: Centre[]
}

export default function AdminCentresPage() {
  const [centres, setCentres] = useState<Centre[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [searchQuery, setSearchQuery] = useState("")

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCentre, setEditingCentre] = useState<Centre | null>(null)
  const [centreForm, setCentreForm] = useState({
    code: "",
    slug: "",
    name: "",
    description: "",
    about: "",
    offerings: "",
    image_url: "",
    is_active: true,
  })

  const splitLines = (value: string) =>
    value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean)

  const loadData = async () => {
    try {
      setIsLoading(true)
      const data = await apiFetch<CentresResponse>("/admin/centres")
      setCentres(data.centres || [])
      setError("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load centres.")
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

  const handleOpenAdd = () => {
    setEditingCentre(null)
    setCentreForm({
      code: "",
      slug: "",
      name: "",
      description: "",
      about: "",
      offerings: "",
      image_url: "",
      is_active: true,
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (centre: Centre) => {
    setEditingCentre(centre)
    setCentreForm({
      code: centre.code,
      slug: centre.slug ?? "",
      name: centre.name,
      description: centre.description,
      about: centre.about ?? "",
      offerings: (centre.offerings ?? []).join("\n"),
      image_url: centre.image_url ?? "",
      is_active: centre.is_active,
    })
    setIsModalOpen(true)
  }

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    setError("")
    setSuccess("")
    const payload = {
      ...centreForm,
      offerings: splitLines(centreForm.offerings),
    }
    try {
      if (editingCentre) {
        await apiFetch(`/admin/centres/${editingCentre.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
        setSuccess("Centre updated successfully.")
      } else {
        await apiFetch("/admin/centres", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess("Centre added successfully.")
      }
      setIsModalOpen(false)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving centre.")
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this centre?")) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/admin/centres/${id}`, { method: "DELETE" })
      setSuccess("Centre deleted successfully.")
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error deleting centre.")
    }
  }

  const filteredCentres = centres.filter((centre) =>
    [centre.name, centre.code]
      .join(" ")
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
  )

  const activeCount = centres.filter((centre) => centre.is_active).length
  const inactiveCount = centres.length - activeCount

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/centres", title: "Centres" },
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
                Centres
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Add, manage, and retire academic and support centres with their
                service details.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleOpenAdd}>
              <Plus className="mr-1.5 size-4" />
              Add Centre
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

        <section className="grid gap-4 sm:grid-cols-3">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Total Centres
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-primary">
                <Building2 className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{centres.length}</p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Active Centres
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-emerald-50 p-2 text-emerald-600">
                <CheckCircle2 className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{activeCount}</p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Inactive Centres
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                <Building2 className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{inactiveCount}</p>
            </CardContent>
          </Card>
        </section>

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-6 lg:grid-cols-[1fr]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Centre Directory</CardTitle>
                <CardDescription>
                  Search, review, and update the centres listed for the portal.
                </CardDescription>
                <div className="relative mt-2">
                  <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                  <Input
                    placeholder="Search centres..."
                    className="pl-9"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {filteredCentres.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">
                    No centres found.
                  </p>
                ) : (
                  filteredCentres.map((centre) => (
                    <div
                      key={centre.id}
                      className="flex items-start justify-between rounded-lg border border-border bg-background p-4 transition hover:bg-muted/50"
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground">
                            {centre.name}
                          </span>
                          <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                            {centre.code}
                          </span>
                          {!centre.is_active && (
                            <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
                              Inactive
                            </span>
                          )}
                        </div>
                        {centre.description && (
                          <p className="text-xs text-muted-foreground">
                            {centre.description}
                          </p>
                        )}
                      </div>
                      <div className="ml-3 flex items-center gap-1.5">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-muted-foreground"
                          onClick={() => handleOpenEdit(centre)}
                        >
                          <Edit className="size-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-destructive hover:bg-destructive/10"
                          onClick={() => handleDelete(centre.id)}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </main>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md border-border bg-card shadow-lg animate-in fade-in zoom-in-95 duration-150">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle>
                {editingCentre ? "Edit Centre" : "Add Centre"}
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                className="size-8"
                onClick={() => setIsModalOpen(false)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <form onSubmit={handleSave}>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="centre-code">Centre Code</Label>
                  <Input
                    id="centre-code"
                    placeholder="e.g. CDAE"
                    required
                    value={centreForm.code}
                    onChange={(event) =>
                      setCentreForm({ ...centreForm, code: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="centre-slug">Public Slug</Label>
                  <Input
                    id="centre-slug"
                    placeholder="e.g. centre-for-development-of-academic-excellence"
                    required
                    value={centreForm.slug}
                    onChange={(event) =>
                      setCentreForm({ ...centreForm, slug: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="centre-name">Centre Name</Label>
                  <Input
                    id="centre-name"
                    placeholder="e.g. Centre for Development of Academic Excellence"
                    required
                    value={centreForm.name}
                    onChange={(event) =>
                      setCentreForm({ ...centreForm, name: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="centre-summary">Summary</Label>
                  <Textarea
                    id="centre-summary"
                    placeholder="Short summary used on list cards."
                    value={centreForm.description}
                    onChange={(event) =>
                      setCentreForm({
                        ...centreForm,
                        description: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="centre-about">About</Label>
                  <Textarea
                    id="centre-about"
                    placeholder="Full about text shown on the public detail page."
                    value={centreForm.about}
                    onChange={(event) =>
                      setCentreForm({
                        ...centreForm,
                        about: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="centre-offerings">
                    Services & Offerings (one per line)
                  </Label>
                  <Textarea
                    id="centre-offerings"
                    placeholder="Add each service or offering on a new line."
                    value={centreForm.offerings}
                    onChange={(event) =>
                      setCentreForm({
                        ...centreForm,
                        offerings: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="centre-image">Hero Image URL</Label>
                  <Input
                    id="centre-image"
                    placeholder="https://aiu.edu.my/wp-content/uploads/..."
                    value={centreForm.image_url}
                    onChange={(event) =>
                      setCentreForm({
                        ...centreForm,
                        image_url: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="centre-active"
                    checked={centreForm.is_active}
                    onChange={(event) =>
                      setCentreForm({
                        ...centreForm,
                        is_active: event.target.checked,
                      })
                    }
                    className="size-4 rounded border-border"
                  />
                  <Label htmlFor="centre-active" className="cursor-pointer">
                    Active Centre
                  </Label>
                </div>
              </CardContent>
              <div className="flex justify-end gap-2 border-t p-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  {editingCentre ? "Save Changes" : "Create Centre"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
