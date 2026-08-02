"use client"

import { useThemePreference } from "@/hooks/use-theme"

export function useIsDarkMode() {
  const { isDark } = useThemePreference()

  return isDark
}
