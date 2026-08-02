"use client"

import { DataChart } from "@/components/charts/data-chart"

export function ValueBarChart({
  title,
  subtitle,
  labels,
  values,
  isDark,
  formatter,
  gradientId,
  startColor,
  endColor,
  totalLabel,
  peakLabel,
  leftPadding = 52,
}: {
  title: string
  subtitle: string
  labels: string[]
  values: number[]
  isDark: boolean
  formatter: (value: number) => string
  gradientId: string
  startColor: string
  endColor: string
  totalLabel: string
  peakLabel: string
  leftPadding?: number
}) {
  return (
    <DataChart
      type="bar"
      title={title}
      subtitle={subtitle}
      labels={labels}
      values={values}
      isDark={isDark}
      formatter={formatter}
      gradientId={gradientId}
      startColor={startColor}
      endColor={endColor}
      totalLabel={totalLabel}
      peakLabel={peakLabel}
      leftPadding={leftPadding}
    />
  )
}
