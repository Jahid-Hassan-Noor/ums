import { NextResponse, type NextRequest } from "next/server"

import {
  SESSION_AUTH_ENDPOINTS,
  backendApiUrl,
  backendErrorResponse,
  clearAuthCookies,
  generateCsrfToken,
  sanitizeSessionPayload,
  sessionFromCookies,
  setAuthCookies,
  setCsrfCookie,
  type TokenSessionPayload,
} from "@/lib/server-session"

function safeJsonParse(text: string): unknown | null {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

export async function GET(request: NextRequest) {
  const session = await sessionFromCookies(request)

  if (!session?.access) {
    const response = NextResponse.json(
      { detail: "Session expired. Please login again." },
      { status: 401 }
    )
    if (!request.cookies.get("ums_refresh")?.value) {
      clearAuthCookies(response, request)
    }
    return response
  }

  const response = NextResponse.json({
    role: session.role,
    user: session.user,
  })
  setAuthCookies(response, request, {
    access: session.refreshedAccess,
    refresh: session.refreshedAccess ? session.refresh : undefined,
    user: session.user,
  })

  const csrfToken = generateCsrfToken()
  setCsrfCookie(response, request, csrfToken)

  return response
}

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => null)) as {
    endpoint?: string
    payload?: unknown
  } | null

  if (!body?.endpoint || !SESSION_AUTH_ENDPOINTS.has(body.endpoint)) {
    return NextResponse.json({ detail: "Unsupported auth endpoint." }, { status: 400 })
  }

  const backendResponse = await fetch(`${backendApiUrl}${body.endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body.payload ?? {}),
    cache: "no-store",
  })
  const text = await backendResponse.text()

  if (!backendResponse.ok) {
    return backendErrorResponse(backendResponse, text)
  }

  const payload = safeJsonParse(text) as Partial<TokenSessionPayload> | null
  if (!payload?.access || !payload.refresh || !payload.user) {
    return NextResponse.json(
      { detail: "Auth service returned an invalid session payload." },
      { status: 502 }
    )
  }

  const response = NextResponse.json(sanitizeSessionPayload(payload as TokenSessionPayload))
  setAuthCookies(response, request, payload as TokenSessionPayload)

  const csrfToken = generateCsrfToken()
  setCsrfCookie(response, request, csrfToken)

  return response
}

export async function DELETE(request: NextRequest) {
  const response = NextResponse.json({ ok: true })
  clearAuthCookies(response, request)
  return response
}
