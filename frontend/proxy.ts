import { NextResponse, type NextRequest } from "next/server"

import {
  backendApiUrl,
  clearAuthCookies,
  fetchUserForAccess,
  refreshAccessToken,
  setAuthCookies,
  type AuthUser,
} from "@/lib/server-session"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  disabledUmsRouteModules,
  isUmsFeaturePathEnabled,
  isUmsRoleFeaturePathEnabled,
  normalizeUmsPublicSettings,
  type UmsPublicSettings,
} from "@/lib/ums-settings"

const roleDashboards = {
  applicant: "/apply/dashboard",
  student: "/student/dashboard",
  teacher: "/teacher/dashboard",
  executive: "/executive/dashboard",
  librarian: "/librarian/dashboard",
  caterer: "/caterer/dashboard",
  technician: "/technician/dashboard",
  accountant: "/accountant/dashboard",
  hr: "/hr/dashboard",
  admin: "/admin/dashboard",
} as const

type Role = keyof typeof roleDashboards

type UmsIdentity = {
  role: Role
  user: AuthUser
}

type ResolvedIdentity = {
  identity: UmsIdentity | null
  refreshedAccess?: string
  refreshToken?: string
}

const PUBLIC_SETTINGS_CACHE_TTL_MS = 30_000

let cachedPublicSettings: UmsPublicSettings | null = null
let cachedPublicSettingsAt = 0
let pendingPublicSettings: Promise<UmsPublicSettings> | null = null

const securityHeaders = {
  "Content-Security-Policy": [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${process.env.NODE_ENV === "production" ? "" : " 'unsafe-eval'"}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
    "frame-src 'none'",
    "upgrade-insecure-requests",
  ].join("; "),
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Frame-Options": "DENY",
  "X-XSS-Protection": "0",
  "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

function withSecurityHeaders(response: NextResponse) {
  Object.entries(securityHeaders).forEach(([key, value]) => {
    response.headers.set(key, value)
  })
  return response
}

function normalizedPath(pathname: string) {
  return pathname.replace(/\/+$/, "") || "/"
}

function roleForPath(pathname: string): Role | null {
  const path = normalizedPath(pathname)

  if (
    path.startsWith("/apply/") &&
    path !== "/apply/login" &&
    path !== "/apply/register"
  ) {
    return "applicant"
  }
  if (path === "/student" || path.startsWith("/student/")) return "student"
  if (path === "/teacher" || path.startsWith("/teacher/")) return "teacher"
  if (path === "/executive" || path.startsWith("/executive/")) return "executive"
  if (path === "/librarian" || path.startsWith("/librarian/")) return "librarian"
  if (path === "/caterer" || path.startsWith("/caterer/")) return "caterer"
  if (path === "/technician" || path.startsWith("/technician/")) return "technician"
  if (path === "/accountant" || path.startsWith("/accountant/")) return "accountant"
  if (path === "/hr" || path.startsWith("/hr/")) return "hr"
  if (path === "/admin" || path.startsWith("/admin/")) return "admin"

  return null
}

function isMaintenanceBypassPath(pathname: string) {
  const path = normalizedPath(pathname)
  if (path === "/login" || path === "/maintenance" || path === "/module-unavailable") return true
  if (
    path.startsWith("/login/") ||
    path.startsWith("/maintenance/") ||
    path.startsWith("/module-unavailable/")
  ) {
    return true
  }
  if (path.startsWith("/_next/") || path.startsWith("/ums-auth/")) return true
  if (path.startsWith("/images/") || path.startsWith("/media/")) return true
  if (path === "/favicon.ico") return true
  return /\.[^/]+$/.test(path)
}

function isRole(value: string | undefined): value is Role {
  return (
    value === "applicant" ||
    value === "student" ||
    value === "teacher" ||
    value === "executive" ||
    value === "librarian" ||
    value === "caterer" ||
    value === "technician" ||
    value === "accountant" ||
    value === "hr" ||
    value === "admin"
  )
}

function loginRedirect(request: NextRequest, clearCookies: boolean) {
  const url = request.nextUrl.clone()
  url.pathname = "/login"
  url.search = `?next=${encodeURIComponent(`${request.nextUrl.pathname}${request.nextUrl.search}`)}`
  const response = NextResponse.redirect(url)
  if (clearCookies) {
    clearAuthCookies(response, request)
  }
  return withSecurityHeaders(response)
}

async function identityForAccessToken(accessToken: string): Promise<UmsIdentity | null> {
  const user = await fetchUserForAccess(accessToken)
  const role = user?.role
  if (!user || !isRole(role)) return null
  return {
    role,
    user,
  }
}

async function fetchPublicSettings(): Promise<UmsPublicSettings> {
  try {
    const response = await fetch(`${backendApiUrl}/settings/public`, {
      cache: "no-store",
    })
    if (!response.ok) return DEFAULT_UMS_PUBLIC_SETTINGS
    return normalizeUmsPublicSettings(await response.json())
  } catch {
    return DEFAULT_UMS_PUBLIC_SETTINGS
  }
}

async function loadPublicSettings(): Promise<UmsPublicSettings> {
  if (
    cachedPublicSettings &&
    Date.now() - cachedPublicSettingsAt < PUBLIC_SETTINGS_CACHE_TTL_MS
  ) {
    return cachedPublicSettings
  }

  if (pendingPublicSettings) return pendingPublicSettings

  pendingPublicSettings = fetchPublicSettings()
    .then((settings) => {
      if (settings !== DEFAULT_UMS_PUBLIC_SETTINGS) {
        cachedPublicSettings = settings
        cachedPublicSettingsAt = Date.now()
      }
      return settings
    })
    .finally(() => {
      pendingPublicSettings = null
    })

  return pendingPublicSettings
}

async function resolveIdentity(request: NextRequest): Promise<ResolvedIdentity> {
  const accessToken = request.cookies.get("ums_access")?.value
  const refreshToken = request.cookies.get("ums_refresh")?.value
  let identity = accessToken ? await identityForAccessToken(accessToken) : null
  let refreshedAccess: string | undefined
  let newRefreshToken: string | undefined

  if (!identity && refreshToken) {
    const refreshed = await refreshAccessToken(refreshToken)
    if (refreshed) {
      identity = await identityForAccessToken(refreshed.access)
      refreshedAccess = refreshed.access
      newRefreshToken = refreshed.refresh
    }
  }

  return {
    identity,
    refreshedAccess,
    refreshToken: newRefreshToken,
  }
}

function maintenanceRedirect(request: NextRequest, clearCookies: boolean) {
  const url = request.nextUrl.clone()
  url.pathname = "/maintenance"
  url.search = ""
  const response = NextResponse.redirect(url)
  if (clearCookies) {
    clearAuthCookies(response, request)
  }
  return withSecurityHeaders(response)
}

function moduleUnavailableRedirect(
  request: NextRequest,
  settings: UmsPublicSettings,
  role?: Role
) {
  const url = request.nextUrl.clone()
  const requestedPath = `${request.nextUrl.pathname}${request.nextUrl.search}`
  const modules = disabledUmsRouteModules(request.nextUrl.pathname, settings, role)
  url.pathname = "/module-unavailable"
  url.search = ""
  url.searchParams.set("next", requestedPath)
  if (modules.length) {
    url.searchParams.set("modules", modules.join(","))
  }
  return withSecurityHeaders(NextResponse.redirect(url))
}

function authenticatedResponse(
  response: NextResponse,
  request: NextRequest,
  identity: UmsIdentity,
  refreshedAccess?: string,
  refreshToken?: string
) {
  setAuthCookies(response, request, {
    access: refreshedAccess,
    refresh: refreshedAccess ? refreshToken : undefined,
    user: identity.user,
  })
  return withSecurityHeaders(response)
}

export async function proxy(request: NextRequest) {
  if (isMaintenanceBypassPath(request.nextUrl.pathname)) {
    return withSecurityHeaders(NextResponse.next())
  }

  const requiredRole = roleForPath(request.nextUrl.pathname)
  const isSharedProtectedRoute =
    request.nextUrl.pathname === "/profile" || request.nextUrl.pathname === "/notifications"
  const publicSettings = await loadPublicSettings()
  const maintenanceEnabled = publicSettings.maintenance.enabled

  if (!requiredRole && !isSharedProtectedRoute) {
    if (!maintenanceEnabled) {
      return withSecurityHeaders(NextResponse.next())
    }
    const resolved = await resolveIdentity(request)
    const response = maintenanceRedirect(
      request,
      resolved.identity?.role !== "admin"
    )
    if (resolved.identity?.role === "admin") {
      return authenticatedResponse(
        response,
        request,
        resolved.identity,
        resolved.refreshedAccess,
        resolved.refreshedAccess ? resolved.refreshToken : undefined
      )
    }
    return response
  }

  const features = publicSettings.features
  if (!isUmsFeaturePathEnabled(request.nextUrl.pathname, features)) {
    return moduleUnavailableRedirect(request, publicSettings)
  }

  const {
    identity: umsIdentity,
    refreshedAccess,
    refreshToken: newRefreshToken,
  } = await resolveIdentity(request)

  if (!umsIdentity) {
    if (maintenanceEnabled && requiredRole !== "admin") {
      return maintenanceRedirect(request, true)
    }
    return loginRedirect(request, !request.cookies.get("ums_refresh")?.value)
  }

  const umsRole = umsIdentity.role
  if (maintenanceEnabled && umsRole !== "admin") {
    return maintenanceRedirect(request, true)
  }

  if (!isUmsRoleFeaturePathEnabled(request.nextUrl.pathname, publicSettings, umsRole)) {
    return moduleUnavailableRedirect(request, publicSettings, umsRole)
  }

  if (requiredRole && umsRole !== requiredRole) {
    const url = request.nextUrl.clone()
    url.pathname = roleDashboards[umsRole]
    url.search = ""
    return authenticatedResponse(
      NextResponse.redirect(url),
      request,
      umsIdentity,
      refreshedAccess,
      refreshedAccess ? newRefreshToken : undefined
    )
  }

  return authenticatedResponse(
    NextResponse.next(),
    request,
    umsIdentity,
    refreshedAccess,
    refreshedAccess ? newRefreshToken : undefined
  )
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)",
  ],
}
