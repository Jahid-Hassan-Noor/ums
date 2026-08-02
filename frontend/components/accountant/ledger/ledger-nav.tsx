"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, ShieldAlert, Zap, CreditCard, AlertCircle } from "lucide-react"

import { cn } from "@/lib/utils"

const TABS = [
  { title: "Overview", url: "/accountant/ledger", icon: LayoutDashboard },
  { title: "Holds", url: "/accountant/ledger/holds", icon: ShieldAlert },
  { title: "Bulk Charge", url: "/accountant/ledger/bulk-charge", icon: Zap },
  { title: "Payment Plans", url: "/accountant/ledger/payment-plans", icon: CreditCard },
  { title: "Fines & Charges", url: "/accountant/ledger/fines", icon: AlertCircle },
]

export function LedgerNav() {
  const pathname = usePathname()

  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-border/70 pb-px">
      {TABS.map((tab) => {
        const isActive = tab.url === "/accountant/ledger"
          ? pathname === tab.url
          : pathname.startsWith(tab.url)
        return (
          <Link
            key={tab.url}
            href={tab.url}
            className={cn(
              "flex items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <tab.icon className="size-4" />
            {tab.title}
          </Link>
        )
      })}
    </nav>
  )
}
