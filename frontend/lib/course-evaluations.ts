"use client"

import { downloadBlob } from "@/lib/admin-directory"
import { apiRequest } from "@/lib/auth"

export type LikertOption = {
  value: string
  label: string
  score: number
}

export type EvaluationQuestion = {
  id: string
  section: string
  text: string
  type: "likert" | "text"
  required: boolean
}

export async function exportCourseEvaluation(surveyId: number, fallbackCode: string) {
  const response = await apiRequest(
    `/executive/evaluations/surveys/${surveyId}/export`
  )
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(payload.detail || "Unable to export the evaluation report.")
  }
  const blob = await response.blob()
  const disposition = response.headers.get("content-disposition")
  const filename =
    disposition?.match(/filename="?([^";]+)"?/i)?.[1] ??
    `sec-set-${fallbackCode.toLowerCase()}.xlsx`
  downloadBlob(blob, filename)
}
