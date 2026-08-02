"use client"

import * as React from "react"

export type ThemeMode = "light" | "dark"

export const THEME_STORAGE_KEY = "theme"

const THEME_CHANGE_EVENT = "ums-theme-change"

function isThemeMode(value: string | null): value is ThemeMode {
  return value === "light" || value === "dark"
}

function systemTheme(): ThemeMode {
  if (
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "dark"
  }

  return "light"
}

export function getPreferredTheme(): ThemeMode {
  if (typeof window === "undefined") return "light"

  try {
    const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
    return isThemeMode(storedTheme) ? storedTheme : systemTheme()
  } catch {
    return systemTheme()
  }
}

export function applyTheme(theme: ThemeMode) {
  if (typeof document === "undefined") return
  document.documentElement.classList.toggle("dark", theme === "dark")
}

function persistTheme(theme: ThemeMode) {
  applyTheme(theme)

  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    window.dispatchEvent(
      new CustomEvent<ThemeMode>(THEME_CHANGE_EVENT, { detail: theme })
    )
  } catch {
    // Storage can be unavailable in restricted browser contexts.
  }
}

export function useThemePreference() {
  const [theme, setThemeState] = React.useState<ThemeMode | null>(null)

  React.useEffect(() => {
    let frameId: number | null = null
    const nextTheme = getPreferredTheme()
    applyTheme(nextTheme)
    frameId = window.requestAnimationFrame(() => {
      setThemeState(nextTheme)
    })

    const handleThemeChange = (event: Event) => {
      const next = (event as CustomEvent<ThemeMode>).detail
      if (isThemeMode(next)) {
        applyTheme(next)
        setThemeState(next)
      }
    }

    const handleStorage = (event: StorageEvent) => {
      if (event.key !== THEME_STORAGE_KEY) return
      const next = isThemeMode(event.newValue) ? event.newValue : systemTheme()
      applyTheme(next)
      setThemeState(next)
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const handleSystemTheme = () => {
      try {
        if (isThemeMode(window.localStorage.getItem(THEME_STORAGE_KEY))) return
      } catch {
        // Fall through and mirror system preference.
      }

      const next = systemTheme()
      applyTheme(next)
      setThemeState(next)
    }

    window.addEventListener(THEME_CHANGE_EVENT, handleThemeChange)
    window.addEventListener("storage", handleStorage)
    media.addEventListener("change", handleSystemTheme)

    return () => {
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId)
      }
      window.removeEventListener(THEME_CHANGE_EVENT, handleThemeChange)
      window.removeEventListener("storage", handleStorage)
      media.removeEventListener("change", handleSystemTheme)
    }
  }, [])

  const setTheme = React.useCallback((nextTheme: ThemeMode) => {
    setThemeState(nextTheme)
    persistTheme(nextTheme)
  }, [])

  const toggleTheme = React.useCallback(() => {
    const currentTheme = theme ?? getPreferredTheme()
    setTheme(currentTheme === "dark" ? "light" : "dark")
  }, [setTheme, theme])

  return {
    theme,
    isDark: theme === "dark",
    setTheme,
    toggleTheme,
  }
}
