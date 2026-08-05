"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { AlertCircle, ArrowLeft, CalendarClock, CheckCircle2, FileText, Save, UserRound } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { formatDateTime } from "@/components/utils/format"
import {
  loadAdminApplicantDetail,
  loadAdminApplicantsSetup,
  updateAdminApplicant,
  updateAdminApplicationStatus,
  updateAdminDocumentReview,
  updateAdminScholarshipReview,
  type AdminApplicant,
  type AdminApplicantDetail,
} from "@/lib/admin-applicants"
import { identityNumberLabel } from "@/lib/countries"
import {
  loadApplyOptions,
  type ApplyApplication,
  type ApplyDocument,
  type ApplyOption,
} from "@/lib/apply"

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

const statusOptions = [
  ["submitted", "Submitted"],
  ["screening", "Screening"],
  ["info_requested", "Information Requested"],
  ["scholarship_review", "Scholarship Review"],
  ["interview", "Call for Interview"],
  ["offered", "Accepted / Offered"],
  ["waitlisted", "Waitlisted"],
  ["rejected", "Rejected"],
  ["enrolled", "Enrolled"],
  ["withdrawn", "Withdrawn"],
]

type ConfiguredStatusOption = ApplyOption & { enabled: boolean }

const documentStatusOptions = [
  ["uploaded", "Uploaded"],
  ["accepted", "Accepted"],
  ["rejected", "Rejected"],
]

const scholarshipStatusOptions = [
  ["draft", "Draft"],
  ["submitted", "Submitted"],
  ["under_review", "Under Review"],
  ["shortlisted", "Shortlisted"],
  ["awarded", "Awarded"],
  ["not_awarded", "Not Awarded"],
  ["withdrawn", "Withdrawn"],
]

type AccountForm = {
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  nationality: string
  country_of_residence: string
  passport_or_identity_no: string
  is_active: boolean
}

type StatusForm = {
  status: string
  note: string
  review_notes: string
  interview_at: string
  interview_location: string
  interview_details: string
}

function accountFormFromApplicant(applicant?: AdminApplicant | null): AccountForm {
  return {
    username: applicant?.username ?? "",
    email: applicant?.email ?? "",
    first_name: applicant?.first_name ?? "",
    last_name: applicant?.last_name ?? "",
    phone: applicant?.phone ?? "",
    nationality: applicant?.nationality ?? "",
    country_of_residence: applicant?.country_of_residence ?? "",
    passport_or_identity_no: applicant?.passport_or_identity_no ?? "",
    is_active: applicant?.is_active ?? true,
  }
}

function statusFormFromApplication(application?: ApplyApplication | null): StatusForm {
  return {
    status: application?.status ?? "screening",
    note: "",
    review_notes: application?.review_notes ?? "",
    interview_at: "",
    interview_location: "",
    interview_details: "",
  }
}

function scholarshipFormFromApplication(application?: ApplyApplication | null) {
  const scholarship = application?.scholarship_application
  return {
    status: scholarship?.status ?? "under_review",
    socioeconomic_score: scholarship?.socioeconomic_score ?? "",
    communication_score: scholarship?.communication_score ?? "",
    attitude_score: scholarship?.attitude_score ?? "",
    statement_score: scholarship?.statement_score ?? "",
    review_notes: scholarship?.review_notes ?? "",
  }
}

function displayName(applicant?: AdminApplicant | null) {
  if (!applicant) return "Applicant"
  return `${applicant.first_name ?? ""} ${applicant.last_name ?? ""}`.trim() || applicant.username
}

function statusLabel(status: string, configuredOptions: ConfiguredStatusOption[] = []) {
  return configuredOptions.find((option) => option.value === status)?.label
    ?? statusOptions.find(([value]) => value === status)?.[1]
    ?? status
}

function documentLabel(options: ApplyOption[], documentType: string) {
  return options.find((option) => option.value === documentType)?.label ?? documentType
}

function stringifyValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "Not submitted"
  if (Array.isArray(value)) return value.filter(Boolean).join(", ") || "Not submitted"
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

export function AdminManageApplicantDetailPage({ applicantId }: { applicantId: string }) {
  const [detail, setDetail] = useState<AdminApplicantDetail | null>(null)
  const [countries, setCountries] = useState<ApplyOption[]>([])
  const [documentTypes, setDocumentTypes] = useState<ApplyOption[]>([])
  const [configuredStatusOptions, setConfiguredStatusOptions] = useState<ConfiguredStatusOption[]>([])
  const [accountForm, setAccountForm] = useState<AccountForm>(accountFormFromApplicant(null))
  const [statusForm, setStatusForm] = useState<StatusForm>(statusFormFromApplication(null))
  const [documentForms, setDocumentForms] = useState<Record<string, { status: string; notes: string }>>({})
  const [scholarshipForm, setScholarshipForm] = useState(scholarshipFormFromApplication(null))
  const [isLoading, setIsLoading] = useState(true)
  const [isSavingAccount, setIsSavingAccount] = useState(false)
  const [isSavingStatus, setIsSavingStatus] = useState(false)
  const [savingDocumentId, setSavingDocumentId] = useState("")
  const [isSavingScholarship, setIsSavingScholarship] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const application = detail?.applications[0] ?? null
  const applicant = detail?.applicant ?? null
  const identityLabel = identityNumberLabel(accountForm.nationality)

  const questionResponses = useMemo(() => {
    const responses = (application?.personal_information?.question_responses ?? {}) as Record<string, unknown>
    return detail?.admissions_setup.custom_questions.map((question) => ({
      question,
      answer: stringifyValue(responses[question.id]),
    })) ?? []
  }, [application?.personal_information, detail?.admissions_setup.custom_questions])

  useEffect(() => {
    let isMounted = true

    async function loadData() {
      setError("")
      const [nextDetail, options, setup] = await Promise.all([
        loadAdminApplicantDetail(applicantId),
        loadApplyOptions(),
        loadAdminApplicantsSetup(),
      ])
      if (!isMounted) return
      setDetail(nextDetail)
      setCountries(options.countries ?? [])
      setDocumentTypes(setup.document_types ?? options.document_types ?? [])
      setConfiguredStatusOptions(options.status_options ?? [])
      setAccountForm(accountFormFromApplicant(nextDetail.applicant))
      const nextApplication = nextDetail.applications[0] ?? null
      setStatusForm(statusFormFromApplication(nextApplication))
      setScholarshipForm(scholarshipFormFromApplication(nextApplication))
      setDocumentForms(
        Object.fromEntries(
          (nextApplication?.documents ?? []).map((document) => [
            document.id,
            { status: document.status, notes: document.notes ?? "" },
          ])
        )
      )
    }

    void loadData()
      .catch((caught) => {
        if (isMounted) setError(caught instanceof Error ? caught.message : "Unable to load applicant.")
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [applicantId])

  function updateAccount(field: keyof AccountForm, value: string | boolean) {
    setAccountForm((current) => ({ ...current, [field]: value }))
  }

  function updateApplication(nextApplication: ApplyApplication) {
    setDetail((current) =>
      current
        ? {
            ...current,
            applications: current.applications.map((item) =>
              item.id === nextApplication.id ? nextApplication : item
            ),
          }
        : current
    )
    setStatusForm(statusFormFromApplication(nextApplication))
    setScholarshipForm(scholarshipFormFromApplication(nextApplication))
    setDocumentForms(
      Object.fromEntries(
        (nextApplication.documents ?? []).map((document) => [
          document.id,
          { status: document.status, notes: document.notes ?? "" },
        ])
      )
    )
  }

  function updateDocument(nextDocument: ApplyDocument) {
    setDetail((current) =>
      current
        ? {
            ...current,
            applications: current.applications.map((item) =>
              item.id === nextDocument.application
                ? {
                    ...item,
                    documents: item.documents.map((document) =>
                      document.id === nextDocument.id ? nextDocument : document
                    ),
                  }
                : item
            ),
          }
        : current
    )
    setDocumentForms((current) => ({
      ...current,
      [nextDocument.id]: {
        status: nextDocument.status,
        notes: nextDocument.notes ?? "",
      },
    }))
  }

  async function saveAccount(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!applicant) return
    setIsSavingAccount(true)
    setError("")
    setSuccess("")
    try {
      const response = await updateAdminApplicant(applicant.id, {
        username: accountForm.username.trim(),
        email: accountForm.email.trim(),
        first_name: accountForm.first_name.trim(),
        last_name: accountForm.last_name.trim(),
        phone: accountForm.phone.trim(),
        nationality: accountForm.nationality,
        country_of_residence: accountForm.country_of_residence,
        passport_or_identity_no: accountForm.passport_or_identity_no.trim(),
        is_active: accountForm.is_active,
      })
      setDetail((current) => (current ? { ...current, applicant: response.applicant } : current))
      setAccountForm(accountFormFromApplicant(response.applicant))
      setSuccess("Applicant account updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update applicant account.")
    } finally {
      setIsSavingAccount(false)
    }
  }

  async function saveStatus(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!application) return
    setIsSavingStatus(true)
    setError("")
    setSuccess("")
    try {
      const nextApplication = await updateAdminApplicationStatus(application.id, {
        status: statusForm.status,
        note: statusForm.note,
        review_notes: statusForm.review_notes,
        interview_at: statusForm.interview_at ? statusForm.interview_at : null,
        interview_location: statusForm.interview_location,
        interview_details: statusForm.interview_details,
      })
      updateApplication(nextApplication)
      setSuccess("Application status updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update application status.")
    } finally {
      setIsSavingStatus(false)
    }
  }

  async function saveDocument(document: ApplyDocument) {
    const form = documentForms[document.id]
    if (!form) return
    setSavingDocumentId(document.id)
    setError("")
    setSuccess("")
    try {
      const nextDocument = await updateAdminDocumentReview(document.id, form)
      updateDocument(nextDocument)
      setSuccess("Document review updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update document review.")
    } finally {
      setSavingDocumentId("")
    }
  }

  async function saveScholarship(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!application) return
    setIsSavingScholarship(true)
    setError("")
    setSuccess("")
    try {
      const scholarship = await updateAdminScholarshipReview(application.id, {
        status: scholarshipForm.status,
        socioeconomic_score: scholarshipForm.socioeconomic_score || null,
        communication_score: scholarshipForm.communication_score || null,
        attitude_score: scholarshipForm.attitude_score || null,
        statement_score: scholarshipForm.statement_score || null,
        review_notes: scholarshipForm.review_notes,
      })
      setDetail((current) =>
        current
          ? {
              ...current,
              applications: current.applications.map((item) =>
                item.id === application.id ? { ...item, scholarship_application: scholarship } : item
              ),
            }
          : current
      )
      setSuccess("Scholarship review updated successfully.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update scholarship review.")
    } finally {
      setIsSavingScholarship(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/applicants", title: "Applicants" },
          { href: `/admin/manage/applicants/${applicantId}`, title: displayName(applicant) },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {displayName(applicant)}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
              Review application details, uploaded documents, scholarship request, and admission decision.
            </p>
          </div>
          <Button variant="outline" render={<Link href="/admin/manage/applicants" />}>
            <ArrowLeft className="size-4" />
            Applicants
          </Button>
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
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            Loading applicant...
          </div>
        ) : applicant ? (
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_28rem]">
            <div className="space-y-4">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex items-center gap-3">
                      <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                        <UserRound className="size-5" />
                      </span>
                      <div>
                        <CardTitle className="text-lg">{displayName(applicant)}</CardTitle>
                        <CardDescription>{applicant.username} • {applicant.email}</CardDescription>
                      </div>
                    </div>
                    <Badge variant={applicant.is_active ? "secondary" : "destructive"}>
                      {applicant.is_active ? "Active account" : "Disabled account"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="grid gap-4 text-sm md:grid-cols-3">
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Phone</p>
                    <p className="mt-1">{applicant.phone || "Not set"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Nationality</p>
                    <p className="mt-1">{applicant.nationality || "Not set"}</p>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase text-muted-foreground">Residence</p>
                    <p className="mt-1">{applicant.country_of_residence || "Not set"}</p>
                  </div>
                </CardContent>
              </Card>

              {application ? (
                <>
                  <Card className="border-border/70 bg-card/95 shadow-sm">
                    <CardHeader>
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <CardTitle className="text-base">Application Review</CardTitle>
                          <CardDescription>
                            {application.application_number || "Draft application"} • {formatDateTime(application.updated_at)}
                          </CardDescription>
                        </div>
                        <Badge variant="outline">{statusLabel(application.status, configuredStatusOptions)}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-5">
                      <div className="grid gap-4 text-sm md:grid-cols-2">
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Intake</p>
                          <p className="mt-1">{application.intake_detail?.title || "Not selected"}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Mode</p>
                          <p className="mt-1">{application.mode_of_study.replace("_", " ")}</p>
                        </div>
                        <div className="md:col-span-2">
                          <p className="text-xs font-medium uppercase text-muted-foreground">Programme Preferences</p>
                          <p className="mt-1">{stringifyValue(application.programme_preferences)}</p>
                        </div>
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="rounded-lg border border-border p-4">
                          <h3 className="text-sm font-semibold">Personal Details</h3>
                          <dl className="mt-3 grid gap-2 text-sm">
                            {Object.entries(application.personal_information ?? {})
                              .filter(([key]) => key !== "question_responses")
                              .map(([key, value]) => (
                                <div key={key}>
                                  <dt className="text-xs uppercase text-muted-foreground">{key.replaceAll("_", " ")}</dt>
                                  <dd>{stringifyValue(value)}</dd>
                                </div>
                              ))}
                          </dl>
                        </div>
                        <div className="rounded-lg border border-border p-4">
                          <h3 className="text-sm font-semibold">Academic Details</h3>
                          <dl className="mt-3 grid gap-2 text-sm">
                            {Object.entries(application.academic_information ?? {}).map(([key, value]) => (
                              <div key={key}>
                                <dt className="text-xs uppercase text-muted-foreground">{key.replaceAll("_", " ")}</dt>
                                <dd>{stringifyValue(value)}</dd>
                              </div>
                            ))}
                          </dl>
                        </div>
                      </div>

                      {questionResponses.length ? (
                        <div className="rounded-lg border border-border p-4">
                          <h3 className="text-sm font-semibold">Applicant Questions</h3>
                          <dl className="mt-3 grid gap-3 text-sm">
                            {questionResponses.map(({ question, answer }) => (
                              <div key={question.id}>
                                <dt className="text-xs uppercase text-muted-foreground">{question.label}</dt>
                                <dd className="mt-1 whitespace-pre-wrap">{answer}</dd>
                              </div>
                            ))}
                          </dl>
                        </div>
                      ) : null}
                    </CardContent>
                  </Card>

                  <Card className="border-border/70 bg-card/95 shadow-sm">
                    <CardHeader>
                      <CardTitle className="text-base">Uploaded Documents</CardTitle>
                      <CardDescription>Open files and record document review decisions.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {application.documents.length ? (
                        application.documents.map((document) => {
                          const form = documentForms[document.id] ?? {
                            status: document.status,
                            notes: document.notes ?? "",
                          }
                          return (
                            <div key={document.id} className="rounded-lg border border-border p-4">
                              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <FileText className="size-4 text-muted-foreground" />
                                    <p className="font-medium">{document.original_name || documentLabel(documentTypes, document.document_type)}</p>
                                  </div>
                                  <p className="mt-1 text-xs text-muted-foreground">
                                    {documentLabel(documentTypes, document.document_type)} • Uploaded {formatDateTime(document.uploaded_at)}
                                  </p>
                                  {document.file_url ? (
                                    <Button className="mt-3" size="sm" variant="outline" render={<Link href={document.file_url} target="_blank" />}>
                                      Open file
                                    </Button>
                                  ) : null}
                                </div>
                                <Badge variant={form.status === "accepted" ? "secondary" : form.status === "rejected" ? "destructive" : "outline"}>
                                  {form.status}
                                </Badge>
                              </div>
                              <div className="mt-4 grid gap-3 md:grid-cols-[12rem_minmax(0,1fr)_auto] md:items-end">
                                <div className="space-y-2">
                                  <Label htmlFor={`document_status_${document.id}`}>Status</Label>
                                  <select
                                    id={`document_status_${document.id}`}
                                    className={selectClass}
                                    value={form.status}
                                    onChange={(event) =>
                                      setDocumentForms((current) => ({
                                        ...current,
                                        [document.id]: { ...form, status: event.target.value },
                                      }))
                                    }
                                  >
                                    {documentStatusOptions.map(([value, label]) => (
                                      <option key={value} value={value}>{label}</option>
                                    ))}
                                  </select>
                                </div>
                                <div className="space-y-2">
                                  <Label htmlFor={`document_notes_${document.id}`}>Notes</Label>
                                  <Input
                                    id={`document_notes_${document.id}`}
                                    value={form.notes}
                                    onChange={(event) =>
                                      setDocumentForms((current) => ({
                                        ...current,
                                        [document.id]: { ...form, notes: event.target.value },
                                      }))
                                    }
                                  />
                                </div>
                                <Button
                                  type="button"
                                  onClick={() => saveDocument(document)}
                                  disabled={savingDocumentId === document.id}
                                >
                                  <Save className="size-4" />
                                  {savingDocumentId === document.id ? "Saving..." : "Save"}
                                </Button>
                              </div>
                            </div>
                          )
                        })
                      ) : (
                        <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
                      )}
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardContent className="p-5 text-sm text-muted-foreground">
                    This applicant has not started an admission application yet.
                  </CardContent>
                </Card>
              )}
            </div>

            <div className="space-y-4">
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base">Account Details</CardTitle>
                  <CardDescription>Edit profile and login status.</CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="grid gap-4" onSubmit={saveAccount}>
                    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
                      <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input id="username" value={accountForm.username} onChange={(event) => updateAccount("username", event.target.value)} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" value={accountForm.email} onChange={(event) => updateAccount("email", event.target.value)} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="first_name">First name</Label>
                        <Input id="first_name" value={accountForm.first_name} onChange={(event) => updateAccount("first_name", event.target.value)} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="last_name">Last name</Label>
                        <Input id="last_name" value={accountForm.last_name} onChange={(event) => updateAccount("last_name", event.target.value)} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone</Label>
                        <Input id="phone" value={accountForm.phone} onChange={(event) => updateAccount("phone", event.target.value)} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="nationality">Nationality</Label>
                        <select
                          id="nationality"
                          className={selectClass}
                          value={accountForm.nationality}
                          onChange={(event) => {
                            updateAccount("nationality", event.target.value)
                            updateAccount("passport_or_identity_no", "")
                          }}
                          required
                        >
                          <option value="">Select nationality</option>
                          {countries.map((country) => (
                            <option key={country.value} value={country.value}>{country.label}</option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="country_of_residence">Country of residence</Label>
                        <select
                          id="country_of_residence"
                          className={selectClass}
                          value={accountForm.country_of_residence}
                          onChange={(event) => updateAccount("country_of_residence", event.target.value)}
                          required
                        >
                          <option value="">Select country</option>
                          {countries.map((country) => (
                            <option key={country.value} value={country.value}>{country.label}</option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="passport_or_identity_no">{identityLabel}</Label>
                        <Input
                          id="passport_or_identity_no"
                          value={accountForm.passport_or_identity_no}
                          onChange={(event) => updateAccount("passport_or_identity_no", event.target.value)}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="account_status">Account status</Label>
                        <select
                          id="account_status"
                          className={selectClass}
                          value={accountForm.is_active ? "active" : "disabled"}
                          onChange={(event) => updateAccount("is_active", event.target.value === "active")}
                        >
                          <option value="active">Active</option>
                          <option value="disabled">Disabled</option>
                        </select>
                      </div>
                    </div>
                    <Button type="submit" disabled={isSavingAccount}>
                      <Save className="size-4" />
                      {isSavingAccount ? "Saving..." : "Save account"}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {application ? (
                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <span className="rounded-lg border border-border bg-muted/50 p-2 text-muted-foreground">
                        <CalendarClock className="size-5" />
                      </span>
                      <div>
                        <CardTitle className="text-base">Decision and Status</CardTitle>
                        <CardDescription>Accept, call for interview, reject, or request information.</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <form className="grid gap-4" onSubmit={saveStatus}>
                      <div className="space-y-2">
                        <Label htmlFor="application_status">Application status</Label>
                        <select
                          id="application_status"
                          className={selectClass}
                          value={statusForm.status}
                          onChange={(event) => setStatusForm((current) => ({ ...current, status: event.target.value }))}
                        >
                          {(configuredStatusOptions.length
                            ? configuredStatusOptions.filter((option) => option.enabled)
                            : statusOptions.map(([value, label]) => ({ value, label, enabled: true }))).map((option) => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                          ))}
                        </select>
                      </div>
                      {statusForm.status === "interview" ? (
                        <div className="grid gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="interview_at">Interview schedule</Label>
                            <Input
                              id="interview_at"
                              type="datetime-local"
                              value={statusForm.interview_at}
                              onChange={(event) => setStatusForm((current) => ({ ...current, interview_at: event.target.value }))}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="interview_location">Interview location or meeting link</Label>
                            <Input
                              id="interview_location"
                              value={statusForm.interview_location}
                              onChange={(event) => setStatusForm((current) => ({ ...current, interview_location: event.target.value }))}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="interview_details">Interview details</Label>
                            <Textarea
                              id="interview_details"
                              value={statusForm.interview_details}
                              onChange={(event) => setStatusForm((current) => ({ ...current, interview_details: event.target.value }))}
                            />
                          </div>
                        </div>
                      ) : null}
                      <div className="space-y-2">
                        <Label htmlFor="status_note">Status note</Label>
                        <Textarea
                          id="status_note"
                          value={statusForm.note}
                          onChange={(event) => setStatusForm((current) => ({ ...current, note: event.target.value }))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="review_notes">Internal review notes</Label>
                        <Textarea
                          id="review_notes"
                          value={statusForm.review_notes}
                          onChange={(event) => setStatusForm((current) => ({ ...current, review_notes: event.target.value }))}
                        />
                      </div>
                      <Button type="submit" disabled={isSavingStatus}>
                        <Save className="size-4" />
                        {isSavingStatus ? "Saving..." : "Update status"}
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              ) : null}

              {application?.scholarship_requested ? (
                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-base">Scholarship Review</CardTitle>
                    <CardDescription>Score and update scholarship decision.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form className="grid gap-4" onSubmit={saveScholarship}>
                      <div className="space-y-2">
                        <Label htmlFor="scholarship_status">Scholarship status</Label>
                        <select
                          id="scholarship_status"
                          className={selectClass}
                          value={scholarshipForm.status}
                          onChange={(event) => setScholarshipForm((current) => ({ ...current, status: event.target.value }))}
                        >
                          {scholarshipStatusOptions.map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                        {[
                          ["socioeconomic_score", "Socioeconomic score"],
                          ["communication_score", "Communication score"],
                          ["attitude_score", "Attitude score"],
                          ["statement_score", "Statement score"],
                        ].map(([field, label]) => (
                          <div key={field} className="space-y-2">
                            <Label htmlFor={field}>{label}</Label>
                            <Input
                              id={field}
                              value={scholarshipForm[field as keyof typeof scholarshipForm]}
                              onChange={(event) =>
                                setScholarshipForm((current) => ({
                                  ...current,
                                  [field]: event.target.value,
                                }))
                              }
                            />
                          </div>
                        ))}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="scholarship_notes">Review notes</Label>
                        <Textarea
                          id="scholarship_notes"
                          value={scholarshipForm.review_notes}
                          onChange={(event) => setScholarshipForm((current) => ({ ...current, review_notes: event.target.value }))}
                        />
                      </div>
                      <Button type="submit" disabled={isSavingScholarship}>
                        <Save className="size-4" />
                        {isSavingScholarship ? "Saving..." : "Save scholarship"}
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              ) : null}
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-background p-5 text-sm text-muted-foreground">
            Applicant not found.
          </div>
        )}
      </main>
    </div>
  )
}
