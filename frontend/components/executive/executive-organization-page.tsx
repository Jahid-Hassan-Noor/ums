"use client"

import { useEffect, useState } from "react"
import { AlertCircle, CheckCircle2, Loader2, Save } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiFetch } from "@/lib/auth"

type Scope = {
  kind: "school" | "center" | null
  id: number | null
  code: string
  name: string
  academic_workflows: boolean
}

type OrganisationUnit = {
  id: number
  code: string
  name: string
  description: string
  about: string
  vision?: string
  mission?: string[]
  programmes?: string[]
  offerings?: string[]
  image_url: string
  is_active: boolean
}

type OrganisationResponse = {
  scope: Scope
  unit_label: "school" | "centre"
  unit: OrganisationUnit
}

const emptyForm = {
  name: "",
  description: "",
  about: "",
  vision: "",
  mission: "",
  offerings: "",
  image_url: "",
}

function splitLines(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
}

export function ExecutiveOrganizationPage() {
  const [scope, setScope] = useState<Scope | null>(null)
  const [unitLabel, setUnitLabel] = useState<"school" | "centre">("centre")
  const [form, setForm] = useState(emptyForm)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    async function loadData() {
      try {
        const data = await apiFetch<OrganisationResponse>("/executive/organization")
        setScope(data.scope)
        setUnitLabel(data.unit_label)
        setForm({
          name: data.unit.name ?? "",
          description: data.unit.description ?? "",
          about: data.unit.about ?? "",
          vision: data.unit.vision ?? "",
          mission: (data.unit.mission ?? []).join("\n"),
          offerings: (data.unit.offerings ?? data.unit.programmes ?? []).join("\n"),
          image_url: data.unit.image_url ?? "",
        })
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Unable to load organisation details.")
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  function updateField(field: keyof typeof emptyForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")
    setIsSaving(true)

    try {
      const payload =
        unitLabel === "school"
          ? {
              name: form.name,
              description: form.description,
              about: form.about,
              vision: form.vision,
              mission: splitLines(form.mission),
              programmes: splitLines(form.offerings),
              image_url: form.image_url,
            }
          : {
              name: form.name,
              description: form.description,
              about: form.about,
              offerings: splitLines(form.offerings),
              image_url: form.image_url,
            }
      await apiFetch("/executive/organization", {
        method: "PATCH",
        body: JSON.stringify(payload),
      })
      setSuccess("Organisation details updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save organisation details.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/organization", title: "Organisation" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Organisation Details
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Edit the public details for your assigned {unitLabel}.
            </p>
          </div>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            <p>{success}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Public Profile</CardTitle>
                <CardDescription>
                  These fields feed the school and centre public pages.
                </CardDescription>
              </CardHeader>
              <form onSubmit={handleSubmit}>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="org-name">Name</Label>
                      <Input
                        id="org-name"
                        value={form.name}
                        onChange={(event) => updateField("name", event.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="org-image">Image URL</Label>
                      <Input
                        id="org-image"
                        value={form.image_url}
                        onChange={(event) => updateField("image_url", event.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-description">Description</Label>
                    <Textarea
                      id="org-description"
                      value={form.description}
                      onChange={(event) => updateField("description", event.target.value)}
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-about">About</Label>
                    <Textarea
                      id="org-about"
                      value={form.about}
                      onChange={(event) => updateField("about", event.target.value)}
                      rows={5}
                    />
                  </div>
                  {unitLabel === "school" ? (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="org-vision">Vision</Label>
                        <Textarea
                          id="org-vision"
                          value={form.vision}
                          onChange={(event) => updateField("vision", event.target.value)}
                          rows={3}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="org-mission">Mission</Label>
                        <Textarea
                          id="org-mission"
                          value={form.mission}
                          onChange={(event) => updateField("mission", event.target.value)}
                          rows={5}
                        />
                      </div>
                    </>
                  ) : null}
                  <div className="space-y-2">
                    <Label htmlFor="org-offerings">
                      {unitLabel === "school" ? "Programme Names" : "Offering Names"}
                    </Label>
                    <Textarea
                      id="org-offerings"
                      value={form.offerings}
                      onChange={(event) => updateField("offerings", event.target.value)}
                      rows={6}
                    />
                  </div>
                </CardContent>
                <div className="flex justify-end border-t p-4">
                  <Button type="submit" disabled={isSaving}>
                    {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                    {isSaving ? "Saving..." : "Save Details"}
                  </Button>
                </div>
              </form>
            </Card>

            <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Assigned Scope</CardTitle>
                <CardDescription>
                  Your edits are limited to this {unitLabel}.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="font-medium">{scope?.name ?? "Unassigned"}</p>
                <p className="text-muted-foreground">{scope?.code}</p>
                <p className="text-muted-foreground">
                  {scope?.academic_workflows ? "Academic workflows enabled" : "Centre programmes only"}
                </p>
              </CardContent>
            </Card>
          </section>
        )}
      </main>
    </div>
  )
}
