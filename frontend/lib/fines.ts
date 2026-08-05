import { apiFetch } from "@/lib/auth"

export type Fine = {
  id: number
  reason: string
  description: string
  amount: string
  amount_display?: string
  currency: string
  status: "pending" | "paid" | "overdue" | "deducted"
  due_date: string | null
  checkout_url: string
  paid_at: string | null
  deducted_at: string | null
  deduction_note: string
  created_at: string
  student: {
    id: number
    name: string
    email: string
    identifier: string
  }
  issued_by: {
    id: number
    name: string
  } | null
}

export type CreateFineInput = {
  student_id: number
  reason: string
  amount: number | string
  description?: string
  due_date?: string | null
}

export async function fetchAccountantFines(params?: {
  status?: string
  student_id?: number
}): Promise<Fine[]> {
  const query = new URLSearchParams()
  if (params?.status) query.set("status", params.status)
  if (params?.student_id) query.set("student_id", String(params.student_id))
  const qs = query.toString()
  const response = await apiFetch<{ fines: Fine[] }>(`/finance/fines${qs ? `?${qs}` : ""}`)
  return response.fines ?? []
}

export async function createFine(data: CreateFineInput): Promise<Fine> {
  const response = await apiFetch<{ fine: Fine; message: string }>("/finance/fines", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return response.fine
}

export async function deductFine(fineId: number, note?: string): Promise<Fine> {
  const response = await apiFetch<{ fine: Fine; message: string }>(`/finance/fines/${fineId}/deduct`, {
    method: "POST",
    body: JSON.stringify({ note: note ?? "" }),
  })
  return response.fine
}

export async function fetchStudentFines(): Promise<Fine[]> {
  const response = await apiFetch<{ fines: Fine[] }>("/finance/my-fines")
  return response.fines ?? []
}

export async function initiateFinePay(fineId: number): Promise<{ checkout_url: string; fine: Fine; message?: string }> {
  return apiFetch<{ checkout_url: string; fine: Fine; message?: string }>(`/finance/my-fines/${fineId}/pay`, {
    method: "POST",
  })
}

export function fineStatusLabel(status: Fine["status"]): string {
  switch (status) {
    case "pending":
      return "Pending Payment"
    case "paid":
      return "Paid Online"
    case "overdue":
      return "Overdue"
    case "deducted":
      return "Deducted from Allowance"
    default:
      return status
  }
}

export function fineStatusColor(status: Fine["status"]): string {
  switch (status) {
    case "pending":
      return "text-amber-600 bg-amber-50 border-amber-200"
    case "paid":
      return "text-emerald-700 bg-emerald-50 border-emerald-200"
    case "overdue":
      return "text-red-700 bg-red-50 border-red-200"
    case "deducted":
      return "text-blue-700 bg-blue-50 border-blue-200"
    default:
      return "text-muted-foreground bg-muted"
  }
}
