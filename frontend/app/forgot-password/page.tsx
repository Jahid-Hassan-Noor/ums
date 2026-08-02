import { AuthCornerHeader } from "@/components/layout/auth-corner-header"
import { ForgotPasswordForm } from "@/components/ui/forgot-password-form"

export default function ForgotPasswordPage() {
  return (
    <div className="relative min-h-svh bg-campus px-4 pb-4 pt-2 sm:px-6 sm:pb-6 sm:pt-2 md:px-10 md:pb-10 md:pt-3">
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-70 dark:opacity-40" />
      <div className="relative z-10 mx-auto flex min-h-[calc(100svh-2rem)] w-full max-w-xl flex-col md:min-h-[calc(100svh-5rem)]">
        <AuthCornerHeader />
        <div className="flex flex-1 items-center justify-center py-6">
          <ForgotPasswordForm className="w-full" />
        </div>
      </div>
    </div>
  )
}
