import { apiFetch } from "@/lib/auth"

export type GradebookScaleRange = {
  id?: number
  letter: string
  min_score: string
  max_score: string
  grade_points: string
  outcome: string
  is_passing: boolean
  sort_order: number
}

export type GradebookScale = {
  id: number
  name: string
  description: string
  is_active: boolean
  is_default: boolean
  ranges: GradebookScaleRange[]
  updated_at: string | null
  updated_by: string
}

export type GradebookOffering = {
  id: number
  course_code: string
  course_title: string
  section: string
  semester: string
  semester_active: boolean
  teacher: string
}

export type GradebookStudent = {
  id: number
  name: string
  username: string
  student_number: string
}

export type GradebookCategory = {
  id: number
  title: string
  weight: string
  drop_lowest: number
  release_to_students: boolean
  is_active: boolean
  sort_order: number
}

export type GradebookItem = {
  id: number
  category_id: number | null
  title: string
  item_type: string
  item_type_label: string
  source_app: string
  source_model: string
  source_id: number | null
  max_score: string
  weight: string
  due_at: string | null
  release_to_students: boolean
  is_extra_credit: boolean
  is_active: boolean
  sort_order: number
}

export type GradebookGrade = {
  id: number
  item_id: number
  student_id: number
  raw_score: string
  feedback: string
  status: "draft" | "released" | "missing" | "excused"
  status_label: string
  is_override: boolean
  graded_by: string
  graded_at: string | null
  released_at: string | null
}

export type GradebookTotal = {
  student_id: number
  score: string
  grade: string
  grade_points: string
}

export type GradebookCourse = {
  offering: GradebookOffering
  students: GradebookStudent[]
  categories: GradebookCategory[]
  items: GradebookItem[]
  grades: GradebookGrade[]
  totals: GradebookTotal[]
}

export type AdminGradebookResponse = {
  title: string
  section: "admin"
  scales: GradebookScale[]
  summary: {
    scales: number
    categories: number
    items: number
    grades: number
  }
  message?: string
}

export type TeacherGradebookResponse = {
  title: string
  section: "teacher"
  offerings: GradebookOffering[]
  scale: GradebookScale
  selected: GradebookCourse | null
  message?: string
}

export type StudentGradebookResponse = {
  title: string
  section: "student"
  scale: GradebookScale
  courses: GradebookCourse[]
}

export type TeacherGradebookAction =
  | {
      action: "sync_sources" | "send_to_result_draft"
      offering_id: number
    }
  | {
      action: "save_category"
      offering_id: number
      category_id?: number
      title: string
      weight: string
      release_to_students: boolean
      is_active: boolean
      sort_order: number
    }
  | {
      action: "save_item"
      offering_id: number
      item_id?: number
      category_id?: number | null
      title: string
      item_type: string
      max_score: string
      weight: string
      release_to_students: boolean
      is_extra_credit: boolean
      is_active: boolean
      sort_order: number
    }
  | {
      action: "update_grade"
      offering_id: number
      item_id: number
      student_id: number
      raw_score: string
      feedback?: string
      status: "draft" | "released" | "missing" | "excused"
      reason?: string
    }
  | {
      action: "release_item"
      offering_id: number
      item_id: number
    }

export function loadAdminGradebook() {
  return apiFetch<AdminGradebookResponse>("/gradebook/admin")
}

export function saveGradebookScale(
  scale: Partial<GradebookScale> & {
    ranges: GradebookScaleRange[]
  }
) {
  return apiFetch<AdminGradebookResponse>("/gradebook/admin", {
    method: "POST",
    body: JSON.stringify({ action: "save_scale", ...scale }),
  })
}

export function loadTeacherGradebook(offeringId?: number | null) {
  const suffix = offeringId ? `?offering_id=${offeringId}` : ""
  return apiFetch<TeacherGradebookResponse>(`/gradebook/teacher${suffix}`)
}

export function runTeacherGradebookAction(action: TeacherGradebookAction) {
  return apiFetch<TeacherGradebookResponse>("/gradebook/teacher", {
    method: "POST",
    body: JSON.stringify(action),
  })
}

export function loadStudentGradebook() {
  return apiFetch<StudentGradebookResponse>("/gradebook/student")
}
