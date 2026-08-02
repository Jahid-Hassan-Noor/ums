"use client"

import { apiFetch, apiRequest } from "@/lib/auth"
import type {
  AdminDirectoryFilters,
  AdminDirectoryOption,
} from "@/lib/admin-directory"
import {
  errorFromResponse,
  filenameFromDisposition,
  queryStringFromFilters,
  triggerBlobDownload,
} from "@/lib/fetch-utils"

export type ExecutiveReportKind = "students" | "teachers" | "final-results"

export type ExecutiveReportsResponse = {
  scope: {
    kind: "school" | "center"
    id: number
    code: string
    name: string
  }
  students: {
    count: number
    filters: Record<string, AdminDirectoryOption[]>
  }
  teachers: {
    count: number
    filters: Record<string, AdminDirectoryOption[]>
  }
  results: {
    count: number
    filters: Record<string, AdminDirectoryOption[]>
  }
}

export function loadExecutiveReports() {
  return apiFetch<ExecutiveReportsResponse>("/executive/reports")
}

export async function exportExecutiveReport(
  kind: ExecutiveReportKind,
  filters: AdminDirectoryFilters
) {
  const query = queryStringFromFilters(filters)
  const response = await apiRequest(
    `/executive/reports/${kind}/export${query ? `?${query}` : ""}`
  )
  if (!response.ok) {
    throw new Error(
      await errorFromResponse(response, "Unable to export report.")
    )
  }
  const blob = await response.blob()
  const filename = filenameFromDisposition(
    response.headers.get("content-disposition"),
    `executive-${kind}.xlsx`
  )
  triggerBlobDownload(blob, filename)
}
