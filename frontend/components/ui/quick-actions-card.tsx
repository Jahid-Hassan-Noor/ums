import Link from "next/link"
import { ArrowRight } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type QuickActionLink = {
  href: string
  label: string
}

type QuickActionsCardProps = {
  description: string
  links: QuickActionLink[]
  title?: string
}

export default function QuickActionsCard({
  description,
  links,
  title = "Quick Actions",
}: QuickActionsCardProps) {
  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-foreground text-base">{title}</CardTitle>
        <CardDescription className="text-muted-foreground text-sm">{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="bg-muted/35 border-border text-foreground hover:bg-muted inline-flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm transition"
          >
            {link.label}
            <ArrowRight className="size-4" />
          </Link>
        ))}
      </CardContent>
    </Card>
  )
}