# Frontend Duplicate & Reusable Code Report
> Ordered by **implementation complexity** — easiest to hardest.

---

## 🟢 TIER 1 — Trivial (drop-in shared util, < 1 hour)

### 1. `normalizeApiPath` — Identical in 5+ lib files
The exact same URL normalization function is copy-pasted into:
- `frontend/lib/auth.ts` (line 172)
- `frontend/lib/apply.ts` (line 11)
- `frontend/lib/admin-directory.ts` (line 17)
- `frontend/lib/admin-reports.ts`
- `frontend/lib/executive-reports.ts`

**Fix:** Extract to `frontend/lib/fetch-utils.ts` and import everywhere.

---

### 2. `throttledMessage` — Identical in `auth.ts` and `apply.ts`
Parses `Retry-After` header from 429 responses. The logic (lines 35–56 in `apply.ts`, lines 114–135 in `auth.ts`) is character-for-character the same.

**Fix:** Move to `frontend/lib/fetch-utils.ts`.

---

### 3. `safeJsonParse` — Identical in `auth.ts` and `apply.ts`
3-line JSON try/catch helper duplicated in both files.

**Fix:** Move to `frontend/lib/fetch-utils.ts`.

---

### 4. `extractErrorMessage` — Near-identical in `auth.ts` and `apply.ts`
Extracts `detail` / `message` / field errors from API response bodies. Minor variable naming difference only (`maybeDetail` vs `detail`), but the logic is 100% the same.

**Fix:** Unify in `frontend/lib/fetch-utils.ts`.

---

### 5. `paramsFromFilters` + `filenameFromDisposition` + `errorFromResponse`
Shared among:
- `frontend/lib/admin-directory.ts`
- `frontend/lib/admin-reports.ts`
- `frontend/lib/executive-reports.ts`

These are small helpers (~10 lines each) for building query params, extracting filenames from `Content-Disposition`, and reading error text from failed responses.

**Fix:** Move to a shared `frontend/lib/report-utils.ts` (or `fetch-utils.ts`) and import in the three report libs.

---

### 6. `fetchJson` / `fetchJsonOrNull` error block — `public-api.ts` (lines 415–440)
```tsx
// This pattern is copy-pasted twice in the same file:
if (!response.ok) {
  const data = await readJson<{ detail?: string; message?: string }>(response)
  const message = data?.detail || data?.message || "Request failed."
  throw new Error(message)
}
```
**Fix:** Extract a `throwIfNotOk(response)` helper inside `public-api.ts`.

---

### 7. `AuthUser` type — duplicated in `auth.ts` and `server-session.ts`
The `AuthUser` interface (with all its fields like `ums_id`, `executive_scope`, etc.) is defined in both files.

**Fix:** Define once in `server-session.ts`, re-export from `auth.ts`.

---

### 8. Chart SVG stat sub-card — `trend-line-chart.tsx` & `value-bar-chart.tsx`
The "summary stat" panel at the bottom of both chart components is pixel-identical:
```tsx
<div className="bg-muted/40 border-border rounded-xl border p-3">
  <p className="text-muted-foreground text-xs uppercase tracking-wide">{label}</p>
  <p className="text-foreground mt-1 text-lg font-semibold">{value}</p>
</div>
```
Both charts also share:
- The same `viewBox="0 0 740 300"` layout
- Identical `isDark` color derivation: `gridColor`, `axisTextColor`
- Identical `<defs><linearGradient>` structure
- Identical `Array.from({ length: 5 })` y-axis grid line rendering

**Fix:** Extract a `<ChartStatCard label value />` component and a `useChartColors(isDark)` hook into `frontend/components/charts/`.

---

### 9. `valuesTotal` helper — in both `trend-line-chart.tsx` and `value-bar-chart.tsx`
```ts
function valuesTotal(values: number[]) {
  return values.reduce((sum, value) => sum + (Number.isFinite(value) ? value : 0), 0)
}
```
Exact duplicate.

**Fix:** Move to `frontend/components/charts/chart-utils.ts`.

---

## 🟡 TIER 2 — Easy (shared component, 1–3 hours)

### 10. `statusClass` / `badgeClass` / `statusVariant` — defined in 10+ component files
Every page that shows a status badge has its own private copy of a `statusClass(status)` or `statusVariant(status)` function:
- `student-courses-page.tsx` line 266
- `student-registration-records-page.tsx` line 129
- `student-results-page.tsx` line 160
- `student-assignments-page.tsx` line 236
- `teacher-results-page.tsx` line 112 (`badgeClass`)
- `executive-results-page.tsx` line 100 (`badgeClass`)
- `executive/evaluations/page.tsx` line 76 (`statusClass`)
- `venue-booking-page.tsx` line 63 (`statusVariant`)
- + others in `apply-status.tsx`, `librarian-workspace-page.tsx`, `admin-semesters-page.tsx`

All map the same statuses (`pending → yellow/secondary`, `approved/active → green/default`, `rejected/inactive → red/destructive`) to Tailwind classes or badge variant strings.

**Fix:** Create `frontend/lib/status-utils.ts` exporting:
```ts
export function statusBadgeVariant(status: string): BadgeVariant
export function statusClassName(status: string): string
```

---

### 11. Download blob trigger — repeated in 6 files
The pattern of fetching a blob, creating an `<a>` element, setting `href = URL.createObjectURL(blob)`, and clicking it exists in:
- `admin-manage-students-page.tsx`
- `admin-manage-teachers-page.tsx`
- `admin-manage-executives-page.tsx`
- `admin-people-reports-page.tsx`
- `student-results-page.tsx`
- `accountant/ledger/export-menu.tsx`

**Fix:** Add a `triggerBlobDownload(blob: Blob, filename: string)` helper to `frontend/lib/fetch-utils.ts`.

---

### 12. Page-level loading + error layout — ~20 components
Nearly every data-driven page follows the same pattern inline:
```tsx
if (isLoading) return <div className="flex items-center justify-center p-12"><Loader2 className="animate-spin" /></div>
if (error) return <div className="p-6 text-red-500">{error}</div>
```
This is repeated as inline JSX (not even a component) in 20+ files.

**Fix:** Create a `<PageLoadState loading={isLoading} error={error}>` wrapper in `frontend/components/ui/`.

---

### 13. Admin "Manage Staff" header row — identical across 5 files
`admin-manage-accountants-page.tsx`, `admin-manage-caterers-page.tsx`, `admin-manage-hr-page.tsx`, `admin-manage-librarians-page.tsx`, `admin-manage-technicians-page.tsx` all share the same imports block (lines 1–12) and search-bar + button header pattern (lines 25–32), confirmed by jscpd as byte-identical clones.

**Fix:** Extract a `<ManagePageHeader title search onSearch onCreate />` component.

---

### 14. Student/Teacher manage-page filter UI — duplicated in students vs teachers
`admin-manage-students-page.tsx` and `admin-manage-teachers-page.tsx` share 9 near-identical jscpd-confirmed blocks covering:
- Semester/department/programme filter rows
- "Filter" pill buttons with clear-all
- Search + filter toolbar layout
- Pagination footer controls

**Fix:** Extract a `<DataTableToolbar>` + `<DataTablePagination>` component pair.

---

### 15. `apply-dashboard.tsx` and `apply-status.tsx` — 24-line JSX clone
jscpd confirms lines 5–28 of `apply-dashboard.tsx` are identical to lines 5–28 of `apply-status.tsx`. Both render the same application status progress steps.

**Fix:** Extract a shared `<ApplicationStatusSteps />` component inside `frontend/components/apply/`.

---

### 16. Statistics page stat blocks — `admin/statistics/page.tsx` vs `executive/statistics/page.tsx`
jscpd found 5 separate identical clone blocks between these two pages totalling 60+ lines. Both show the same stat grid layout, date-range filters, and chart containers.

**Fix:** Extract shared stat sections into `frontend/components/role-zone/role-statistics-page.tsx` (already exists) and have both pages use it.

---

## 🟠 TIER 3 — Medium (custom hook or compound component, 3–8 hours)

### 17. `useAsyncLoad` custom hook — needed in 20+ components
Every data-fetching page has this manual pattern:
```tsx
const [data, setData] = useState(null)
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

const fetchData = useCallback(async () => {
  setIsLoading(true)
  try {
    const result = await apiFetch(...)
    setData(result)
  } catch (e) {
    setError(e.message)
  } finally {
    setIsLoading(false)
  }
}, [deps])

useEffect(() => { fetchData() }, [fetchData])
```
Appears in 20+ components with identical structure (confirmed by the `isLoading`/`fetchData` grep showing 20+ files).

**Fix:** A generic `useAsync<T>(fn, deps)` hook in `frontend/hooks/use-async.ts` returning `{ data, isLoading, error, reload }`.

---

### 18. Page-level "search + filter + sort + paginate" state — 8+ components
Pages like `student-courses-page.tsx`, `student-assignments-page.tsx`, `teacher-courses-page.tsx`, `teacher-attendance-page.tsx`, `admin-academic-directory-page.tsx` each manage 4–6 local state variables that all do the same thing: search query, active filters, sort field/direction, current page.

**Fix:** A `useTableState({ initialFilters })` hook in `frontend/hooks/use-table-state.ts`.

---

### 19. `TrendLineChart` vs `ValueBarChart` — merge into a single `<DataChart type="line"|"bar">`
The two chart components share:
- Identical Card wrapper structure (same className, same CardHeader, same stat cards at bottom)
- Identical SVG coordinate system (`width=740, height=300`, same padding formula)
- Identical y-axis grid rendering (`Array.from({ length: 5 }, ...)` loop)
- Identical `isDark` color tokens
- Identical `linearGradient` defs structure
- Shared `valuesTotal` helper

Only the actual data rendering differs (line+area path vs bars).

**Fix:** Merge into a single `<DataChart type="line" | "bar" {...sharedProps}>` component. Move all shared logic (coordinate computation, grid lines, stat cards) into a `ChartCanvas` inner component.

---

### 20. Admin "Manage Role" pages — 5 near-identical page components
`admin-manage-accountants-page.tsx`, `admin-manage-caterers-page.tsx`, `admin-manage-hr-page.tsx`, `admin-manage-librarians-page.tsx`, `admin-manage-technicians-page.tsx` each:
1. Fetch a paginated list from the API
2. Show a search + filter bar
3. Render a table with name, email, status, actions
4. Handle activate/deactivate/delete actions with the same confirm-then-mutate pattern

jscpd confirmed 8+ identical blocks across these files.

**Fix:** A single `<AdminManageStaffPage role="librarian" | "caterer" | ...>` parameterized component, or a `useManageStaff(role)` hook that contains all the shared data-fetching and mutation logic.

---

### 21. Admin `manage-students` vs `manage-teachers` vs `manage-executives` — near-identical UI
jscpd found 12 separate cloned blocks of 8–28 lines between these three files. They share:
- Filter UI (semester, department, search)
- Table column structure (name, id, programme, actions)
- Detail action buttons (view profile, reset password, ban)
- Download/export logic

**Fix:** Parameterized `<AdminManagePersonPage role="student" | "teacher" | "executive">` or extract a shared `<PersonTable>` component.

---

### 22. `admin-academic-directory-page.tsx` vs `admin-public-content-page.tsx` — 8 cloned blocks
jscpd found 8 confirmed clone blocks totalling 100+ lines. Both pages share:
- The same collapsible-section card pattern (`CardHeader` with expand toggle)
- The same form field layout for editing entity name/code/description
- The same save/cancel button row
- The same delete-with-confirmation flow

**Fix:** Extract a `<EntityEditorCard title fields onSave onDelete>` compound component.

---

## 🔴 TIER 4 — Hard (major refactor, 8+ hours)

### 23. `admin-create-account-page.tsx` (1,254 lines) — duplicated form sections
The "Create Student Account" and "Create Staff Account" sections within this single file have near-identical form field groups (personal info, contact info, address info) that appear twice (lines 815–897 and lines 1047–1121), confirmed by jscpd as 4 separate clone blocks.

**Fix:** Extract `<PersonalInfoFields>`, `<ContactInfoFields>`, `<AddressInfoFields>` sub-components reused for both form variants.

---

### 24. `admin-settings-page.tsx` vs `admin-ui-customization-page.tsx` — 8 cloned blocks
jscpd confirmed 8 identical blocks totalling 140+ lines shared between these two huge settings pages. They share:
- Toggle switch rows with label + description
- Section header patterns
- Save/discard button bars
- Color picker input rows

**Fix:** Extract a `<SettingsSection>`, `<SettingsToggleRow>`, `<SettingsColorRow>` component library inside `frontend/components/admin/settings/`.

---

### 25. `student-courses-page.tsx` (1,268 lines) + `teacher-courses-page.tsx` (972 lines) — course card & tab design
Both pages render course cards with the same design (course code badge, semester pill, credit hours, enrolled count) and manage similar tab-based navigation (Overview, Schedule, Assignments, Attendance). Multiple jscpd-confirmed clones exist between them.

**Fix:** Extract a shared `<CourseCard>` component and `<CourseTabLayout>` into `frontend/components/role-zone/`.

---

### 26. `executive-results-page.tsx` vs `teacher-results-page.tsx` — 6 cloned blocks
jscpd found 6 blocks of 7–24 lines each. Both pages share the same result batch listing UI, batch status badge, and grade distribution table design.

**Fix:** Extract a `<ResultBatchTable>` and `<GradeDistributionCard>` into a shared `frontend/components/results/` directory.

---

## Summary Table

| # | What | Where | Files Affected | Complexity |
|---|------|--------|----------------|------------|
| 1–4 | `normalizeApiPath`, `throttledMessage`, `safeJsonParse`, `extractErrorMessage` | `lib/*.ts` | 5 files | 🟢 Trivial |
| 5 | Filter/report helpers | `lib/*.ts` | 3 files | 🟢 Trivial |
| 6 | `throwIfNotOk` inline block | `public-api.ts` | 1 file | 🟢 Trivial |
| 7 | `AuthUser` type duplication | `auth.ts`, `server-session.ts` | 2 files | 🟢 Trivial |
| 8–9 | Chart stat card, `valuesTotal` | `charts/*.tsx` | 2 files | 🟢 Trivial |
| 10 | `statusClass`/`badgeClass` functions | components (10+ files) | 10+ files | 🟡 Easy |
| 11 | Blob download trigger | various | 6 files | 🟡 Easy |
| 12 | Inline loading/error layout | all data pages | 20+ files | 🟡 Easy |
| 13 | Admin manage-staff header row | `admin-manage-*.tsx` | 5 files | 🟡 Easy |
| 14 | Filter/pagination toolbar | student/teacher pages | 3+ files | 🟡 Easy |
| 15 | Application status steps | `apply-*.tsx` | 2 files | 🟡 Easy |
| 16 | Statistics page stat blocks | statistics pages | 2 files | 🟡 Easy |
| 17 | `useAsync` data-fetch hook | all data pages | 20+ files | 🟠 Medium |
| 18 | `useTableState` hook | table pages | 8+ files | 🟠 Medium |
| 19 | Merge line & bar chart | `charts/` | 2 files | 🟠 Medium |
| 20 | Admin manage-staff parameterized | `admin-manage-*.tsx` | 5 files | 🟠 Medium |
| 21 | Admin manage-person (student/teacher/exec) | `admin-manage-*.tsx` | 3 files | 🟠 Medium |
| 22 | `EntityEditorCard` | `admin-academic`, `admin-public` | 2 files | 🟠 Medium |
| 23 | Create account form fields | `admin-create-account-page.tsx` | 1 file (internal) | 🔴 Hard |
| 24 | Settings section components | `admin-settings`, `admin-ui-customization` | 2 files | 🔴 Hard |
| 25 | Course card + tab layout | `student/teacher-courses-page.tsx` | 2 files | 🔴 Hard |
| 26 | Result batch/grade UI | `teacher/executive-results-page.tsx` | 2 files | 🔴 Hard |
