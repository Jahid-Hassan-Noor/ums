import { redirect } from "next/navigation"

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ code?: string | string[] }>
}) {
  const params = await searchParams
  const code = Array.isArray(params.code) ? params.code[0] : params.code
  const query = code ? `?code=${encodeURIComponent(code)}` : ""
  redirect(`/student/attendance/code${query}`)
}
