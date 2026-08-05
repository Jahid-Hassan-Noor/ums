export type PublicLink = {
  label: string
  href: string
  description?: string
}

export type PublicNavGroup = PublicLink & {
  children?: PublicLink[]
}

export type PublicStat = {
  value: string
  label: string
}

export type PublicContentItem = {
  title: string
  summary: string
  meta?: string
  href?: string
}

export type PublicContentSection = {
  eyebrow?: string
  title: string
  body?: string[]
  items?: PublicContentItem[]
  links?: PublicLink[]
}

export type PublicDetailPage = {
  path: string
  active?: string
  eyebrow: string
  title: string
  description: string
  image?: string
  stats?: PublicStat[]
  sections: PublicContentSection[]
}

export const umsContact = {
  address: "",
  phone: "",
  email: "",
}

export const contactChannels: PublicContentItem[] = []
export const publicNavGroups: PublicNavGroup[] = []
export const publicNavLinks: PublicLink[] = []

export const applyLinks: PublicLink[] = [
  { label: "Apply", href: "/apply" },
  { label: "Applicant Login", href: "/login?next=/apply/dashboard" },
]

export const officialLinks: PublicContentItem[] = []
export const umsValues: PublicContentItem[] = []
export const schools: PublicDetailPage[] = []
export const centres: PublicDetailPage[] = []
export const departments: string[] = []
export const units: string[] = []
export const latestNews: PublicContentItem[] = []
export const monthlyHighlights: PublicContentItem[] = []

export const intakeNotice = {
  intake: "Admissions",
  status: "Admissions information is managed in the public CMS.",
  deadline: "a CMS-managed deadline",
}

export const scholarshipCriteria: string[] = []
export const scholarshipAssessment: PublicStat[] = []
export const scholarshipStaff: string[] = []
export const scholarshipContact = {
  phone: "",
  email: "",
  whatsapp: "",
}

export const governanceGroups: Record<string, PublicContentItem[]> = {}
export const umsModules: string[] = []
export const umsRoles: { title: string; summary?: string }[] = []
export const publicDetailPages: PublicDetailPage[] = []
export const publicDetailPageMap = new Map<string, PublicDetailPage>()

export function getPublicDetailPage(slug: string[]) {
  return publicDetailPageMap.get(`/${slug.join("/")}`)
}
