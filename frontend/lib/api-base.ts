const DEFAULT_API_BASE = "/api"

export function resolveApiBase(rawValue: string | null | undefined) {
  const value = String(rawValue ?? "").trim()

  if (!value || value === "/") {
    return DEFAULT_API_BASE
  }

  if (/^https?:\/\//i.test(value)) {
    return value.replace(/\/+$/, "")
  }

  const normalizedPath = `${value.startsWith("/") ? "" : "/"}${value}`.replace(/\/+$/, "")
  return normalizedPath || DEFAULT_API_BASE
}

export const API_BASE = resolveApiBase(
  process.env.NEXT_PUBLIC_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL,
)
