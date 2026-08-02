"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useMemo, useState } from "react"
import ErrorModal from "@/components/modals/error-modal"
import InfoModal from "@/components/modals/info-modal"
import SuccessModal from "@/components/modals/success-modal"
import WarningModal from "@/components/modals/warning-modal"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { resetPasswordRequest } from "@/lib/auth"
import { cn } from "@/lib/utils"

const MAX_PASSWORD_LENGTH = 20

export function ResetPasswordForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const token = useMemo(() => (searchParams.get("token") ?? "").trim(), [searchParams])

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [errorMessage, setErrorMessage] = useState("")
  const [isErrorOpen, setIsErrorOpen] = useState(false)

  const [isInfoOpen, setIsInfoOpen] = useState(false)

  const [warningMessage, setWarningMessage] = useState("")
  const [isWarningOpen, setIsWarningOpen] = useState(false)

  const [successMessage, setSuccessMessage] = useState("")
  const [isSuccessOpen, setIsSuccessOpen] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!token) {
      setErrorMessage("Missing reset token. Please open the reset link from your email.")
      setIsErrorOpen(true)
      return
    }

    if (!password || !confirmPassword) {
      setWarningMessage("Please fill both password fields.")
      setIsWarningOpen(true)
      return
    }

    if (password.length < 8) {
      setWarningMessage("Password must be at least 8 characters long.")
      setIsWarningOpen(true)
      return
    }

    if (
      password.length > MAX_PASSWORD_LENGTH ||
      confirmPassword.length > MAX_PASSWORD_LENGTH
    ) {
      setWarningMessage(`Password must be ${MAX_PASSWORD_LENGTH} characters or fewer.`)
      setIsWarningOpen(true)
      return
    }

    if (password !== confirmPassword) {
      setWarningMessage("Password and confirm password do not match.")
      setIsWarningOpen(true)
      return
    }

    try {
      setIsSubmitting(true)
      const response = await resetPasswordRequest(token, password, confirmPassword)
      setSuccessMessage(response.detail || "Password reset successful.")
      setIsSuccessOpen(true)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to reset password"
      setErrorMessage(message)
      setIsErrorOpen(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <div className={cn("flex flex-col gap-6", className)} {...props}>
        <Card className="border-slate-200/70 bg-white/90 backdrop-blur dark:border-slate-700 dark:bg-slate-950/75">
          <CardContent className="p-6 md:p-8">
            <form className="space-y-6" onSubmit={handleSubmit}>
              <FieldGroup>
                <div className="flex flex-col gap-2 text-center">
                  <h1 className="font-display text-3xl font-semibold">Reset password</h1>
                  <p className="text-muted-foreground">
                    Set a new password for your account.
                  </p>
                </div>

                <Field>
                  <FieldLabel htmlFor="password">New password</FieldLabel>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter new password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    maxLength={MAX_PASSWORD_LENGTH}
                    required
                  />
                </Field>

                <Field>
                  <div className="flex items-center justify-between">
                    <FieldLabel htmlFor="confirm_password">Confirm password</FieldLabel>
                    <button
                      type="button"
                      onClick={() => setIsInfoOpen(true)}
                      className="text-xs underline-offset-2 hover:underline"
                    >
                      Password tips
                    </button>
                  </div>
                  <Input
                    id="confirm_password"
                    type="password"
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    maxLength={MAX_PASSWORD_LENGTH}
                    required
                  />
                </Field>

                <Field>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-emerald-600 text-white hover:bg-emerald-500"
                  >
                    {isSubmitting ? "Updating..." : "Update password"}
                  </Button>
                </Field>

                <FieldDescription className="text-center">
                  Back to <Link href="/login">login</Link>
                </FieldDescription>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      </div>

      <ErrorModal
        open={isErrorOpen}
        onOpenChange={setIsErrorOpen}
        message={errorMessage || "Unable to reset password."}
      />

      <InfoModal
        open={isInfoOpen}
        onOpenChange={setIsInfoOpen}
        title="Password tips"
        message="Use at least 8 characters and avoid common words or personal information."
      />

      <WarningModal
        open={isWarningOpen}
        onOpenChange={setIsWarningOpen}
        message={warningMessage || "Please review your input."}
      />

      <SuccessModal
        open={isSuccessOpen}
        onOpenChange={setIsSuccessOpen}
        title="Password updated"
        message={successMessage || "Your password has been updated successfully."}
        actionLabel="Go to login"
        onAction={() => {
          router.replace("/login")
        }}
      />
    </>
  )
}

export default ResetPasswordForm
