import Link from "next/link"
import type { LucideIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { statusClassName } from "@/lib/status-utils"

export type ResultTab<View extends string> = {
  view: View
  label: string
  href: string
}

export function ResultTabsNav<View extends string>({
  tabs,
  active,
}: {
  tabs: ResultTab<View>[]
  active: View
}) {
  return (
    <nav className="flex gap-2 overflow-x-auto pb-1">
      {tabs.map((tab) => (
        <Link
          key={tab.view}
          href={tab.href}
          className={`inline-flex h-10 shrink-0 items-center rounded-lg border px-3 text-sm font-medium transition ${
            tab.view === active
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border bg-background hover:bg-muted"
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  )
}

export function ResultSummaryCards({
  cards,
}: {
  cards: Array<{ label: string; value: number | string; icon: LucideIcon }>
}) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <Card key={card.label} className="border-border/70 shadow-sm">
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm text-muted-foreground">{card.label}</p>
                <p className="mt-1 text-2xl font-semibold">{card.value}</p>
              </div>
              <Icon className="size-5 text-muted-foreground" />
            </CardContent>
          </Card>
        )
      })}
    </section>
  )
}

export function ResultBatchHeader({
  title,
  description,
  status,
  statusLabel,
}: {
  title: string
  description: string
  status: string
  statusLabel: string
}) {
  return (
    <CardHeader>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle className="text-lg">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <Badge variant="outline" className={statusClassName(status)}>
          {statusLabel}
        </Badge>
      </div>
    </CardHeader>
  )
}
