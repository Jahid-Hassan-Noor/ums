import Link from "next/link"
import { AlertTriangle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  isOptionalFeatureKey,
  loadPublicUmsSettings,
  umsModuleLabels,
  type OptionalFeatureKey,
} from "@/lib/ums-settings"

type ModuleUnavailableSearchParams = {
  modules?: string | string[]
  next?: string | string[]
}

function firstParam(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value
}

function safePath(value: string | undefined) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return ""
  return value
}

function moduleKeys(value: string | undefined): OptionalFeatureKey[] {
  return Array.from(
    new Set(
      String(value ?? "")
        .split(",")
        .map((item) => item.trim())
        .filter(isOptionalFeatureKey)
    )
  )
}

function formatList(values: string[], locale: string) {
  if (values.length <= 1) return values[0] ?? ""
  try {
    return new Intl.ListFormat(locale || "en-US", {
      style: "long",
      type: "conjunction",
    }).format(values)
  } catch {
    return values.join(", ")
  }
}

export default async function ModuleUnavailablePage({
  searchParams,
}: {
  searchParams: Promise<ModuleUnavailableSearchParams>
}) {
  const params = await searchParams
  const settings = await loadPublicUmsSettings()
  const requestedPath = safePath(firstParam(params.next))
  const labels = umsModuleLabels(
    moduleKeys(firstParam(params.modules)),
    settings
  )
  const moduleLabel = formatList(labels, settings.localization.locale)
  const subject = moduleLabel || "This module"
  const remainingSetupItems = Math.max(
    settings.setup.total - settings.setup.completed,
    0
  )

  return (
    <main className="flex min-h-svh items-center justify-center bg-muted/25 px-4 py-10">
      <Card className="w-full max-w-2xl border-border/70 bg-card/95 shadow-sm">
        <CardHeader className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex size-11 items-center justify-center rounded-xl border border-border bg-muted/60 text-muted-foreground">
              <AlertTriangle aria-hidden="true" />
            </span>
            <Badge variant="outline">Unavailable</Badge>
          </div>
          <div className="flex flex-col gap-2">
            <CardTitle className="text-2xl">Module unavailable</CardTitle>
            <CardDescription className="text-sm leading-6">
              {subject} is not enabled for this institution or is not assigned
              to your role. The portal is hiding this route so users only see
              configured services.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 text-sm text-muted-foreground">
          {requestedPath ? (
            <div className="rounded-lg border border-border bg-background px-3 py-2">
              <span className="font-medium text-foreground">Requested route:</span>{" "}
              <code>{requestedPath}</code>
            </div>
          ) : null}
          {!settings.setup.complete && settings.setup.total ? (
            <div className="rounded-lg border border-border bg-background px-3 py-2">
              Institution setup still has {remainingSetupItems} required{" "}
              {remainingSetupItems === 1 ? "item" : "items"} remaining. An
              administrator can finish setup from portal settings.
            </div>
          ) : null}
        </CardContent>
        <CardFooter className="flex flex-wrap gap-2">
          <Button render={<Link href="/login" />}>Open Portal Login</Button>
          <Button variant="outline" render={<Link href="/" />}>
            Go Home
          </Button>
          {settings.general.support_email ? (
            <Button
              variant="ghost"
              render={<Link href={`mailto:${settings.general.support_email}`} />}
            >
              Contact Support
            </Button>
          ) : null}
        </CardFooter>
      </Card>
    </main>
  )
}
