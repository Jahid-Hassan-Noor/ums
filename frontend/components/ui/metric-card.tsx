import type { ComponentType, ReactNode } from "react"

import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type MetricCardProps = {
  title: string
  value: ReactNode
  subtitle: ReactNode
  icon: ComponentType<{ className?: string }>
  className?: string
  valueClassName?: string
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  className,
  valueClassName,
}: MetricCardProps) {
  return (
    <Card className={cn("border-border/70 bg-card/95 shadow-sm", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardDescription className="text-muted-foreground text-sm font-medium">{title}</CardDescription>
          <span className="text-muted-foreground bg-muted/50 border-border rounded-lg border p-2">
            <Icon className="size-5" />
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-1">
        <div className={cn("text-foreground text-2xl font-semibold tracking-tight", valueClassName)}>{value}</div>
        <p className="text-muted-foreground text-xs">{subtitle}</p>
      </CardContent>
    </Card>
  )
}
