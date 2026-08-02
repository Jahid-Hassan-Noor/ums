"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { BookOpen, Building2, Download, History, Loader2, Users } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { loadReportExports, type ReportExportsResponse } from "@/lib/admin-reports"

const sections = [
  {
    title: "People Reports",
    href: "/admin/reports/people",
    description: "Filtered XLSX exports for students, teachers, executives, and applicants.",
    icon: Users,
    detail: "Role directories and admissions accounts",
  },
  {
    title: "Academic Reports",
    href: "/admin/reports/academic",
    description: "Academic directory, offerings, registrations, attendance, and leave.",
    icon: BookOpen,
    detail: "Learning and academic administration",
  },
  {
    title: "Operations Reports",
    href: "/admin/reports/operations",
    description: "Venue, hostel, canteen, library, ICT, and audit exports.",
    icon: Building2,
    detail: "Campus operations and governance",
  },
  {
    title: "Export History",
    href: "/admin/reports/exports",
    description: "Review, redownload, and remove generated report files.",
    icon: History,
    detail: "Stored export files and statuses",
  },
]

export function AdminReportsOverviewPage() {
  const [history, setHistory] = useState<ReportExportsResponse | null>(null)

  useEffect(() => {
    void loadReportExports().then(setHistory).catch(() => setHistory(null))
  }, [])

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/reports", title: "Reports" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Reports</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Generate focused exports by report category and revisit every completed workbook
            from one history.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          {sections.map((section) => (
            <Link key={section.href} href={section.href} className="group">
              <Card className="h-full border-border/70 bg-card/95 shadow-sm transition group-hover:border-primary/40 group-hover:shadow-md">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="rounded-lg border bg-muted/50 p-2.5">
                      <section.icon className="size-5 text-primary" />
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">Open reports</span>
                  </div>
                  <CardTitle className="pt-2 text-lg">{section.title}</CardTitle>
                  <CardDescription className="leading-6">{section.description}</CardDescription>
                </CardHeader>
                <CardContent className="text-xs font-medium text-muted-foreground">
                  {section.detail}
                </CardContent>
              </Card>
            </Link>
          ))}
        </section>

        <Card className="border-border/70 bg-card/95 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Download className="size-5" />
              Export Activity
            </CardTitle>
            <CardDescription>Current stored-export totals.</CardDescription>
          </CardHeader>
          <CardContent>
            {!history ? (
              <Loader2 className="size-5 animate-spin text-muted-foreground" />
            ) : (
              <div className="grid gap-3 sm:grid-cols-4">
                {[
                  ["Total", history.summary.total],
                  ["Processing", history.summary.processing],
                  ["Completed", history.summary.completed],
                  ["Failed", history.summary.failed],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg border bg-muted/20 p-3">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="mt-1 text-xl font-semibold">{value}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
