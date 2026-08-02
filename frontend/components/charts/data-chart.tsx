"use client"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ChartStatCard } from "@/components/charts/chart-stat-card"
import {
  chartColors,
  chartDimensions,
  valuesTotal,
  yAxisGridLines,
} from "@/components/charts/chart-utils"

type Point = {
  x: number
  y: number
}

type CommonChartProps = {
  title: string
  subtitle: string
  labels: string[]
  values: number[]
  isDark: boolean
  formatter: (value: number) => string
  gradientId: string
  startColor: string
  endColor: string
  leftPadding?: number
}

type BarChartProps = CommonChartProps & {
  type: "bar"
  totalLabel: string
  peakLabel: string
}

type LineChartProps = CommonChartProps & {
  type: "line"
  lineColor: string
  xLabelFormatter: (value: string) => string
}

export type DataChartProps = BarChartProps | LineChartProps

function tickIndexes(length: number, desiredTicks = 6) {
  if (length <= desiredTicks) return Array.from({ length }, (_, idx) => idx)
  const last = length - 1
  const steps = desiredTicks - 1
  const indexes = new Set<number>()
  for (let idx = 0; idx < desiredTicks; idx += 1) {
    indexes.add(Math.round((idx * last) / steps))
  }
  return Array.from(indexes).sort((a, b) => a - b)
}

function createLinePath(points: Point[]) {
  if (!points.length) return ""
  return points
    .map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ")
}

function createAreaPath(points: Point[], baselineY: number) {
  if (!points.length) return ""
  const linePath = createLinePath(points)
  const first = points[0]
  const last = points[points.length - 1]
  return `${linePath} L ${last.x} ${baselineY} L ${first.x} ${baselineY} Z`
}

export function DataChart(props: DataChartProps) {
  const { width, height, padding, chartWidth, chartHeight } = chartDimensions(
    props.leftPadding,
    props.type
  )
  const maxValue = Math.max(1, ...props.values)
  const { gridColor, axisTextColor } = chartColors(props.isDark)
  const total = valuesTotal(props.values)
  const peak = Math.max(...props.values, 0)

  const linePoints =
    props.type === "line"
      ? props.values.map((value, idx) => {
          const x =
            padding.left +
            (idx / Math.max(props.values.length - 1, 1)) * chartWidth
          const y = padding.top + (1 - value / maxValue) * chartHeight
          return { x, y }
        })
      : []
  const linePath = createLinePath(linePoints)
  const areaPath = createAreaPath(linePoints, padding.top + chartHeight)
  const xTicks =
    props.type === "line" ? tickIndexes(props.labels.length, 6) : []
  const average = props.values.length ? total / props.values.length : 0
  const slotWidth = chartWidth / Math.max(props.labels.length, 1)
  const barWidth = Math.min(30, slotWidth * 0.58)

  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader className="space-y-1 pb-2">
        <CardTitle className="text-base text-foreground">
          {props.title}
        </CardTitle>
        <CardDescription className="text-sm text-muted-foreground">
          {props.subtitle}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-x-auto">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="h-72 min-w-[680px]"
          >
            <defs>
              <linearGradient id={props.gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor={props.startColor}
                  stopOpacity={props.type === "line" ? "0.38" : "0.95"}
                />
                <stop
                  offset="100%"
                  stopColor={props.endColor}
                  stopOpacity={props.type === "line" ? "0.02" : "0.5"}
                />
              </linearGradient>
            </defs>
            {yAxisGridLines({
              padding,
              chartWidth,
              chartHeight,
              maxValue,
              formatter: props.formatter,
              gridColor,
              axisTextColor,
            }).map((line) => (
              <g key={line.idx}>
                <line
                  x1={padding.left}
                  y1={line.y}
                  x2={padding.left + chartWidth}
                  y2={line.y}
                  stroke={line.gridColor}
                  strokeWidth="1"
                  strokeDasharray="4 8"
                />
                <text
                  x={8}
                  y={line.y + 4}
                  fill={line.axisTextColor}
                  fontSize="11"
                >
                  {line.formatter(line.value)}
                </text>
              </g>
            ))}
            {props.type === "bar"
              ? props.values.map((value, idx) => {
                  const x =
                    padding.left + idx * slotWidth + (slotWidth - barWidth) / 2
                  const barHeight = (value / maxValue) * chartHeight
                  const y = padding.top + chartHeight - barHeight
                  const duration = `${0.5 + idx * 0.06}s`
                  return (
                    <g key={`${props.labels[idx] ?? idx}-${value}`}>
                      <rect
                        x={x}
                        y={y}
                        width={barWidth}
                        height={barHeight}
                        rx="8"
                        fill={`url(#${props.gradientId})`}
                        opacity="0.95"
                      >
                        <animate
                          attributeName="y"
                          from={padding.top + chartHeight}
                          to={y}
                          dur={duration}
                          calcMode="spline"
                          keySplines="0.22 0.61 0.36 1"
                          fill="freeze"
                        />
                        <animate
                          attributeName="height"
                          from="0"
                          to={barHeight}
                          dur={duration}
                          calcMode="spline"
                          keySplines="0.22 0.61 0.36 1"
                          fill="freeze"
                        />
                        <animate
                          attributeName="opacity"
                          from="0.45"
                          to="0.95"
                          dur={duration}
                          fill="freeze"
                        />
                      </rect>
                      <text
                        x={x + barWidth / 2}
                        y={height - 12}
                        fill={axisTextColor}
                        fontSize="11"
                        textAnchor="middle"
                      >
                        {props.labels[idx]}
                      </text>
                    </g>
                  )
                })
              : null}
            {props.type === "line" && areaPath ? (
              <path d={areaPath} fill={`url(#${props.gradientId})`} />
            ) : null}
            {props.type === "line" && linePath ? (
              <path
                d={linePath}
                fill="none"
                stroke={props.lineColor}
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ) : null}
            {props.type === "line"
              ? linePoints.map((point, idx) => {
                  const isEdge = idx === 0 || idx === linePoints.length - 1
                  if (!isEdge && idx % 6 !== 0) return null
                  return (
                    <circle
                      key={idx}
                      cx={point.x}
                      cy={point.y}
                      r="4"
                      fill={props.lineColor}
                    />
                  )
                })
              : null}
            {props.type === "line"
              ? xTicks.map((idx) => {
                  const x =
                    padding.left +
                    (idx / Math.max(props.labels.length - 1, 1)) * chartWidth
                  return (
                    <text
                      key={idx}
                      x={x}
                      y={height - 12}
                      fill={axisTextColor}
                      fontSize="11"
                      textAnchor="middle"
                    >
                      {props.xLabelFormatter(props.labels[idx] ?? "")}
                    </text>
                  )
                })
              : null}
          </svg>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <ChartStatCard
            label={props.type === "bar" ? props.totalLabel : "Range Total"}
            value={props.formatter(total)}
          />
          <ChartStatCard
            label={props.type === "bar" ? props.peakLabel : "Daily Average"}
            value={props.formatter(props.type === "bar" ? peak : average)}
          />
        </div>
      </CardContent>
    </Card>
  )
}
