import { RoleSchedulePage } from "@/components/role-zone/role-schedule-page"
import type { UserRole } from "@/lib/ums-roles"

export function createRoleSchedulePage(
  role: Extract<UserRole, "student" | "teacher">,
  path: readonly string[]
) {
  return function GeneratedRoleSchedulePage() {
    return <RoleSchedulePage role={role} path={[...path]} />
  }
}
