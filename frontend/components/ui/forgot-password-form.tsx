"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import ErrorModal from "@/components/modals/error-modal"
import InfoModal from "@/components/modals/info-modal"
import SuccessModal from "@/components/modals/success-modal"
import WarningModal from "@/components/modals/warning-modal"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { forgotPasswordRequest } from "@/lib/auth"
import { cn } from "@/lib/utils"

export function ForgotPasswordForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter()

  const [email, setEmail] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [errorMessage, setErrorMessage] = useState("")
  const [isErrorOpen, setIsErrorOpen] = useState(false)

  const [isInfoOpen, setIsInfoOpen] = useState(false)
  const [warningMessage, setWarningMessage] = useState("")
  const [isWarningOpen, setIsWarningOpen] = useState(false)

  const [successMessage, setSuccessMessage] = useState("")
  const [isSuccessOpen, setIsSuccessOpen] = useState(false)
  const [debugResetLink, setDebugResetLink] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!email.trim()) {
      setWarningMessage("Please provide your email address.")
      setIsWarningOpen(true)
      return
    }

    try {
      setIsSubmitting(true)
      const response = await forgotPasswordRequest(email.trim())
      const debugText =
        response.debug && !response.debug.email_sent
          ? ` ${response.debug.reason}`
          : ""
      setSuccessMessage(
        (response.detail || "Verification link has been sent.") + debugText
      )
      setDebugResetLink(response.reset_link ?? null)
      setIsSuccessOpen(true)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to send verification link"
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
                  <h1 className="font-display text-3xl font-semibold">Forgot password</h1>
                  <p className="text-muted-foreground">
                    Enter your account email and we will send a reset link.
                  </p>
                </div>

                <Field>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@x.aiu.edu.my"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </Field>

                <Field>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-amber-500 text-white hover:bg-amber-400"
                  >
                    {isSubmitting ? "Sending..." : "Send reset link"}
                  </Button>
                </Field>

                <FieldDescription className="text-center">
                  Remembered it? <Link href="/login">Back to login</Link>
                </FieldDescription>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      </div>

      <ErrorModal
        open={isErrorOpen}
        onOpenChange={setIsErrorOpen}
        message={errorMessage || "Unable to send verification link."}
      />

      <InfoModal
        open={isInfoOpen}
        onOpenChange={setIsInfoOpen}
        message="Check your spam folder if you do not receive the email in a few minutes."
      />

      <WarningModal
        open={isWarningOpen}
        onOpenChange={setIsWarningOpen}
        message={warningMessage || "Please review your input."}
      />

      <SuccessModal
        open={isSuccessOpen}
        onOpenChange={setIsSuccessOpen}
        title="Verification link sent"
        message={successMessage || "Please check your email for the verification link."}
        actionLabel={debugResetLink ? "Open reset page" : "Go to login"}
        onAction={() => {
          if (debugResetLink) {
            try {
              const target = new URL(debugResetLink)
              router.replace(`${target.pathname}${target.search}`)
              return
            } catch {
              router.replace(debugResetLink)
              return
            }
          }
          router.replace("/login")
        }}
      />
    </>
  )
}

export default ForgotPasswordForm
