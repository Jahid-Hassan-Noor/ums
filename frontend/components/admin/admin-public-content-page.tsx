"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertCircle,
  Archive,
  CheckCircle2,
  Edit3,
  ExternalLink,
  Loader2,
  Search,
} from "lucide-react"

import { EntityEditorCard } from "@/components/admin/entity-editor-card"
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

export type PublicContentKind =
  | "pages"
  | "news"
  | "events"
  | "announcements"
  | "official-links"

type Choice = {
  value: string
  label: string
}

type PublicContentRecord = {
  id: number
  title: string
  slug?: string
  route_path?: string
  section?: string
  summary?: string
  body?: string
  metadata?: Record<string, unknown> | null
  status?: string
  published_at?: string | null
  description?: string
  starts_at?: string | null
  ends_at?: string | null
  location?: string
  audience?: string
  is_pinned?: boolean
  is_published?: boolean
  url?: string
  category?: string
  sort_order?: number
  is_active?: boolean
}

type PublicContentResponse = {
  pages?: PublicContentRecord[]
  news?: PublicContentRecord[]
  events?: PublicContentRecord[]
  announcements?: PublicContentRecord[]
  official_links?: PublicContentRecord[]
  sections?: Choice[]
  statuses?: Choice[]
  audiences?: Choice[]
}

type FormState = {
  title: string
  slug: string
  route_path: string
  section: string
  summary: string
  body: string
  metadata: string
  nav_show: boolean
  nav_label: string
  nav_parent: string
  status: string
  published_at: string
  description: string
  starts_at: string
  ends_at: string
  location: string
  audience: string
  is_pinned: boolean
  is_published: boolean
  url: string
  category: string
  sort_order: string
  is_active: boolean
}

const config = {
  pages: {
    title: "Public Content",
    description: "Manage public page copy and page-level metadata.",
    endpoint: "/admin/public-content",
    collectionKey: "pages",
    itemLabel: "Page",
  },
  news: {
    title: "News",
    description: "Manage public news shown on the website.",
    endpoint: "/admin/public-content/news",
    collectionKey: "news",
    itemLabel: "News item",
  },
  events: {
    title: "Events",
    description: "Manage public events shown on the website.",
    endpoint: "/admin/public-content/events",
    collectionKey: "events",
    itemLabel: "Event",
  },
  announcements: {
    title: "Announcements",
    description: "Manage public and role-targeted announcements.",
    endpoint: "/admin/public-content/announcements",
    collectionKey: "announcements",
    itemLabel: "Announcement",
  },
  "official-links": {
    title: "Official Links",
    description: "Manage public resource links and role-specific links.",
    endpoint: "/admin/public-content/official-links",
    collectionKey: "official_links",
    itemLabel: "Official link",
  },
} as const

function defaultDateTime() {
  return new Date().toISOString().slice(0, 16)
}

function emptyForm(kind: PublicContentKind): FormState {
  return {
    title: "",
    slug: "",
    route_path: kind === "pages" ? "/" : "",
    section: "home",
    summary: "",
    body: "",
    metadata: "{}",
    nav_show: true,
    nav_label: "",
    nav_parent: "",
    status: "draft",
    published_at: "",
    description: "",
    starts_at: kind === "events" ? defaultDateTime() : "",
    ends_at: "",
    location: "",
    audience: "public",
    is_pinned: false,
    is_published: kind === "announcements",
    url: "",
    category: "",
    sort_order: "0",
    is_active: true,
  }
}

function toDateTimeLocal(value?: string | null) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  return date.toISOString().slice(0, 16)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function textValue(value: unknown) {
  return typeof value === "string" ? value : ""
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null
}

function formFromRecord(
  kind: PublicContentKind,
  record: PublicContentRecord
): FormState {
  const metadata = isRecord(record.metadata) ? record.metadata : {}
  const navigation = isRecord(metadata.navigation) ? metadata.navigation : {}
  return {
    title: record.title ?? "",
    slug: record.slug ?? "",
    route_path: record.route_path ?? "",
    section: record.section ?? "home",
    summary: record.summary ?? "",
    body: record.body ?? "",
    metadata: JSON.stringify(record.metadata ?? {}, null, 2),
    nav_show:
      booleanValue(navigation.show) ??
      booleanValue(navigation.show_in_navigation) ??
      booleanValue(metadata.show_in_navigation) ??
      (record.route_path !== "/"),
    nav_label:
      textValue(navigation.label) || textValue(metadata.navigation_label),
    nav_parent:
      textValue(navigation.parent) ||
      textValue(navigation.parent_path) ||
      textValue(metadata.parent_path),
    status: record.status ?? "draft",
    published_at: toDateTimeLocal(record.published_at),
    description: record.description ?? "",
    starts_at: toDateTimeLocal(record.starts_at),
    ends_at: toDateTimeLocal(record.ends_at),
    location: record.location ?? "",
    audience: record.audience ?? "public",
    is_pinned: Boolean(record.is_pinned),
    is_published: Boolean(record.is_published),
    url: record.url ?? "",
    category: record.category ?? "",
    sort_order: String(record.sort_order ?? 0),
    is_active: record.is_active ?? true,
  }
}

function recordSummary(kind: PublicContentKind, record: PublicContentRecord) {
  if (kind === "pages") return record.route_path || record.slug || "No route"
  if (kind === "events") {
    return [record.starts_at?.slice(0, 10), record.location]
      .filter(Boolean)
      .join(" · ")
  }
  if (kind === "official-links") return record.url || "No URL"
  if (kind === "announcements") return record.audience || "public"
  return record.summary || record.slug || "No summary"
}

function statusLabel(kind: PublicContentKind, record: PublicContentRecord) {
  if (kind === "announcements") {
    return record.is_published ? "Published" : "Draft"
  }
  if (kind === "official-links") {
    return record.is_active ? "Active" : "Inactive"
  }
  return record.status ?? "draft"
}

function maybeNull(value: string) {
  return value.trim() ? value : null
}

function numberValue(value: string) {
  return Number(value || 0)
}

export function AdminPublicContentPage({ kind }: { kind: PublicContentKind }) {
  const page = config[kind]
  const [records, setRecords] = useState<PublicContentRecord[]>([])
  const [sections, setSections] = useState<Choice[]>([])
  const [statuses, setStatuses] = useState<Choice[]>([])
  const [audiences, setAudiences] = useState<Choice[]>([])
  const [form, setForm] = useState<FormState>(() => emptyForm(kind))
  const [editingRecord, setEditingRecord] =
    useState<PublicContentRecord | null>(null)
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const data = await apiFetch<PublicContentResponse>(page.endpoint)
    const items = data[page.collectionKey] ?? []
    setRecords(items)
    setSections(data.sections ?? [])
    setStatuses(data.statuses ?? [])
    setAudiences(data.audiences ?? [])
  }, [page.collectionKey, page.endpoint])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setForm(emptyForm(kind))
      setEditingRecord(null)
      setIsLoading(true)
      void loadData()
        .catch((caught) => {
          setError(
            caught instanceof Error
              ? caught.message
              : `Unable to load ${page.title.toLowerCase()}.`
          )
        })
        .finally(() => setIsLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [kind, loadData, page.title])

  const filteredRecords = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return records
    return records.filter((record) =>
      [
        record.title,
        record.slug,
        record.route_path,
        record.summary,
        record.description,
        record.body,
        record.url,
        record.category,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized)
    )
  }, [query, records])

  function updateField(field: keyof FormState, value: string | boolean) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function resetForm() {
    setEditingRecord(null)
    setForm(emptyForm(kind))
    setError("")
  }

  function startEdit(record: PublicContentRecord) {
    setEditingRecord(record)
    setForm(formFromRecord(kind, record))
    setError("")
    setSuccess("")
  }

  function buildPayload() {
    if (kind === "pages") {
      let metadata: Record<string, unknown> | null = null
      try {
        metadata = form.metadata.trim() ? JSON.parse(form.metadata) : null
      } catch {
        setError("Metadata must be valid JSON.")
        return null
      }
      const normalizedMetadata = isRecord(metadata) ? { ...metadata } : {}
      const navigation = isRecord(normalizedMetadata.navigation)
        ? { ...normalizedMetadata.navigation }
        : {}
      navigation.show = form.nav_show
      if (form.nav_label.trim()) {
        navigation.label = form.nav_label.trim()
      } else {
        delete navigation.label
      }
      if (form.nav_parent.trim()) {
        navigation.parent = form.nav_parent.trim()
      } else {
        delete navigation.parent
      }
      normalizedMetadata.navigation = navigation
      return {
        title: form.title.trim(),
        slug: form.slug.trim(),
        route_path: form.route_path.trim(),
        section: form.section,
        summary: form.summary,
        body: form.body,
        metadata: normalizedMetadata,
        status: form.status,
        published_at: maybeNull(form.published_at),
        sort_order: numberValue(form.sort_order),
      }
    }

    if (kind === "news") {
      return {
        title: form.title.trim(),
        slug: form.slug.trim(),
        summary: form.summary,
        body: form.body,
        status: form.status,
        published_at: maybeNull(form.published_at),
      }
    }

    if (kind === "events") {
      return {
        title: form.title.trim(),
        slug: form.slug.trim(),
        description: form.description,
        starts_at: form.starts_at,
        ends_at: maybeNull(form.ends_at),
        location: form.location,
        status: form.status,
      }
    }

    if (kind === "announcements") {
      return {
        title: form.title.trim(),
        body: form.body,
        audience: form.audience,
        starts_at: maybeNull(form.starts_at),
        ends_at: maybeNull(form.ends_at),
        is_pinned: form.is_pinned,
        is_published: form.is_published,
      }
    }

    return {
      title: form.title.trim(),
      url: form.url.trim(),
      category: form.category,
      audience: form.audience,
      description: form.description,
      sort_order: numberValue(form.sort_order),
      is_active: form.is_active,
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setSuccess("")

    const payload = buildPayload()
    if (!payload) return

    setIsSaving(true)
    try {
      if (editingRecord) {
        await apiFetch(`${page.endpoint}/${editingRecord.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
        setSuccess(`${page.itemLabel} updated successfully.`)
      } else {
        await apiFetch(page.endpoint, {
          method: "POST",
          body: JSON.stringify(payload),
        })
        setSuccess(`${page.itemLabel} created successfully.`)
      }
      await loadData()
      resetForm()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : `Unable to save ${page.itemLabel.toLowerCase()}.`
      )
    } finally {
      setIsSaving(false)
    }
  }

  async function deleteRecord(record: PublicContentRecord) {
    if (!confirm(`Delete ${record.title}?`)) return
    setError("")
    setSuccess("")
    try {
      await apiFetch(`${page.endpoint}/${record.id}`, { method: "DELETE" })
      setSuccess(`${page.itemLabel} deleted successfully.`)
      await loadData()
      if (editingRecord?.id === record.id) resetForm()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : `Unable to delete ${page.itemLabel.toLowerCase()}.`
      )
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/public-content", title: "Public Content" },
          { href: `/admin/public-content/${kind}`, title: page.title },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {page.title}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              {page.description}
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
          <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_26rem]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <CardTitle className="text-lg">{page.title}</CardTitle>
                    <CardDescription>{records.length} records</CardDescription>
                  </div>
                  <div className="relative md:w-72">
                    <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      className="pl-9"
                      placeholder={`Search ${page.title.toLowerCase()}`}
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {filteredRecords.map((record) => (
                  <div
                    key={record.id}
                    className="rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold">{record.title}</p>
                          <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {statusLabel(kind, record)}
                          </span>
                          {record.category ? (
                            <span className="rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              {record.category}
                            </span>
                          ) : null}
                        </div>
                        <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">
                          {recordSummary(kind, record)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {kind === "official-links" && record.url ? (
                          <Button
                            variant="outline"
                            size="sm"
                            render={
                              <a
                                href={record.url}
                                target="_blank"
                                rel="noreferrer"
                              />
                            }
                          >
                            <ExternalLink className="size-4" />
                          </Button>
                        ) : null}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startEdit(record)}
                        >
                          <Edit3 className="size-4" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteRecord(record)}
                        >
                          <Archive className="size-4" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredRecords.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                    No records found.
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <EntityEditorCard
              title={
                editingRecord
                  ? `Edit ${page.itemLabel}`
                  : `Add ${page.itemLabel}`
              }
              description={page.description}
              isEditing={Boolean(editingRecord)}
              isSaving={isSaving}
              onSubmit={handleSubmit}
              onCancel={resetForm}
            >
              <div className="space-y-2">
                <Label htmlFor="public-title">Title</Label>
                <Input
                  id="public-title"
                  value={form.title}
                  onChange={(event) => updateField("title", event.target.value)}
                  required
                />
              </div>

              {kind === "pages" || kind === "news" || kind === "events" ? (
                <div className="space-y-2">
                  <Label htmlFor="public-slug">Slug</Label>
                  <Input
                    id="public-slug"
                    value={form.slug}
                    onChange={(event) =>
                      updateField("slug", event.target.value)
                    }
                    placeholder="Auto-generated when empty"
                  />
                </div>
              ) : null}

              {kind === "pages" ? (
                <>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="public-route">Route Path</Label>
                      <Input
                        id="public-route"
                        value={form.route_path}
                        onChange={(event) =>
                          updateField("route_path", event.target.value)
                        }
                        placeholder="/about"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="public-section">Section</Label>
                      <select
                        id="public-section"
                        value={form.section}
                        onChange={(event) =>
                          updateField("section", event.target.value)
                        }
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        {sections.map((section) => (
                          <option key={section.value} value={section.value}>
                            {section.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/30 p-3">
                    <label className="flex items-start gap-2 text-sm font-medium">
                      <input
                        type="checkbox"
                        checked={form.nav_show}
                        onChange={(event) =>
                          updateField("nav_show", event.target.checked)
                        }
                        className="mt-1"
                      />
                      <span>
                        Show this published page in public navigation.
                      </span>
                    </label>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="public-nav-label">
                          Navigation Label
                        </Label>
                        <Input
                          id="public-nav-label"
                          value={form.nav_label}
                          onChange={(event) =>
                            updateField("nav_label", event.target.value)
                          }
                          placeholder="Defaults to page title"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="public-nav-parent">Parent Path</Label>
                        <Input
                          id="public-nav-parent"
                          value={form.nav_parent}
                          onChange={(event) =>
                            updateField("nav_parent", event.target.value)
                          }
                          placeholder="/about"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="public-summary">Summary</Label>
                    <Textarea
                      id="public-summary"
                      value={form.summary}
                      onChange={(event) =>
                        updateField("summary", event.target.value)
                      }
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="public-body">Body</Label>
                    <Textarea
                      id="public-body"
                      value={form.body}
                      onChange={(event) =>
                        updateField("body", event.target.value)
                      }
                      rows={7}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="public-metadata">Metadata JSON</Label>
                    <Textarea
                      id="public-metadata"
                      value={form.metadata}
                      onChange={(event) =>
                        updateField("metadata", event.target.value)
                      }
                      rows={7}
                      className="font-mono text-xs"
                    />
                  </div>
                </>
              ) : null}

              {kind === "news" ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="public-summary">Summary</Label>
                    <Textarea
                      id="public-summary"
                      value={form.summary}
                      onChange={(event) =>
                        updateField("summary", event.target.value)
                      }
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="public-body">Body</Label>
                    <Textarea
                      id="public-body"
                      value={form.body}
                      onChange={(event) =>
                        updateField("body", event.target.value)
                      }
                      rows={8}
                    />
                  </div>
                </>
              ) : null}

              {kind === "events" ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="event-description">Description</Label>
                    <Textarea
                      id="event-description"
                      value={form.description}
                      onChange={(event) =>
                        updateField("description", event.target.value)
                      }
                      rows={5}
                    />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="event-starts">Starts At</Label>
                      <Input
                        id="event-starts"
                        type="datetime-local"
                        value={form.starts_at}
                        onChange={(event) =>
                          updateField("starts_at", event.target.value)
                        }
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="event-ends">Ends At</Label>
                      <Input
                        id="event-ends"
                        type="datetime-local"
                        value={form.ends_at}
                        onChange={(event) =>
                          updateField("ends_at", event.target.value)
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="event-location">Location</Label>
                    <Input
                      id="event-location"
                      value={form.location}
                      onChange={(event) =>
                        updateField("location", event.target.value)
                      }
                    />
                  </div>
                </>
              ) : null}

              {kind === "announcements" ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="announcement-body">Body</Label>
                    <Textarea
                      id="announcement-body"
                      value={form.body}
                      onChange={(event) =>
                        updateField("body", event.target.value)
                      }
                      rows={6}
                      required
                    />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="announcement-starts">Starts At</Label>
                      <Input
                        id="announcement-starts"
                        type="datetime-local"
                        value={form.starts_at}
                        onChange={(event) =>
                          updateField("starts_at", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="announcement-ends">Ends At</Label>
                      <Input
                        id="announcement-ends"
                        type="datetime-local"
                        value={form.ends_at}
                        onChange={(event) =>
                          updateField("ends_at", event.target.value)
                        }
                      />
                    </div>
                  </div>
                </>
              ) : null}

              {kind === "official-links" ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="official-url">URL</Label>
                    <Input
                      id="official-url"
                      value={form.url}
                      onChange={(event) =>
                        updateField("url", event.target.value)
                      }
                      required
                    />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="official-category">Category</Label>
                      <Input
                        id="official-category"
                        value={form.category}
                        onChange={(event) =>
                          updateField("category", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="official-sort">Sort Order</Label>
                      <Input
                        id="official-sort"
                        type="number"
                        min="0"
                        value={form.sort_order}
                        onChange={(event) =>
                          updateField("sort_order", event.target.value)
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="official-description">Description</Label>
                    <Textarea
                      id="official-description"
                      value={form.description}
                      onChange={(event) =>
                        updateField("description", event.target.value)
                      }
                      rows={4}
                    />
                  </div>
                </>
              ) : null}

              {kind === "pages" || kind === "news" || kind === "events" ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="public-status">Status</Label>
                    <select
                      id="public-status"
                      value={form.status}
                      onChange={(event) =>
                        updateField("status", event.target.value)
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      {statuses.map((statusOption) => (
                        <option
                          key={statusOption.value}
                          value={statusOption.value}
                        >
                          {statusOption.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {kind !== "events" ? (
                    <div className="space-y-2">
                      <Label htmlFor="published-at">Published At</Label>
                      <Input
                        id="published-at"
                        type="datetime-local"
                        value={form.published_at}
                        onChange={(event) =>
                          updateField("published_at", event.target.value)
                        }
                      />
                    </div>
                  ) : null}
                </div>
              ) : null}

              {kind === "announcements" || kind === "official-links" ? (
                <div className="space-y-2">
                  <Label htmlFor="public-audience">Audience</Label>
                  <select
                    id="public-audience"
                    value={form.audience}
                    onChange={(event) =>
                      updateField("audience", event.target.value)
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {audiences.map((audience) => (
                      <option key={audience.value} value={audience.value}>
                        {audience.label}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

              {kind === "pages" ? (
                <div className="space-y-2">
                  <Label htmlFor="page-sort">Sort Order</Label>
                  <Input
                    id="page-sort"
                    type="number"
                    min="0"
                    value={form.sort_order}
                    onChange={(event) =>
                      updateField("sort_order", event.target.value)
                    }
                  />
                </div>
              ) : null}

              {kind === "announcements" ? (
                <div className="flex flex-wrap gap-4 text-sm">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.is_pinned}
                      onChange={(event) =>
                        updateField("is_pinned", event.target.checked)
                      }
                    />
                    Pinned
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.is_published}
                      onChange={(event) =>
                        updateField("is_published", event.target.checked)
                      }
                    />
                    Published
                  </label>
                </div>
              ) : null}

              {kind === "official-links" ? (
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(event) =>
                      updateField("is_active", event.target.checked)
                    }
                  />
                  Active
                </label>
              ) : null}
            </EntityEditorCard>
          </section>
        )}
      </main>
    </div>
  )
}
