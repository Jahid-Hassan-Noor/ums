"use client"

import { API_BASE } from "@/lib/api-base"
import {
  extractErrorMessage,
  normalizeApiPath,
  readJsonResponse,
  safeJsonParse,
  throttledMessage,
} from "@/lib/fetch-utils"
import type { AuthUser } from "@/lib/server-session"
import {
  defaultUmsRouteForRole,
  normalizeUmsRole,
  roleForUmsPath,
  type UserRole,
} from "@/lib/ums-roles"

export type { AuthUser } from "@/lib/server-session"
export type { UserRole } from "@/lib/ums-roles"

export type AuthSession = {
  role: UserRole
  user: AuthUser
}

type SessionResponse = {
  role?: string
  user: AuthUser
}

type SessionEndpoint =
  | "/auth/login"
  | "/applicant/auth/login"
  | "/applicant/auth/register"

const SESSION_API_PATH = "/ums-auth/session"
const CSRF_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"])

let cachedSession: AuthSession | null = null

const PUBLIC_PATHS = new Set([
  "/",
  "/apply",
  "/apply/login",
  "/apply/register",
  "/login",
  "/forgot-password",
  "/recover-account",
  "/logout",
  "/payment-return",
  "/reset-password",
])

const PUBLIC_PATH_PREFIXES = [
  "/about",
  "/academics",
  "/academic-programmes",
  "/ace-sedi",
  "/admissions",
  "/admissions-and-applications",
  "/alumni",
  "/apply-now",
  "/career",
  "/centers",
  "/centres",
  "/contact",
  "/convocation",
  "/departments",
  "/directories",
  "/events",
  "/news",
  "/official-links",
  "/ums-overview",
  "/press-release",
  "/privacy",
  "/programmes",
  "/programs",
  "/public-lecture-series",
  "/publications",
  "/repository",
  "/scholarship",
  "/schools",
  "/services",
  "/student-life",
  "/students",
  "/terms",
  "/units",
]

const PROTECTED_STANDALONE_PATHS = new Set(["/profile", "/notifications"])

function normalizePath(pathname: string): string {
  const cleaned = pathname.replace(/\/+$/, "")
  return cleaned || "/"
}

function umsApiPath(path: string) {
  return `/ums-auth/backend${normalizeApiPath(path)}`
}

function csrfTokenFromCookie() {
  if (typeof document === "undefined") return ""
  const match = document.cookie.match(/(?:^|;\s*)ums_csrf=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ""
}

async function csrfHeaderForRequest(
  needsCsrf: boolean
): Promise<Record<string, string>> {
  if (!needsCsrf || typeof document === "undefined") return {}

  let token = csrfTokenFromCookie()
  if (!token) {
    await ensureValidSession()
    token = csrfTokenFromCookie()
  }

  return token ? { "X-CSRF-Token": token } : {}
}

function sessionFromResponse(payload: SessionResponse): AuthSession {
  const role = normalizeRole(payload.role ?? payload.user?.role)
  return {
    role,
    user: {
      ...payload.user,
      role,
    },
  }
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${normalizeApiPath(path)}`, init)
  const text = await response.text()
  const data = text ? safeJsonParse(text) : {}

  if (!response.ok) {
    const throttled = throttledMessage(response, data)
    if (throttled) throw new Error(throttled)
    const fallback = text.trim().startsWith("<")
      ? `Server returned HTML error page (${response.status}). Check backend logs.`
      : "Request failed"
    throw new Error(extractErrorMessage(data, fallback))
  }

  if (text && data === null) {
    throw new Error("Server returned invalid JSON.")
  }

  return (data ?? {}) as T
}

export function normalizeRole(role: string | null | undefined): UserRole {
  return normalizeUmsRole(role)
}

export function canAccessRole(
  userRole: UserRole,
  requiredRole: UserRole
): boolean {
  return userRole === requiredRole
}

export function getRequiredRole(pathname: string): UserRole | null {
  return roleForUmsPath(pathname)
}

export function isProtectedUmsPath(pathname: string): boolean {
  const path = normalizePath(pathname)
  return PROTECTED_STANDALONE_PATHS.has(path) || getRequiredRole(path) !== null
}

export function isPublicPath(pathname: string): boolean {
  const path = normalizePath(pathname)
  return (
    PUBLIC_PATHS.has(path) ||
    PUBLIC_PATH_PREFIXES.some(
      (prefix) => path === prefix || path.startsWith(`${prefix}/`)
    )
  )
}

export function defaultRouteForRole(role: UserRole): string {
  return defaultUmsRouteForRole(role)
}

export function getStoredSession(): AuthSession | null {
  return cachedSession
}

export function clearSession() {
  cachedSession = null
  if (typeof window === "undefined") return
  void fetch(SESSION_API_PATH, {
    method: "DELETE",
    cache: "no-store",
    keepalive: true,
  }).catch(() => undefined)
}

export async function createBackendSession(
  endpoint: SessionEndpoint,
  payload: Record<string, unknown>
): Promise<AuthSession> {
  const response = await fetch(SESSION_API_PATH, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint, payload }),
    cache: "no-store",
  })
  const session = sessionFromResponse(
    await readJsonResponse<SessionResponse>(response, "Unable to login")
  )
  cachedSession = session
  return session
}

export function mergeStoredUser(userPatch: Partial<AuthUser>) {
  const session = getStoredSession()
  if (!session) return null

  const user = {
    ...session.user,
    ...userPatch,
  }
  const nextSession = {
    ...session,
    user,
  }
  cachedSession = nextSession
  return nextSession
}

export function profilePictureUrl(picture: string | null | undefined) {
  if (!picture) return ""
  if (/^https?:\/\//i.test(picture)) return picture
  return `${API_BASE}${picture.startsWith("/") ? "" : "/"}${picture}`
}

export async function updateProfilePicture(file: File) {
  const formData = new FormData()
  formData.append("profile_picture", file)
  const response = await apiFetch<{ user: AuthUser }>("/auth/me", {
    method: "PATCH",
    body: formData,
  })
  mergeStoredUser(response.user)
  return response.user
}

export async function loginRequest(username: string, password: string) {
  return createBackendSession("/auth/login", { username, password })
}

export async function forgotPasswordRequest(email: string) {
  return requestJson<{
    detail: string
    reset_link?: string
    debug?: { email_sent: boolean; reason: string }
  }>("/auth/forgot-password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  })
}

export async function resetPasswordRequest(
  token: string,
  password: string,
  confirmPassword: string
) {
  return requestJson<{ detail: string }>("/auth/reset-password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token,
      password,
      confirm_password: confirmPassword,
    }),
  })
}

export async function changePasswordRequest(
  oldPassword: string,
  newPassword: string,
  confirmPassword: string
) {
  return apiFetch<{ detail: string }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }),
  })
}

export async function ensureValidSession(): Promise<AuthSession | null> {
  try {
    const response = await fetch(SESSION_API_PATH, {
      method: "GET",
      cache: "no-store",
    })
    if (response.status === 401) {
      cachedSession = null
      return null
    }
    const session = sessionFromResponse(
      await readJsonResponse<SessionResponse>(
        response,
        "Session expired. Please login again."
      )
    )
    cachedSession = session
    return session
  } catch {
    cachedSession = null
    return null
  }
}

export async function apiRequest(
  endpoint: string,
  init?: RequestInit
): Promise<Response> {
  const isFormData =
    typeof FormData !== "undefined" && init?.body instanceof FormData
  const method = (init?.method ?? "GET").toUpperCase()
  const needsCsrf = CSRF_METHODS.has(method)

  const request = async () => {
    const headers = new Headers(init?.headers)
    if (!isFormData && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json")
    }
    const csrfHeader = await csrfHeaderForRequest(needsCsrf)
    Object.entries(csrfHeader).forEach(([key, value]) => {
      headers.set(key, value)
    })
    return fetch(umsApiPath(endpoint), {
      ...init,
      headers,
      cache: init?.cache ?? "no-store",
    })
  }

  let response = await request()

  if (needsCsrf && response.status === 403 && typeof document !== "undefined") {
    await ensureValidSession()
    response = await request()
  }

  if (response.status === 401) {
    cachedSession = null
  }

  return response
}

export async function apiFetch<T>(
  endpoint: string,
  init?: RequestInit
): Promise<T> {
  const response = await apiRequest(endpoint, init)

  const text = await response.text()
  const data = text ? safeJsonParse(text) : {}

  if (!response.ok) {
    const throttled = throttledMessage(response, data)
    if (throttled) throw new Error(throttled)
    const fallback = text.trim().startsWith("<")
      ? `Server returned HTML error page (${response.status}). Check backend logs.`
      : "API request failed"
    throw new Error(extractErrorMessage(data, fallback))
  }

  if (text && data === null) {
    throw new Error("Server returned invalid JSON.")
  }

  return (data ?? {}) as T
}

export async function sendEmailVerificationRequest() {
  return apiFetch<{
    detail: string
    is_email_verified: boolean
    debug?: {
      email_sent: boolean
      reason: string
      verification_link?: string
      verification_token?: string
    }
  }>("/auth/send-email-verification", {
    method: "POST",
  })
}

export async function verifyEmailRequest(token: string) {
  return apiFetch<{
    detail: string
    username: string
    is_email_verified: boolean
  }>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  })
}
