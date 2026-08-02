"use client"

import dynamic from "next/dynamic"
import type { ComponentType, CSSProperties } from "react"

import {
  DEFAULT_UMS_LOADER_SIZE,
  DEFAULT_UMS_LOADER_SPINNER,
  normalizeUmsLoaderSize,
  normalizeUmsLoaderSpinner,
  type UmsLoaderSpinner,
} from "@/lib/loader-settings"

type LoaderComponentProps = {
  height?: string | number
  width?: string | number
  color?: string
  colors?: string[]
  dnaColorOne?: string
  dnaColorTwo?: string
  ariaLabel?: string
  wrapperStyle?: CSSProperties
  wrapperClass?: string
  visible?: boolean
}

type ReactLoaderModule = typeof import("react-loader-spinner")
type ReactLoaderExport = keyof ReactLoaderModule
type LoaderComponent = ComponentType<LoaderComponentProps>

function loaderComponent(exportName: ReactLoaderExport) {
  return dynamic<LoaderComponentProps>(
    () =>
      import("react-loader-spinner").then(
        (module) => module[exportName] as LoaderComponent
      ),
    { ssr: false }
  )
}

const LOADER_COMPONENTS: Record<UmsLoaderSpinner, LoaderComponent> = {
  audio: loaderComponent("Audio"),
  "ball-triangle": loaderComponent("BallTriangle"),
  bars: loaderComponent("Bars"),
  blocks: loaderComponent("Blocks"),
  "circles-with-bar": loaderComponent("CirclesWithBar"),
  circles: loaderComponent("Circles"),
  "circular-progress": loaderComponent("CircularProgress"),
  "color-ring": loaderComponent("ColorRing"),
  comment: loaderComponent("Comment"),
  discuss: loaderComponent("Discuss"),
  dna: loaderComponent("DNA"),
  "falling-lines": loaderComponent("FallingLines"),
  "fidget-spinner": loaderComponent("FidgetSpinner"),
  grid: loaderComponent("Grid"),
  hearts: loaderComponent("Hearts"),
  hourglass: loaderComponent("Hourglass"),
  "infinity-spin": loaderComponent("InfinitySpin"),
  "line-wave": loaderComponent("LineWave"),
  "magnifying-glass": loaderComponent("MagnifyingGlass"),
  "mutating-dots": loaderComponent("MutatingDots"),
  oval: loaderComponent("Oval"),
  "progress-bar": loaderComponent("ProgressBar"),
  puff: loaderComponent("Puff"),
  radio: loaderComponent("Radio"),
  "revolving-dot": loaderComponent("RevolvingDot"),
  rings: loaderComponent("Rings"),
  "rotating-lines": loaderComponent("RotatingLines"),
  "rotating-square": loaderComponent("RotatingSquare"),
  "rotating-triangles": loaderComponent("RotatingTriangles"),
  "tail-spin": loaderComponent("TailSpin"),
  "three-circles": loaderComponent("ThreeCircles"),
  "three-dots": loaderComponent("ThreeDots"),
  triangle: loaderComponent("Triangle"),
  vortex: loaderComponent("Vortex"),
  watch: loaderComponent("Watch"),
}

type ConfigurableLoaderProps = {
  spinner?: unknown
  size?: unknown
  color?: string
  className?: string
}

export function ConfigurableLoader({
  spinner = DEFAULT_UMS_LOADER_SPINNER,
  size = DEFAULT_UMS_LOADER_SIZE,
  color = "#4fa94d",
  className,
}: ConfigurableLoaderProps) {
  const normalizedSpinner = normalizeUmsLoaderSpinner(spinner)
  const normalizedSize = normalizeUmsLoaderSize(size)
  const Loader = LOADER_COMPONENTS[normalizedSpinner] ?? LOADER_COMPONENTS.dna
  const accentColors = [color, "#46dff0", "#e90c59", "#f59e0b", "#8b5cf6"]

  return (
    <Loader
      visible
      height={normalizedSize}
      width={normalizedSpinner === "progress-bar" ? normalizedSize * 1.8 : normalizedSize}
      color={color}
      colors={accentColors}
      dnaColorOne="rgba(233, 12, 89, 0.58)"
      dnaColorTwo="#46dff0"
      ariaLabel={`${normalizedSpinner}-loading`}
      wrapperClass={className}
    />
  )
}
