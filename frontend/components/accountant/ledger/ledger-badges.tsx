"use client"

import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary/10 text-primary border-primary/20",
        secondary: "bg-secondary text-secondary-foreground border-secondary/50",
        destructive: "bg-destructive/10 text-destructive border-destructive/20",
        success: "bg-emerald-50 text-emerald-700 border-emerald-200",
        warning: "bg-amber-50 text-amber-700 border-amber-200",
        info: "bg-blue-50 text-blue-700 border-blue-200",
        outline: "text-muted-foreground border-border",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export function Badge({
  className,
  variant,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}

export function LedgerEntryBadge({ type }: { type: string }) {
  const variantMap: Record<string, "destructive" | "success" | "info" | "warning" | "secondary" | "default"> = {
    debit: "destructive",
    payment: "success",
    waiver: "info",
    refund: "warning",
    reversal: "secondary",
    adjustment: "default",
  }
  return <Badge variant={variantMap[type] ?? "outline"}>{type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}</Badge>
}

export function ChargeStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, "destructive" | "success" | "info" | "warning" | "secondary" | "default"> = {
    draft: "secondary",
    posted: "default",
    waived: "info",
    reversed: "warning",
  }
  return <Badge variant={variantMap[status] ?? "outline"}>{status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}</Badge>
}

export function HoldStatusBadge({ isActive }: { isActive: boolean }) {
  return <Badge variant={isActive ? "destructive" : "success"}>{isActive ? "Active" : "Released"}</Badge>
}

export function PlanStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, "destructive" | "success" | "info" | "warning" | "secondary" | "default"> = {
    active: "info",
    completed: "success",
    cancelled: "destructive",
  }
  return <Badge variant={variantMap[status] ?? "outline"}>{status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}</Badge>
}

export function InstallmentStatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, "destructive" | "success" | "info" | "warning" | "secondary" | "default"> = {
    pending: "secondary",
    paid: "success",
    overdue: "destructive",
    cancelled: "warning",
  }
  return <Badge variant={variantMap[status] ?? "outline"}>{status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}</Badge>
}
