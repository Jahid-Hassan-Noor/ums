import { RoleZonePage } from "@/components/role-zone/role-zone-page"
import type { UserRole } from "@/lib/ums-roles"

export function createRoleZonePage(role: UserRole, path: readonly string[]) {
  return function GeneratedRoleZonePage() {
    return <RoleZonePage role={role} path={[...path]} />
  }
}
