"use client"

import { Sun, Moon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useThemePreference } from "@/hooks/use-theme"
import { cn } from "@/lib/utils"

type ThemeToggleProps = {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { isDark, toggleTheme } = useThemePreference()

  return (
    <Button
      variant="outline"
      size="icon-md"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label="Toggle color scheme"
      title={isDark ? "Switch to light" : "Switch to dark"}
      className={cn(
        "border-slate-200 bg-white text-slate-950 shadow-sm hover:bg-slate-100 dark:border-white/12 dark:bg-white/10 dark:text-white dark:hover:bg-white/16",
        className
      )}
    >
      {isDark ? <Sun className="size-6" /> : <Moon className="size-6" />}
    </Button>
  )
}
