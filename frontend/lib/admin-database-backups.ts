"use client"

import { apiFetch, apiRequest } from "@/lib/auth"
import { filenameFromDisposition, triggerBlobDownload } from "@/lib/fetch-utils"

export type DatabaseBackupSettings = {
  monthly_email_enabled: boolean
  recipients: string[]
}

export type DatabaseBackupMaintenance = {
  enabled: boolean
}

export type DatabaseBackupSettingsResponse = {
  settings: DatabaseBackupSettings
  maintenance: DatabaseBackupMaintenance
}

export type BackupDownloadResult = {
  filename: string
  size: number
}

export type BackupRestoreResult = {
  message: string
  restored_at: string
  database_format: "sql" | "json"
  media_files_restored: number
  maintenance_mode: boolean
  maintenance_mode_changed: boolean
  manifest?: {
    created_at?: string
    generated_by?: string
    media_file_count?: number
    media_total_bytes?: number
    database_formats?: string[]
    sql_backup_warning?: string
  }
}

async function errorMessageFromResponse(response: Response) {
  const fallback = `Backup action failed (${response.status}).`
  try {
    const data = await response.json()
    if (data && typeof data === "object") {
      const message =
        (data as { message?: unknown; detail?: unknown }).message ??
        (data as { detail?: unknown }).detail
      if (typeof message === "string" && message.trim()) return message
    }
  } catch {
    return fallback
  }
  return fallback
}

export function loadDatabaseBackupSettings() {
  return apiFetch<DatabaseBackupSettingsResponse>(
    "/admin/database-backup/settings"
  )
}

export function saveDatabaseBackupEmailSettings(
  settings: DatabaseBackupSettings
) {
  return apiFetch<{ message: string } & DatabaseBackupSettingsResponse>(
    "/admin/database-backup/settings",
    {
      method: "PATCH",
      body: JSON.stringify(settings),
    }
  )
}

export function updateDatabaseBackupMaintenance(
  maintenanceMode: boolean,
  reason: string
) {
  return apiFetch<{ message: string; maintenance: DatabaseBackupMaintenance }>(
    "/admin/database-backup/maintenance",
    {
      method: "PATCH",
      body: JSON.stringify({
        maintenance_mode: maintenanceMode,
        reason,
      }),
    }
  )
}

export async function downloadDatabaseBackup(): Promise<BackupDownloadResult> {
  const response = await apiRequest("/admin/database-backup", {
    method: "POST",
  })

  if (!response.ok) {
    throw new Error(await errorMessageFromResponse(response))
  }

  const blob = await response.blob()
  const filename = filenameFromDisposition(
    response.headers.get("Content-Disposition"),
    "ums-backup.zip"
  )
  triggerBlobDownload(blob, filename)

  return { filename, size: blob.size }
}

export async function restoreDatabaseBackup(
  file: File
): Promise<BackupRestoreResult> {
  const formData = new FormData()
  formData.append("backup_file", file)
  formData.append("confirm_restore", "true")

  const response = await apiRequest("/admin/database-backup/restore", {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await errorMessageFromResponse(response))
  }

  return (await response.json()) as BackupRestoreResult
}
