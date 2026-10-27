import { ExecutiveCalendarPage } from "@/components/executive/executive-calendar-page"
import { redirect } from "next/navigation"
import { disabledUmsRouteModules, isUmsRoleFeaturePathEnabled, loadPublicUmsSettings } from "@/lib/ums-settings"

export default async function Page() {
  const settings = await loadPublicUmsSettings()
  if (!isUmsRoleFeaturePathEnabled("/executive/calendar", settings, "executive")) {
    const params = new URLSearchParams({ next: "/executive/calendar" })
    const modules = disabledUmsRouteModules("/executive/calendar", settings, "executive")
    if (modules.length) params.set("modules", modules.join(","))
    redirect(`/module-unavailable?${params.toString()}`)
  }
  return <ExecutiveCalendarPage />
}
