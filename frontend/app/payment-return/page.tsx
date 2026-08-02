"use client"

import Link from "next/link"
import { Suspense, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { CheckCircle2, Clock, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const SUBSCRIPTION_PATH_BY_ROLE: Record<string, string> = {
  accountant: "/accountant/my-subscriptions",
  admin: "/admin/subscriptions",
  caterer: "/caterer/subscriptions",
  executive: "/executive/subscriptions",
  hr: "/hr/subscriptions",
  librarian: "/librarian/subscriptions",
  student: "/student/subscriptions",
  teacher: "/teacher/subscriptions",
  technician: "/technician/subscriptions",
}

type SessionPayload = {
  role?: string
}

export default function PaymentReturnPage() {
  return (
    <Suspense fallback={null}>
      <PaymentReturnContent />
    </Suspense>
  )
}

function PaymentReturnContent() {
  const searchParams = useSearchParams()
  const status = searchParams.get("status") ?? "pending"
  const [returnHref, setReturnHref] = useState("/login")
  const [returnLabel, setReturnLabel] = useState("Go to Portal")
  const Icon = status === "success" ? CheckCircle2 : status === "failed" ? XCircle : Clock
  const title = status === "success" ? "Payment Successful" : status === "failed" ? "Payment Not Completed" : "Payment Processing"
  const description =
    status === "success"
      ? "Your subscription will appear as active after the gateway confirmation is processed."
      : status === "failed"
        ? "The payment was cancelled or failed. You can start a new checkout from your subscription page."
        : "The gateway has not confirmed the final payment status yet."

  useEffect(() => {
    let active = true

    async function resolveReturnPath() {
      try {
        const response = await fetch("/ums-auth/session", { cache: "no-store" })
        if (!response.ok) return
        const session = (await response.json()) as SessionPayload
        const path = session.role ? SUBSCRIPTION_PATH_BY_ROLE[session.role] : undefined
        if (active && path) {
          setReturnHref(path)
          setReturnLabel("Back to Subscriptions")
        }
      } catch {
        // Keep the login fallback when there is no readable portal session.
      }
    }

    void resolveReturnPath()

    return () => {
      active = false
    }
  }, [])

  return (
    <main className="flex min-h-svh items-center justify-center bg-muted/25 px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Icon className="size-5" /> {title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button render={<Link href={returnHref} />}>{returnLabel}</Button>
        </CardContent>
      </Card>
    </main>
  )
}
