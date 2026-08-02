import { NextResponse, type NextRequest } from "next/server"

export const CSRF_COOKIE_NAME = "ums_csrf"

export const backendApiUrl = (
  process.env.BACKEND_API_URL ??
  process.env.NEXT_API_PROXY_TARGET ??
  "http://backend:8000"
).replace(/\/+$/, "")

export const SESSION_AUTH_ENDPOINTS = new Set([
  "/auth/login",
  "/applicant/auth/login",
  "/applicant/auth/register",
])

const roles = [
  "applicant",
  "student",
  "teacher",
  "executive",
  "librarian",
  "caterer",
  "technician",
  "accountant",
  "hr",
  "admin",
] as const

export type Role = (typeof roles)[number]

export type AuthUser = {
  id?: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  role?: string
  ums_id?: string | null
  phone_number?: string | null
  profile_picture?: string | null
  is_email_verified?: boolean
  is_account_banned?: boolean
  executive_scope?: {
    kind: "school" | "center" | null
    id: number | null
    code: string
    name: string
    academic_workflows: boolean
    unit_id?: number | null
    unit_name?: string
  } | null
}

export type TokenSessionPayload = {
  access: string
  refresh?: string
  user: AuthUser
  [key: string]: unknown
}

export type CookieSession = {
  access: string
  refresh?: string
  refreshedAccess?: string
}

type RefreshResult = { access: string; refresh: string } | null

export const UMS_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
const ACCESS_TOKEN_FALLBACK_SECONDS = 60 * 5
const REFRESH_DEDUPE_WINDOW_MS = 5000
const refreshRequests = new Map<string, Promise<RefreshResult>>()

function isRole(value: string | undefined): value is Role {
  return roles.includes(value as Role)
}

export function normalizeSessionRole(role: string | null | undefined): Role {
  return isRole(role ?? undefined) ? (role as Role) : "student"
}

export function normalizeSessionUser(user: AuthUser) {
  const role = normalizeSessionRole(user.role)
  return {
    role,
    user: user.role === role ? user : { ...user, role },
  }
}

function decodeJwtPayload(token: string): { exp?: number } | null {
  try {
    const payload = token.split(".")[1]
    if (!payload) return null

    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/")
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      "="
    )
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

function tokenMaxAge(token: string, fallbackSeconds: number) {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return fallbackSeconds
  return Math.max(1, payload.exp - Math.floor(Date.now() / 1000))
}

function isTokenExpired(token: string, skewSeconds = 15): boolean {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return true
  const now = Math.floor(Date.now() / 1000)
  return payload.exp <= now + skewSeconds
}

function cookieBase(request: NextRequest, maxAge: number) {
  return {
    path: "/",
    maxAge,
    sameSite: "lax" as const,
    secure: request.nextUrl.protocol === "https:",
    httpOnly: true,
  }
}

export function setAuthCookies(
  response: NextResponse,
  request: NextRequest,
  payload: {
    access?: string
    refresh?: string
    role?: Role
    user?: AuthUser
  }
) {
  if (payload.access) {
    response.cookies.set("ums_access", payload.access, {
      ...cookieBase(request, tokenMaxAge(payload.access, ACCESS_TOKEN_FALLBACK_SECONDS)),
    })
  }

  if (payload.refresh) {
    response.cookies.set("ums_refresh", payload.refresh, {
      ...cookieBase(request, tokenMaxAge(payload.refresh, UMS_SESSION_MAX_AGE_SECONDS)),
    })
  }

  const role = payload.user
    ? normalizeSessionRole(payload.user.role)
    : payload.role

  if (role) {
    response.cookies.set("ums_role", role, {
      ...cookieBase(request, UMS_SESSION_MAX_AGE_SECONDS),
    })
  }

  if (payload.user?.role === "executive") {
    const academicWorkflows =
      payload.user.executive_scope?.academic_workflows !== false
    response.cookies.set("ums_academic_workflows", academicWorkflows ? "1" : "0", {
      ...cookieBase(request, UMS_SESSION_MAX_AGE_SECONDS),
    })
  } else if (payload.user) {
    response.cookies.set("ums_academic_workflows", "", {
      ...cookieBase(request, 0),
    })
  }
}

export function clearAuthCookies(response: NextResponse, request: NextRequest) {
  const expired = cookieBase(request, 0)
  response.cookies.set("ums_access", "", expired)
  response.cookies.set("ums_refresh", "", expired)
  response.cookies.set("ums_role", "", expired)
  response.cookies.set("ums_academic_workflows", "", expired)
  response.cookies.set("ums_csrf", "", expired)
}

const CSRF_COOKIE = "ums_csrf"
const CSRF_HEADER = "x-csrf-token"
const CSRF_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"])
const CSRF_TRUSTED_ORIGIN_ENV_KEYS = [
  "FRONTEND_BASE_URL",
  "NEXT_PUBLIC_FRONTEND_BASE_URL",
  "NEXT_PUBLIC_SITE_URL",
  "NEXTAUTH_URL",
  "UMS_TRUSTED_ORIGINS",
  "DJANGO_CORS_ALLOWED_ORIGINS",
  "DJANGO_CSRF_TRUSTED_ORIGINS",
]
const LOCAL_DEVELOPMENT_ORIGINS = [
  "http://localhost:3000",
  "http://127.0.0.1:3000",
  "http://localhost:8080",
  "http://127.0.0.1:8080",
]

export function generateCsrfToken(): string {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
}

export function setCsrfCookie(
  response: NextResponse,
  request: NextRequest,
  token: string
) {
  response.cookies.set(CSRF_COOKIE, token, {
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
    sameSite: "lax",
    secure: request.nextUrl.protocol === "https:",
    httpOnly: false,
  })
}

function splitHeaderValues(value: string | null | undefined): string[] {
  return (value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizedOrigin(value: string): string | null {
  try {
    return new URL(value).origin.toLowerCase()
  } catch {
    return null
  }
}

function trustedCsrfOrigins(): Set<string> {
  const origins = new Set<string>()
  CSRF_TRUSTED_ORIGIN_ENV_KEYS.forEach((key) => {
    splitHeaderValues(process.env[key]).forEach((value) => {
      const origin = normalizedOrigin(value)
      if (origin) origins.add(origin)
    })
  })

  if (process.env.NODE_ENV !== "production") {
    LOCAL_DEVELOPMENT_ORIGINS.forEach((value) => {
      const origin = normalizedOrigin(value)
      if (origin) origins.add(origin)
    })
  }

  return origins
}

function requestHostCandidates(request: NextRequest): Set<string> {
  const hosts = new Set<string>()
  const forwardedPorts = splitHeaderValues(request.headers.get("x-forwarded-port"))

  const addHost = (value: string) => {
    const host = value.toLowerCase()
    hosts.add(host)
    if (!host.includes(":")) {
      forwardedPorts.forEach((port) => hosts.add(`${host}:${port}`))
    }
  }

  splitHeaderValues(request.headers.get("x-forwarded-host")).forEach(addHost)
  splitHeaderValues(request.headers.get("host")).forEach(addHost)
  if (request.nextUrl.host) addHost(request.nextUrl.host)

  return hosts
}

function originMatchesRequest(request: NextRequest, origin: string): boolean {
  try {
    const originUrl = new URL(origin)
    const originValue = originUrl.origin.toLowerCase()
    if (trustedCsrfOrigins().has(originValue)) return true

    return requestHostCandidates(request).has(originUrl.host.toLowerCase())
  } catch {
    return false
  }
}

export function validateCsrfRequest(request: NextRequest): boolean {
  if (!CSRF_METHODS.has(request.method)) return true

  const origin = request.headers.get("origin")
  if (origin && !originMatchesRequest(request, origin)) {
    return false
  }

  const cookieToken = request.cookies.get(CSRF_COOKIE)?.value
  const headerToken = request.headers.get(CSRF_HEADER)

  if (!cookieToken || !headerToken) return false
  return cookieToken === headerToken
}

export function sanitizeSessionPayload(payload: TokenSessionPayload) {
  const { user } = payload
  const rest = { ...payload } as Record<string, unknown>
  delete rest.access
  delete rest.refresh
  delete rest.user
  return {
    ...rest,
    ...normalizeSessionUser(user),
  }
}

async function requestAccessTokenRefresh(refreshToken: string): Promise<RefreshResult> {
  try {
    const response = await fetch(`${backendApiUrl}/auth/token/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
      cache: "no-store",
    })
    if (!response.ok) return null
    const payload = (await response.json()) as { access?: string; refresh?: string }
    if (!payload.access) return null
    return { access: payload.access, refresh: payload.refresh || refreshToken }
  } catch {
    return null
  }
}

export async function refreshAccessToken(refreshToken: string) {
  const pendingRefresh = refreshRequests.get(refreshToken)
  if (pendingRefresh) return pendingRefresh

  const refreshPromise = requestAccessTokenRefresh(refreshToken)
  refreshRequests.set(refreshToken, refreshPromise)

  void refreshPromise.finally(() => {
    setTimeout(() => {
      if (refreshRequests.get(refreshToken) === refreshPromise) {
        refreshRequests.delete(refreshToken)
      }
    }, REFRESH_DEDUPE_WINDOW_MS)
  })

  return refreshPromise
}

export async function fetchUserForAccess(accessToken: string) {
  try {
    const response = await fetch(`${backendApiUrl}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    })
    if (!response.ok) return null
    const payload = (await response.json()) as { user?: AuthUser }
    return payload.user ?? null
  } catch {
    return null
  }
}

export async function sessionFromCookies(request: NextRequest) {
  const accessToken = request.cookies.get("ums_access")?.value
  let refreshToken = request.cookies.get("ums_refresh")?.value
  let user = accessToken ? await fetchUserForAccess(accessToken) : null
  let refreshedAccess: string | undefined

  if (!user && refreshToken) {
    const refreshed = await refreshAccessToken(refreshToken)
    if (refreshed) {
      user = await fetchUserForAccess(refreshed.access)
      refreshedAccess = refreshed.access
      refreshToken = refreshed.refresh
    }
  }

  if (!user) return null

  return {
    access: refreshedAccess ?? accessToken,
    refresh: refreshToken,
    refreshedAccess,
    ...normalizeSessionUser(user),
  }
}

export async function accessFromCookies(
  request: NextRequest
): Promise<CookieSession | null> {
  const accessToken = request.cookies.get("ums_access")?.value
  const refreshToken = request.cookies.get("ums_refresh")?.value

  if (accessToken && !isTokenExpired(accessToken)) {
    return { access: accessToken, refresh: refreshToken }
  }

  if (!refreshToken) return null

  const refreshed = await refreshAccessToken(refreshToken)
  if (!refreshed) return null

  return {
    access: refreshed.access,
    refresh: refreshed.refresh,
    refreshedAccess: refreshed.access,
  }
}

export function backendErrorResponse(response: Response, text: string) {
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  })
}
