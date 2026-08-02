import Link from "next/link"
import { ArrowLeft, Compass, Home } from "lucide-react"

import { NotFoundRouteMarker } from "@/components/layout/not-found-route-context"
import {
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"

export default function NotFound() {
  return (
    <PublicPage
      active="/"
      hero={
        <PublicHero
          eyebrow="404"
          title="Page not found."
          description="The page you are looking for is not available in the public website or portal."
          image="/images/aiu/campus-welcome.jpg"
          actions={[
            { label: "Go Home", href: "/" },
            {
              label: "Open Portal Login",
              href: "/login",
              variant: "secondary",
            },
          ]}
        />
      }
    >
      <NotFoundRouteMarker />
      <PageBand>
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <SectionHeading
            eyebrow="Missing Page"
            title="Use a verified destination."
            description="Public pages stay in the university website navigation, while private student, staff, and admin tools start from the portal dashboard after login."
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Link
              href="/"
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
            >
              <Home className="size-5 text-teal-700 dark:text-teal-300" />
              <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-white">
                Public Website
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Return to the AIU public homepage and continue through the main
                navigation.
              </p>
            </Link>
            <Link
              href="/student-life"
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
            >
              <Compass className="size-5 text-teal-700 dark:text-teal-300" />
              <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-white">
                Student Resources
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Visit Student Life for public student services, library,
                facilities, and campus resources.
              </p>
            </Link>
          </div>
        </div>
        <Link
          href="/"
          className="mt-10 inline-flex items-center gap-2 text-sm font-bold text-teal-700 hover:text-teal-900 dark:text-teal-300 dark:hover:text-teal-100"
        >
          <ArrowLeft className="size-4" />
          Back to homepage
        </Link>
      </PageBand>
    </PublicPage>
  )
}
