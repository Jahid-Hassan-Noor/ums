"use client"

import * as React from "react"
import { usePathname } from "next/navigation"

type BackendRouteResponse = {
  path: string
  endpoint: string
  ok: boolean
  status: number
  contentType: string
  data: unknown
  checkedAt: string
  error?: string
}

declare global {
  interface Window {
    __AIU_BACKEND_ROUTE_RESPONSE__?: BackendRouteResponse
  }
}

function normalizeApiPath(pathname: string) {
  if (["/admin", "/executive", "/student", "/teacher"].includes(pathname)) {
    return `/ums-auth/backend${pathname}`
  }

  const path = pathname === "/" ? "" : pathname.replace(/\/+$/, "")
  return `/ums-auth/backend${path || "/"}`
}

async function readResponseData(response: Response) {
  const contentType = response.headers.get("content-type") ?? ""
  const text = await response.text()

  if (!text) return null

  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(text)
    } catch {
      return text
    }
  }

  return text
}

export function BackendRouteConnector() {
  const pathname = usePathname()
  const [result, setResult] = React.useState<BackendRouteResponse | null>(null)

  React.useEffect(() => {
    const controller = new AbortController()
    const endpoint = normalizeApiPath(pathname)

    async function connectRoute() {
      try {
        const response = await fetch(endpoint, {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
          signal: controller.signal,
        })
        const data = await readResponseData(response)
        const nextResult: BackendRouteResponse = {
          path: pathname,
          endpoint,
          ok: response.ok,
          status: response.status,
          contentType: response.headers.get("content-type") ?? "",
          data,
          checkedAt: new Date().toISOString(),
        }

        window.__AIU_BACKEND_ROUTE_RESPONSE__ = nextResult
        window.dispatchEvent(
          new CustomEvent("ums:backend-route-response", {
            detail: nextResult,
          })
        )
        setResult(nextResult)
      } catch (error) {
        if (controller.signal.aborted) return

        const nextResult: BackendRouteResponse = {
          path: pathname,
          endpoint,
          ok: false,
          status: 0,
          contentType: "",
          data: null,
          checkedAt: new Date().toISOString(),
          error: error instanceof Error ? error.message : "Backend route request failed.",
        }

        window.__AIU_BACKEND_ROUTE_RESPONSE__ = nextResult
        window.dispatchEvent(
          new CustomEvent("ums:backend-route-response", {
            detail: nextResult,
          })
        )
        setResult(nextResult)
      }
    }

    connectRoute()

    return () => {
      controller.abort()
    }
  }, [pathname])

  return (
    <span
      aria-hidden="true"
      data-backend-route-connector=""
      data-backend-route-path={result?.path ?? pathname}
      data-backend-route-status={result?.status ?? "pending"}
      hidden
    />
  )
}
