import { NextResponse, type NextRequest } from "next/server"

import {
  accessFromCookies,
  backendApiUrl,
  clearAuthCookies,
  refreshAccessToken,
  setAuthCookies,
  validateCsrfRequest,
  type CookieSession,
} from "@/lib/server-session"

type RouteContext = {
  params: Promise<{ path?: string[] }>
}

const hopByHopHeaders = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "cookie",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
])

async function resolvePath(context: RouteContext) {
  const params = await context.params
  return `/${(params.path ?? []).join("/")}`
}

function targetUrl(request: NextRequest, backendPath: string) {
  const url = new URL(`${backendApiUrl}${backendPath}`)
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.append(key, value)
  })
  return url
}

function requestHeaders(request: NextRequest, accessToken: string) {
  const headers = new Headers(request.headers)
  hopByHopHeaders.forEach((header) => headers.delete(header))
  headers.set("Authorization", `Bearer ${accessToken}`)
  return headers
}

function responseHeaders(response: Response) {
  const headers = new Headers()
  response.headers.forEach((value, key) => {
    if (!hopByHopHeaders.has(key.toLowerCase())) {
      headers.set(key, value)
    }
  })
  return headers
}

async function forwardRequest(
  request: NextRequest,
  url: URL,
  session: CookieSession,
  body: ArrayBuffer | undefined
) {
  return fetch(url, {
    method: request.method,
    headers: requestHeaders(request, session.access),
    body,
    cache: "no-store",
  })
}

async function proxyRequest(request: NextRequest, context: RouteContext) {
  if (!validateCsrfRequest(request)) {
    return NextResponse.json(
      { detail: "Invalid CSRF token." },
      { status: 403 }
    )
  }

  let session = await accessFromCookies(request)
  if (!session) {
    const response = NextResponse.json(
      { detail: "Session expired. Please login again." },
      { status: 401 }
    )
    if (!request.cookies.get("ums_refresh")?.value) {
      clearAuthCookies(response, request)
    }
    return response
  }

  const backendPath = await resolvePath(context)
  const url = targetUrl(request, backendPath)
  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer()

  let backendResponse = await forwardRequest(request, url, session, body)

  if (backendResponse.status === 401 && session.refresh && !session.refreshedAccess) {
    const refreshed = await refreshAccessToken(session.refresh)
    if (refreshed) {
      session = {
        access: refreshed.access,
        refresh: refreshed.refresh,
        refreshedAccess: refreshed.access,
      }
      backendResponse = await forwardRequest(request, url, session, body)
    }
  }

  const response = new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders(backendResponse),
  })

  if (session.refreshedAccess) {
    setAuthCookies(response, request, {
      access: session.refreshedAccess,
      refresh: session.refresh,
    })
  }

  if (backendResponse.status === 401) {
    if (!request.cookies.get("ums_refresh")?.value) {
      clearAuthCookies(response, request)
    }
  }

  return response
}

export const GET = proxyRequest
export const POST = proxyRequest
export const PUT = proxyRequest
export const PATCH = proxyRequest
export const DELETE = proxyRequest
