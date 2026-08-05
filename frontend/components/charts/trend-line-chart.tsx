"use client"

import { DataChart } from "@/components/charts/data-chart"
import { formatDateOnly } from "@/components/utils/format"

function defaultDateLabel(isoDate: string) {
  const [year, month, day] = isoDate.split("-").map(Number)
  if (!year || !month || !day) return isoDate
  const formatted = formatDateOnly(
    `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`,
    { formatOptions: { month: "short", day: "numeric" } }
  )
  return formatted === "N/A" ? isoDate : formatted
}

export function TrendLineChart({
  title,
  subtitle,
  labels,
  values,
  lineColor,
  startColor,
  endColor,
  gradientId,
  isDark,
  formatter,
  leftPadding = 52,
  xLabelFormatter = defaultDateLabel,
}: {
  title: string
  subtitle: string
  labels: string[]
  values: number[]
  lineColor: string
  startColor: string
  endColor: string
  gradientId: string
  isDark: boolean
  formatter: (value: number) => string
  leftPadding?: number
  xLabelFormatter?: (value: string) => string
}) {
  return (
    <DataChart
      type="line"
      title={title}
      subtitle={subtitle}
      labels={labels}
      values={values}
      lineColor={lineColor}
      startColor={startColor}
      endColor={endColor}
      gradientId={gradientId}
      isDark={isDark}
      formatter={formatter}
      leftPadding={leftPadding}
      xLabelFormatter={xLabelFormatter}
    />
  )
}
