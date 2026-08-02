export type ChartPadding = {
  top: number
  right: number
  bottom: number
  left: number
}

export function valuesTotal(values: number[]) {
  return values.reduce(
    (sum, value) => sum + (Number.isFinite(value) ? value : 0),
    0
  )
}

export function chartColors(isDark: boolean) {
  return {
    gridColor: isDark ? "rgba(148, 163, 184, 0.28)" : "#e2e8f0",
    axisTextColor: isDark ? "#cbd5e1" : "#64748b",
  }
}

export function chartDimensions(leftPadding = 52, variant: "bar" | "line") {
  const width = 740
  const height = 300
  const padding =
    variant === "bar"
      ? { top: 22, right: 18, bottom: 42, left: leftPadding }
      : { top: 24, right: 20, bottom: 40, left: leftPadding }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  return { width, height, padding, chartWidth, chartHeight }
}

export function yAxisGridLines({
  padding,
  chartWidth,
  chartHeight,
  maxValue,
  formatter,
  gridColor,
  axisTextColor,
}: {
  padding: ChartPadding
  chartWidth: number
  chartHeight: number
  maxValue: number
  formatter: (value: number) => string
  gridColor: string
  axisTextColor: string
}) {
  return Array.from({ length: 5 }, (_, idx) => {
    const y = padding.top + (idx / 4) * chartHeight
    const value = maxValue - (idx / 4) * maxValue
    return { idx, y, value, chartWidth, formatter, gridColor, axisTextColor }
  })
}
