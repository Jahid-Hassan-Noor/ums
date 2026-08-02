"use client"

import { BaseStatusModal } from "@/components/modals/base-status-modal"

type ErrorModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  message: string
  actionLabel?: string
  onAction?: () => void
}

export function ErrorModal({
  open,
  onOpenChange,
  title = "Something went wrong",
  message,
  actionLabel,
  onAction,
}: ErrorModalProps) {
  return (
    <BaseStatusModal
      open={open}
      onOpenChange={onOpenChange}
      tone="error"
      title={title}
      message={message}
      actionLabel={actionLabel}
      onAction={onAction}
    />
  )
}

export default ErrorModal
