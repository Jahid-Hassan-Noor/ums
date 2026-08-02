"use client"

import { useState } from "react"
import { FileText, FileSpreadsheet, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { triggerBlobDownload } from "@/lib/fetch-utils"

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

  async function handleExport(format: "pdf" | "xlsx") {
    if (!studentId) return
    setExporting(format)
    try {
      const params = new URLSearchParams({
        student_id: String(studentId),
        format,
      })
      const response = await fetch(
        `/api/finance/ledger/export?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
          },
        }
      )
      if (!response.ok) throw new Error("Export failed")
      const blob = await response.blob()
      triggerBlobDownload(blob, `student-ledger-${studentId}.${format}`)
    } catch {
    } finally {
      setExporting(null)
    }
  }

  return (
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
  )
}
