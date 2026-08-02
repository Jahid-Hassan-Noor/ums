"use client"

import { AlertTriangle, CheckCircle2, Info, type LucideIcon, XCircle } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { cn } from "@/lib/utils"

type ModalTone = "error" | "info" | "success" | "warning"

type BaseStatusModalProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  message: string
  actionLabel?: string
  onAction?: () => void
  cancelLabel?: string
  onCancel?: () => void
  tone: ModalTone
}

const toneConfig: Record<
  ModalTone,
  {
    icon: LucideIcon
    mediaClassName: string
    actionClassName: string
  }
> = {
  error: {
    icon: XCircle,
    mediaClassName: "bg-destructive/10 text-destructive",
    actionClassName: "bg-destructive text-white hover:bg-destructive/90",
  },
  info: {
    icon: Info,
    mediaClassName: "bg-sky-500/15 text-sky-600 dark:text-sky-300",
    actionClassName: "bg-sky-600 text-white hover:bg-sky-500",
  },
  success: {
    icon: CheckCircle2,
    mediaClassName: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300",
    actionClassName: "bg-emerald-600 text-white hover:bg-emerald-500",
  },
  warning: {
    icon: AlertTriangle,
    mediaClassName: "bg-amber-500/15 text-amber-600 dark:text-amber-300",
    actionClassName: "bg-amber-500 text-white hover:bg-amber-400",
  },
}

export function BaseStatusModal({
  open,
  onOpenChange,
  title,
  message,
  actionLabel = "Okay",
  onAction,
  cancelLabel,
  onCancel,
  tone,
}: BaseStatusModalProps) {
  const config = toneConfig[tone]
  const Icon = config.icon

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent
        size="default"
        className="max-w-[32rem] p-6 data-open:slide-in-from-top-3 data-open:duration-300"
      >
        <AlertDialogHeader className="gap-3">
          <AlertDialogMedia className={cn("size-14 rounded-2xl", config.mediaClassName)}>
            <Icon className="size-8 animate-pulse" />
          </AlertDialogMedia>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{message}</AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter className="flex-row justify-center gap-3 sm:flex-row sm:justify-center">
          {cancelLabel ? (
            <AlertDialogCancel
              className="min-w-28"
              onClick={() => {
                onCancel?.()
                onOpenChange(false)
              }}
            >
              {cancelLabel}
            </AlertDialogCancel>
          ) : null}
          <AlertDialogAction
            className={cn("min-w-28", config.actionClassName)}
            onClick={() => {
              onAction?.()
              onOpenChange(false)
            }}
          >
            {actionLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default BaseStatusModal
