import { apiFetch } from "@/lib/auth"

export type UmsNotification = {
  id: number
  verb: string
  unread: boolean
  data: Record<string, unknown>
  created_at: string
  actor: {
    name: string
    role: string
  } | null
}

export type NotificationListResponse = {
  notifications: UmsNotification[]
  unread_count: number
  total_count: number
}

export function loadNotifications() {
  return apiFetch<NotificationListResponse>("/notifications/")
}

export function markNotificationRead(notificationId: number) {
  return apiFetch<{ notification: UmsNotification; unread_count: number }>(
    `/notifications/${notificationId}/read/`,
    { method: "POST" }
  )
}

export function markAllNotificationsRead() {
  return apiFetch<{ updated_count: number; unread_count: number }>(
    "/notifications/read-all/",
    { method: "POST" }
  )
}

export function deleteNotification(notificationId: number) {
  return apiFetch<{
    deleted_count: number
    unread_count: number
    total_count: number
  }>(`/notifications/${notificationId}/`, { method: "DELETE" })
}

export function deleteReadNotifications() {
  return apiFetch<{
    deleted_count: number
    unread_count: number
    total_count: number
  }>("/notifications/read/", { method: "DELETE" })
}
