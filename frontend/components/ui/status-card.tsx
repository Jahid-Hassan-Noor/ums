"use client"

import * as React from "react"
import { AlertTriangle, CheckCircle2, Info, XCircle, type LucideIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardFooter, CardHeader, CardDescription, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type StatusTone = "neutral" | "info" | "success" | "warning" | "error"

type StatusCardProps = {
  tone?: StatusTone
  title: string
  description?: string
  icon?: LucideIcon
  action?: React.ReactNode
  actionLabel?: string
  onAction?: () => void
  actionVariant?: "default" | "outline" | "secondary" | "ghost" | "destructive" | "link"
  className?: string
}

const toneConfig: Record<
  StatusTone,
  {
    icon: LucideIcon
    card: string
    iconWrap: string
    title: string
    description: string
  }
> = {
  neutral: {
    icon: Info,
    card: "border-border/70 bg-card/95",
    iconWrap: "bg-muted/70 text-muted-foreground",
    title: "text-foreground",
    description: "text-muted-foreground",
  },
  info: {
    icon: Info,
    card: "border-sky-200/70 bg-sky-50/70 dark:border-sky-900 dark:bg-sky-950/30",
    iconWrap: "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200",
    title: "text-sky-900 dark:text-sky-100",
    description: "text-sky-800/80 dark:text-sky-200/80",
  },
  success: {
    icon: CheckCircle2,
    card: "border-emerald-300/70 bg-emerald-50/80 dark:border-emerald-900 dark:bg-emerald-950/30",
    iconWrap: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200",
    title: "text-emerald-800 dark:text-emerald-100",
    description: "text-emerald-700/80 dark:text-emerald-200/80",
  },
  warning: {
    icon: AlertTriangle,
    card: "border-amber-300/70 bg-amber-50/80 dark:border-amber-900 dark:bg-amber-950/30",
    iconWrap: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
    title: "text-amber-800 dark:text-amber-100",
    description: "text-amber-700/80 dark:text-amber-200/80",
  },
  error: {
    icon: XCircle,
    card: "border-red-300/70 bg-red-50/80 dark:border-red-900 dark:bg-red-950/30",
    iconWrap: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200",
    title: "text-red-800 dark:text-red-100",
    description: "text-red-700/80 dark:text-red-200/80",
  },
}

export function StatusCard({
  tone = "neutral",
  title,
  description,
  icon,
  action,
  actionLabel,
  onAction,
  actionVariant = "outline",
  className,
}: StatusCardProps) {
  const cardRef = React.useRef<HTMLDivElement | null>(null)
  const config = toneConfig[tone]
  const Icon = icon ?? config.icon
  const actionNode =
    action ??
    (actionLabel ? (
      <Button variant={actionVariant} onClick={onAction}>
        {actionLabel}
      </Button>
    ) : null)

  React.useEffect(() => {
    if (tone === "neutral") return
    const handle = window.setTimeout(() => {
      cardRef.current?.scrollIntoView({ behavior: "smooth", block: "center" })
    }, 50)
    return () => window.clearTimeout(handle)
  }, [tone, title, description])

  return (
    <Card ref={cardRef} className={cn("shadow-sm", config.card, className)}>
      <CardHeader className="flex flex-row items-start gap-3">
        <span className={cn("inline-flex size-10 items-center justify-center rounded-xl", config.iconWrap)}>
          <Icon className="size-5" />
        </span>
        <div className="space-y-1">
          <CardTitle className={cn("text-base", config.title)}>{title}</CardTitle>
          {description ? (
            <CardDescription className={cn("text-sm", config.description)}>{description}</CardDescription>
          ) : null}
        </div>
      </CardHeader>
      {actionNode ? <CardFooter className="bg-transparent">{actionNode}</CardFooter> : null}
    </Card>
  )
}

export default StatusCard
