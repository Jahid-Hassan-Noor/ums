"use client"

import { useEffect, useState } from "react"

import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  loadPublicUmsSettings,
  type UmsPublicSettings,
} from "@/lib/ums-settings"

export function usePublicUmsSettings() {
  const [settings, setSettings] = useState<UmsPublicSettings>(DEFAULT_UMS_PUBLIC_SETTINGS)

  useEffect(() => {
    let active = true
    void loadPublicUmsSettings().then((nextSettings) => {
      if (active) setSettings(nextSettings)
    })
    return () => {
      active = false
    }
  }, [])

  return settings
}
