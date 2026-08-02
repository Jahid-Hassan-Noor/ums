"use client"

import { ChevronRight, type LucideIcon } from "lucide-react"
import { useMemo, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Collapsible,
  CollapsibleContent,
} from "@/components/ui/collapsible"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon: LucideIcon
    isActive?: boolean
    items?: {
      title: string
      url: string
    }[]
  }[]
}) {
  const pathname = usePathname()

  const activeMenuTitle = useMemo(() => {
    for (const item of items) {
      if (item.items?.some((subItem) => pathname === subItem.url || pathname.startsWith(subItem.url + "/"))) {
        return item.title
      }
      if (pathname === item.url || pathname.startsWith(item.url + "/")) {
        return item.title
      }
    }
    return null
  }, [items, pathname])

  const [openItems, setOpenItems] = useState<string[]>([])

  const setItemOpen = (title: string, nextOpen: boolean) => {
    setOpenItems((prev) => {
      if (nextOpen) {
        return prev.includes(title) ? prev : [...prev, title]
      }
      return prev.filter((itemTitle) => itemTitle !== title)
    })
  }

  const isSubItemActive = (url: string) => {
    return pathname === url || pathname.startsWith(url + "/")
  }

  const isItemActive = (url: string) => {
    return pathname === url || pathname.startsWith(url + "/")
  }

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => {
          if (!item.items?.length) {
            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  render={<Link href={item.url} />}
                  tooltip={item.title}
                  className={isItemActive(item.url) ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}
                >
                  <item.icon />
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          }

          const isOpen = openItems.includes(item.title) || activeMenuTitle === item.title

          return (
            <Collapsible
              key={item.title}
              open={isOpen}
              onOpenChange={(nextOpen) => {
                if (item.items?.length) {
                  setItemOpen(item.title, nextOpen)
                }
              }}
            >
              <SidebarMenuItem>
                <SidebarMenuButton
                  type="button"
                  onClick={() => {
                    setItemOpen(item.title, !isOpen)
                  }}
                  tooltip={item.title}
                  className={isItemActive(item.url) ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}
                  aria-expanded={isOpen}
                >
                  <item.icon />
                  <span>{item.title}</span>
                  <ChevronRight className={`ml-auto transition-transform duration-200 ${isOpen ? "rotate-90" : ""}`} />
                </SidebarMenuButton>
              </SidebarMenuItem>
              <CollapsibleContent>
                <SidebarMenuSub>
                  {item.items.map((subItem) => (
                    <SidebarMenuSubItem key={subItem.title}>
                      <SidebarMenuSubButton
                        render={<Link href={subItem.url} />}
                        className={isSubItemActive(subItem.url) ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}
                      >
                        <span>{subItem.title}</span>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
              </CollapsibleContent>
            </Collapsible>
          )
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}
