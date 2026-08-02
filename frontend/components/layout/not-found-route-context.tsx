"use client"

import * as React from "react"

export const NotFoundRouteContext = React.createContext<
  ((isNotFoundRoute: boolean) => void) | null
>(null)

export function NotFoundRouteMarker() {
  const setIsNotFoundRoute = React.useContext(NotFoundRouteContext)

  React.useEffect(() => {
    setIsNotFoundRoute?.(true)
  }, [setIsNotFoundRoute])

  return null
}
