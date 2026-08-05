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

type School = {
  id: number
  code: string
  slug: string | null
  name: string
  description: string
  about: string
  vision: string
  mission: string[]
  programmes: string[]
  image_url: string
  is_active: boolean
}

type SchoolsResponse = {
  title: string
  section: string
  schools: School[]
}

export default function AdminSchoolsPage() {
  const [schools, setSchools] = useState<School[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [searchQuery, setSearchQuery] = useState("")

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSchool, setEditingSchool] = useState<School | null>(null)
  const [schoolForm, setSchoolForm] = useState({
    code: "",
    slug: "",
    name: "",
    description: "",
    about: "",
    vision: "",
    mission: "",
    programmes: "",
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
      const data = await apiFetch<SchoolsResponse>("/admin/schools")
      setSchools(data.schools || [])
      setError("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load schools.")
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
    setEditingSchool(null)
    setSchoolForm({
      code: "",
      slug: "",
      name: "",
      description: "",
      about: "",
      vision: "",
      mission: "",
      programmes: "",
      image_url: "",
      is_active: true,
    })
    setIsModalOpen(true)
  }

  const handleOpenEdit = (school: School) => {
    setEditingSchool(school)
    setSchoolForm({
      code: school.code,
      slug: school.slug ?? "",
      name: school.name,
      description: school.description,
      about: school.about ?? "",
      vision: school.vision ?? "",
      mission: (school.mission ?? []).join("\n"),
      programmes: (school.programmes ?? []).join("\n"),
      image_url: school.image_url ?? "",
      is_active: school.is_active,
    })
    setIsModalOpen(true)
  }

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    setError("")
    setSuccess("")
    const payload = {
      ...schoolForm,
      mission: splitLines(schoolForm.mission),
      programmes: splitLines(schoolForm.programmes),
    }
    try {
      if (editingSchool) {
        await apiFetch(`/admin/schools/${editingSchool.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
        setSuccess("School updated successfully.")
      } else {
        await apiFetch("/admin/schools", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess("School added successfully.")
      }
      setIsModalOpen(false)
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving school.")
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this school?")) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/admin/schools/${id}`, { method: "DELETE" })
      setSuccess("School deleted successfully.")
      loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error deleting school.")
    }
  }

  const filteredSchools = schools.filter((school) =>
    [school.name, school.code]
      .join(" ")
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
  )

  const activeCount = schools.filter((school) => school.is_active).length
  const inactiveCount = schools.length - activeCount

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/schools", title: "Schools" },
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
                Schools
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Add, manage, and retire academic schools shown on the public site.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleOpenAdd}>
              <Plus className="mr-1.5 size-4" />
              Add School
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
                Total Schools
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <span className="rounded-lg border border-border bg-muted/50 p-2 text-primary">
                <Building2 className="size-5" />
              </span>
              <p className="text-2xl font-bold tracking-tight">{schools.length}</p>
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">
                Active Schools
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
                Inactive Schools
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
                <CardTitle className="text-lg">School Directory</CardTitle>
                <CardDescription>
                  Search, review, and update the schools listed for the portal.
                </CardDescription>
                <div className="relative mt-2">
                  <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                  <Input
                    placeholder="Search schools..."
                    className="pl-9"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                  />
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {filteredSchools.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">
                    No schools found.
                  </p>
                ) : (
                  filteredSchools.map((school) => (
                    <div
                      key={school.id}
                      className="flex items-start justify-between rounded-lg border border-border bg-background p-4 transition hover:bg-muted/50"
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground">
                            {school.name}
                          </span>
                          <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                            {school.code}
                          </span>
                          {!school.is_active && (
                            <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
                              Inactive
                            </span>
                          )}
                        </div>
                        {school.description && (
                          <p className="text-xs text-muted-foreground">
                            {school.description}
                          </p>
                        )}
                      </div>
                      <div className="ml-3 flex items-center gap-1.5">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-muted-foreground"
                          onClick={() => handleOpenEdit(school)}
                        >
                          <Edit className="size-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-destructive hover:bg-destructive/10"
                          onClick={() => handleDelete(school.id)}
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
                {editingSchool ? "Edit School" : "Add School"}
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
                  <Label htmlFor="school-code">School Code</Label>
                  <Input
                    id="school-code"
                    placeholder="e.g. BUS"
                    required
                    value={schoolForm.code}
                    onChange={(event) =>
                      setSchoolForm({ ...schoolForm, code: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-slug">Public Slug</Label>
                  <Input
                    id="school-slug"
                    placeholder="e.g. school-of-business-social-sciences"
                    required
                    value={schoolForm.slug}
                    onChange={(event) =>
                      setSchoolForm({ ...schoolForm, slug: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-name">School Name</Label>
                  <Input
                    id="school-name"
                    placeholder="e.g. School of Business and Social Sciences"
                    required
                    value={schoolForm.name}
                    onChange={(event) =>
                      setSchoolForm({ ...schoolForm, name: event.target.value })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-summary">Summary</Label>
                  <Textarea
                    id="school-summary"
                    placeholder="Short summary used on list cards."
                    value={schoolForm.description}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        description: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-about">About</Label>
                  <Textarea
                    id="school-about"
                    placeholder="Full about text shown on the public detail page."
                    value={schoolForm.about}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        about: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-vision">Vision</Label>
                  <Textarea
                    id="school-vision"
                    placeholder="Vision statement"
                    value={schoolForm.vision}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        vision: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-mission">Mission (one per line)</Label>
                  <Textarea
                    id="school-mission"
                    placeholder="Add each mission item on a new line."
                    value={schoolForm.mission}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        mission: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-programmes">
                    Programmes Offered (one per line)
                  </Label>
                  <Textarea
                    id="school-programmes"
                    placeholder="Add each programme on a new line."
                    value={schoolForm.programmes}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        programmes: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="school-image">Hero Image URL</Label>
                  <Input
                    id="school-image"
                    placeholder="https://example.edu/images/school.jpg"
                    value={schoolForm.image_url}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        image_url: event.target.value,
                      })
                    }
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="school-active"
                    checked={schoolForm.is_active}
                    onChange={(event) =>
                      setSchoolForm({
                        ...schoolForm,
                        is_active: event.target.checked,
                      })
                    }
                    className="size-4 rounded border-border"
                  />
                  <Label htmlFor="school-active" className="cursor-pointer">
                    Active School
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
                  {editingSchool ? "Save Changes" : "Create School"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
