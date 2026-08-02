"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileArchive,
  Loader2,
  Mail,
  Plus,
  Power,
  PowerOff,
  RefreshCcw,
  Save,
  Trash2,
  UploadCloud,
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
import {
  downloadDatabaseBackup,
  loadDatabaseBackupSettings,
  restoreDatabaseBackup,
  saveDatabaseBackupEmailSettings,
  updateDatabaseBackupMaintenance,
  type BackupRestoreResult,
  type DatabaseBackupSettings,
} from "@/lib/admin-database-backups"

const emptySettings: DatabaseBackupSettings = {
  monthly_email_enabled: false,
  recipients: [],
}

function uniqueRecipients(recipients: string[]) {
  const seen = new Set<string>()
  return recipients
    .map((recipient) => recipient.trim())
    .filter((recipient) => {
      if (!recipient) return false
      const key = recipient.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

function formatBytes(size: number | undefined) {
  if (!size) return "0 KB"
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

export function AdminBackupRestorePage() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [settings, setSettings] = useState<DatabaseBackupSettings>(emptySettings)
  const [maintenanceEnabled, setMaintenanceEnabled] = useState(false)
  const [maintenanceReason, setMaintenanceReason] = useState("")
  const [restoreFile, setRestoreFile] = useState<File | null>(null)
  const [restoreConfirmed, setRestoreConfirmed] = useState(false)
  const [restoreResult, setRestoreResult] = useState<BackupRestoreResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [savingSettings, setSavingSettings] = useState(false)
  const [maintenanceSaving, setMaintenanceSaving] = useState(false)
  const [backupRunning, setBackupRunning] = useState(false)
  const [restoreRunning, setRestoreRunning] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const response = await loadDatabaseBackupSettings()
      setSettings(response.settings)
      setMaintenanceEnabled(response.maintenance.enabled)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load backup settings.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const hasRecipientDrafts = useMemo(
    () => settings.recipients.some((recipient) => recipient.trim()),
    [settings.recipients]
  )

  function updateRecipient(index: number, value: string) {
    setSettings((current) => ({
      ...current,
      recipients: current.recipients.map((recipient, currentIndex) =>
        currentIndex === index ? value : recipient
      ),
    }))
    setSuccess("")
  }

  function addRecipient() {
    setSettings((current) => ({
      ...current,
      recipients: [...current.recipients, ""],
    }))
    setSuccess("")
  }

  function removeRecipient(index: number) {
    setSettings((current) => ({
      ...current,
      recipients: current.recipients.filter((_, currentIndex) => currentIndex !== index),
    }))
    setSuccess("")
  }

  async function saveEmailSettings() {
    setSavingSettings(true)
    setError("")
    setSuccess("")
    try {
      const response = await saveDatabaseBackupEmailSettings({
        monthly_email_enabled: settings.monthly_email_enabled,
        recipients: uniqueRecipients(settings.recipients),
      })
      setSettings(response.settings)
      setMaintenanceEnabled(response.maintenance.enabled)
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save backup email settings.")
    } finally {
      setSavingSettings(false)
    }
  }

  async function toggleMaintenance() {
    if (!maintenanceReason.trim()) {
      setError("Provide a reason before changing maintenance mode.")
      return
    }

    setMaintenanceSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await updateDatabaseBackupMaintenance(
        !maintenanceEnabled,
        maintenanceReason
      )
      setMaintenanceEnabled(response.maintenance.enabled)
      setMaintenanceReason("")
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update maintenance mode.")
    } finally {
      setMaintenanceSaving(false)
    }
  }

  async function downloadBackup() {
    setBackupRunning(true)
    setError("")
    setSuccess("")
    try {
      const result = await downloadDatabaseBackup()
      setSuccess(`${result.filename} downloaded. Maintenance mode was not changed.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to download backup.")
    } finally {
      setBackupRunning(false)
    }
  }

  async function restoreBackup() {
    if (!restoreFile) {
      setError("Choose a UMS backup zip or generated SQL file first.")
      return
    }
    if (!maintenanceEnabled) {
      setError("Turn on maintenance mode manually before restoring a backup.")
      return
    }
    if (!restoreConfirmed) {
      setError("Confirm that this restore can replace the current database and media files.")
      return
    }

    setRestoreRunning(true)
    setError("")
    setSuccess("")
    try {
      const result = await restoreDatabaseBackup(restoreFile)
      setRestoreResult(result)
      setMaintenanceEnabled(result.maintenance_mode)
      setRestoreConfirmed(false)
      setSuccess(`${restoreFile.name} restored successfully. Maintenance mode remains on.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to restore backup.")
    } finally {
      setRestoreRunning(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/backup-restore", title: "Backup and Restore" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Backup and Restore
            </h1>
            <p className="text-sm leading-6 text-muted-foreground">
              Download full system backups, restore approved UMS backups, and manage monthly backup email delivery.
            </p>
          </div>
          <Button variant="outline" onClick={() => void load()} disabled={loading}>
            <RefreshCcw />
            Refresh
          </Button>
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
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {maintenanceEnabled ? <PowerOff className="size-5" /> : <Power className="size-5" />}
                  Maintenance Mode
                </CardTitle>
                <CardDescription>
                  Manual control for public access and non-admin sessions.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div
                  className={`rounded-lg border p-4 ${
                    maintenanceEnabled
                      ? "border-amber-300 bg-amber-50 text-amber-950"
                      : "border-border/70 bg-muted/20"
                  }`}
                >
                  <p className="text-sm font-semibold">
                    Maintenance mode is {maintenanceEnabled ? "on" : "off"}
                  </p>
                  <p className="mt-1 text-sm leading-5 text-muted-foreground">
                    {maintenanceEnabled
                      ? "Public pages and non-admin sessions are blocked while admin accounts retain access."
                      : "Backups can be downloaded anytime. Turn this on manually before restoring data."}
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="maintenance-reason">Reason for change</Label>
                  <Textarea
                    id="maintenance-reason"
                    value={maintenanceReason}
                    onChange={(event) => setMaintenanceReason(event.target.value)}
                    placeholder="Reference the maintenance window, restore, or server update."
                  />
                </div>
                <Button
                  variant={maintenanceEnabled ? "outline" : "destructive"}
                  onClick={() => void toggleMaintenance()}
                  disabled={maintenanceSaving || !maintenanceReason.trim()}
                >
                  {maintenanceSaving ? (
                    <Loader2 className="animate-spin" />
                  ) : maintenanceEnabled ? (
                    <PowerOff />
                  ) : (
                    <Power />
                  )}
                  {maintenanceEnabled ? "Turn off maintenance" : "Turn on maintenance"}
                </Button>
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileArchive className="size-5" />
                  Full Backup
                </CardTitle>
                <CardDescription>
                  Download a zip containing SQL when available, JSON fallback, media, manifest, and restore notes.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => void downloadBackup()}
                  disabled={backupRunning || restoreRunning}
                >
                  {backupRunning ? <Loader2 className="animate-spin" /> : <Download />}
                  {backupRunning ? "Preparing backup..." : "Download backup"}
                </Button>
                <p className="text-sm leading-6 text-muted-foreground">
                  Downloading a backup does not turn maintenance mode on or off.
                </p>
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UploadCloud className="size-5" />
                  Restore Backup
                </CardTitle>
                <CardDescription>
                  Restore only UMS-generated .zip or .sql backups after maintenance mode is on.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!maintenanceEnabled ? (
                  <p className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                    <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                    Turn on maintenance mode manually before uploading a backup.
                  </p>
                ) : null}
                <div className="flex flex-col gap-3 rounded-lg border border-border/70 bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium">
                      {restoreFile ? restoreFile.name : "No file selected"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {restoreFile ? formatBytes(restoreFile.size) : "Choose a .zip or .sql backup."}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={restoreRunning || backupRunning}
                  >
                    <UploadCloud />
                    Choose file
                  </Button>
                  <input
                    ref={fileInputRef}
                    className="sr-only"
                    type="file"
                    accept=".zip,.sql,application/zip,application/sql,text/plain"
                    onChange={(event) => {
                      setRestoreFile(event.target.files?.[0] ?? null)
                      setRestoreResult(null)
                      event.target.value = ""
                    }}
                  />
                </div>
                <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border/70 bg-muted/20 p-3">
                  <input
                    className="mt-1 size-4 accent-primary"
                    type="checkbox"
                    checked={restoreConfirmed}
                    onChange={(event) => setRestoreConfirmed(event.target.checked)}
                  />
                  <span className="text-sm leading-5">
                    This restore can replace the current database and media files.
                  </span>
                </label>
                <Button
                  onClick={() => void restoreBackup()}
                  disabled={
                    restoreRunning ||
                    backupRunning ||
                    !maintenanceEnabled ||
                    !restoreFile ||
                    !restoreConfirmed
                  }
                >
                  {restoreRunning ? <Loader2 className="animate-spin" /> : <UploadCloud />}
                  {restoreRunning ? "Restoring..." : "Restore backup"}
                </Button>
                {restoreResult ? (
                  <div className="grid gap-3 rounded-lg border border-border/70 bg-background p-4 text-sm sm:grid-cols-3">
                    <div>
                      <p className="text-muted-foreground">Format</p>
                      <p className="mt-1 font-semibold">{restoreResult.database_format.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Media restored</p>
                      <p className="mt-1 font-semibold">{restoreResult.media_files_restored}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Backup date</p>
                      <p className="mt-1 font-semibold">
                        {restoreResult.manifest?.created_at || "Recorded in archive"}
                      </p>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card className="border-border/70 bg-card/95 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="size-5" />
                  Monthly Backup Email
                </CardTitle>
                <CardDescription>
                  Send the full backup archive on the 1st of each month when enabled.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border/70 bg-muted/20 p-3">
                  <input
                    className="mt-1 size-4 accent-primary"
                    type="checkbox"
                    checked={settings.monthly_email_enabled}
                    onChange={(event) =>
                      setSettings((current) => ({
                        ...current,
                        monthly_email_enabled: event.target.checked,
                      }))
                    }
                  />
                  <span className="space-y-1">
                    <span className="block text-sm font-medium">
                      Email backup on the 1st day of every month
                    </span>
                    <span className="block text-xs leading-5 text-muted-foreground">
                      The scheduled job skips delivery when this is off or no recipient is configured.
                    </span>
                  </span>
                </label>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <Label>Receiving email addresses</Label>
                    <Button type="button" variant="outline" size="sm" onClick={addRecipient}>
                      <Plus />
                      Add email
                    </Button>
                  </div>
                  {settings.recipients.length ? (
                    <div className="space-y-2">
                      {settings.recipients.map((recipient, index) => (
                        <div key={index} className="flex gap-2">
                          <Input
                            type="email"
                            value={recipient}
                            placeholder="backup@example.edu"
                            onChange={(event) => updateRecipient(index, event.target.value)}
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            aria-label="Remove email"
                            onClick={() => removeRecipient(index)}
                          >
                            <Trash2 />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                      No backup recipient addresses configured.
                    </p>
                  )}
                </div>

                <Button
                  onClick={() => void saveEmailSettings()}
                  disabled={savingSettings || (settings.monthly_email_enabled && !hasRecipientDrafts)}
                >
                  {savingSettings ? <Loader2 className="animate-spin" /> : <Save />}
                  Save email settings
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  )
}
