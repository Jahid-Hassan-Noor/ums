"use client"

import { useEffect, useState } from "react"

import { ConfigurableLoader } from "@/components/ui/configurable-loader"
import { cn } from "@/lib/utils"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  loadPublicUmsSettings,
  type UmsPublicSettings,
} from "@/lib/ums-settings"

type LoadingScreenProps = {
  label?: string | null
  className?: string
}

export function LoadingScreen({ label = "Loading...", className }: LoadingScreenProps) {
  const [settings, setSettings] = useState<UmsPublicSettings>(
    DEFAULT_UMS_PUBLIC_SETTINGS
  )

  useEffect(() => {
    let isMounted = true

    void loadPublicUmsSettings().then((nextSettings) => {
      if (isMounted) setSettings(nextSettings)
    })

    return () => {
      isMounted = false
    }
  }, [])

  const customization = settings.uiCustomization

  return (
    <div className={cn("flex min-h-[70vh] items-center justify-center p-6", className)}>
      <div className="flex flex-col items-center gap-3 text-sm text-muted-foreground">
        <ConfigurableLoader
          spinner={customization.loading_spinner}
          size={customization.loading_spinner_size}
          color={customization.icon_color || customization.button_color}
        />
        {label ? <span>{label}</span> : null}
      </div>
    </div>
  )
}

export default LoadingScreen
