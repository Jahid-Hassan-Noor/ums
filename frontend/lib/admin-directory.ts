"use client"

import { apiRequest } from "@/lib/auth"
import {
  errorFromResponse,
  filenameFromDisposition,
  normalizeApiPath,
  paramsFromFilters,
  triggerBlobDownload,
  type QueryFilters,
} from "@/lib/fetch-utils"

export type AdminDirectoryKind =
  | "students"
  | "teachers"
  | "executives"
  | "applicants"

export type AdminDirectoryOption = {
  value: string
  label: string
}

export type AdminDirectoryFilters = QueryFilters

export async function fetchAdminDirectoryExport(
  kind: AdminDirectoryKind,
  filters: AdminDirectoryFilters = {}
) {
  const params = paramsFromFilters(filters)
  const query = params.toString()
  const path = `/admin/manage/${kind}/export${query ? `?${query}` : ""}`
  const response = await apiRequest(normalizeApiPath(path))

  if (!response.ok) {
    throw new Error(await errorFromResponse(response, "Export failed."))
  }

  const blob = await response.blob()
  const filename = filenameFromDisposition(
    response.headers.get("content-disposition"),
    `admin-${kind}.xlsx`
  )
  return { blob, filename }
}

export function downloadBlob(blob: Blob, filename: string) {
  triggerBlobDownload(blob, filename)
}
