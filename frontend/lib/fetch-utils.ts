export type QueryFilters = Record<
  string,
  string | number | boolean | null | undefined
>

const RETRY_AFTER_RE = /(\d+)\s*seconds?/

export function normalizeApiPath(path: string): string {
  const queryIndex = path.indexOf("?")
  const hashIndex = path.indexOf("#")
  const suffixIndex =
    queryIndex === -1
      ? hashIndex
      : hashIndex === -1
        ? queryIndex
        : Math.min(queryIndex, hashIndex)

  let pathname = suffixIndex === -1 ? path : path.slice(0, suffixIndex)
  const suffix = suffixIndex === -1 ? "" : path.slice(suffixIndex)

  if (!pathname.startsWith("/")) {
    pathname = `/${pathname}`
  }

  if (pathname !== "/") {
    pathname = pathname.replace(/\/+$/, "")
  }

  return `${pathname}${suffix}`
}

export function safeJsonParse(text: string): unknown | null {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

export function throttledMessage(
  response: Response,
  data: unknown
): string | null {
  if (response.status !== 429) return null

  let seconds: number | null = null
  const header = response.headers.get("Retry-After")
  if (header) {
    const n = parseInt(header, 10)
    if (!Number.isNaN(n) && n > 0) seconds = n
  }

  if (seconds === null && data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === "string") {
      const match = detail.match(RETRY_AFTER_RE)
      if (match) seconds = parseInt(match[1], 10)
    }
  }

  if (seconds !== null && seconds > 0) {
    return `Too many requests, Please try again in ${seconds} seconds.`
  }
  return "Too many requests, Please try again later."
}

export function extractErrorMessage(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail
    if (typeof detail === "string" && detail.trim()) return detail

    const message = (data as { message?: unknown }).message
    if (typeof message === "string" && message.trim()) return message

    const fieldError = Object.entries(data as Record<string, unknown>).find(
      ([field, value]) =>
        field !== "debug" &&
        (typeof value === "string" ||
          (Array.isArray(value) && typeof value[0] === "string"))
    )
    if (fieldError) {
      const [field, value] = fieldError
      const errorMessage = Array.isArray(value) ? value[0] : value
      return field === "non_field_errors"
        ? String(errorMessage)
        : `${field}: ${errorMessage}`
    }
  }
  return fallback
}

export async function readJsonResponse<T>(
  response: Response,
  fallbackMessage: string
): Promise<T> {
  const text = await response.text()
  const data = text ? safeJsonParse(text) : {}

  if (!response.ok) {
    const throttled = throttledMessage(response, data)
    if (throttled) throw new Error(throttled)
    const fallback = text.trim().startsWith("<")
      ? `Server returned HTML error page (${response.status}). Check backend logs.`
      : fallbackMessage
    throw new Error(extractErrorMessage(data, fallback))
  }

  if (text && data === null) {
    throw new Error("Server returned invalid JSON.")
  }

  return (data ?? {}) as T
}

export function paramsFromFilters(filters: QueryFilters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return
    params.set(key, String(value))
  })
  return params
}

export function queryStringFromFilters(filters: QueryFilters) {
  return paramsFromFilters(filters).toString()
}

export function filenameFromDisposition(
  disposition: string | null,
  fallback: string
) {
  if (!disposition) return fallback
  const match = disposition.match(/filename\*?=(?:UTF-8''|")?([^";]+)"?/i)
  return match?.[1] ? decodeURIComponent(match[1]) : fallback
}

export async function errorFromResponse(
  response: Response,
  fallback = "Request failed."
) {
  const text = await response.text()
  const data = text ? safeJsonParse(text) : null
  return extractErrorMessage(data, text.trim() || fallback)
}

export function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
