import { apiFetch } from "@/lib/auth"

export type SettingValue = string | number | boolean

export type SettingChoice = {
  value: string
  label: string
}

export type SettingField = {
  key: string
  label: string
  default: SettingValue
  type:
    | "text"
    | "email"
    | "tel"
    | "textarea"
    | "number"
    | "select"
    | "boolean"
    | "url"
    | "image"
    | "color"
  help_text?: string
  high_impact?: boolean
  min?: number
  max?: number
  max_length?: number
  choices?: SettingChoice[]
}

export type SettingsSection = {
  key: string
  title: string
  description: string
  fields: SettingField[]
  values: Record<string, SettingValue>
  updated_at: string | null
  updated_by: string
}

export type AdminSettingsResponse = {
  title: string
  section: "admin"
  sections: SettingsSection[]
}

export function loadAdminSettings() {
  return apiFetch<AdminSettingsResponse>("/admin/settings")
}

export function saveAdminSettings(
  section: string,
  values: Record<string, SettingValue>,
  reason: string
) {
  return apiFetch<{ message: string; section: SettingsSection }>(
    "/admin/settings",
    {
      method: "PATCH",
      body: JSON.stringify({ section, values, reason }),
    }
  )
}

export function uploadAdminSettingsImage(
  section: string,
  field: string,
  file: File,
  reason = ""
) {
  const body = new FormData()
  body.append("action", "upload_image")
  body.append("section", section)
  body.append("field", field)
  body.append("file", file)
  if (reason.trim()) body.append("reason", reason.trim())

  return apiFetch<{ message: string; url: string; section: SettingsSection }>(
    "/admin/settings",
    {
      method: "POST",
      body,
    }
  )
}

export function sendSettingsTestNotification() {
  return apiFetch<{ message: string }>("/admin/settings", {
    method: "POST",
    body: JSON.stringify({ action: "test_notification" }),
  })
}
