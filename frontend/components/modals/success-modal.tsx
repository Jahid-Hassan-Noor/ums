"use client"

import { BaseStatusModal } from "@/components/modals/base-status-modal"

type SuccessModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  message: string
  actionLabel?: string
  onAction?: () => void
}

export function SuccessModal({
  open,
  onOpenChange,
  title = "Success",
  message,
  actionLabel,
  onAction,
}: SuccessModalProps) {
  return (
    <BaseStatusModal
      open={open}
      onOpenChange={onOpenChange}
      tone="success"
      title={title}
      message={message}
      actionLabel={actionLabel}
      onAction={onAction}
    />
  )
}

export default SuccessModal
