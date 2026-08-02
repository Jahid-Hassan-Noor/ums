"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Save, Send } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { identityNumberLabel } from "@/lib/countries"
import {
  createApplyApplication,
  loadApplyApplications,
  loadApplyOptions,
  loadApplyProfile,
  submitApplyApplication,
  updateApplyApplication,
  type ApplyApplication,
  type ApplyApplicant,
  type ApplyOptions,
} from "@/lib/apply"

type FormState = {
  id?: string
  intake: string
  application_type: string
  mode_of_study: string
  programme_preferences: string[]
  personal_information: {
    first_name: string
    last_name: string
    email: string
    phone: string
    identity_number: string
    country: string
    nationality: string
    question_responses: Record<string, string>
  }
  academic_information: {
    highest_qualification: string
    institution_name: string
    graduation_year: string
    cgpa: string
    english_proficiency: string
  }
  scholarship_requested: boolean
  scholarship_information: {
    household_income: string
    dependents_count: string
    personal_statement: string
    financial_need_notes: string
  }
  statement_accepted: boolean
}

type PersonalTextField = Exclude<
  keyof FormState["personal_information"],
  "question_responses"
>

const emptyForm: FormState = {
  intake: "",
  application_type: "undergraduate_october",
  mode_of_study: "full_time",
  programme_preferences: ["", "", "", ""],
  personal_information: {
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    identity_number: "",
    country: "",
    nationality: "",
    question_responses: {},
  },
  academic_information: {
    highest_qualification: "",
    institution_name: "",
    graduation_year: "",
    cgpa: "",
    english_proficiency: "",
  },
  scholarship_requested: false,
  scholarship_information: {
    household_income: "",
    dependents_count: "",
    personal_statement: "",
    financial_need_notes: "",
  },
  statement_accepted: false,
}

const inputClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

const personalFields: { field: PersonalTextField; label: string }[] = [
  { field: "first_name", label: "First name" },
  { field: "last_name", label: "Last name" },
  { field: "email", label: "Email address" },
  { field: "phone", label: "Contact number" },
]

function stateFromApplication(application?: ApplyApplication): FormState {
  if (!application) return emptyForm
  return {
    ...emptyForm,
    id: application.id,
    intake: application.intake ? String(application.intake) : "",
    application_type: application.application_type,
    mode_of_study: application.mode_of_study,
    programme_preferences: [
      ...(application.programme_preferences ?? []),
      "",
      "",
      "",
      "",
    ].slice(0, 4),
    personal_information: {
      ...emptyForm.personal_information,
      ...(application.personal_information as Partial<FormState["personal_information"]>),
      question_responses: {
        ...emptyForm.personal_information.question_responses,
        ...((application.personal_information?.question_responses ?? {}) as Record<string, string>),
      },
    },
    academic_information: {
      ...emptyForm.academic_information,
      ...(application.academic_information as Partial<FormState["academic_information"]>),
    },
    scholarship_requested: application.scholarship_requested,
    scholarship_information: {
      ...emptyForm.scholarship_information,
      ...(application.scholarship_information as Partial<FormState["scholarship_information"]>),
    },
    statement_accepted: application.statement_accepted,
  }
}

function stateFromApplicant(applicant: ApplyApplicant): FormState {
  return {
    ...emptyForm,
    personal_information: {
      first_name: applicant.first_name || "",
      last_name: applicant.last_name || "",
      email: applicant.email || "",
      phone: applicant.phone || "",
      identity_number: applicant.passport_or_identity_no || "",
      country: applicant.country_of_residence || "",
      nationality: applicant.nationality || "",
      question_responses: {},
    },
  }
}

export function ApplyApplicationForm() {
  const [options, setOptions] = useState<ApplyOptions | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm)
  const [message, setMessage] = useState("")
  const [errors, setErrors] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function load() {
      try {
        const [nextOptions, applications, applicant] = await Promise.all([
          loadApplyOptions(),
          loadApplyApplications(),
          loadApplyProfile().catch(() => null),
        ])
        if (!isMounted) return
        setOptions(nextOptions)
        setForm(applications[0] ? stateFromApplication(applications[0]) : applicant ? stateFromApplicant(applicant) : emptyForm)
      } catch (caught) {
        if (isMounted) setErrors([caught instanceof Error ? caught.message : "Unable to load application form"])
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void load()
    return () => {
      isMounted = false
    }
  }, [])

  const activeApplicationId = form.id
  const identityLabel = identityNumberLabel(form.personal_information.nationality)

  const programmeOptions = useMemo(
    () =>
      options?.programmes.filter(
        (programme) =>
          programme.level === form.application_type ||
          (form.application_type.startsWith("undergraduate") &&
            programme.level === "undergraduate")
      ) ?? [],
    [form.application_type, options?.programmes]
  )

  function updatePersonal(field: PersonalTextField, value: string) {
    setForm((current) => ({
      ...current,
      personal_information: { ...current.personal_information, [field]: value },
    }))
  }

  function updateAcademic(field: keyof FormState["academic_information"], value: string) {
    setForm((current) => ({
      ...current,
      academic_information: { ...current.academic_information, [field]: value },
    }))
  }

  function updateQuestionResponse(questionId: string, value: string) {
    setForm((current) => ({
      ...current,
      personal_information: {
        ...current.personal_information,
        question_responses: {
          ...current.personal_information.question_responses,
          [questionId]: value,
        },
      },
    }))
  }

  function updateScholarship(field: keyof FormState["scholarship_information"], value: string) {
    setForm((current) => ({
      ...current,
      scholarship_information: { ...current.scholarship_information, [field]: value },
    }))
  }

  function updateProgrammePreference(index: number, value: string) {
    setForm((current) => {
      const next = [...current.programme_preferences]
      next[index] = value
      return { ...current, programme_preferences: next }
    })
  }

  function payloadFromForm() {
    return {
      intake: form.intake ? Number(form.intake) : null,
      application_type: form.application_type,
      mode_of_study: form.mode_of_study,
      programme_preferences: form.programme_preferences.filter(Boolean),
      personal_information: form.personal_information,
      academic_information: form.academic_information,
      scholarship_requested: options?.admissions_setup.scholarship_enabled
        ? form.scholarship_requested
        : false,
      scholarship_information: options?.admissions_setup.scholarship_enabled
        ? form.scholarship_information
        : {},
      statement_accepted: form.statement_accepted,
    }
  }

  async function saveDraft() {
    setMessage("")
    setErrors([])
    setIsSaving(true)
    try {
      const payload = payloadFromForm()
      const application = activeApplicationId
        ? await updateApplyApplication(activeApplicationId, payload)
        : await createApplyApplication(payload)
      setForm(stateFromApplication(application))
      setMessage("Application draft saved.")
      return application
    } catch (caught) {
      setErrors([caught instanceof Error ? caught.message : "Unable to save application"])
      return null
    } finally {
      setIsSaving(false)
    }
  }

  async function submitApplication() {
    const application = await saveDraft()
    if (!application) return
    setIsSaving(true)
    setMessage("")
    setErrors([])
    try {
      const submitted = await submitApplyApplication(application.id)
      setForm(stateFromApplication(submitted))
      setMessage("Application submitted.")
    } catch (caught) {
      const error = caught as Error & { missing?: string[] }
      setErrors([error.message || "Unable to submit application"])
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/apply", title: "Apply" },
          { href: "/apply/application", title: "Application Form" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold text-teal-700 dark:text-teal-300">Six Section Form</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              Admission Application
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Save each section as a draft, then submit after documents and statement are ready.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button variant="outline" onClick={saveDraft} disabled={isSaving || isLoading}>
              <Save className="size-4" />
              Save Draft
            </Button>
            <Button onClick={submitApplication} disabled={isSaving || isLoading}>
              <Send className="size-4" />
              Submit
            </Button>
          </div>
        </section>

        {message ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700">
            {message}
          </div>
        ) : null}
        {errors.length ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
            {errors.map((error) => (
              <p key={error}>{error}</p>
            ))}
          </div>
        ) : null}

        <div className="grid gap-5">
          <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Programme Selection</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="application_type">Application type</Label>
                <select
                  id="application_type"
                  className={inputClass}
                  value={form.application_type}
                  onChange={(event) => setForm((current) => ({ ...current, application_type: event.target.value }))}
                >
                  {(options?.application_types ?? []).map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="intake">Intake</Label>
                <select
                  id="intake"
                  className={inputClass}
                  value={form.intake}
                  onChange={(event) => setForm((current) => ({ ...current, intake: event.target.value }))}
                >
                  <option value="">Select intake</option>
                  {(options?.intakes ?? []).map((intake) => (
                    <option key={intake.id} value={intake.id}>{intake.title}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="mode_of_study">Mode of study</Label>
                <select
                  id="mode_of_study"
                  className={inputClass}
                  value={form.mode_of_study}
                  onChange={(event) => setForm((current) => ({ ...current, mode_of_study: event.target.value }))}
                >
                  <option value="full_time">Full-Time</option>
                  <option value="part_time">Part-Time</option>
                </select>
              </div>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {form.programme_preferences.map((value, index) => (
                <div key={index} className="space-y-2">
                  <Label htmlFor={`preference_${index}`}>Preference {index + 1}</Label>
                  <select
                    id={`preference_${index}`}
                    className={inputClass}
                    value={value}
                    onChange={(event) => updateProgrammePreference(index, event.target.value)}
                  >
                    <option value="">Select programme</option>
                    {programmeOptions.map((programme) => (
                      <option key={programme.id} value={programme.name}>{programme.name}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Personal Information</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {personalFields.map(({ field, label }) => (
                <div key={field} className="space-y-2">
                  <Label htmlFor={field}>{label}</Label>
                  <Input
                    id={field}
                    type={field === "email" ? "email" : "text"}
                    value={form.personal_information[field]}
                    onChange={(event) => updatePersonal(field, event.target.value)}
                  />
                </div>
              ))}
              <div className="space-y-2">
                <Label htmlFor="nationality">Nationality</Label>
                <select
                  id="nationality"
                  className={inputClass}
                  value={form.personal_information.nationality}
                  onChange={(event) => {
                    updatePersonal("nationality", event.target.value)
                    updatePersonal("identity_number", "")
                  }}
                >
                  <option value="">Select nationality</option>
                  {(options?.countries ?? []).map((country) => (
                    <option key={country.value} value={country.value}>
                      {country.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">Country of residence</Label>
                <select
                  id="country"
                  className={inputClass}
                  value={form.personal_information.country}
                  onChange={(event) => updatePersonal("country", event.target.value)}
                >
                  <option value="">Select country</option>
                  {(options?.countries ?? []).map((country) => (
                    <option key={country.value} value={country.value}>
                      {country.label}
                    </option>
                  ))}
                </select>
              </div>
              {form.personal_information.nationality ? (
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="identity_number">{identityLabel}</Label>
                  <Input
                    id="identity_number"
                    value={form.personal_information.identity_number}
                    onChange={(event) => updatePersonal("identity_number", event.target.value)}
                  />
                </div>
              ) : null}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Academic Information</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {[
                ["highest_qualification", "Highest qualification"],
                ["institution_name", "Previous institution"],
                ["graduation_year", "Graduation year"],
                ["cgpa", "CGPA or equivalent"],
                ["english_proficiency", "English proficiency"],
              ].map(([field, label]) => (
                <div key={field} className="space-y-2">
                  <Label htmlFor={field}>{label}</Label>
                  <Input
                    id={field}
                    value={form.academic_information[field as keyof FormState["academic_information"]]}
                    onChange={(event) =>
                      updateAcademic(field as keyof FormState["academic_information"], event.target.value)
                    }
                  />
                </div>
              ))}
            </div>
          </section>

          {(options?.admissions_setup.custom_questions ?? []).length ? (
            <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
              <h2 className="text-lg font-semibold">Additional Questions</h2>
              <div className="mt-4 grid gap-4">
                {(options?.admissions_setup.custom_questions ?? []).map((question) => (
                  <div key={question.id} className="space-y-2">
                    <Label htmlFor={`question_${question.id}`}>
                      {question.label}
                      {question.required ? <span className="text-destructive"> *</span> : null}
                    </Label>
                    {question.help_text ? (
                      <p className="text-xs text-muted-foreground">{question.help_text}</p>
                    ) : null}
                    <Textarea
                      id={`question_${question.id}`}
                      value={form.personal_information.question_responses[question.id] ?? ""}
                      onChange={(event) => updateQuestionResponse(question.id, event.target.value)}
                    />
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {options?.admissions_setup.scholarship_enabled ? (
            <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
              <div className="flex items-start gap-3">
                <input
                  id="scholarship_requested"
                  type="checkbox"
                  className="mt-1 size-4"
                  checked={form.scholarship_requested}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, scholarship_requested: event.target.checked }))
                  }
                />
                <div>
                  <Label htmlFor="scholarship_requested">Apply for scholarship review</Label>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Scholarship details are reviewed with the admission application.
                  </p>
                </div>
              </div>
              {form.scholarship_requested ? (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="household_income">Household income</Label>
                    <Input
                      id="household_income"
                      value={form.scholarship_information.household_income}
                      onChange={(event) => updateScholarship("household_income", event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dependents_count">Dependents</Label>
                    <Input
                      id="dependents_count"
                      value={form.scholarship_information.dependents_count}
                      onChange={(event) => updateScholarship("dependents_count", event.target.value)}
                    />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="personal_statement">Personal statement</Label>
                    <Textarea
                      id="personal_statement"
                      value={form.scholarship_information.personal_statement}
                      onChange={(event) => updateScholarship("personal_statement", event.target.value)}
                    />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="financial_need_notes">Financial need notes</Label>
                    <Textarea
                      id="financial_need_notes"
                      value={form.scholarship_information.financial_need_notes}
                      onChange={(event) => updateScholarship("financial_need_notes", event.target.value)}
                    />
                  </div>
                </div>
              ) : null}
            </section>
          ) : null}

          <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Documents Upload</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Upload supporting files after saving the draft application.
            </p>
            <Button className="mt-4" variant="outline" render={<Link href="/apply/documents" />}>
              Go to Documents
            </Button>
          </section>

          <section className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <input
                id="statement_accepted"
                type="checkbox"
                className="mt-1 size-4"
                checked={form.statement_accepted}
                onChange={(event) =>
                  setForm((current) => ({ ...current, statement_accepted: event.target.checked }))
                }
              />
              <div>
                <Label htmlFor="statement_accepted">Statement of truth</Label>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">
                  I confirm that the information provided is true and complete.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
