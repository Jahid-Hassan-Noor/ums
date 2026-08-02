import { PublicBrand } from "@/components/public/public-site"
import { ThemeToggle } from "@/components/ui/theme-toggle"

export function AuthCornerHeader() {
  return (
    <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-1 py-1">
      <PublicBrand
        size="xl"
        className="pr-2"
      />
      <ThemeToggle />
    </div>
  )
}

export default AuthCornerHeader
