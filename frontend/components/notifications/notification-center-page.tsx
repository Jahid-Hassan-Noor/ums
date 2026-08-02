"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Bell,
  BellRing,
  Check,
  CheckCheck,
  ExternalLink,
  Inbox,
  Loader2,
  RefreshCw,
  Trash2,
} from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  deleteNotification,
  deleteReadNotifications,
  loadNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type UmsNotification,
} from "@/lib/notifications"
import { runOptimisticUpdate } from "@/lib/optimistic"

type Filter = "all" | "unread" | "read"

type NotificationRole = {
  href: string
  label: string
}

type NotificationSnapshot = {
  notifications: UmsNotification[]
  totalCount: number
  unreadCount: number
}

function relatedUrl(notification: UmsNotification) {
  const url = notification.data.url
  return typeof url === "string" && url.startsWith("/") && !url.startsWith("//")
    ? url
    : null
}

function metadata(notification: UmsNotification) {
  return Object.entries(notification.data)
    .filter(
      ([key, value]) =>
        key !== "url" &&
        !key.endsWith("_id") &&
        key !== "event_type" &&
        value !== null &&
        value !== undefined &&
        ["string", "number", "boolean"].includes(typeof value)
    )
    .slice(0, 4)
}

function metadataLabel(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatMetadataValue(value: unknown) {
  if (typeof value === "boolean") return value ? "Yes" : "No"
  return String(value)
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

export function NotificationCenterPage({ role }: { role?: NotificationRole }) {
  const router = useRouter()
  const [notifications, setNotifications] = useState<UmsNotification[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [unreadCount, setUnreadCount] = useState(0)
  const [filter, setFilter] = useState<Filter>("all")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<number | "all" | "read" | null>(null)
  const [error, setError] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const response = await loadNotifications()
      setNotifications(response.notifications ?? [])
      setTotalCount(response.total_count ?? response.notifications?.length ?? 0)
      setUnreadCount(response.unread_count ?? 0)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to load notifications."
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load])

  const loadedUnreadCount = notifications.filter(
    (notification) => notification.unread
  ).length
  const loadedReadCount = notifications.length - loadedUnreadCount
  const readCount = Math.max(totalCount - unreadCount, 0)
  const visibleNotifications = useMemo(
    () =>
      notifications.filter((notification) => {
        if (filter === "unread") return notification.unread
        if (filter === "read") return !notification.unread
        return true
      }),
    [filter, notifications]
  )

  async function markRead(notification: UmsNotification) {
    if (!notification.unread) return
    setSaving(notification.id)
    setError("")
    try {
      await runOptimisticUpdate({
        snapshot: () => ({ notifications, totalCount, unreadCount }),
        apply: () => {
          setNotifications((current) =>
            current.map((item) =>
              item.id === notification.id ? { ...item, unread: false } : item
            )
          )
          setUnreadCount((current) => Math.max(current - 1, 0))
        },
        request: () => markNotificationRead(notification.id),
        commit: (response) => {
          setNotifications((current) =>
            current.map((item) =>
              item.id === notification.id ? response.notification : item
            )
          )
          setUnreadCount(response.unread_count)
        },
        rollback: restoreNotifications,
      })
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to mark the notification as read."
      )
    } finally {
      setSaving(null)
    }
  }

  async function markAllRead() {
    setSaving("all")
    setError("")
    try {
      await runOptimisticUpdate({
        snapshot: () => ({ notifications, totalCount, unreadCount }),
        apply: () => {
          setNotifications((current) =>
            current.map((notification) => ({ ...notification, unread: false }))
          )
          setUnreadCount(0)
        },
        request: markAllNotificationsRead,
        commit: (response) => setUnreadCount(response.unread_count),
        rollback: restoreNotifications,
      })
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to mark all notifications as read."
      )
    } finally {
      setSaving(null)
    }
  }

  async function deleteOne(notification: UmsNotification) {
    setSaving(notification.id)
    setError("")
    try {
      await runOptimisticUpdate({
        snapshot: () => ({ notifications, totalCount, unreadCount }),
        apply: () => {
          setNotifications((current) =>
            current.filter((item) => item.id !== notification.id)
          )
          setTotalCount((current) => Math.max(current - 1, 0))
          if (notification.unread) {
            setUnreadCount((current) => Math.max(current - 1, 0))
          }
        },
        request: () => deleteNotification(notification.id),
        commit: (response) => {
          setTotalCount(response.total_count)
          setUnreadCount(response.unread_count)
        },
        rollback: restoreNotifications,
      })
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to delete the notification."
      )
    } finally {
      setSaving(null)
    }
  }

  async function deleteRead() {
    setSaving("read")
    setError("")
    try {
      await runOptimisticUpdate({
        snapshot: () => ({ notifications, totalCount, unreadCount }),
        apply: () => {
          setNotifications((current) =>
            current.filter((notification) => notification.unread)
          )
          setTotalCount((current) => Math.max(current - loadedReadCount, 0))
        },
        request: deleteReadNotifications,
        commit: (response) => {
          setTotalCount(response.total_count)
          setUnreadCount(response.unread_count)
        },
        rollback: restoreNotifications,
      })
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to delete read notifications."
      )
    } finally {
      setSaving(null)
    }
  }

  async function openRelated(notification: UmsNotification, url: string) {
    await markRead(notification)
    router.push(url)
  }

  function restoreNotifications(snapshot: NotificationSnapshot) {
    setNotifications(snapshot.notifications)
    setTotalCount(snapshot.totalCount)
    setUnreadCount(snapshot.unreadCount)
  }

  const breadcrumbs = role
    ? [
        { href: role.href, title: role.label },
        { href: `${role.href}/notifications`, title: "Notifications" },
      ]
    : [{ href: "/notifications", title: "Notifications" }]

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={breadcrumbs} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Notifications
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Review portal alerts, open related work, and keep track of what
              still needs your attention.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => void load()} disabled={loading}>
              <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              onClick={() => void markAllRead()}
              disabled={unreadCount === 0 || saving !== null}
            >
              {saving === "all" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <CheckCheck className="size-4" />
              )}
              Mark all read
            </Button>
            <Button
              variant="outline"
              className="border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={() => void deleteRead()}
              disabled={readCount === 0 || saving !== null}
            >
              {saving === "read" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Trash2 className="size-4" />
              )}
              Delete all read
            </Button>
          </div>
        </section>

        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <section className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader>
              <CardDescription>All notifications</CardDescription>
              <CardTitle className="text-3xl">{totalCount}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Needs attention</CardDescription>
              <CardTitle className="text-3xl">{unreadCount}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Read in recent history</CardDescription>
              <CardTitle className="text-3xl">{readCount}</CardTitle>
            </CardHeader>
          </Card>
        </section>

        <section className="flex flex-wrap gap-2" aria-label="Notification filters">
          {(
            [
              ["all", `All (${notifications.length})`],
              ["unread", `Unread (${loadedUnreadCount})`],
              ["read", `Read (${loadedReadCount})`],
            ] as const
          ).map(([value, label]) => (
            <Button
              key={value}
              size="sm"
              variant={filter === value ? "default" : "outline"}
              onClick={() => setFilter(value)}
            >
              {label}
            </Button>
          ))}
        </section>

        {loading ? (
          <Card>
            <CardContent className="flex items-center justify-center gap-3 py-16 text-sm text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
              Loading notifications...
            </CardContent>
          </Card>
        ) : visibleNotifications.length ? (
          <section className="space-y-3">
            {visibleNotifications.map((notification) => {
              const url = relatedUrl(notification)
              const details = metadata(notification)
              return (
                <Card
                  key={notification.id}
                  className={
                    notification.unread
                      ? "border-primary/35 bg-primary/[0.035]"
                      : "border-border/70"
                  }
                >
                  <CardContent className="flex flex-col gap-4 py-5 sm:flex-row sm:items-start">
                    <span
                      className={`flex size-10 shrink-0 items-center justify-center rounded-full ${
                        notification.unread
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {notification.unread ? (
                        <BellRing className="size-5" />
                      ) : (
                        <Bell className="size-5" />
                      )}
                    </span>
                    <div className="min-w-0 flex-1 space-y-3">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium leading-6">
                              {notification.verb}
                            </p>
                            {notification.unread ? (
                              <Badge>Unread</Badge>
                            ) : (
                              <Badge variant="secondary">Read</Badge>
                            )}
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {notification.actor
                              ? `${notification.actor.name} · ${notification.actor.role}`
                              : "Portal notification"}{" "}
                            · {formatTimestamp(notification.created_at)}
                          </p>
                        </div>
                      </div>
                      {details.length ? (
                        <div className="flex flex-wrap gap-2">
                          {details.map(([key, value]) => (
                            <span
                              key={key}
                              className="rounded-md border bg-background px-2.5 py-1 text-xs text-muted-foreground"
                            >
                              <strong className="font-medium text-foreground">
                                {metadataLabel(key)}:
                              </strong>{" "}
                              {formatMetadataValue(value)}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      <div className="flex flex-wrap gap-2">
                        {url ? (
                          <Button
                            size="sm"
                            onClick={() => void openRelated(notification, url)}
                            disabled={saving === notification.id}
                          >
                            <ExternalLink className="size-4" />
                            Open related page
                          </Button>
                        ) : null}
                        {notification.unread ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => void markRead(notification)}
                            disabled={saving === notification.id}
                          >
                            {saving === notification.id ? (
                              <Loader2 className="size-4 animate-spin" />
                            ) : (
                              <Check className="size-4" />
                            )}
                            Mark as read
                          </Button>
                        ) : null}
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => void deleteOne(notification)}
                          disabled={saving === notification.id}
                        >
                          {saving === notification.id ? (
                            <Loader2 className="size-4 animate-spin" />
                          ) : (
                            <Trash2 className="size-4" />
                          )}
                          Delete
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </section>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
              <Inbox className="size-9 text-muted-foreground" />
              <p className="font-medium">No {filter !== "all" ? filter : ""} notifications</p>
              <p className="max-w-md text-sm text-muted-foreground">
                {filter === "all"
                  ? "Workflow alerts and portal notices will appear here when they are created."
                  : "Choose another filter to review the rest of your notification history."}
              </p>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
