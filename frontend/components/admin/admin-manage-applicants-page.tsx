"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { FileCheck2, MessageSquarePlus, Save, Search, Settings2, UserX, X } from "lucide-react"

import { Header } from "@/components/layout/header"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { formatDateTime } from "@/components/utils/format"
import {
  disableAdminApplicant,
  loadAdminApplicants,
  loadAdminApplicantsSetup,
  updateAdminApplicantsSetup,
  type AdminApplicant,
  type AdminApplicantSetupPayload,
} from "@/lib/admin-applicants"
import type { ApplyAdmissionsSetup, ApplyDocumentType, ApplyQuestion } from "@/lib/apply"

const emptySetup: ApplyAdmissionsSetup = {
  application_number_prefix: "",
  application_number_format: "{prefix}-{period}-{token}",
  document_types: [],
  required_documents: [],
  required_detail_fields: [],
  custom_questions: [],
  scholarship_enabled: true,
  scholarship_label: "Scholarship Application",
  workflow_steps: [],
  status_options: [],
}

function normalizeSetup(setup?: ApplyAdmissionsSetup | null): ApplyAdmissionsSetup {
  return {
    application_number_prefix: setup?.application_number_prefix ?? "",
    application_number_format: setup?.application_number_format ?? "{prefix}-{period}-{token}",
    document_types: setup?.document_types ?? [],
    required_documents: setup?.required_documents ?? [],
    required_detail_fields: setup?.required_detail_fields ?? [],
    custom_questions: setup?.custom_questions ?? [],
    scholarship_enabled: setup?.scholarship_enabled ?? true,
    scholarship_label: setup?.scholarship_label ?? "Scholarship Application",
    workflow_steps: setup?.workflow_steps ?? [],
    status_options: setup?.status_options ?? [],
  }
}

function blankQuestion(): ApplyQuestion {
  return {
    id: `question_${Date.now()}`,
    label: "",
    help_text: "",
    required: false,
  }
}

function toggleValue(values: string[], value: string, checked: boolean) {
  if (checked) {
    return values.includes(value) ? values : [...values, value]
  }
  return values.filter((item) => item !== value)
}

function updateDocument(
  documents: ApplyDocumentType[],
  index: number,
  patch: Partial<ApplyDocumentType>
) {
  return documents.map((document, documentIndex) =>
    documentIndex === index ? { ...document, ...patch } : document
  )
}

export function AdminManageApplicantsPage() {
  const [overview, setOverview] = useState<{
    summary: {
      total: number
      active: number
      inactive: number
      current_session: number
      previous_sessions: number
    }
    applicants: AdminApplicant[]
  } | null>(null)
  const [setupPayload, setSetupPayload] = useState<AdminApplicantSetupPayload | null>(null)
  const [setupForm, setSetupForm] = useState<ApplyAdmissionsSetup>(emptySetup)
  const [isLoading, setIsLoading] = useState(true)
  const [isSavingSetup, setIsSavingSetup] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [search, setSearch] = useState("")
  const [deleteTarget, setDeleteTarget] = useState<AdminApplicant | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const breadcrumbs = [
    { href: "/admin", title: "Admin" },
    { href: "/admin/manage", title: "Manage" },
    { href: "/admin/manage/applicants", title: "Manage Applicants" },
  ]

  useEffect(() => {
    let isMounted = true

    async function loadInitialData() {
      setIsLoading(true)
      setError("")
      try {
        const [overviewResponse, setupResponse] = await Promise.all([
          loadAdminApplicants(),
          loadAdminApplicantsSetup(),
        ])
        if (!isMounted) return
        setOverview(overviewResponse)
        setSetupPayload(setupResponse)
        setSetupForm(normalizeSetup(setupResponse.settings))
      } catch (caught) {
        if (!isMounted) return
        setError(caught instanceof Error ? caught.message : "Unable to load applicants.")
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void loadInitialData()

    return () => {
      isMounted = false
    }
  }, [])

  const filteredApplicants = useMemo(() => {
    const applicants = overview?.applicants ?? []
    if (!search.trim()) return applicants
    const value = search.trim().toLowerCase()
    return applicants.filter((applicant) => {
      const name = `${applicant.first_name ?? ""} ${applicant.last_name ?? ""}`.trim()
      return [
        applicant.username,
        applicant.email,
        name,
        applicant.nationality,
        applicant.country_of_residence,
      ]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(value))
    })
  }, [overview, search])

  async function refreshData() {
    setIsLoading(true)
    setError("")
    try {
      const [overviewResponse, setupResponse] = await Promise.all([
        loadAdminApplicants(),
        loadAdminApplicantsSetup(),
      ])
      setOverview(overviewResponse)
      setSetupPayload(setupResponse)
      setSetupForm(normalizeSetup(setupResponse.settings))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load applicants.")
    } finally {
      setIsLoading(false)
    }
  }

  function updateQuestion(index: number, patch: Partial<ApplyQuestion>) {
    setSetupForm((current) => ({
      ...current,
      custom_questions: current.custom_questions.map((question, questionIndex) =>
        questionIndex === index ? { ...question, ...patch } : question
      ),
    }))
  }

  function removeQuestion(index: number) {
    setSetupForm((current) => ({
      ...current,
      custom_questions: current.custom_questions.filter((_question, questionIndex) => questionIndex !== index),
    }))
  }

  function removeDocument(index: number) {
    setSetupForm((current) => {
      const document_types = current.document_types.filter((_document, documentIndex) => documentIndex !== index)
      return {
        ...current,
        document_types,
        required_documents: document_types.filter((document) => document.required).map((document) => document.value),
      }
    })
  }

  function updateDocumentAt(index: number, patch: Partial<ApplyDocumentType>) {
    setSetupForm((current) => {
      const document_types = updateDocument(current.document_types, index, patch)
      return {
        ...current,
        document_types,
        required_documents: document_types.filter((document) => document.required).map((document) => document.value),
      }
    })
  }

  function addDocument(document?: ApplyDocumentType) {
    setSetupForm((current) => ({
      ...current,
      document_types: [
        ...current.document_types,
        document ?? {
          value: `document_${Date.now()}`,
          label: "New document",
          kind: "file",
          required: false,
        },
      ],
    }))
  }

  async function handleSaveSetup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSavingSetup(true)
    setError("")
    setMessage("")
    try {
      const saved = await updateAdminApplicantsSetup({
        ...setupForm,
        required_documents: setupForm.document_types
          .filter((document) => document.required)
          .map((document) => document.value),
        custom_questions: setupForm.custom_questions.filter((question) => question.label.trim()),
      })
      setSetupPayload(saved)
      setSetupForm(normalizeSetup(saved.settings))
      setMessage(saved.message || "Admissions setup updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update admissions setup.")
    } finally {
      setIsSavingSetup(false)
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return
    setIsDeleting(true)
    setError("")
    setMessage("")
    try {
      await disableAdminApplicant(deleteTarget.id)
      setMessage("Applicant account deleted (disabled).")
      setDeleteTarget(null)
      await refreshData()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to disable applicant.")
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={breadcrumbs} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <span className="inline-flex h-6 w-fit items-center rounded-full border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground">
              Admin Zone
            </span>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Manage Applicants
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Review applicant accounts, configure admission requirements, and open individual applicant review pages.
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={refreshData} disabled={isLoading}>
            Refresh
          </Button>
        </section>

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
            {error}
          </div>
        ) : null}
        {message ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700">
            {message}
          </div>
        ) : null}

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>Total Applicants</CardDescription>
              <CardTitle className="text-2xl">{overview?.summary.total ?? 0}</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              All applicant accounts created in the system.
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>This Session</CardDescription>
              <CardTitle className="text-2xl">{overview?.summary.current_session ?? 0}</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Applicants tied to active intake sessions.
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>Previous Sessions</CardDescription>
              <CardTitle className="text-2xl">{overview?.summary.previous_sessions ?? 0}</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Applicants with prior intake applications.
            </CardContent>
          </Card>
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="pb-2">
              <CardDescription>Active Accounts</CardDescription>
              <CardTitle className="text-2xl">{overview?.summary.active ?? 0}</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              Applicants who can log in today.
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_28rem]">
          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader className="gap-2">
              <CardTitle className="text-base">Applicant Accounts</CardTitle>
              <CardDescription>
                Search applicants and open their individual management workspace.
              </CardDescription>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search by name, username, email, or country"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <p className="text-sm text-muted-foreground">Loading applicants...</p>
              ) : filteredApplicants.length === 0 ? (
                <p className="text-sm text-muted-foreground">No applicants found.</p>
              ) : (
                <div className="divide-y divide-border/70">
                  {filteredApplicants.map((applicant) => {
                    const fullName = `${applicant.first_name ?? ""} ${applicant.last_name ?? ""}`.trim()
                    return (
                      <div
                        key={applicant.id}
                        className="flex flex-col gap-3 py-4 md:flex-row md:items-center md:justify-between"
                      >
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium text-foreground">
                              {fullName || applicant.username}
                            </p>
                            <Badge variant={applicant.is_active ? "secondary" : "destructive"}>
                              {applicant.is_active ? "Active" : "Disabled"}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {applicant.username} • {applicant.email}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {applicant.nationality || "Nationality not set"} •{" "}
                            {applicant.country_of_residence || "Residence not set"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Created {formatDateTime(applicant.created_at)}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            render={<Link href={`/admin/manage/applicants/${applicant.id}`} />}
                          >
                            Manage
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => setDeleteTarget(applicant)}
                          >
                            Delete
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/70 bg-card/95 shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-3">
                <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                  <Settings2 className="size-5" />
                </span>
                <div>
                  <CardTitle className="text-base">Admissions Setup</CardTitle>
                  <CardDescription>Questions, documents, details, and scholarship controls.</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <form className="space-y-6" onSubmit={handleSaveSetup}>
                <div className="space-y-3 rounded-lg border border-border bg-muted/30 p-3">
                  <div>
                    <Label>Application number format</Label>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Tokens: {"{prefix}"}, {"{year}"}, {"{month}"}, {"{period}"}, and {"{token}"}.
                    </p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input
                      value={setupForm.application_number_prefix}
                      onChange={(event) =>
                        setSetupForm((current) => ({ ...current, application_number_prefix: event.target.value }))
                      }
                      placeholder="APP"
                      aria-label="Application number prefix"
                    />
                    <Input
                      value={setupForm.application_number_format}
                      onChange={(event) =>
                        setSetupForm((current) => ({ ...current, application_number_format: event.target.value }))
                      }
                      aria-label="Application number format"
                    />
                  </div>
                </div>

                <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-3">
                  <input
                    id="scholarship_enabled"
                    type="checkbox"
                    className="mt-1 size-4"
                    checked={setupForm.scholarship_enabled}
                    onChange={(event) =>
                      setSetupForm((current) => ({
                        ...current,
                        scholarship_enabled: event.target.checked,
                      }))
                    }
                  />
                  <div>
                    <Label htmlFor="scholarship_enabled">Enable scholarship stage</Label>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Applicants can request scholarship review when this is enabled. The label is configurable below.
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="scholarship_label">Scholarship section label</Label>
                  <Input
                    id="scholarship_label"
                    value={setupForm.scholarship_label}
                    onChange={(event) =>
                      setSetupForm((current) => ({ ...current, scholarship_label: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <FileCheck2 className="size-4 text-muted-foreground" />
                    <Label>Required Details</Label>
                  </div>
                  <div className="grid max-h-64 gap-2 overflow-y-auto rounded-lg border border-border p-3">
                    {(setupPayload?.detail_fields ?? []).map((field) => (
                      <label key={field.value} className="flex items-start gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="mt-1 size-4"
                          checked={setupForm.required_detail_fields.includes(field.value)}
                          onChange={(event) =>
                            setSetupForm((current) => ({
                              ...current,
                              required_detail_fields: toggleValue(
                                current.required_detail_fields,
                                field.value,
                                event.target.checked
                              ),
                            }))
                          }
                        />
                        <span>
                          <span className="font-medium">{field.label}</span>
                          <span className="block text-xs text-muted-foreground">{field.section}</span>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                    <FileCheck2 className="size-4 text-muted-foreground" />
                      <Label>Document Types</Label>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => addDocument()}
                    >
                      Add custom
                    </Button>
                  </div>
                  <div className="space-y-3 rounded-lg border border-border p-3">
                    {setupForm.document_types.map((documentType, index) => (
                      <div key={documentType.value + "_" + index} className="space-y-2 rounded-md border border-border/70 p-3">
                        <div className="flex items-center gap-2">
                          <Input
                            value={documentType.label}
                            onChange={(event) => updateDocumentAt(index, { label: event.target.value })}
                            aria-label={"Document " + (index + 1) + " label"}
                          />
                          <Button
                            type="button"
                            size="icon-xs"
                            variant="ghost"
                            onClick={() => removeDocument(index)}
                            aria-label={"Remove " + documentType.label}
                          >
                            <X className="size-3" />
                          </Button>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-xs">
                          <span className="rounded bg-muted px-2 py-1">{documentType.value}</span>
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              className="size-4"
                              checked={Boolean(documentType.required)}
                              onChange={(event) => updateDocumentAt(index, { required: event.target.checked })}
                            />
                            Required
                          </label>
                          <label className="flex items-center gap-2">
                            <span>File type</span>
                            <select
                              className="h-8 rounded-md border border-input bg-transparent px-2"
                              value={documentType.kind ?? "file"}
                              onChange={(event) =>
                                updateDocumentAt(index, { kind: event.target.value as "file" | "image" })
                              }
                            >
                              <option value="file">Any allowed file</option>
                              <option value="image">Image only</option>
                            </select>
                          </label>
                        </div>
                      </div>
                    ))}
                    {setupForm.document_types.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No document types enabled.</p>
                    ) : null}
                    {(setupPayload?.document_type_options ?? [])
                      .filter((item) => !setupForm.document_types.some((document) => document.value === item.value))
                      .length ? (
                      <div className="flex flex-wrap items-center gap-2 border-t border-border/70 pt-3">
                        <select
                          className="h-9 min-w-0 flex-1 rounded-md border border-input bg-transparent px-2 text-sm"
                          defaultValue=""
                          onChange={(event) => {
                            const item = setupPayload?.document_type_options.find(
                              (option) => option.value === event.target.value
                            )
                            if (item) addDocument({ ...item, required: false })
                            event.target.value = ""
                          }}
                        >
                          <option value="">Add a standard document type...</option>
                          {(setupPayload?.document_type_options ?? [])
                            .filter((item) => !setupForm.document_types.some((document) => document.value === item.value))
                            .map((item) => (
                              <option key={item.value} value={item.value}>{item.label}</option>
                            ))}
                        </select>
                      </div>
                    ) : null}
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <Label>Workflow stages and status labels</Label>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Disable scholarship or interview stages for institutions that do not use them.
                    </p>
                  </div>
                  <div className="space-y-2 rounded-lg border border-border p-3">
                    {setupForm.workflow_steps.map((step, index) => (
                      <label key={step.value} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="size-4"
                          checked={step.enabled}
                          onChange={(event) =>
                            setSetupForm((current) => ({
                              ...current,
                              workflow_steps: current.workflow_steps.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, enabled: event.target.checked } : item
                              ),
                            }))
                          }
                        />
                        <Input
                          value={step.label}
                          onChange={(event) =>
                            setSetupForm((current) => ({
                              ...current,
                              workflow_steps: current.workflow_steps.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, label: event.target.value } : item
                              ),
                            }))
                          }
                          className="h-8"
                          aria-label={step.value + " step label"}
                        />
                      </label>
                    ))}
                    {setupForm.status_options.map((statusOption, index) => (
                      <label key={statusOption.value} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="size-4"
                          checked={statusOption.enabled}
                          onChange={(event) =>
                            setSetupForm((current) => ({
                              ...current,
                              status_options: current.status_options.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, enabled: event.target.checked } : item
                              ),
                            }))
                          }
                        />
                        <Input
                          value={statusOption.label}
                          onChange={(event) =>
                            setSetupForm((current) => ({
                              ...current,
                              status_options: current.status_options.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, label: event.target.value } : item
                              ),
                            }))
                          }
                          className="h-8"
                          aria-label={statusOption.value + " status label"}
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <MessageSquarePlus className="size-4 text-muted-foreground" />
                      <Label>Applicant Questions</Label>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setSetupForm((current) => ({
                          ...current,
                          custom_questions: [...current.custom_questions, blankQuestion()],
                        }))
                      }
                    >
                      Add
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {setupForm.custom_questions.length ? (
                      setupForm.custom_questions.map((question, index) => (
                        <div key={question.id || index} className="space-y-3 rounded-lg border border-border p-3">
                          <div className="flex items-center justify-between gap-2">
                            <Label htmlFor={`question_${index}`}>Question</Label>
                            <Button type="button" size="icon-xs" variant="ghost" onClick={() => removeQuestion(index)}>
                              <X className="size-3" />
                            </Button>
                          </div>
                          <Input
                            id={`question_${index}`}
                            value={question.label}
                            onChange={(event) => updateQuestion(index, { label: event.target.value })}
                            placeholder="Future goals, vision, SOP, or other prompt"
                          />
                          <Textarea
                            value={question.help_text ?? ""}
                            onChange={(event) => updateQuestion(index, { help_text: event.target.value })}
                            placeholder="Optional help text"
                          />
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              className="size-4"
                              checked={question.required}
                              onChange={(event) => updateQuestion(index, { required: event.target.checked })}
                            />
                            Required
                          </label>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-lg border border-dashed border-border bg-muted/30 p-3 text-sm text-muted-foreground">
                        No additional applicant questions configured.
                      </div>
                    )}
                  </div>
                </div>

                <Button className="w-full" type="submit" disabled={isSavingSetup}>
                  <Save className="size-4" />
                  {isSavingSetup ? "Saving..." : "Save admissions setup"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </section>
      </main>

      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) setDeleteTarget(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete applicant account?</AlertDialogTitle>
            <AlertDialogDescription>
              This will disable the applicant login and mark the account as inactive.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              <UserX className="size-4" />
              {isDeleting ? "Deleting..." : "Delete account"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
