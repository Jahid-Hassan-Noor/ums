import { apiFetch } from "@/lib/auth"

export type SettingValue = string | number | boolean

export type SettingChoice = {
  value: string
  label: string
}

export type UiSettingField = {
  key: string
  label: string
  default: SettingValue
  type:
    | "text"
    | "select"
    | "boolean"
    | "image"
    | "color"
    | "number"
  help_text?: string
  min?: number
  max?: number
  max_length?: number
  choices?: SettingChoice[]
}

export type UiSection = {
  key: string
  title: string
  description: string
  fields: UiSettingField[]
  values: Record<string, SettingValue>
  updated_at: string | null
  updated_by: string
}

export type PublicUiPayload = {
  maintenance: { enabled: boolean }
  university: Record<string, string>
  uiCustomization: Record<string, SettingValue>
  features: Record<string, boolean>
}

export type AdminUiCustomizationResponse = {
  section: UiSection
  public_payload: PublicUiPayload
}

export function loadUiCustomization() {
  return apiFetch<AdminUiCustomizationResponse>("/admin/ui-customization")
}

export function saveUiCustomization(
  values: Record<string, SettingValue>,
  reason: string
) {
  return apiFetch<{
    message: string
    section: UiSection
    public_payload: PublicUiPayload
  }>("/admin/ui-customization", {
    method: "PATCH",
    body: JSON.stringify({ values, reason }),
  })
}

export function uploadUiCustomizationImage(
  field: string,
  file: File,
  reason = ""
) {
  const body = new FormData()
  body.append("action", "upload_image")
  body.append("field", field)
  body.append("file", file)
  if (reason.trim()) body.append("reason", reason.trim())

  return apiFetch<{
    message: string
    url: string
    section: UiSection
    public_payload: PublicUiPayload
  }>("/admin/ui-customization", {
    method: "POST",
    body,
  })
}

export function restoreUiDefaults(reason: string) {
  return apiFetch<{
    message: string
    section: UiSection
    public_payload: PublicUiPayload
  }>("/admin/ui-customization", {
    method: "POST",
    body: JSON.stringify({ action: "restore_defaults", reason }),
  })
}
