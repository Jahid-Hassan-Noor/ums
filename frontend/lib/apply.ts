"use client"

import { API_BASE } from "@/lib/api-base"
import {
  apiFetch,
  createBackendSession,
  mergeStoredUser,
  type AuthSession,
} from "@/lib/auth"
import { normalizeApiPath, readJsonResponse } from "@/lib/fetch-utils"

async function publicApplyFetch<T>(endpoint: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${normalizeApiPath(endpoint)}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  })
  return readJsonResponse<T>(response, "Request failed")
}

export type ApplyApplicant = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: "applicant"
  phone?: string
  nationality?: string
  country_of_residence?: string
  passport_or_identity_no?: string
}

export type ApplyOption = {
  value: string
  label: string
}

export type ApplyQuestion = {
  id: string
  label: string
  help_text?: string
  required: boolean
}

export type ApplyAdmissionsSetup = {
  required_documents: string[]
  required_detail_fields: string[]
  custom_questions: ApplyQuestion[]
  scholarship_enabled: boolean
}

export type ApplyIntake = {
  id: number
  code: string
  title: string
  application_type: string
  academic_year: string
  closes_at?: string | null
}

export type ApplyProgramme = {
  id: number
  code: string
  name: string
  level: string
  school: string
}

export type ApplyOptions = {
  intakes: ApplyIntake[]
  programmes: ApplyProgramme[]
  application_types: ApplyOption[]
  document_types: ApplyOption[]
  countries: ApplyOption[]
  steps: ApplyOption[]
  admissions_setup: ApplyAdmissionsSetup
}

export type ApplyDocument = {
  id: string
  application?: string
  document_type: string
  file?: string | null
  file_url?: string | null
  original_name: string
  status: string
  notes: string
  uploaded_at: string
  reviewed_at?: string | null
}

export type ApplyStatusEvent = {
  id: number
  from_status: string
  to_status: string
  note: string
  created_by_name?: string | null
  created_at: string
}

export type ApplyApplication = {
  id: string
  application_number: string
  intake?: number | null
  intake_detail?: ApplyIntake | null
  application_type: string
  status: string
  current_step: string
  mode_of_study: string
  programme_preferences: string[]
  personal_information: Record<string, unknown>
  academic_information: Record<string, unknown>
  scholarship_requested: boolean
  scholarship_information: Record<string, unknown>
  scholarship_application?: {
    id: number
    status: string
    household_income?: string | null
    dependents_count: number
    personal_statement: string
    financial_need_notes: string
    socioeconomic_score?: string | null
    communication_score?: string | null
    attitude_score?: string | null
    statement_score?: string | null
    review_notes: string
    reviewed_at?: string | null
    created_at: string
    updated_at: string
  } | null
  statement_accepted: boolean
  submitted_at?: string | null
  review_notes: string
  documents: ApplyDocument[]
  status_events: ApplyStatusEvent[]
  created_at: string
  updated_at: string
}

export async function loadApplyOptions() {
  return publicApplyFetch<ApplyOptions>("/applicant/options")
}

export async function applyRegister(payload: {
  username: string
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
  phone: string
  nationality: string
  country_of_residence: string
  passport_or_identity_no: string
}): Promise<AuthSession> {
  return createBackendSession("/applicant/auth/register", payload)
}

export async function applyLogin(
  email: string,
  password: string
): Promise<AuthSession> {
  return createBackendSession("/applicant/auth/login", { email, password })
}

export async function loadApplyProfile() {
  const response = await apiFetch<{ applicant: ApplyApplicant }>(
    "/applicant/me"
  )
  return response.applicant
}

export async function updateApplyProfile(payload: {
  first_name: string
  last_name: string
  phone: string
  nationality: string
  country_of_residence: string
  passport_or_identity_no: string
}) {
  const response = await apiFetch<{ applicant: ApplyApplicant }>(
    "/applicant/me",
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  )
  mergeStoredUser({
    first_name: response.applicant.first_name,
    last_name: response.applicant.last_name,
    phone_number: response.applicant.phone,
  })
  return response.applicant
}

export async function loadApplyApplications() {
  return apiFetch<ApplyApplication[]>("/applicant/applications")
}

export async function createApplyApplication(
  payload: Partial<ApplyApplication>
) {
  return apiFetch<ApplyApplication>("/applicant/applications", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updateApplyApplication(
  applicationId: string,
  payload: Partial<ApplyApplication>
) {
  return apiFetch<ApplyApplication>(
    `/applicant/applications/${applicationId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  )
}

export async function submitApplyApplication(applicationId: string) {
  return apiFetch<ApplyApplication>(
    `/applicant/applications/${applicationId}/submit`,
    {
      method: "POST",
      body: JSON.stringify({ confirm: true }),
    }
  )
}

export async function uploadApplyDocument(
  applicationId: string,
  formData: FormData
) {
  return apiFetch<ApplyDocument>(
    `/applicant/applications/${applicationId}/documents`,
    {
      method: "POST",
      body: formData,
    }
  )
}
