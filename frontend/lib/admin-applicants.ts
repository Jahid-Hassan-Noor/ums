"use client"

import { apiFetch } from "@/lib/auth"
import type {
  ApplyAdmissionsSetup,
  ApplyApplication,
  ApplyDocumentType,
  ApplyDocument,
  ApplyOption,
} from "@/lib/apply"

export type AdminApplicant = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: "applicant"
  phone?: string | null
  nationality?: string | null
  country_of_residence?: string | null
  passport_or_identity_no?: string | null
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export type AdminApplicantSummary = {
  total: number
  active: number
  inactive: number
  current_session: number
  previous_sessions: number
}

export type AdminApplicantOverview = {
  summary: AdminApplicantSummary
  applicants: AdminApplicant[]
}

export type AdminApplicantSetupPayload = {
  settings: ApplyAdmissionsSetup
  detail_fields: (ApplyOption & { section: string })[]
  document_types: ApplyDocumentType[]
  document_type_options: ApplyDocumentType[]
  steps: ApplyOption[]
  status_options: (ApplyOption & { enabled: boolean })[]
  message?: string
}

export type AdminApplicantDetail = {
  applicant: AdminApplicant
  applications: ApplyApplication[]
  admissions_setup: ApplyAdmissionsSetup
}

export async function loadAdminApplicants() {
  return apiFetch<AdminApplicantOverview>("/admin/manage/applicants")
}

export async function updateAdminApplicant(
  applicantId: number,
  payload: Partial<AdminApplicant> & { is_active?: boolean }
) {
  return apiFetch<{ applicant: AdminApplicant }>(
    `/admin/manage/applicants/${applicantId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  )
}

export async function loadAdminApplicantDetail(applicantId: number | string) {
  return apiFetch<AdminApplicantDetail>(`/admin/manage/applicants/${applicantId}`)
}

export async function loadAdminApplicantsSetup() {
  return apiFetch<AdminApplicantSetupPayload>("/admin/manage/applicants/setup")
}

export async function updateAdminApplicantsSetup(payload: ApplyAdmissionsSetup) {
  return apiFetch<AdminApplicantSetupPayload>("/admin/manage/applicants/setup", {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export async function updateAdminApplicationStatus(
  applicationId: string,
  payload: {
    status: string
    note?: string
    review_notes?: string
    interview_at?: string | null
    interview_location?: string
    interview_details?: string
  }
) {
  return apiFetch<ApplyApplication>(`/applicant/staff/applications/${applicationId}/status`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export async function updateAdminDocumentReview(
  documentId: string,
  payload: { status: string; notes?: string }
) {
  return apiFetch<ApplyDocument>(`/applicant/staff/documents/${documentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export async function updateAdminScholarshipReview(
  applicationId: string,
  payload: {
    status: string
    socioeconomic_score?: string | null
    communication_score?: string | null
    attitude_score?: string | null
    statement_score?: string | null
    review_notes?: string
  }
) {
  return apiFetch<ApplyApplication["scholarship_application"]>(
    `/applicant/staff/applications/${applicationId}/scholarship`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  )
}

export async function disableAdminApplicant(applicantId: number) {
  return apiFetch<{ message: string }>(
    `/admin/manage/applicants/${applicantId}`,
    {
      method: "DELETE",
    }
  )
}
