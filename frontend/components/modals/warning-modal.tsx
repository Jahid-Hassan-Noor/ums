"use client"

import { BaseStatusModal } from "@/components/modals/base-status-modal"

type WarningModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  message: string
  actionLabel?: string
  onAction?: () => void
  cancelLabel?: string
  onCancel?: () => void
}

export function WarningModal({
  open,
  onOpenChange,
  title = "Action needed",
  message,
  actionLabel,
  onAction,
  cancelLabel,
  onCancel,
}: WarningModalProps) {
  return (
    <BaseStatusModal
      open={open}
      onOpenChange={onOpenChange}
      tone="warning"
      title={title}
      message={message}
      actionLabel={actionLabel}
      onAction={onAction}
      cancelLabel={cancelLabel}
      onCancel={onCancel}
    />
  )
}

export default WarningModal
