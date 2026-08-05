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

export type SettingsSetupChecklist = {
  complete: boolean
  completed: number
  total: number
  items: Array<{
    key: string
    section: string
    field: string
    label: string
    complete: boolean
  }>
}

export type AdminSettingsResponse = {
  title: string
  section: "admin"
  setup_checklist: SettingsSetupChecklist
  sections: SettingsSection[]
}

export type SetupWizardAction = {
  label: string
  href: string
}

export type SetupWizardSettingsTarget = {
  section: string
  fields: string[]
}

export type SetupWizardItem = {
  key: string
  label: string
  complete: boolean
  required: boolean
  detail: string
  href: string
  message: string
  section: string
  field: string
}

export type SetupWizardStep = {
  key: string
  title: string
  description: string
  complete: boolean
  completed: number
  total: number
  href: string
  items: SetupWizardItem[]
  actions: SetupWizardAction[]
  settings_sections: SetupWizardSettingsTarget[]
}

export type SetupWizardMessage = {
  key: string
  step: string
  label: string
  message: string
  href: string
  severity: "warning" | "error" | "info"
}

export type SetupWizardResponse = {
  title: string
  section: "admin"
  summary: {
    complete: boolean
    completed_steps: number
    total_steps: number
    completed_required_items: number
    total_required_items: number
    missing_required_items: number
  }
  setup_checklist: SettingsSetupChecklist
  steps: SetupWizardStep[]
  messages: SetupWizardMessage[]
}

export function loadAdminSettings() {
  return apiFetch<AdminSettingsResponse>("/admin/settings")
}

export function loadSetupWizard() {
  return apiFetch<SetupWizardResponse>("/admin/setup-wizard")
}

export function saveAdminSettings(
  section: string,
  values: Record<string, SettingValue>,
  reason: string
) {
  return apiFetch<{ message: string; section: SettingsSection; setup_checklist: SettingsSetupChecklist }>(
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

  return apiFetch<{ message: string; url: string; section: SettingsSection; setup_checklist: SettingsSetupChecklist }>(
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
