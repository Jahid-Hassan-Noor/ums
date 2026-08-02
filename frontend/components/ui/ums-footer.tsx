"use client"

import * as React from "react"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  loadPublicUmsSettings,
} from "@/lib/ums-settings"

export function UmsFooter() {
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

  if (!publicSettings.uiCustomization.show_footer) return null

  const university = publicSettings.university

  return (
    <footer className="border-t border-border/70 bg-card px-6 py-4 text-center text-xs text-muted-foreground">
      <p>
        &copy; {new Date().getFullYear()}{" "}
        {university.legal_name || university.name}. All rights reserved.
      </p>
      {university.tagline ? (
        <p className="mt-0.5">{university.tagline}</p>
      ) : null}
    </footer>
  )
}
