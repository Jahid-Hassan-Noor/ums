"use client"

import { useState } from "react"
import { FileText, FileSpreadsheet, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { apiRequest } from "@/lib/auth"
import {
  errorFromResponse,
  filenameFromDisposition,
  triggerBlobDownload,
} from "@/lib/fetch-utils"

type ExportMenuProps = {
  studentId?: number
  variant?: "default" | "outline" | "ghost"
  size?: "default" | "sm" | "lg" | "icon"
}

export function ExportMenu({
  studentId,
  variant = "outline",
  size = "sm",
}: ExportMenuProps) {
  const [exporting, setExporting] = useState<string | null>(null)
  const [error, setError] = useState("")

  async function handleExport(format: "pdf" | "xlsx") {
    if (!studentId) return
    setExporting(format)
    setError("")
    try {
      const params = new URLSearchParams({
        student_id: String(studentId),
        export_format: format,
      })
      const response = await apiRequest(
        `/finance/ledger/export?${params.toString()}`
      )
      if (!response.ok) {
        throw new Error(await errorFromResponse(response, "Export failed."))
      }
      const blob = await response.blob()
      const filename = filenameFromDisposition(
        response.headers.get("content-disposition"),
        `student-ledger-${studentId}.${format}`
      )
      triggerBlobDownload(blob, filename)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Export failed.")
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="space-y-1">
      <div className="flex gap-1">
        <Button
          variant={variant}
          size={size}
          disabled={exporting !== null || !studentId}
          onClick={() => void handleExport("pdf")}
        >
          {exporting === "pdf" ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <FileText className="size-3" />
          )}
          PDF
        </Button>
        <Button
          variant={variant}
          size={size}
          disabled={exporting !== null || !studentId}
          onClick={() => void handleExport("xlsx")}
        >
          {exporting === "xlsx" ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <FileSpreadsheet className="size-3" />
          )}
          Excel
        </Button>
      </div>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  )
}
