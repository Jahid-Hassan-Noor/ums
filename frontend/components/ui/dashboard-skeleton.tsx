import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type DashboardSkeletonProps = {
  metricCards: number
  chartCards: number
  summaryCards?: number
  metricGridClassName?: string
  summaryGridClassName?: string
  chartGridClassName?: string
  summaryCardHeightClassName?: string
}

export default function DashboardSkeleton({
  metricCards,
  chartCards,
  summaryCards = 0,
  metricGridClassName = "md:grid-cols-2 xl:grid-cols-6",
  summaryGridClassName = "xl:grid-cols-3",
  chartGridClassName = "xl:grid-cols-2",
  summaryCardHeightClassName = "h-40",
}: DashboardSkeletonProps) {
  return (
    <div className="space-y-6">
      <div className={cn("grid gap-4", metricGridClassName)}>
        {Array.from({ length: metricCards }, (_, idx) => (
          <Card key={idx} className="border-border/70 bg-card/90 shadow-sm">
            <CardHeader className="pb-2">
              <div className="bg-muted h-4 w-32 animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="bg-muted h-8 w-24 animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>

      {summaryCards ? (
        <div className={cn("grid gap-4", summaryGridClassName)}>
          {Array.from({ length: summaryCards }, (_, idx) => (
            <Card key={idx} className="border-border/70 bg-card/90 shadow-sm">
              <CardHeader className="pb-2">
                <div className="bg-muted h-5 w-40 animate-pulse rounded" />
              </CardHeader>
              <CardContent>
                <div className={cn("bg-muted/70 animate-pulse rounded-xl", summaryCardHeightClassName)} />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}

      <div className={cn("grid gap-6", chartGridClassName)}>
        {Array.from({ length: chartCards }, (_, idx) => (
          <Card key={idx} className="border-border/70 bg-card/90 shadow-sm">
            <CardHeader className="pb-2">
              <div className="bg-muted h-5 w-48 animate-pulse rounded" />
              <div className="bg-muted/70 h-4 w-64 animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="bg-muted/70 h-64 animate-pulse rounded-xl" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}