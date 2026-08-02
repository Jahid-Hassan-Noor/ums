"use client"

import { BaseStatusModal } from "@/components/modals/base-status-modal"

type InfoModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  message: string
  actionLabel?: string
  onAction?: () => void
}

export function InfoModal({
  open,
  onOpenChange,
  title = "For your information",
  message,
  actionLabel,
  onAction,
}: InfoModalProps) {
  return (
    <BaseStatusModal
      open={open}
      onOpenChange={onOpenChange}
      tone="info"
      title={title}
      message={message}
      actionLabel={actionLabel}
      onAction={onAction}
    />
  )
}

export default InfoModal
