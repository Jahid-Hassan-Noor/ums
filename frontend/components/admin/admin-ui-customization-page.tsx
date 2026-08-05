"use client"

/* eslint-disable @next/next/no-img-element */

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  ImageIcon,
  Loader2,
  Paintbrush,
  Palette,
  RotateCcw,
  Save,
  Upload,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  Sun,
  Moon,
} from "lucide-react"

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

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { ConfigurableLoader } from "@/components/ui/configurable-loader"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

import {
  loadUiCustomization,
  restoreUiDefaults,
  saveUiCustomization,
  uploadUiCustomizationImage,
  type UiSettingField,
  type SettingValue,
  type UiSection,
} from "@/lib/admin-ui-customization"

const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"

type ValueMap = Record<string, SettingValue>

const FIELD_GROUPS: { label: string; keys: string[] }[] = [
  {
    label: "Brand & Identity",
    keys: [
      "brand_name",
      "sidebar_label",
      "logo_url",
      "logo_alt_text",
      "default_avatar_url",
    ],
  },
  {
    label: "Loading Screen",
    keys: ["loading_spinner", "loading_spinner_size"],
  },
  {
    label: "Dashboard",
    keys: [
      "card_density",
      "show_scope_badge",
      "show_link_descriptions",
      "dashboard_background_image_url",
    ],
  },
  {
    label: "Colors (Light Mode)",
    keys: [
      "primary_text_color",
      "secondary_text_color",
      "background_color",
      "button_color",
      "button_text_color",
      "secondary_button_color",
      "secondary_button_text_color",
      "button_border_radius",
      "icon_color",
    ],
  },
  {
    label: "Colors (Dark Mode)",
    keys: [
      "dark_primary_text_color",
      "dark_secondary_text_color",
      "dark_background_color",
      "dark_button_color",
      "dark_button_text_color",
      "dark_secondary_button_color",
      "dark_secondary_button_text_color",
      "dark_accent_color",
      "dark_icon_color",
    ],
  },
  {
    label: "Typography",
    keys: ["font_family", "font_size_base"],
  },
  {
    label: "Sidebar",
    keys: [
      "sidebar_font_size",
      "sidebar_font_weight",
      "sidebar_icon_size",
      "sidebar_width",
      "sidebar_collapsed_by_default",
    ],
  },
  {
    label: "Layout",
    keys: ["sticky_header", "show_breadcrumbs", "show_footer"],
  },
  {
    label: "Cards",
    keys: [
      "card_border_radius",
      "card_shadow",
      "card_background_color",
    ],
  },
  {
    label: "Avatar",
    keys: ["avatar_shape", "avatar_size"],
  },
  {
    label: "Table & Modal",
    keys: ["table_stripe_color", "modal_overlay_opacity"],
  },
]

function FieldControl({
  field,
  value,
  onChange,
  onUpload,
  uploading = false,
}: {
  field: UiSettingField
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
        </span>
      </label>
    )
  }

  return (
    <div className="space-y-2">
      <Label htmlFor={`ui-${field.key}`}>{field.label}</Label>
      {field.type === "select" ? (
        <select
          id={`ui-${field.key}`}
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
                id={`ui-${field.key}`}
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
          id={`ui-${field.key}`}
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

function shadowValue(val: string): string {
  if (val === "none") return "none"
  if (val === "light") return "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)"
  if (val === "strong") return "0 10px 25px rgba(0,0,0,0.15), 0 4px 10px rgba(0,0,0,0.1)"
  return "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)"
}

function avatarRadius(shape: string): string {
  if (shape === "circle") return "50%"
  if (shape === "rounded") return "8px"
  return "0"
}

function avatarSizeVal(size: string): string {
  if (size === "sm") return "32px"
  if (size === "lg") return "48px"
  return "40px"
}

function LivePreview({
  values,
  darkPreview,
}: {
  values: ValueMap
  darkPreview: boolean
}) {
  const bgColor = darkPreview
    ? String(values.dark_background_color || "#09090b")
    : String(values.background_color || "#ffffff")
  const textPrimary = darkPreview
    ? String(values.dark_primary_text_color || "#ffffff")
    : String(values.primary_text_color || "#000000")
  const textSecondary = darkPreview
    ? String(values.dark_secondary_text_color || "#a1a1aa")
    : String(values.secondary_text_color || "#666666")
  const btnBg = darkPreview
    ? String(values.dark_button_color || "#fafafa")
    : String(values.button_color || "#18181b")
  const btnText = darkPreview
    ? String(values.dark_button_text_color || "#18181b")
    : String(values.button_text_color || "#fafafa")
  const secondaryBtnBg = darkPreview
    ? String(values.dark_secondary_button_color || "#27272a")
    : String(values.secondary_button_color || "#f4f4f5")
  const secondaryBtnText = darkPreview
    ? String(values.dark_secondary_button_text_color || "#fafafa")
    : String(values.secondary_button_text_color || "#18181b")
  const btnRadius = String(values.button_border_radius || "0.625rem")
  const cardBg = darkPreview
    ? String(values.dark_background_color || "#09090b")
    : String(values.card_background_color || "#ffffff")
  const cardRadius = String(values.card_border_radius || "0.5rem")
  const cardShad = shadowValue(String(values.card_shadow || "default"))
  const fontFamily = String(values.font_family || "Inter")
  const fontSizeBase = String(values.font_size_base || "16")
  const sidebarWidth = String(values.sidebar_width || "16rem")
  const sidebarFontSize = String(values.sidebar_font_size || "14px")
  const sidebarFontWeight = String(values.sidebar_font_weight || "medium")
  const sidebarIconSize = String(values.sidebar_icon_size || "16px")
  const iconColor = darkPreview
    ? String(values.dark_icon_color || "#ffffff")
    : String(values.icon_color || "#000000")
  const avatarShape = String(values.avatar_shape || "circle")
  const avatarSize = avatarSizeVal(String(values.avatar_size || "md"))
  const brandName = String(values.brand_name || "University Management System")
  const logoUrl = String(values.logo_url || "/images/ums/ums-logo.svg")
  const logoAlt = String(values.logo_alt_text || "University logo")
  const loadingSpinner = String(values.loading_spinner || "dna")
  const loadingSpinnerSize =
    typeof values.loading_spinner_size === "number"
      ? values.loading_spinner_size
      : Number(values.loading_spinner_size || 80)

  const fwMap: Record<string, number> = {
    normal: 400,
    medium: 500,
    semibold: 600,
  }

  return (
    <div
      className="overflow-hidden rounded-xl border shadow-sm"
      style={{
        backgroundColor: bgColor,
        color: textPrimary,
        fontFamily,
        fontSize: `${fontSizeBase}px`,
        transition: "all 0.2s ease",
      }}
    >
      <div className="flex min-h-[480px]">
        <div
          className="flex shrink-0 flex-col border-r"
          style={{
            width: sidebarWidth,
            borderColor: darkPreview
              ? "rgba(255,255,255,0.1)"
              : "rgba(0,0,0,0.08)",
            backgroundColor: darkPreview ? "#111113" : "#f8fafc",
          }}
        >
          <div
            className="flex items-center gap-2 border-b p-3"
            style={{
              borderColor: darkPreview
                ? "rgba(255,255,255,0.08)"
                : "rgba(0,0,0,0.06)",
            }}
          >
            <div
              className="flex shrink-0 items-center justify-center overflow-hidden bg-white p-1 shadow-sm"
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "6px",
              }}
            >
              <img
                src={logoUrl}
                alt={logoAlt}
                className="h-5 w-5 object-contain"
              />
            </div>
            <span
              className="truncate font-medium"
              style={{
                fontSize: sidebarFontSize,
                fontWeight: fwMap[sidebarFontWeight] ?? 500,
              }}
            >
              {brandName}
            </span>
          </div>
          <div className="flex-1 space-y-1 p-3">
            {[
              { label: "Dashboard", icon: "▨" },
              { label: "Courses", icon: "📖" },
              { label: "Users", icon: "👥" },
              { label: "Reports", icon: "📊" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5"
                style={{
                  fontSize: sidebarFontSize,
                  color: textSecondary,
                }}
              >
                <span style={{ fontSize: sidebarIconSize }}>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-1 flex-col">
          <div
            className="flex items-center justify-between border-b px-4 py-2"
            style={{
              borderColor: darkPreview
                ? "rgba(255,255,255,0.08)"
                : "rgba(0,0,0,0.06)",
              backgroundColor: darkPreview ? "rgba(0,0,0,0.2)" : "rgba(255,255,255,0.8)",
            }}
          >
            <div className="flex items-center gap-2 text-sm" style={{ color: textSecondary }}>
              <span>Home</span>
              <span>/</span>
              <span style={{ color: textPrimary }}>Dashboard</span>
            </div>
            <div
              className="flex items-center gap-2"
              style={{ color: textSecondary, fontSize: sidebarFontSize }}
            >
              <span>🔔</span>
              <span
                className="flex items-center justify-center overflow-hidden border"
                style={{
                  width: avatarSize,
                  height: avatarSize,
                  borderRadius: avatarRadius(avatarShape),
                  borderColor: darkPreview
                    ? "rgba(255,255,255,0.15)"
                    : "rgba(0,0,0,0.1)",
                }}
              >
                <img
                  src={String(values.default_avatar_url || "/images/avatar.png")}
                  alt="Avatar"
                  className="h-full w-full object-cover"
                />
              </span>
            </div>
          </div>

          <div className="flex-1 space-y-4 p-4">
            <h2
              className="text-xl font-semibold tracking-tight"
              style={{ color: textPrimary }}
            >
              Dashboard Preview
            </h2>
            <p style={{ color: textSecondary, fontSize: "14px" }}>
              This preview shows how your UI customizations will look.
            </p>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Students", value: "2,450" },
                { label: "Teachers", value: "180" },
                { label: "Courses", value: "64" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-lg p-3"
                  style={{
                    backgroundColor: cardBg,
                    borderRadius: cardRadius,
                    boxShadow: cardShad,
                  }}
                >
                  <p className="text-xs" style={{ color: textSecondary }}>
                    {stat.label}
                  </p>
                  <p
                    className="mt-1 text-lg font-semibold"
                    style={{ color: textPrimary }}
                  >
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>

            <div
              className="rounded-lg p-4"
              style={{
                backgroundColor: cardBg,
                borderRadius: cardRadius,
                boxShadow: cardShad,
              }}
            >
              <h3
                className="mb-2 text-sm font-semibold"
                style={{ color: textPrimary }}
              >
                Actions
              </h3>
              <div className="flex flex-wrap gap-2">
                <button
                  className="inline-flex items-center justify-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium"
                  style={{
                    backgroundColor: btnBg,
                    color: btnText,
                    borderRadius: btnRadius,
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: "16px", height: "16px" }}>
                    <path d="M5 12h14" /><path d="M12 5l7 7-7 7" />
                  </svg>
                  Primary
                </button>
                <button
                  className="inline-flex items-center justify-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-medium"
                  style={{
                    backgroundColor: secondaryBtnBg,
                    color: secondaryBtnText,
                    borderRadius: btnRadius,
                    borderColor: darkPreview
                      ? "rgba(255,255,255,0.12)"
                      : "rgba(0,0,0,0.08)",
                    cursor: "pointer",
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: "16px", height: "16px" }}>
                    <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                  </svg>
                  Edit
                </button>
                <button
                  className="inline-flex items-center justify-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-medium"
                  style={{
                    backgroundColor: secondaryBtnBg,
                    color: secondaryBtnText,
                    borderRadius: btnRadius,
                    borderColor: darkPreview
                      ? "rgba(255,255,255,0.12)"
                      : "rgba(0,0,0,0.08)",
                    cursor: "pointer",
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: "16px", height: "16px" }}>
                    <path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                  Delete
                </button>
              </div>
            </div>

            <div
              className="flex items-center gap-4 rounded-lg p-4"
              style={{
                backgroundColor: cardBg,
                borderRadius: cardRadius,
                boxShadow: cardShad,
              }}
            >
              <ConfigurableLoader
                spinner={loadingSpinner}
                size={Math.min(120, Math.max(32, loadingSpinnerSize))}
                color={iconColor}
              />
              <div>
                <h3
                  className="text-sm font-semibold"
                  style={{ color: textPrimary }}
                >
                  Loading screen
                </h3>
                <p className="mt-1 text-sm" style={{ color: textSecondary }}>
                  {loadingSpinner.replaceAll("-", " ")} at{" "}
                  {Number.isFinite(loadingSpinnerSize)
                    ? loadingSpinnerSize
                    : 80}
                  px
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function AdminUiCustomizationPage() {
  const [section, setSection] = useState<UiSection | null>(null)
  const [draftValues, setDraftValues] = useState<ValueMap>({})
  const [savedValues, setSavedValues] = useState<ValueMap>({})
  const [reason, setReason] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingField, setUploadingField] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showPreview, setShowPreview] = useState(true)
  const [darkPreview, setDarkPreview] = useState(false)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
    () => Object.fromEntries(FIELD_GROUPS.map((g) => [g.label, true]))
  )
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const response = await loadUiCustomization()
      setSection(response.section)
      const vals = { ...response.section.values }
      setDraftValues(vals)
      setSavedValues(vals)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load UI customization settings."
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const fieldMap = useMemo(() => {
    if (!section) return {}
    return Object.fromEntries(section.fields.map((f) => [f.key, f]))
  }, [section])

  const changedFields = useMemo(() => {
    if (!section) return []
    return section.fields.filter(
      (field) => draftValues[field.key] !== savedValues[field.key]
    )
  }, [draftValues, savedValues, section])

  function toggleGroup(label: string) {
    setExpandedGroups((prev) => ({ ...prev, [label]: !prev[label] }))
  }

  function updateValue(field: string, value: SettingValue) {
    setDraftValues((prev) => ({ ...prev, [field]: value }))
    setSuccess("")
  }

  function discardChanges() {
    if (!section) return
    setDraftValues({ ...savedValues })
    setReason("")
    setSuccess("")
  }

  async function saveChanges() {
    if (!section || !changedFields.length || uploadingField) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await saveUiCustomization(draftValues, reason)
      setSection(response.section)
      const vals = { ...response.section.values }
      setDraftValues(vals)
      setSavedValues(vals)
      setReason("")
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to save UI customization."
      )
    } finally {
      setSaving(false)
    }
  }

  async function confirmRestoreDefaults() {
    if (!section || uploadingField) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await restoreUiDefaults(reason)
      setSection(response.section)
      const vals = { ...response.section.values }
      setDraftValues(vals)
      setSavedValues(vals)
      setReason("")
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to restore defaults."
      )
    } finally {
      setSaving(false)
      setRestoreDialogOpen(false)
    }
  }

  async function uploadImage(field: UiSettingField, file: File) {
    if (!section || saving || uploadingField) return
    setUploadingField(field.key)
    setError("")
    setSuccess("")
    try {
      const response = await uploadUiCustomizationImage(
        field.key,
        file,
        reason
      )
      setDraftValues((prev) => ({
        ...prev,
        [field.key]: response.url,
      }))
      setSuccess(response.message)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to upload image."
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
          { href: "/admin/ui-customization", title: "UI Customization" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <section className="flex flex-col gap-3 border-b border-border/70 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-3xl space-y-2">
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <Palette className="size-7" />
              UI Customization
            </h1>
            <p className="text-sm leading-6 text-muted-foreground">
              Customize the appearance of the UMS portal. Changes take effect
              immediately for all users after saving.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => setDarkPreview((prev) => !prev)}
              disabled={!showPreview}
            >
              {darkPreview ? <Sun /> : <Moon />}
              {darkPreview ? "Light preview" : "Dark preview"}
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowPreview((prev) => !prev)}
            >
              {showPreview ? <EyeOff /> : <Eye />}
              {showPreview ? "Hide preview" : "Show preview"}
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
        ) : section ? (
          <div
            className={`grid gap-6 ${
              showPreview ? "xl:grid-cols-[1fr_1fr]" : ""
            }`}
          >
            <div className="space-y-4">
              {FIELD_GROUPS.map((group) => {
                const groupFields = group.keys
                  .map((k) => fieldMap[k])
                  .filter(Boolean) as UiSettingField[]
                if (!groupFields.length) return null
                const expanded = expandedGroups[group.label] ?? true

                return (
                  <Card
                    key={group.label}
                    className="border-border/70 bg-card/95 shadow-sm"
                  >
                    <CardHeader
                      className="cursor-pointer select-none pb-3"
                      onClick={() => toggleGroup(group.label)}
                    >
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Paintbrush className="size-4" />
                          {group.label}
                        </CardTitle>
                        {expanded ? (
                          <ChevronDown className="size-4 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="size-4 text-muted-foreground" />
                        )}
                      </div>
                    </CardHeader>
                    {expanded ? (
                      <CardContent className="space-y-4 pt-0">
                        {groupFields.map((field) => (
                          <FieldControl
                            key={field.key}
                            field={field}
                            value={draftValues[field.key] ?? field.default}
                            onChange={(value) => updateValue(field.key, value)}
                            onUpload={(file) => void uploadImage(field, file)}
                            uploading={
                              saving || uploadingField === field.key
                            }
                          />
                        ))}
                      </CardContent>
                    ) : null}
                  </Card>
                )
              })}

              <Card className="border-border/70 bg-card/95 shadow-sm">
                <CardContent className="space-y-4 pt-5">
                  <div className="space-y-2">
                    <Label htmlFor="ui-reason">
                      Reason for change
                    </Label>
                    <textarea
                      id="ui-reason"
                      className="min-h-[60px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                      placeholder="Reference the design decision or ticket."
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                    />
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
                    <p className="text-sm text-muted-foreground">
                      {changedFields.length
                        ? `${changedFields.length} unsaved change(s)`
                        : "No unsaved changes"}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setRestoreDialogOpen(true)}
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
                        onClick={() => void saveChanges()}
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
                        Save changes
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {showPreview ? (
              <div className="space-y-3">
                <p className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Eye className="size-4" />
                  Live preview
                  <span className="ml-auto text-xs text-muted-foreground/60">
                    {darkPreview ? "Dark mode" : "Light mode"}
                  </span>
                </p>
                <div className="sticky top-4">
                  <LivePreview
                    values={draftValues}
                    darkPreview={darkPreview}
                  />
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </main>

      <AlertDialog
        open={restoreDialogOpen}
        onOpenChange={setRestoreDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Restore default values</AlertDialogTitle>
            <AlertDialogDescription>
              This will reset all UI customization settings to their factory
              default values and save immediately. Any customizations you have
              made will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={saving || Boolean(uploadingField)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={saving || Boolean(uploadingField)}
              onClick={() => void confirmRestoreDefaults()}
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
