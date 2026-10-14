"use client"

import * as React from "react"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Archive,
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FileText,
  GraduationCap,
  Home,
  LayoutDashboard,
  Palette,
  Settings,
  Upload,
  Users,
  Vote,
  type LucideIcon,
} from "lucide-react"

import { NavMain } from "@/components/sidebar/nav-main"
import { NavSecondary } from "@/components/sidebar/nav-secondary"
import { NavUser } from "@/components/sidebar/nav-user"
import { type AuthUser, type UserRole } from "@/lib/auth"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  filterUmsNavItemsBySettings,
  loadPublicUmsSettings,
  zoneForUmsRole,
} from "@/lib/ums-settings"
import {
  type UmsIconKey,
  type UmsNavItem,
} from "@/lib/ums-roles"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"

const iconMap: Record<UmsIconKey, LucideIcon> = {
  academic: Building2,
  assignments: FileText,
  attendance: ClipboardCheck,
  calendar: CalendarDays,
  courses: BookOpen,
  dashboard: LayoutDashboard,
  elections: Vote,
  hostels: Home,
  imports: Upload,
  leave: ClipboardList,
  notifications: Bell,
  palette: Palette,
  records: Archive,
  results: GraduationCap,
  semesters: CalendarDays,
  settings: Settings,
  statistics: BarChart3,
  users: Users,
}

function withIcons(items: UmsNavItem[]) {
  return items.map((item) => ({
    title: item.title,
    url: item.url,
    icon: iconMap[item.icon],
    items: item.items?.map(({ title, url }) => ({ title, url })),
  }))
}

function filterExecutiveItems(items: UmsNavItem[], user: AuthUser) {
  if (user.executive_scope?.academic_workflows !== false) return items

  const hiddenTopLevel = new Set(["/executive/courses", "/executive/results"])
  const hiddenChildren = new Set([
    "/executive/manage/students",
    "/executive/manage/schedule",
  ])

  return items
    .filter((item) => !hiddenTopLevel.has(item.url))
    .map((item) => ({
      ...item,
      items: item.items?.filter((child) => !hiddenChildren.has(child.url)),
    }))
}

export function AppSidebar({
  role,
  user,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  role: UserRole
  user: AuthUser
}) {
  const { setOpen, setOpenMobile } = useSidebar()
  const pathname = usePathname()
  const [publicSettings, setPublicSettings] = React.useState(
    DEFAULT_UMS_PUBLIC_SETTINGS
  )
  const zone = zoneForUmsRole(role, publicSettings)

  React.useEffect(() => {
    let ignore = false
    void loadPublicUmsSettings().then((settings) => {
      if (!ignore) {
        setPublicSettings(settings)
      }
    })
    return () => {
      ignore = true
    }
  }, [])

  React.useEffect(() => {
    if (publicSettings.uiCustomization.sidebar_collapsed_by_default) {
      setOpen(false)
    }
  }, [publicSettings.uiCustomization.sidebar_collapsed_by_default, setOpen])

  React.useEffect(() => {
    setOpenMobile(false)
  }, [pathname, setOpenMobile])

  const navMain = React.useMemo(
    () => {
      const featureItems = filterUmsNavItemsBySettings(
        zone.navMain,
        publicSettings,
        role
      )
      return withIcons(
        role === "executive"
          ? filterExecutiveItems(featureItems, user)
          : featureItems
      )
    },
    [publicSettings, role, user, zone.navMain]
  )
  const navSecondary = React.useMemo(
    () =>
      withIcons(
        filterUmsNavItemsBySettings(zone.navSecondary, publicSettings, role)
      ),
    [publicSettings, role, zone.navSecondary]
  )
  const displayName =
    [user.first_name, user.last_name].filter(Boolean).join(" ").trim() || user.username || "User"
  const dashboardBrand =
    publicSettings.uiCustomization.sidebar_label ||
    publicSettings.uiCustomization.brand_name ||
    publicSettings.university.name
  const logoSrc =
    publicSettings.uiCustomization.logo_url || publicSettings.university.logo_url
  const logoAlt =
    publicSettings.uiCustomization.logo_alt_text ||
    `${publicSettings.university.short_name} logo`
  const userAvatar =
    user.profile_picture || publicSettings.uiCustomization.default_avatar_url

  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" render={<Link href={zone.dashboardPath} />}>
              <div className="flex shrink-0 items-center justify-center rounded-lg bg-white p-1 shadow-sm h-8 w-8 ring-1 ring-slate-200 dark:ring-white/10">
                <Image
                  src={logoSrc}
                  alt={logoAlt}
                  width={24}
                  height={24}
                  unoptimized
                  className="object-contain"
                />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{dashboardBrand}</span>
                <span className="truncate text-xs">{zone.shortLabel.toUpperCase()}</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
        <NavSecondary items={navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser
          user={{
            name: displayName,
            email: user.email || "no-email@example.edu",
            avatar: userAvatar,
          }}
        />
      </SidebarFooter>
    </Sidebar>
  )
}
