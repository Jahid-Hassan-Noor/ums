"use client"

import Image from "next/image"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useMemo, useState } from "react"
import ErrorModal from "@/components/modals/error-modal"
import InfoModal from "@/components/modals/info-modal"
import SuccessModal from "@/components/modals/success-modal"
import WarningModal from "@/components/modals/warning-modal"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldSeparator,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  canAccessRole,
  defaultRouteForRole,
  getRequiredRole,
  loginRequest,
  type UserRole,
} from "@/lib/auth"
import { cn } from "@/lib/utils"

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const nextPath = searchParams.get("next")

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [errorMessage, setErrorMessage] = useState("")
  const [isErrorOpen, setIsErrorOpen] = useState(false)

  const [infoMessage, setInfoMessage] = useState("")
  const [isInfoOpen, setIsInfoOpen] = useState(false)

  const [warningMessage, setWarningMessage] = useState("")
  const [isWarningOpen, setIsWarningOpen] = useState(false)

  const [isSuccessOpen, setIsSuccessOpen] = useState(false)
  const [loggedInRole, setLoggedInRole] = useState<UserRole>("student")

  const redirectTarget = useMemo(() => {
    if (!nextPath || !nextPath.startsWith("/")) {
      return defaultRouteForRole(loggedInRole)
    }

    const requiredRole = getRequiredRole(nextPath)
    if (!requiredRole || canAccessRole(loggedInRole, requiredRole)) {
      return nextPath
    }

    return defaultRouteForRole(loggedInRole)
  }, [loggedInRole, nextPath])

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!username.trim() || !password.trim()) {
      setWarningMessage("Please enter both username and password.")
      setIsWarningOpen(true)
      return
    }

    try {
      setIsSubmitting(true)
      const session = await loginRequest(username.trim(), password)
      setLoggedInRole(session.role)
      setIsSuccessOpen(true)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to login"
      setErrorMessage(message)
      setIsErrorOpen(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <div className={cn("flex flex-col gap-6", className)} {...props}>
        <Card className="overflow-hidden border-slate-200/70 bg-white/90 p-0 backdrop-blur dark:border-slate-700 dark:bg-slate-950/75">
          <CardContent className="grid p-0 md:grid-cols-2">
            <form className="p-6 md:p-8" onSubmit={handleSubmit}>
              <FieldGroup>
                <div className="flex flex-col items-center gap-2 text-center">
                  <h1 className="font-display text-2xl font-semibold">Welcome back</h1>
                  <p className="text-muted-foreground text-balance">
                    Login to your university portal account
                  </p>
                </div>
                <Field>
                  <FieldLabel htmlFor="username">Username</FieldLabel>
                  <Input
                    id="username"
                    type="text"
                    placeholder="Your username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    required
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </Field>
                <Field>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Logging in..." : "Login"}
                  </Button>
                </Field>
                <FieldDescription className="text-center">
                  <Link href="/forgot-password">Forgot password?</Link>
                </FieldDescription>
                <FieldSeparator className="*:data-[slot=field-separator-content]:bg-card">
                  Or continue with
                </FieldSeparator>
                <Field className="justify-center">
                  <Button
                    variant="outline"
                    type="button"
                    onClick={() => {
                      setInfoMessage("Social login will be available soon.")
                      setIsInfoOpen(true)
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                      <path
                        d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                        fill="currentColor"
                      />
                    </svg>
                    <span className="sr-only">Login with Google</span>
                  </Button>
                </Field>
                <FieldDescription className="text-center">
                  Want to apply? <Link href="/apply/register">Create an applicant account now</Link>.
                </FieldDescription>
              </FieldGroup>
            </form>
            <div className="bg-muted relative hidden md:block">
              <Image
                src="/images/login_image.jpg"
                alt="Campus"
                fill
                loading="eager"
                sizes="(max-width: 768px) 0px, 50vw"
                className="absolute inset-0 h-full w-full object-cover dark:brightness-[0.7]"
              />
            </div>
          </CardContent>
        </Card>
        <FieldDescription className="px-6 text-center">
          By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
          and <a href="#">Privacy Policy</a>.
        </FieldDescription>
      </div>

      <ErrorModal
        open={isErrorOpen}
        onOpenChange={setIsErrorOpen}
        message={errorMessage || "Unable to login. Please try again."}
      />

      <InfoModal
        open={isInfoOpen}
        onOpenChange={setIsInfoOpen}
        message={infoMessage || "Information"}
      />

      <WarningModal
        open={isWarningOpen}
        onOpenChange={setIsWarningOpen}
        message={warningMessage || "Please review your input."}
      />

      <SuccessModal
        open={isSuccessOpen}
        onOpenChange={setIsSuccessOpen}
        title="Login successful"
        message="You are now authenticated."
        actionLabel="Continue"
        onAction={() => {
          router.replace(redirectTarget)
        }}
      />
    </>
  )
}
