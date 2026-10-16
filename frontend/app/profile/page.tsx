"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import { Camera, KeyRound, Save, Upload } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { identityNumberLabel } from "@/lib/countries"
import {
  loadApplyOptions,
  loadApplyProfile,
  updateApplyProfile,
  type ApplyOption,
} from "@/lib/apply"
import {
  changePasswordRequest,
  ensureValidSession,
  profilePictureUrl,
  updateProfilePicture,
  type AuthSession,
} from "@/lib/auth"

const MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024
const MAX_PASSWORD_LENGTH = 20
const ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]
const IMAGE_ACCEPT = ALLOWED_IMAGE_EXTENSIONS.join(",")

function fileExtension(filename: string) {
  const dotIndex = filename.lastIndexOf(".")
  return dotIndex >= 0 ? filename.slice(dotIndex).toLowerCase() : ""
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

const emptyForm = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  phone: "",
  nationality: "",
  country_of_residence: "",
  passport_or_identity_no: "",
}

export default function ProfilePage() {
  const router = useRouter()
  const [session, setSession] = useState<AuthSession | null>(null)
  const [countries, setCountries] = useState<ApplyOption[]>([])
  const [form, setForm] = useState(emptyForm)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [pictureFile, setPictureFile] = useState<File | null>(null)
  const [isUploadingPicture, setIsUploadingPicture] = useState(false)
  const [oldPassword, setOldPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordMessage, setPasswordMessage] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function loadProfile() {
      try {
        const nextSession = await ensureValidSession()
        if (!isMounted) return
        setSession(nextSession)

        if (!nextSession) {
          router.replace("/login?next=%2Fprofile")
          return
        }

        if (nextSession.role !== "applicant") {
          setForm({
            ...emptyForm,
            username: nextSession.user.username || "",
            email: nextSession.user.email || "",
            first_name: nextSession.user.first_name || "",
            last_name: nextSession.user.last_name || "",
            phone: nextSession.user.phone_number || "",
          })
          return
        }

        const [options, applicant] = await Promise.all([
          loadApplyOptions(),
          loadApplyProfile(),
        ])
        if (!isMounted) return
        setCountries(options.countries)
        setForm({
          username: applicant.username || "",
          email: applicant.email || "",
          first_name: applicant.first_name || "",
          last_name: applicant.last_name || "",
          phone: applicant.phone || "",
          nationality: applicant.nationality || "",
          country_of_residence: applicant.country_of_residence || "",
          passport_or_identity_no: applicant.passport_or_identity_no || "",
        })
      } catch (caught) {
        if (isMounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load profile")
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void loadProfile()
    return () => {
      isMounted = false
    }
  }, [router])

  const identityLabel = useMemo(
    () => identityNumberLabel(form.nationality),
    [form.nationality]
  )
  const isApplicant = session?.role === "applicant"
  const displayName =
    `${form.first_name} ${form.last_name}`.trim() || form.username || "Portal User"
  const initials =
    displayName
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join("") || "PU"

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isApplicant) return

    setMessage("")
    setError("")
    setIsSaving(true)
    try {
      const applicant = await updateApplyProfile({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone.trim(),
        nationality: form.nationality,
        country_of_residence: form.country_of_residence,
        passport_or_identity_no: form.passport_or_identity_no.trim(),
      })
      setForm({
        username: applicant.username || "",
        email: applicant.email || "",
        first_name: applicant.first_name || "",
        last_name: applicant.last_name || "",
        phone: applicant.phone || "",
        nationality: applicant.nationality || "",
        country_of_residence: applicant.country_of_residence || "",
        passport_or_identity_no: applicant.passport_or_identity_no || "",
      })
      setMessage("Profile updated.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update profile")
    } finally {
      setIsSaving(false)
    }
  }

  function selectPicture(file: File | null) {
    setMessage("")
    setError("")
    if (!file) {
      setPictureFile(null)
      return
    }
    if (file.type && !file.type.startsWith("image/")) {
      setError("Choose a valid image file.")
      return
    }
    const extension = fileExtension(file.name)
    if (!ALLOWED_IMAGE_EXTENSIONS.includes(extension)) {
      setError("Choose a jpg, jpeg, png, webp, heic, or heif image.")
      return
    }
    if (file.size > MAX_PROFILE_PICTURE_SIZE) {
      setError("Profile picture must be 5 MB or smaller.")
      return
    }
    setPictureFile(file)
  }

  async function handlePictureUpload() {
    if (!pictureFile) return
    setMessage("")
    setError("")
    setIsUploadingPicture(true)
    try {
      const user = await updateProfilePicture(pictureFile)
      setSession((current) => (current ? { ...current, user } : current))
      setPictureFile(null)
      setMessage("Profile picture updated.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update profile picture")
    } finally {
      setIsUploadingPicture(false)
    }
  }

  async function handlePasswordChange(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPasswordMessage("")
    setPasswordError("")

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.")
      return
    }
    if (
      newPassword.length > MAX_PASSWORD_LENGTH ||
      confirmPassword.length > MAX_PASSWORD_LENGTH
    ) {
      setPasswordError(`New password must be ${MAX_PASSWORD_LENGTH} characters or fewer.`)
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirm password do not match.")
      return
    }

    setIsChangingPassword(true)
    try {
      const response = await changePasswordRequest(
        oldPassword,
        newPassword,
        confirmPassword
      )
      setOldPassword("")
      setNewPassword("")
      setConfirmPassword("")
      setPasswordMessage(response.detail || "Password changed successfully.")
    } catch (caught) {
      setPasswordError(
        caught instanceof Error ? caught.message : "Unable to change password"
      )
    } finally {
      setIsChangingPassword(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Profile</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Review your portal account details and manage your account security.
          </p>
        </section>

        {message ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700">
            {message}
          </div>
        ) : null}
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
            {error}
          </div>
        ) : null}

        <Card className="max-w-4xl border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle>Profile Picture</CardTitle>
            <CardDescription>
              Upload an image up to 5 MB. This picture is shared across your portal role.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <Avatar className="size-24">
              <AvatarImage
                src={profilePictureUrl(session?.user.profile_picture)}
                alt={displayName}
              />
              <AvatarFallback className="text-xl">{initials}</AvatarFallback>
            </Avatar>
            <div className="space-y-3">
              <Label
                htmlFor="profile_picture"
                className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium shadow-xs hover:bg-accent hover:text-accent-foreground"
              >
                <Camera className="size-4" />
                Choose image
              </Label>
              <Input
                id="profile_picture"
                type="file"
                accept={IMAGE_ACCEPT}
                className="sr-only"
                onChange={(event) => selectPicture(event.target.files?.[0] ?? null)}
                disabled={isLoading || isUploadingPicture}
              />
              <p className="text-sm text-muted-foreground">
                {pictureFile ? pictureFile.name : "No new image selected."}
              </p>
              <Button
                type="button"
                onClick={handlePictureUpload}
                disabled={!pictureFile || isLoading || isUploadingPicture}
              >
                <Upload className="size-4" />
                {isUploadingPicture ? "Uploading..." : "Upload Picture"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="max-w-4xl border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle>Portal Account</CardTitle>
            <CardDescription>
              Username and email address are locked for account security.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input id="username" value={form.username} disabled readOnly />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <Input id="email" type="email" value={form.email} disabled readOnly />
              </div>
              <div className="space-y-2">
                <Label htmlFor="first_name">First name</Label>
                <Input
                  id="first_name"
                  value={form.first_name}
                  onChange={(event) => updateField("first_name", event.target.value)}
                  disabled={!isApplicant || isLoading}
                  required={isApplicant}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last name</Label>
                <Input
                  id="last_name"
                  value={form.last_name}
                  onChange={(event) => updateField("last_name", event.target.value)}
                  disabled={!isApplicant || isLoading}
                  required={isApplicant}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={form.phone}
                  onChange={(event) => updateField("phone", event.target.value)}
                  disabled={!isApplicant || isLoading}
                  required={isApplicant}
                />
              </div>
              {isApplicant ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="nationality">Nationality</Label>
                    <select
                      id="nationality"
                      className={selectClass}
                      value={form.nationality}
                      onChange={(event) => {
                        updateField("nationality", event.target.value)
                        updateField("passport_or_identity_no", "")
                      }}
                      disabled={isLoading}
                      required
                    >
                      <option value="">Select nationality</option>
                      {countries.map((country) => (
                        <option key={country.value} value={country.value}>
                          {country.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="country_of_residence">Country of residence</Label>
                    <select
                      id="country_of_residence"
                      className={selectClass}
                      value={form.country_of_residence}
                      onChange={(event) => updateField("country_of_residence", event.target.value)}
                      disabled={isLoading}
                      required
                    >
                      <option value="">Select country</option>
                      {countries.map((country) => (
                        <option key={country.value} value={country.value}>
                          {country.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {form.nationality ? (
                    <div className="space-y-2">
                      <Label htmlFor="passport_or_identity_no">{identityLabel}</Label>
                      <Input
                        id="passport_or_identity_no"
                        value={form.passport_or_identity_no}
                        onChange={(event) =>
                          updateField("passport_or_identity_no", event.target.value)
                        }
                        disabled={isLoading}
                        required
                      />
                    </div>
                  ) : null}
                  <div className="flex items-end">
                    <Button type="submit" disabled={isSaving || isLoading}>
                      <Save className="size-4" />
                      {isSaving ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="rounded-lg border border-border bg-muted/35 p-3 text-sm text-muted-foreground sm:col-span-2">
                  Profile changes for this role are managed by an administrator.
                </div>
              )}
            </form>
          </CardContent>
        </Card>

        <Card className="max-w-4xl border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="size-5" />
              Change Password
            </CardTitle>
            <CardDescription>
              Enter your current password before choosing a new one.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 sm:grid-cols-2" onSubmit={handlePasswordChange}>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="old_password">Current password</Label>
                <Input
                  id="old_password"
                  type="password"
                  autoComplete="current-password"
                  value={oldPassword}
                  onChange={(event) => setOldPassword(event.target.value)}
                  disabled={isLoading || isChangingPassword}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new_password">New password</Label>
                <Input
                  id="new_password"
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  maxLength={MAX_PASSWORD_LENGTH}
                  disabled={isLoading || isChangingPassword}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm new password</Label>
                <Input
                  id="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  maxLength={MAX_PASSWORD_LENGTH}
                  disabled={isLoading || isChangingPassword}
                  required
                />
              </div>

              {passwordMessage ? (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700 sm:col-span-2">
                  {passwordMessage}
                </div>
              ) : null}
              {passwordError ? (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700 sm:col-span-2">
                  {passwordError}
                </div>
              ) : null}

              <div className="flex flex-col gap-3 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Cannot remember your current password?{" "}
                  <Link className="font-medium text-foreground underline" href="/forgot-password">
                    Use forgot password
                  </Link>
                </p>
                <Button type="submit" disabled={isLoading || isChangingPassword}>
                  <KeyRound className="size-4" />
                  {isChangingPassword ? "Changing..." : "Change Password"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
