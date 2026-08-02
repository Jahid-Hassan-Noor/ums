"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"

export function NotificationsButton({
  count = 0,
  onClick,
}: {
  count?: number
  onClick?: (e: React.MouseEvent) => void
}) {
  const router = useRouter()
  const label = count > 9 ? "9+" : String(count)

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon-md"
        onClick={(e) => {
          onClick?.(e)
          router.push("/notifications")
        }}
        aria-label={`You have ${count} notifications`}
        title={`${count} notifications`}
      >
        <Bell className="size-6" />

      {count > 0 && (
        <span className="absolute -top-1 -right-1 inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-destructive text-destructive-foreground text-xs font-medium px-1.5">
          {label}
        </span>
      )}
      </Button>
    </div>
  )
}

export default NotificationsButton
