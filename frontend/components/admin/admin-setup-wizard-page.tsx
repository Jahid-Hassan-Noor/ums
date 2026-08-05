"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  Loader2,
  RotateCcw,
  Save,
  WandSparkles,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  loadAdminSettings,
  loadSetupWizard,
  saveAdminSettings,
  type SettingField,
  type SettingsSection,
  type SettingValue,
  type SetupWizardResponse,
  type SetupWizardStep,
} from "@/lib/admin-settings"
import { cn } from "@/lib/utils"

type ValuesBySection = Record<string, Record<string, SettingValue>>

type FieldGroupState = {
  section: SettingsSection
  fields: SettingField[]
}

const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"

function cloneSectionValues(sections: SettingsSection[]): ValuesBySection {
  return Object.fromEntries(
    sections.map((section) => [section.key, { ...section.values }])
  )
}

function requestedStepFromLocation() {
  if (typeof window === "undefined") return ""
  return new URLSearchParams(window.location.search).get("step") ?? ""
}

function stepStatusLabel(step: SetupWizardStep) {
  if (step.total === 0) return "Optional"
  return step.complete ? "Complete" : `${step.completed}/${step.total}`
}

function WizardField({
  field,
  value,
  onChange,
}: {
  field: SettingField
  value: SettingValue
  onChange: (value: SettingValue) => void
}) {
  if (field.type === "boolean") {
    return (
      <Field orientation="horizontal">
        <input
          id={`setup-field-${field.key}`}
          className="mt-1 size-4 accent-primary"
          type="checkbox"
          checked={Boolean(value)}
          onChange={(event) => onChange(event.target.checked)}
        />
        <div className="flex flex-col gap-1">
          <FieldLabel htmlFor={`setup-field-${field.key}`}>
            {field.label}
          </FieldLabel>
          {field.help_text ? (
            <FieldDescription>{field.help_text}</FieldDescription>
          ) : null}
        </div>
      </Field>
    )
  }

  return (
    <Field>
      <div className="flex flex-wrap items-center gap-2">
        <FieldLabel htmlFor={`setup-field-${field.key}`}>
          {field.label}
        </FieldLabel>
        {field.high_impact ? (
          <Badge variant="outline">High impact</Badge>
        ) : null}
      </div>
      {field.type === "select" ? (
        <select
          id={`setup-field-${field.key}`}
          className={selectClass}
          value={String(value)}
          onChange={(event) => onChange(event.target.value)}
        >
          {field.choices?.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      ) : field.type === "textarea" ? (
        <Textarea
          id={`setup-field-${field.key}`}
          value={String(value ?? "")}
          maxLength={field.max_length}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <Input
          id={`setup-field-${field.key}`}
          type={field.type === "image" ? "text" : field.type}
          value={value as string | number}
          min={field.min}
          max={field.max}
          maxLength={field.max_length}
          onChange={(event) =>
            onChange(
              field.type === "number"
                ? Number(event.target.value)
                : event.target.value
            )
          }
        />
      )}
      {field.help_text ? (
        <FieldDescription>{field.help_text}</FieldDescription>
      ) : null}
    </Field>
  )
}

export function AdminSetupWizardPage() {
  const [wizard, setWizard] = useState<SetupWizardResponse | null>(null)
  const [sections, setSections] = useState<SettingsSection[]>([])
  const [drafts, setDrafts] = useState<ValuesBySection>({})
  const [activeKey, setActiveKey] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [wizardResponse, settingsResponse] = await Promise.all([
        loadSetupWizard(),
        loadAdminSettings(),
      ])
      setWizard(wizardResponse)
      setSections(settingsResponse.sections)
      setDrafts(cloneSectionValues(settingsResponse.sections))
      setActiveKey((current) => {
        const requestedStep = requestedStepFromLocation()
        if (requestedStep && wizardResponse.steps.some((step) => step.key === requestedStep)) {
          return requestedStep
        }
        if (wizardResponse.steps.some((step) => step.key === current)) {
          return current
        }
        return wizardResponse.steps[0]?.key ?? ""
      })
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load setup wizard."
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const activeStep = wizard?.steps.find((step) => step.key === activeKey) ?? null
  const sectionsByKey = useMemo(
    () => Object.fromEntries(sections.map((section) => [section.key, section])),
    [sections]
  )

  const editableGroups = useMemo<FieldGroupState[]>(() => {
    if (!activeStep) return []
    return activeStep.settings_sections
      .map((target) => {
        const section = sectionsByKey[target.section]
        if (!section) return null
        const wanted = new Set(target.fields)
        const fields = section.fields.filter((field) => wanted.has(field.key))
        return fields.length ? { section, fields } : null
      })
      .filter((group): group is FieldGroupState => Boolean(group))
  }, [activeStep, sectionsByKey])

  const changedBySection = useMemo(() => {
    const changed: Record<string, Record<string, SettingValue>> = {}
    for (const group of editableGroups) {
      const draft = drafts[group.section.key] ?? {}
      for (const field of group.fields) {
        if (draft[field.key] !== group.section.values[field.key]) {
          changed[group.section.key] = {
            ...(changed[group.section.key] ?? {}),
            [field.key]: draft[field.key],
          }
        }
      }
    }
    return changed
  }, [drafts, editableGroups])

  const changedCount = Object.values(changedBySection).reduce(
    (count, values) => count + Object.keys(values).length,
    0
  )

  function updateDraft(sectionKey: string, fieldKey: string, value: SettingValue) {
    setDrafts((current) => ({
      ...current,
      [sectionKey]: {
        ...(current[sectionKey] ?? {}),
        [fieldKey]: value,
      },
    }))
    setSuccess("")
  }

  async function saveStepSettings() {
    if (!activeStep || changedCount === 0) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      for (const [section, values] of Object.entries(changedBySection)) {
        await saveAdminSettings(
          section,
          values,
          `Updated from setup wizard: ${activeStep.title}`
        )
      }
      setSuccess(`${activeStep.title} updated successfully.`)
      await load()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to save setup wizard changes."
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/setup-wizard", title: "Setup Wizard" },
        ]}
      />
      <main className="flex flex-1 flex-col gap-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-4 border-b border-border/70 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex max-w-3xl flex-col gap-2">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <WandSparkles className="size-4" />
              Phase 18
            </div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Universal Setup Wizard
            </h1>
            <p className="text-sm leading-6 text-muted-foreground">
              Complete the institution profile, operating defaults, academic
              structure, module ownership, admissions, and public website from
              one guided admin flow.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" render={<Link href="/admin/settings" />}>
              <ExternalLink data-icon="inline-start" />
              Settings
            </Button>
            <Button
              variant="outline"
              onClick={() => void load()}
              disabled={loading || saving}
            >
              <RotateCcw data-icon="inline-start" />
              Refresh
            </Button>
          </div>
        </section>

        {error ? (
          <div className="flex gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}
        {success ? (
          <div className="flex gap-2 rounded-lg border border-border bg-card p-3 text-sm text-foreground">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
            <p>{success}</p>
          </div>
        ) : null}

        {loading || !wizard ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <section className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-border bg-card p-4">
                <p className="text-sm text-muted-foreground">Steps complete</p>
                <p className="mt-1 text-2xl font-semibold">
                  {wizard.summary.completed_steps}/{wizard.summary.total_steps}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-card p-4">
                <p className="text-sm text-muted-foreground">Required items</p>
                <p className="mt-1 text-2xl font-semibold">
                  {wizard.summary.completed_required_items}/
                  {wizard.summary.total_required_items}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-card p-4">
                <p className="text-sm text-muted-foreground">Setup status</p>
                <p className="mt-1 text-2xl font-semibold">
                  {wizard.summary.complete ? "Ready" : "Needs work"}
                </p>
              </div>
            </section>

            {wizard.messages.length ? (
              <section className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4">
                <div className="flex flex-col gap-1">
                  <h2 className="text-base font-semibold">
                    Actionable setup messages
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    The first missing required items are listed here. Complete
                    them to move the institution toward launch readiness.
                  </p>
                </div>
                <div className="grid gap-2 md:grid-cols-2">
                  {wizard.messages.slice(0, 6).map((message) => (
                    <Link
                      key={message.key}
                      href={message.href || `/admin/setup-wizard?step=${message.step}`}
                      className="flex items-start justify-between gap-3 rounded-lg border border-border bg-background p-3 text-sm transition-colors hover:bg-muted/50"
                    >
                      <span className="flex flex-col gap-1">
                        <span className="font-medium">{message.label}</span>
                        <span className="text-muted-foreground">
                          {message.message}
                        </span>
                      </span>
                      <ArrowRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    </Link>
                  ))}
                </div>
              </section>
            ) : null}

            <section className="grid gap-5 xl:grid-cols-[20rem_minmax(0,1fr)]">
              <aside className="flex flex-col gap-2">
                {wizard.steps.map((step) => (
                  <button
                    key={step.key}
                    type="button"
                    onClick={() => {
                      setActiveKey(step.key)
                      setError("")
                      setSuccess("")
                    }}
                    className={cn(
                      "flex w-full items-start justify-between gap-3 rounded-lg border p-3 text-left transition-colors",
                      activeKey === step.key
                        ? "border-primary/50 bg-primary/5"
                        : "border-border bg-card hover:bg-muted/50"
                    )}
                  >
                    <span className="flex min-w-0 flex-col gap-1">
                      <span className="font-medium">{step.title}</span>
                      <span className="line-clamp-2 text-xs leading-5 text-muted-foreground">
                        {step.description}
                      </span>
                    </span>
                    <Badge variant={step.complete ? "secondary" : "outline"}>
                      {stepStatusLabel(step)}
                    </Badge>
                  </button>
                ))}
              </aside>

              {activeStep ? (
                <Card className="border-border/70 bg-card/95 shadow-sm">
                  <CardHeader>
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="flex flex-col gap-2">
                        <CardTitle>{activeStep.title}</CardTitle>
                        <CardDescription>
                          {activeStep.description}
                        </CardDescription>
                      </div>
                      <Badge variant={activeStep.complete ? "secondary" : "outline"}>
                        {activeStep.complete ? "Complete" : "Needs setup"}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-6">
                    <div className="flex flex-col gap-2">
                      <div className="h-2 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{
                            width:
                              activeStep.total > 0
                                ? `${Math.round((activeStep.completed / activeStep.total) * 100)}%`
                                : "100%",
                          }}
                        />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {activeStep.total
                          ? `${activeStep.completed} of ${activeStep.total} required items complete.`
                          : "This step is informational because the related module is disabled."}
                      </p>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2">
                      {activeStep.items.map((item) => (
                        <div
                          key={item.key}
                          className="flex items-start gap-3 rounded-lg border border-border bg-background p-3"
                        >
                          <span
                            className={cn(
                              "mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border",
                              item.complete
                                ? "border-primary bg-primary text-primary-foreground"
                                : "border-border bg-muted text-muted-foreground"
                            )}
                          >
                            {item.complete ? (
                              <CheckCircle2 className="size-3.5" />
                            ) : (
                              <span className="size-1.5 rounded-full bg-current" />
                            )}
                          </span>
                          <span className="flex min-w-0 flex-1 flex-col gap-1">
                            <span className="flex flex-wrap items-center gap-2">
                              <span className="font-medium">{item.label}</span>
                              {!item.required ? (
                                <Badge variant="outline">Optional</Badge>
                              ) : null}
                            </span>
                            {item.detail ? (
                              <span className="break-words text-sm text-muted-foreground">
                                {item.detail}
                              </span>
                            ) : null}
                            {!item.complete && item.message ? (
                              <span className="text-sm text-muted-foreground">
                                {item.message}
                              </span>
                            ) : null}
                          </span>
                        </div>
                      ))}
                    </div>

                    {editableGroups.length ? (
                      <div className="flex flex-col gap-5 border-t border-border pt-5">
                        {editableGroups.map((group) => (
                          <FieldGroup key={group.section.key}>
                            <div className="flex flex-col gap-1">
                              <h3 className="font-semibold">
                                {group.section.title}
                              </h3>
                              <p className="text-sm text-muted-foreground">
                                {group.section.description}
                              </p>
                            </div>
                            <div className="grid gap-4 lg:grid-cols-2">
                              {group.fields.map((field) => (
                                <WizardField
                                  key={`${group.section.key}.${field.key}`}
                                  field={field}
                                  value={
                                    drafts[group.section.key]?.[field.key] ??
                                    field.default
                                  }
                                  onChange={(value) =>
                                    updateDraft(
                                      group.section.key,
                                      field.key,
                                      value
                                    )
                                  }
                                />
                              ))}
                            </div>
                          </FieldGroup>
                        ))}
                        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5">
                          <p className="text-sm text-muted-foreground">
                            {changedCount
                              ? `${changedCount} unsaved setup setting(s)`
                              : "No unsaved setup changes"}
                          </p>
                          <Button
                            onClick={() => void saveStepSettings()}
                            disabled={saving || changedCount === 0}
                          >
                            {saving ? (
                              <Loader2
                                data-icon="inline-start"
                                className="animate-spin"
                              />
                            ) : (
                              <Save data-icon="inline-start" />
                            )}
                            Save step
                          </Button>
                        </div>
                      </div>
                    ) : null}

                    {activeStep.actions.length ? (
                      <div className="flex flex-wrap gap-2 border-t border-border pt-5">
                        {activeStep.actions.map((action) => (
                          <Button
                            key={`${activeStep.key}.${action.href}`}
                            variant="outline"
                            render={<Link href={action.href} />}
                          >
                            <ExternalLink data-icon="inline-start" />
                            {action.label}
                          </Button>
                        ))}
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              ) : null}
            </section>
          </>
        )}
      </main>
    </div>
  )
}
