import type { Metadata } from "next"
import { Suspense, type CSSProperties } from "react"
import "./globals.css"
import Shell from "@/components/layout/shell"
import { ThemeScript } from "@/components/ui/theme-script"
import { UmsStyleInject } from "@/components/ui/ums-style-inject"
import { getPublicUmsSettings } from "@/lib/public-api"

const fontVariables = {
  "--font-sans":
    '"Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif',
  "--font-display":
    '"Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif',
  "--font-geist-mono":
    '"SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", monospace',
} as CSSProperties

export async function generateMetadata(): Promise<Metadata> {
  const settings = await getPublicUmsSettings()
  const university = settings.university
  return {
    title: `${settings.uiCustomization.brand_name} | ${university.name}`,
    description:
      university.description ||
      "University management system for students, teachers, executives, and administrators.",
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const settings = await getPublicUmsSettings()
  return (
    <html lang="en" suppressHydrationWarning style={fontVariables}>
      <head>
        <ThemeScript />
        <UmsStyleInject settings={settings} />
      </head>
      <body suppressHydrationWarning className="font-sans antialiased">
        <Suspense fallback={null}>
          <Shell>{children}</Shell>
        </Suspense>
      </body>
    </html>
  )
}
