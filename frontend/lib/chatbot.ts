"use client"

import { apiRequest } from "@/lib/auth"

export type ChatbotSource = {
  title: string
  type: string
  url?: string
}

export type ChatbotResponse = {
  answer: string
  intent: string
  scope: "public" | "private" | "privacy" | string
  requires_auth: boolean
  data?: unknown
  sources: ChatbotSource[]
  model: string
}

export type ChatbotSearchResult = {
  title: string
  summary: string
  domain: string
  type: string
  icon?: string
  url?: string
  breadcrumbs: string[]
  source_label: string
  metadata: Record<string, string | number | boolean | null>
  last_indexed_at?: string
}

export type ChatbotSearchResponse = {
  query: string
  mode: "topbar" | "full" | "chatbot"
  count: number
  results: ChatbotSearchResult[]
  pagination: {
    page: number
    page_size: number
    has_next: boolean
  }
}

function safeJsonParse(value: string) {
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function errorMessage(data: unknown, fallback: string) {
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>
    const detail = record.detail ?? record.error ?? record.message
    if (typeof detail === "string" && detail.trim()) {
      return detail
    }
    const questionError = record.question
    if (Array.isArray(questionError) && typeof questionError[0] === "string") {
      return questionError[0]
    }
  }
  return fallback
}

async function chatbotRequest(
  endpoint: string,
  init?: RequestInit
): Promise<Response> {
  const response = await apiRequest(endpoint, init)
  if (response.status !== 401) {
    return response
  }

  const isFormData =
    typeof FormData !== "undefined" && init?.body instanceof FormData

  return fetch(`/api${endpoint}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
    cache: init?.cache ?? "no-store",
  })
}

export async function sendChatbotQuestion(
  question: string
): Promise<ChatbotResponse> {
  const response = await chatbotRequest("/chatbot/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  })
  const text = await response.text()
  const data = text ? safeJsonParse(text) : null

  if (!response.ok || !data) {
    throw new Error(
      errorMessage(data, "The assistant could not answer right now.")
    )
  }

  return data as ChatbotResponse
}

export async function searchChatbotDocuments(
  params: {
    query: string
    mode?: "topbar" | "full" | "chatbot"
    domain?: string
    type?: string
    limit?: number
    page?: number
    pageSize?: number
  },
  init?: Pick<RequestInit, "signal">
): Promise<ChatbotSearchResponse> {
  const searchParams = new URLSearchParams()
  searchParams.set("q", params.query)
  searchParams.set("mode", params.mode ?? "topbar")
  if (params.domain) searchParams.set("domain", params.domain)
  if (params.type) searchParams.set("type", params.type)
  if (params.limit) searchParams.set("limit", String(params.limit))
  if (params.page) searchParams.set("page", String(params.page))
  if (params.pageSize) searchParams.set("page_size", String(params.pageSize))

  const response = await chatbotRequest(`/chatbot/search?${searchParams}`, {
    method: "GET",
    signal: init?.signal,
  })
  const text = await response.text()
  const data = text ? safeJsonParse(text) : null

  if (!response.ok || !data) {
    throw new Error(errorMessage(data, "Search is unavailable right now."))
  }

  return data as ChatbotSearchResponse
}
