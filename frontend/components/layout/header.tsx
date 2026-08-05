"use client"

import * as React from "react"
import { usePathname } from "next/navigation"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb"
import { SearchForm } from "@/components/sidebar/search-form"
import NotificationsButton from "@/components/ui/notifications-button"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { apiFetch } from "@/lib/auth"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  loadPublicUmsSettings,
} from "@/lib/ums-settings"

import { cn } from "@/lib/utils"

type HeaderBreadcrumb = {
  href: string
  title: string
}

function titleFromPath(pathname: string | null) {
  if (!pathname || pathname === "/") return "Home"
  // remove trailing slash
  const path = pathname.replace(/\/$/, "")
  const parts = path.split("/").filter(Boolean)
  // If root of a section like /dashboard -> Dashboard
  const last = parts[parts.length - 1]
  // map common names
  const mapping: Record<string, string> = {
    academic: "Academic Setup",
    dashboard: "Dashboard",
    executive: "Executive",
    librarian: "Librarian",
    caterer: "Caterer",
    technician: "Technician",
    "ict-helpdesk": "Service Desk",
    "schools-centers": "Schools & Centers",
    profile: "Profile",
    notifications: "Notifications",
    register: "Course Registration",
    results: "Results",
    semesters: "Semesters",
    settings: "Settings",
    student: "Student",
    teacher: "Teacher",
  }
  if (mapping[last]) return mapping[last]
  // Convert kebab/camel to Title Case
  const words = last.replace(/[-_]/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2")
  return words
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ")
}

function generateBreadcrumbs(pathname: string | null) {
  if (!pathname || pathname === "/") return []
  const path = pathname.replace(/\/$/, "")
  const parts = path.split("/").filter(Boolean)
  
  return parts.map((part, index) => {
    const href = "/" + parts.slice(0, index + 1).join("/")
    const title = titleFromPath(href)
    return { href, title }
  })
}

type HeaderProps = {
  breadcrumbItems?: HeaderBreadcrumb[]
}

export function Header({ breadcrumbItems }: HeaderProps) {
  const pathname = usePathname()
  const breadcrumbs = breadcrumbItems ?? generateBreadcrumbs(pathname)
  const isSingleLevel = breadcrumbs.length === 1
  const [notificationCount, setNotificationCount] = React.useState(0)
  const [publicSettings, setPublicSettings] = React.useState(
    DEFAULT_UMS_PUBLIC_SETTINGS
  )

  React.useEffect(() => {
    let ignore = false
    void loadPublicUmsSettings().then((settings) => {
      if (!ignore) setPublicSettings(settings)
    })
    return () => {
      ignore = true
    }
  }, [])

  React.useEffect(() => {
    let isMounted = true

    const loadNotificationCount = async () => {
      try {
        const response = await apiFetch<{ unread_count?: number }>("/notifications/summary/")
        if (isMounted) {
          setNotificationCount(response.unread_count ?? 0)
        }
      } catch {
        if (isMounted) {
          setNotificationCount(0)
        }
      }
    }

    void loadNotificationCount()
    const interval = window.setInterval(() => {
      void loadNotificationCount()
    }, 60000)

    return () => {
      isMounted = false
      window.clearInterval(interval)
    }
  }, [])

  const showBreadcrumbs = publicSettings.uiCustomization.show_breadcrumbs

  return (
    <header className={cn(
      "flex min-w-0 shrink-0 flex-col gap-3 py-2 sm:h-16 sm:flex-row sm:items-center sm:justify-between ums-sticky-header",
    )}>
      <div className="flex min-w-0 items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1 shrink-0" />
        <Separator orientation="vertical" className="mr-2 shrink-0 data-[orientation=vertical]:h-7" />
        {showBreadcrumbs ? (
          <Breadcrumb className="min-w-0">
            <BreadcrumbList className="min-w-0 flex-nowrap sm:flex-wrap">
              {breadcrumbs.length === 0 ? (
                <BreadcrumbItem className="min-w-0">
                  <BreadcrumbPage className="block max-w-[10rem] truncate sm:max-w-none">Home</BreadcrumbPage>
                </BreadcrumbItem>
              ) : isSingleLevel ? (
                <BreadcrumbItem className="min-w-0">
                  <BreadcrumbPage className="block max-w-[10rem] truncate sm:max-w-none">{breadcrumbs[0].title}</BreadcrumbPage>
                </BreadcrumbItem>
              ) : (
                <>
                  {breadcrumbs.map((crumb, index) => (
                    <React.Fragment key={crumb.href}>
                      <BreadcrumbItem className={index === 0 ? "hidden min-w-0 md:block" : "min-w-0"}>
                        {index === breadcrumbs.length - 1 ? (
                          <BreadcrumbPage className="block max-w-[10rem] truncate sm:max-w-none">{crumb.title}</BreadcrumbPage>
                        ) : (
                          <BreadcrumbLink className="block max-w-[9rem] truncate sm:max-w-none" href={crumb.href}>
                            {crumb.title}
                          </BreadcrumbLink>
                        )}
                      </BreadcrumbItem>
                      {index < breadcrumbs.length - 1 && (
                        <BreadcrumbSeparator className={index === 0 ? "hidden md:block" : ""} />
                      )}
                    </React.Fragment>
                  ))}
                </>
              )}
            </BreadcrumbList>
          </Breadcrumb>
        ) : null}
      </div>

      <div className="flex w-full min-w-0 items-center justify-end gap-2 px-4 sm:w-auto sm:px-0 sm:pr-6">
        <SearchForm className="min-w-0 flex-1 sm:w-72 sm:flex-none" />
        <NotificationsButton count={notificationCount} />
        <ThemeToggle />
      </div>
    </header>
  )
}

export default Header
