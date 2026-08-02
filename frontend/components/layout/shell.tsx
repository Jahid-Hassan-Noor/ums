"use client"

import * as React from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import InfoModal from "@/components/modals/info-modal"
import WarningModal from "@/components/modals/warning-modal"
import { BackendRouteConnector } from "@/components/backend-route-connector"
import { UmsChatbot } from "@/components/chatbot/ums-chatbot"
import { UmsFooter } from "@/components/ui/ums-footer"
import LoadingScreen from "@/components/ui/loading-screen"
import { NotFoundRouteContext } from "@/components/layout/not-found-route-context"
import { AppSidebar } from "@/components/sidebar/app-sidebar"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import {
  canAccessRole,
  defaultRouteForRole,
  ensureValidSession,
  getRequiredRole,
  isProtectedUmsPath,
  isPublicPath,
  type AuthSession,
} from "@/lib/auth"

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const searchParams = useSearchParams()
  const isAuthEntryPath = pathname === "/login"
  const [session, setSession] = React.useState<AuthSession | null>(null)
  const [isChecking, setIsChecking] = React.useState(true)
  const [isUnauthorized, setIsUnauthorized] = React.useState(false)
  const [notFoundPathname, setNotFoundPathname] = React.useState<string | null>(
    null
  )
  const [showUnauthorizedModal, setShowUnauthorizedModal] =
    React.useState(false)
  const [showAlreadyLoggedInModal, setShowAlreadyLoggedInModal] =
    React.useState(false)
  const isPublicRoute = isPublicPath(pathname)
  const isUmsRoute = isProtectedUmsPath(pathname)
  const isNotFoundRoute = notFoundPathname === pathname
  const rendersWithoutUmsShell =
    isPublicRoute || isNotFoundRoute || !isUmsRoute
  const setCurrentRouteNotFound = React.useCallback(
    (nextIsNotFoundRoute: boolean) => {
      if (nextIsNotFoundRoute) {
        setNotFoundPathname(pathname)
      }
    },
    [pathname]
  )

  React.useEffect(() => {
    let isMounted = true

    const validateRoute = async () => {
      const query = typeof window !== "undefined" ? window.location.search : ""
      const currentPath = query ? `${pathname}${query}` : pathname

      if (isPublicRoute || !isUmsRoute || isNotFoundRoute) {
        if (isAuthEntryPath) {
          setIsChecking(true)
          const nextSession = await ensureValidSession()

          if (!isMounted) return

          if (nextSession) {
            setSession(nextSession)
            setIsUnauthorized(false)
            setIsChecking(false)
            router.replace(
              `${defaultRouteForRole(nextSession.role)}?already_logged_in=1`
            )
            return
          }
        }

        if (!isMounted) return
        setIsChecking(false)
        setSession(null)
        setIsUnauthorized(false)
        return
      }

      setIsChecking(true)
      const nextSession = await ensureValidSession()

      if (!isMounted) return

      if (!nextSession) {
        setSession(null)
        setIsChecking(false)
        setIsUnauthorized(false)
        router.replace(`/login?next=${encodeURIComponent(currentPath)}`)
        return
      }

      const requiredRole = getRequiredRole(pathname)
      const blocked =
        requiredRole !== null && !canAccessRole(nextSession.role, requiredRole)

      setSession(nextSession)
      setIsUnauthorized(blocked)
      setShowUnauthorizedModal(blocked)
      setIsChecking(false)
    }

    validateRoute()
    return () => {
      isMounted = false
    }
  }, [
    isAuthEntryPath,
    isNotFoundRoute,
    isUmsRoute,
    isPublicRoute,
    pathname,
    router,
  ])

  React.useEffect(() => {
    let frameId: number | null = null

    if (rendersWithoutUmsShell) return
    if (isChecking || !session || isUnauthorized) return
    if (searchParams.get("already_logged_in") !== "1") return

    frameId = window.requestAnimationFrame(() => {
      setShowAlreadyLoggedInModal(true)
    })

    const params = new URLSearchParams(searchParams.toString())
    params.delete("already_logged_in")
    const nextQuery = params.toString()
    router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname)

    return () => {
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId)
      }
    }
  }, [
    isChecking,
    isUnauthorized,
    pathname,
    rendersWithoutUmsShell,
    router,
    searchParams,
    session,
  ])

  const content = (
    <NotFoundRouteContext.Provider value={setCurrentRouteNotFound}>
      {children}
    </NotFoundRouteContext.Provider>
  )

  if (rendersWithoutUmsShell) {
    if (isAuthEntryPath && isChecking) {
      return (
        <>
          <BackendRouteConnector />
          <LoadingScreen label={null} className="min-h-screen" />
        </>
      )
    }
    return (
      <>
        <BackendRouteConnector />
        {content}
        <UmsFooter />
        <UmsChatbot />
      </>
    )
  }

  if (!session) {
    return <LoadingScreen label={null} className="min-h-screen" />
  }

  if (isUnauthorized) {
    return (
      <WarningModal
        open={showUnauthorizedModal}
        onOpenChange={setShowUnauthorizedModal}
        title="Access restricted"
        message="Your account role does not allow access to this page."
        actionLabel="Go to my dashboard"
        onAction={() => {
          setIsUnauthorized(false)
          router.replace(defaultRouteForRole(session.role))
        }}
      />
    )
  }

  return (
    <>
      <BackendRouteConnector />
      <InfoModal
        open={showAlreadyLoggedInModal}
        onOpenChange={setShowAlreadyLoggedInModal}
        title="Already logged in"
        message="You are already logged in."
        actionLabel="OK"
      />
      <SidebarProvider>
        <AppSidebar role={session.role} user={session.user} />
        <SidebarInset>
          {content}
          <UmsFooter />
        </SidebarInset>
      </SidebarProvider>
      <UmsChatbot />
    </>
  )
}

export default Shell
