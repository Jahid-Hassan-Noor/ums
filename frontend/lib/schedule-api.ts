"use client"

import { apiFetch } from "@/lib/auth"
import type { UserRole } from "@/lib/ums-roles"
import {
  normalizeScheduleApiEvents,
  type ScheduleApiEvent,
  type ScheduleEvent,
  type ScheduleRouteKind,
} from "@/lib/role-schedule"

export type ScheduleSemester = {
  id: number
  name: string
  start_date: string | null
  end_date: string | null
  starting_week: number
}

export type RoleScheduleData = {
  events: ScheduleEvent[]
  semester: ScheduleSemester | null
}

type ScheduleResponse = {
  schedule?: {
    events?: ScheduleApiEvent[]
    semester?: ScheduleSemester | null
  }
}

function endpointForSchedule(
  role: Extract<UserRole, "student" | "teacher">,
  kind: ScheduleRouteKind
) {
  return kind === "calendar" ? `/${role}/calendar` : `/${role}/timetable`
}

export async function fetchRoleSchedule(
  role: Extract<UserRole, "student" | "teacher">,
  kind: ScheduleRouteKind
): Promise<RoleScheduleData> {
  const response = await apiFetch<ScheduleResponse>(
    endpointForSchedule(role, kind)
  )

  return {
    events: normalizeScheduleApiEvents(role, response.schedule?.events ?? []),
    semester: response.schedule?.semester ?? null,
  }
}
