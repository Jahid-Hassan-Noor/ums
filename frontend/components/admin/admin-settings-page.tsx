"use client"

/* eslint-disable @next/next/no-img-element */

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import {
  AlertTriangle,
  BellRing,
  CheckCircle2,
  History,
  ImageIcon,
  Loader2,
  RotateCcw,
  Save,
  Send,
  Settings,
  Upload,
} from "lucide-react"

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
import {
  loadAdminSettings,
  saveAdminSettings,
  sendSettingsTestNotification,
  uploadAdminSettingsImage,
  type SettingField,
  type SettingValue,
  type SettingsSection,
} from "@/lib/admin-settings"

type ValuesBySection = Record<string, Record<string, SettingValue>>

const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"

function cloneSectionValues(sections: SettingsSection[]): ValuesBySection {
  return Object.fromEntries(
    sections.map((section) => [section.key, { ...section.values }])
  )
}

function updatedLabel(section: SettingsSection) {
  if (!section.updated_at) return "Using UMS defaults"
  const timestamp = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(section.updated_at))
  return `Updated ${timestamp}${section.updated_by ? ` by ${section.updated_by}` : ""}`
}

function FieldControl({
  field,
  value,
  onChange,
  onUpload,
  uploading = false,
}: {
  field: SettingField
  value: SettingValue
  onChange: (value: SettingValue) => void
  onUpload?: (file: File) => void
  uploading?: boolean
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (field.type === "boolean") {
    return (
      <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border/70 bg-muted/20 p-3">
        <input
          className="mt-1 size-4 accent-primary"
          type="checkbox"
          checked={Boolean(value)}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span className="space-y-1">
          <span className="block text-sm font-medium">{field.label}</span>
          {field.help_text ? (
            <span className="block text-xs leading-5 text-muted-foreground">
              {field.help_text}
            </span>
          ) : null}
          {field.high_impact ? (
            <span className="block text-xs font-medium text-amber-700">
              High-impact setting
            </span>
          ) : null}
        </span>
      </label>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <Label htmlFor={`setting-${field.key}`}>{field.label}</Label>
        {field.high_impact ? (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-800">
            High impact
          </span>
        ) : null}
      </div>
      {field.type === "select" ? (
        <select
          id={`setting-${field.key}`}
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
          id={`setting-${field.key}`}
          value={String(value)}
          maxLength={field.max_length}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : field.type === "image" ? (
        <div className="space-y-3">
          <div className="flex gap-3 rounded-lg border border-border/70 bg-muted/20 p-3">
            <div className="flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-md border bg-background">
              {String(value || "").trim() ? (
                <img
                  src={String(value)}
                  alt={field.label}
                  className="h-full w-full object-contain"
                />
              ) : (
                <ImageIcon className="size-6 text-muted-foreground" />
              )}
            </div>
            <div className="min-w-0 flex-1 space-y-2">
              <Input
                id={`setting-${field.key}`}
                type="text"
                value={String(value ?? "")}
                maxLength={field.max_length}
                onChange={(event) => onChange(event.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={!onUpload || uploading}
                >
                  {uploading ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    <Upload />
                  )}
                  Upload
                </Button>
                <input
                  ref={fileInputRef}
                  className="sr-only"
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                  onChange={(event) => {
                    const file = event.target.files?.[0]
                    event.target.value = ""
                    if (file && onUpload) onUpload(file)
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <Input
          id={`setting-${field.key}`}
          type={field.type}
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
        <p className="text-xs leading-5 text-muted-foreground">
          {field.help_text}
        </p>
      ) : null}
    </div>
  )
}

export function AdminSettingsPage() {
  const [sections, setSections] = useState<SettingsSection[]>([])
  const [drafts, setDrafts] = useState<ValuesBySection>({})
  const [activeKey, setActiveKey] = useState("general")
  const [reason, setReason] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingField, setUploadingField] = useState("")
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [restoreDefaultsConfirmOpen, setRestoreDefaultsConfirmOpen] =
    useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const response = await loadAdminSettings()
      setSections(response.sections)
      setDrafts(cloneSectionValues(response.sections))
      setActiveKey((current) =>
        response.sections.some((section) => section.key === current)
          ? current
          : (response.sections[0]?.key ?? "general")
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load UMS settings."
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const activeSection = sections.find((section) => section.key === activeKey)
  const activeFields = useMemo(
    () =>
      activeSection?.fields.filter(
        (field) =>
          !(activeSection.key === "security" && field.key === "maintenance_mode")
      ) ?? [],
    [activeSection]
  )
  const activeDraft = useMemo(
    () => (activeSection ? (drafts[activeSection.key] ?? {}) : {}),
    [activeSection, drafts]
  )
  const changedFields = useMemo(
    () => {
      if (!activeSection) return []
      return activeFields.filter(
        (field) => activeDraft[field.key] !== activeSection.values[field.key]
      )
    },
    [activeDraft, activeFields, activeSection]
  )
  const hasHighImpactChanges = changedFields.some((field) => field.high_impact)

  function updateValue(field: string, value: SettingValue) {
    if (!activeSection) return
    setDrafts((current) => ({
      ...current,
      [activeSection.key]: {
        ...current[activeSection.key],
        [field]: value,
      },
    }))
    setSuccess("")
  }

  function requestRestoreDefaults() {
    setError("")
    setSuccess("")
    setRestoreDefaultsConfirmOpen(true)
  }

  async function saveDefaults() {
    if (!activeSection) return
    const defaultValues = Object.fromEntries(
      activeFields.map((field) => [field.key, field.default])
    )
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await saveAdminSettings(
        activeSection.key,
        defaultValues,
        "Restored to default values"
      )
      setSections((current) =>
        current.map((section) =>
          section.key === response.section.key ? response.section : section
        )
      )
      setDrafts((current) => ({
        ...current,
        [response.section.key]: { ...response.section.values },
      }))
      setReason("")
      setSuccess("All settings in this section have been restored to defaults.")
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to restore default settings."
      )
    } finally {
      setSaving(false)
      setRestoreDefaultsConfirmOpen(false)
    }
  }

  function discardChanges() {
    if (!activeSection) return
    setDrafts((current) => ({
      ...current,
      [activeSection.key]: { ...activeSection.values },
    }))
    setReason("")
    setSuccess("")
  }

  async function saveSection() {
    if (!activeSection || !changedFields.length || uploadingField) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await saveAdminSettings(
        activeSection.key,
        Object.fromEntries(
          changedFields.map((field) => [field.key, activeDraft[field.key]])
        ),
        reason
      )
      setSections((current) =>
        current.map((section) =>
          section.key === response.section.key ? response.section : section
        )
      )
      setDrafts((current) => ({
        ...current,
        [response.section.key]: { ...response.section.values },
      }))
      setReason("")
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to save UMS settings."
      )
    } finally {
      setSaving(false)
      setConfirmOpen(false)
    }
  }

  function requestSave() {
    setError("")
    if (!changedFields.length) return
    if (hasHighImpactChanges) {
      if (!reason.trim()) {
        setError("Provide a reason before saving high-impact settings changes.")
        return
      }
      setConfirmOpen(true)
      return
    }
    void saveSection()
  }

  async function testNotification() {
    if (uploadingField) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await sendSettingsTestNotification()
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to create test notification."
      )
    } finally {
      setSaving(false)
    }
  }

  async function uploadImage(field: SettingField, file: File) {
    if (!activeSection || saving || uploadingField) return
    const uploadKey = `${activeSection.key}.${field.key}`
    setUploadingField(uploadKey)
    setError("")
    setSuccess("")
    try {
      const response = await uploadAdminSettingsImage(
        activeSection.key,
        field.key,
        file,
        reason
      )
      setDrafts((current) => ({
        ...current,
        [response.section.key]: {
          ...(current[response.section.key] ?? response.section.values),
          [field.key]: response.url,
        },
      }))
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to upload settings image."
      )
    } finally {
      setUploadingField("")
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/settings", title: "Settings" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              UMS Settings
            </h1>
            <p className="text-sm leading-6 text-muted-foreground">
              Configure UMS-wide defaults and policies. Each section saves
              independently, and every successful update is recorded in the
              audit log.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" render={<Link href="/admin/audit-log" />}>
              <History />
              View Audit Log
            </Button>
            <Button
              variant="outline"
              onClick={() => void load()}
              disabled={loading || saving}
            >
              <RotateCcw />
              Refresh
            </Button>
          </div>
        </section>

        {error ? (
          <p className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
            {success}
          </p>
        ) : null}

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid gap-5 xl:grid-cols-[18rem_minmax(0,1fr)]">
            <aside className="space-y-2">
              {sections.map((section) => (
                <button
                  key={section.key}
                  type="button"
                  onClick={() => {
                    setActiveKey(section.key)
                    setReason("")
                    setError("")
                    setSuccess("")
                  }}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    activeKey === section.key
                      ? "border-primary/50 bg-primary/5"
                      : "border-border/70 bg-card hover:bg-muted/50"
                  }`}
                >
                  <span className="block text-sm font-medium">
                    {section.title}
                  </span>
                  <span className="mt-1 line-clamp-2 block text-xs leading-5 text-muted-foreground">
                    {section.description}
                  </span>
                </button>
              ))}
            </aside>

            {activeSection ? (
              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardHeader>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Settings className="size-5" />
                        {activeSection.title}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        {activeSection.description}
                      </CardDescription>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {updatedLabel(activeSection)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-5 lg:grid-cols-2">
                    {activeFields.map((field) => (
                      <FieldControl
                        key={field.key}
                        field={field}
                        value={activeDraft[field.key] ?? field.default}
                        onChange={(value) => updateValue(field.key, value)}
                        onUpload={(file) => void uploadImage(field, file)}
                        uploading={
                          saving ||
                          uploadingField === `${activeSection.key}.${field.key}`
                        }
                      />
                    ))}
                  </div>

                  {activeSection.key === "notifications" ? (
                    <div className="rounded-lg border border-border/70 bg-muted/20 p-4">
                      <p className="font-medium">Test notification</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Create an in-app test notification for your
                        administrator account.
                      </p>
                      <Button
                        className="mt-3"
                        variant="outline"
                        disabled={saving || Boolean(uploadingField)}
                        onClick={() => void testNotification()}
                      >
                        <Send />
                        Send test notification
                      </Button>
                    </div>
                  ) : null}

                  <div className="space-y-2 border-t pt-5">
                    <Label htmlFor="settings-reason">
                      Reason for change{" "}
                      {hasHighImpactChanges ? "(required)" : "(optional)"}
                    </Label>
                    <Textarea
                      id="settings-reason"
                      placeholder="Reference the policy, decision, or operational reason for this update."
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                    />
                    {hasHighImpactChanges ? (
                      <p className="text-xs font-medium text-amber-700">
                        This update changes a high-impact policy and requires
                        confirmation.
                      </p>
                    ) : null}
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-5">
                    <p className="text-sm text-muted-foreground">
                      {changedFields.length
                        ? `${changedFields.length} unsaved setting(s)`
                        : "No unsaved changes"}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        onClick={requestRestoreDefaults}
                        disabled={saving || Boolean(uploadingField)}
                      >
                        <RotateCcw />
                        Restore defaults
                      </Button>
                      <Button
                        variant="outline"
                        onClick={discardChanges}
                        disabled={
                          saving ||
                          Boolean(uploadingField) ||
                          !changedFields.length
                        }
                      >
                        Discard
                      </Button>
                      <Button
                        onClick={requestSave}
                        disabled={
                          saving ||
                          Boolean(uploadingField) ||
                          !changedFields.length
                        }
                      >
                        {saving ? (
                          <Loader2 className="animate-spin" />
                        ) : (
                          <Save />
                        )}
                        Save section
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : null}
          </div>
        )}
      </main>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Confirm high-impact settings change
            </AlertDialogTitle>
            <AlertDialogDescription>
              This update can immediately affect UMS access or active workflows.
              The previous values, new values, administrator, timestamp, and
              reason will be recorded in the audit log.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={saving || Boolean(uploadingField)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={saving || Boolean(uploadingField)}
              onClick={() => void saveSection()}
            >
              {saving ? <Loader2 className="animate-spin" /> : <BellRing />}
              Confirm and save
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={restoreDefaultsConfirmOpen}
        onOpenChange={setRestoreDefaultsConfirmOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Restore default settings
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will reset all settings in the current section to their
              factory default values and save immediately. Any customizations
              you have made will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={saving || Boolean(uploadingField)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={saving || Boolean(uploadingField)}
              onClick={() => void saveDefaults()}
            >
              {saving ? <Loader2 className="animate-spin" /> : <RotateCcw />}
              Restore defaults
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
