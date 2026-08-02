"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import { UserPlus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { applyRegister, loadApplyOptions, type ApplyOption } from "@/lib/apply"
import { identityNumberLabel } from "@/lib/countries"

const selectClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
const MAX_PASSWORD_LENGTH = 20

export default function ApplyRegisterPage() {
  const router = useRouter()
  const [countries, setCountries] = useState<ApplyOption[]>([])
  const [form, setForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: "",
    nationality: "",
    country_of_residence: "",
    passport_or_identity_no: "",
  })
  const [error, setError] = useState("")
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function loadCountries() {
      try {
        const options = await loadApplyOptions()
        if (isMounted) setCountries(options.countries)
      } catch (caught) {
        if (isMounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load country options")
        }
      } finally {
        if (isMounted) setIsLoadingOptions(false)
      }
    }

    void loadCountries()
    return () => {
      isMounted = false
    }
  }, [])

  const identityLabel = useMemo(
    () => identityNumberLabel(form.nationality),
    [form.nationality]
  )

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    if (!form.password || !form.confirm_password) {
      setError("Please fill both password fields.")
      return
    }
    if (
      form.password.length > MAX_PASSWORD_LENGTH ||
      form.confirm_password.length > MAX_PASSWORD_LENGTH
    ) {
      setError(`Password must be ${MAX_PASSWORD_LENGTH} characters or fewer.`)
      return
    }
    if (form.password !== form.confirm_password) {
      setError("Password and confirm password do not match.")
      return
    }
    setIsSubmitting(true)
    try {
      await applyRegister({
        username: form.username.trim(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirm_password,
        phone: form.phone.trim(),
        nationality: form.nationality,
        country_of_residence: form.country_of_residence,
        passport_or_identity_no: form.passport_or_identity_no.trim(),
      })
      router.replace("/apply/dashboard")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create account")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-svh bg-slate-50 px-4 py-8 dark:bg-slate-950">
      <div className="mx-auto w-full max-w-2xl">
        <Link href="/apply" className="text-sm font-semibold text-teal-700 dark:text-teal-300">
          AIU Apply
        </Link>
        <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-slate-900">
          <h1 className="font-display text-2xl font-semibold text-slate-950 dark:text-white">
            Create applicant account
          </h1>
          <form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                autoComplete="username"
                value={form.username}
                onChange={(event) => updateField("username", event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="first_name">First name</Label>
              <Input
                id="first_name"
                value={form.first_name}
                onChange={(event) => updateField("first_name", event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">Last name</Label>
              <Input
                id="last_name"
                value={form.last_name}
                onChange={(event) => updateField("last_name", event.target.value)}
                required
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={(event) => updateField("email", event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                value={form.password}
                onChange={(event) => updateField("password", event.target.value)}
                maxLength={MAX_PASSWORD_LENGTH}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm password</Label>
              <Input
                id="confirm_password"
                type="password"
                autoComplete="new-password"
                value={form.confirm_password}
                onChange={(event) => updateField("confirm_password", event.target.value)}
                maxLength={MAX_PASSWORD_LENGTH}
                required
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                type="tel"
                autoComplete="tel"
                value={form.phone}
                onChange={(event) => updateField("phone", event.target.value)}
                required
              />
            </div>
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
                disabled={isLoadingOptions}
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
                disabled={isLoadingOptions}
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
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="passport_or_identity_no">{identityLabel}</Label>
                <Input
                  id="passport_or_identity_no"
                  value={form.passport_or_identity_no}
                  onChange={(event) => updateField("passport_or_identity_no", event.target.value)}
                  required
                />
              </div>
            ) : null}
            {error ? <p className="text-sm font-medium text-red-600 sm:col-span-2">{error}</p> : null}
            <Button type="submit" className="sm:col-span-2" disabled={isSubmitting || isLoadingOptions}>
              <UserPlus className="size-4" />
              {isSubmitting ? "Creating account..." : "Create account"}
            </Button>
          </form>
          <p className="mt-5 text-center text-sm text-slate-600 dark:text-slate-300">
            Already registered?{" "}
            <Link href="/login?next=/apply/dashboard" className="font-semibold text-teal-700 dark:text-teal-300">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
