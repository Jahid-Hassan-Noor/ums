"use client"

import { apiFetch, apiRequest } from "@/lib/auth"
import type { AdminDirectoryFilters } from "@/lib/admin-directory"
import {
  errorFromResponse,
  filenameFromDisposition,
  queryStringFromFilters,
  triggerBlobDownload,
} from "@/lib/fetch-utils"

export type AdminReportDefinition = {
  key: string
  group: "academic" | "operations"
  name: string
  description: string
  statuses: string[]
}

export type ReportExportRecord = {
  id: number
  name: string
  export_type: string
  status: "pending" | "running" | "completed" | "failed"
  requested_by: string
  filters: Record<string, string | number>
  filename: string
  error_message: string
  created_at: string
  completed_at: string | null
}

export type ReportExportsResponse = {
  summary: {
    total: number
    processing: number
    completed: number
    failed: number
  }
  exports: ReportExportRecord[]
}

async function fetchAuthenticatedBlob(path: string, fallbackFilename: string) {
  const response = await apiRequest(path)
  if (!response.ok) {
    throw new Error(await errorFromResponse(response, "Export failed."))
  }
  return {
    blob: await response.blob(),
    filename: filenameFromDisposition(
      response.headers.get("content-disposition"),
      fallbackFilename
    ),
  }
}

export function loadReportCatalog() {
  return apiFetch<{ reports: AdminReportDefinition[] }>("/admin/reports")
}

export function loadReportExports() {
  return apiFetch<ReportExportsResponse>("/admin/reports/exports")
}

export async function generateCatalogReport(
  reportType: string,
  filters: AdminDirectoryFilters
) {
  const query = queryStringFromFilters(filters)
  const result = await fetchAuthenticatedBlob(
    `/admin/reports/generate/${reportType}${query ? `?${query}` : ""}`,
    `${reportType}.xlsx`
  )
  triggerBlobDownload(result.blob, result.filename)
}

export async function downloadStoredReport(
  id: number,
  fallbackFilename: string
) {
  const result = await fetchAuthenticatedBlob(
    `/admin/reports/exports/${id}`,
    fallbackFilename || `report-${id}.xlsx`
  )
  triggerBlobDownload(result.blob, result.filename)
}

export function deleteStoredReport(id: number) {
  return apiFetch<{ message: string }>(`/admin/reports/exports/${id}`, {
    method: "DELETE",
  })
}
