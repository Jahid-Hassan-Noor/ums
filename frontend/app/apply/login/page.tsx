import { redirect } from "next/navigation"

export default function ApplyLoginPage() {
  redirect("/login?next=/apply/dashboard")
}
