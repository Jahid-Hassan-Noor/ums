import type { Metadata } from "next"
import Image from "next/image"
import Link from "next/link"
import { ArrowRight, FileCheck2, GraduationCap, ShieldCheck, Upload } from "lucide-react"

import { PublicBrand } from "@/components/public/public-site"
import { getPublicUmsSettings } from "@/lib/public-api"

export async function generateMetadata(): Promise<Metadata> {
  const settings = await getPublicUmsSettings()
  const university = settings.university
  return {
    title: `Apply | ${university.name}`,
    description:
      "Applicant account, admission application, scholarship application, and document upload.",
  }
}

const steps = [
  {
    title: "Create Account",
    text: "Use an email address applicants can access throughout admission review.",
    icon: ShieldCheck,
  },
  {
    title: "Choose Programmes",
    text: "Select four programme preferences for the active intake.",
    icon: GraduationCap,
  },
  {
    title: "Scholarship Details",
    text: "Submit household and personal statement details where scholarship support is requested.",
    icon: FileCheck2,
  },
  {
    title: "Upload Documents",
    text: "Attach identity, academic, English proficiency, scholarship, and reference documents.",
    icon: Upload,
  },
]

export default async function ApplyLandingPage() {
  const settings = await getPublicUmsSettings()
  const heroImage =
    settings.university.login_image_url ||
    settings.university.public_hero_image_url

  return (
    <main className="min-h-svh bg-white text-slate-950 dark:bg-slate-950 dark:text-white">
      <section className="relative overflow-hidden bg-slate-950 text-white">
        {heroImage ? (
          <Image
            src={heroImage}
            alt=""
            fill
            priority
            sizes="100vw"
            className="object-cover"
          />
        ) : null}
        <div className="absolute inset-0 bg-slate-950/72" />
        <div className="relative mx-auto flex min-h-[88svh] max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <PublicBrand tone="inverse" size="lg" />
            <div className="flex items-center gap-2">
              <Link
                href="/login?next=/apply/dashboard"
                className="rounded-lg border border-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Login
              </Link>
              <Link
                href="/apply/register"
                className="rounded-lg bg-teal-300 px-4 py-2 text-sm font-bold text-slate-950 transition hover:bg-teal-200"
              >
                Create Account
              </Link>
            </div>
          </div>

          <div className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[minmax(0,0.95fr)_minmax(26rem,0.75fr)]">
            <div className="max-w-3xl">
              <p className="text-xs font-bold tracking-[0.18em] text-teal-200 uppercase">
                Apply
              </p>
              <h1 className="mt-4 font-display text-4xl leading-tight font-semibold sm:text-5xl lg:text-6xl">
                Admission and scholarship applications in one place.
              </h1>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-white/78">
                Students from around the world can create an applicant account,
                complete the application form, upload documents, and track
                admission or scholarship review.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/apply/register"
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-teal-300 px-4 text-sm font-bold text-slate-950 transition hover:bg-teal-200"
                >
                  Start Application <ArrowRight className="size-4" />
                </Link>
                <Link
                  href="/login?next=/apply/dashboard"
                  className="inline-flex h-11 items-center justify-center rounded-lg border border-white/20 bg-white/10 px-4 text-sm font-bold text-white transition hover:bg-white/18"
                >
                  Continue Application
                </Link>
              </div>
            </div>

            <div className="grid gap-3">
              {steps.map((step) => {
                const Icon = step.icon
                return (
                  <div
                    key={step.title}
                    className="rounded-lg border border-white/14 bg-white/10 p-4 backdrop-blur"
                  >
                    <div className="flex gap-3">
                      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-teal-300 text-slate-950">
                        <Icon className="size-5" />
                      </span>
                      <div>
                        <h2 className="font-semibold">{step.title}</h2>
                        <p className="mt-1 text-sm leading-6 text-white/70">{step.text}</p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
