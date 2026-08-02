# AGENTS.md — Codex Instructions for AIU Portal Project

## Project overview

This is a full-stack AIU portal project with:

- Django / DRF backend in `backend/`
- Next.js / React frontend in `frontend/`
- Role-based modules for admin, student, teacher, executive, applicant, caterer, librarian, technician, and public website users
- Graphify knowledge graph output in `graphify-out/`

The current Graphify graph is large: about **2,718 nodes**, **6,414 edges**, and **227 communities**. Treat the graph as the first navigation layer, not as a file to read directly.

I am using docker containers not any virtual environments for frontend or backend. And don't change any docker configurations.And http://127.0.0.1:8080 port is running.

## Graphify-first rule

Before reading many files or editing code, use Graphify context first.

Do **not** read `graphify-out/graph.html` unless the user explicitly asks for the visual HTML file. It is very large and wastes context.

Prefer this order:

1. `graphify query "<specific question>"`
2. `graphify explain "<feature or concept>"`
3. `graphify path "<source>" "<target>"` when checking relationships
4. `graphify-out/wiki/index.md` for broad navigation, if it exists
5. `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/explain/path is insufficient

Dirty `graphify-out/` files are expected after hooks or incremental updates. Dirty graph files are not a reason to skip Graphify. Only skip Graphify if the task is about stale or incorrect graph output, or if the user explicitly says not to use Graphify.

After modifying code, run:

```bash
graphify update .
```

This keeps the AST graph current without reading `graph.html`.

## Token-saving workflow for every task

1. Identify the feature area first: auth/account, admin, student, teacher, executive, applicant/admission, public site, election, course schedule, course registration, attendance, assignments, leave, venue booking, hostel, canteen, library, ICT/helpdesk, dashboard, academic directory, or shared UI.
2. Run a targeted Graphify query for that feature area.
3. Read only the smallest relevant file set returned by Graphify.
4. Avoid scanning whole folders such as `frontend/app`, `frontend/components`, `backend/admin_app`, `backend/student_app`, or `backend/teacher_app`.
5. Avoid generated/dependency folders: `node_modules`, `.next`, `graphify-out`, `dist`, `build`, `coverage`, `__pycache__`, and migration folders unless the task is specifically about migrations.
6. Before editing, list the affected files and explain why each file is needed.
7. Make the smallest working change.
8. Run only the relevant targeted check or test.
9. Summarize exactly what changed, list modified files, provide the test command, and mention risks/follow-ups.

## Never open central hub files first

Never start by opening a central hub file. First find the feature-specific view, service, component, route, or API file.

Only open a central hub file if Graphify shows it is directly connected to the requested feature.

Central hub / high-impact files include:

- `backend/admin_app/models.py`
- `backend/admin_app/serializers.py`
- `backend/admin_app/permissions.py`
- `frontend/lib/auth.ts`
- `frontend/lib/utils.ts`
- `frontend/components/role-zone/role-dashboard.tsx`
- `frontend/components/role-zone/create-role-page.tsx`
- `frontend/components/layout/header.tsx`
- `frontend/components/ui/button.tsx`
- `frontend/components/ui/card.tsx`
- `frontend/components/ui/sidebar.tsx`
- `frontend/components/ui/input.tsx`
- `frontend/components/ui/label.tsx`
- `backend/executive_app/course_schedule.py`
- `frontend/components/public/public-site.tsx`
- `frontend/lib/aiu-public-data.ts`

Ask before touching these high-impact shared files unless the user request clearly requires it.

## Shared backend utilities (`backend/core/common/`) — reuse before you write

The backend keeps consolidated, reusable helpers in `backend/core/common/`. **Always
check here (and `backend/core/` generally) for an existing helper before writing a new
small utility.** Duplicating these helpers is not allowed — import from `core.common`.

Currently available:

- `core/common/errors.py`
  - `first_error(errors, default="Operation failed.")` — flatten a DRF
    `serializer.errors` structure into a single `"field: message"` string. Pass a
    custom `default` for a context-specific fallback (e.g. account creation).
  - `validation_error_response(errors, default=..., status_code=400)` — build the
    standard `{"detail": ..., "errors": ...}` error `Response`.
- `core/common/profiles.py`
  - `profile_display_name(profile)` — human-friendly name (`""` if `None`).
  - `profile_identifier(profile)` — stable public identifier (`""` if `None`).
  - `get_role_profile(user, role, select_related=None)` — active `Profile` for a role.
  - `get_student_profile(user)` / `get_teacher_profile(user)` / `get_executive_profile(user)`
    — role-specific wrappers with the correct `select_related`.
- `core/common/money.py`
  - `format_money(value)` — two-decimal string (`"0.00"` for falsy/blank, never raises).
  - `parse_decimal(value, *, default=None, max_digits=None, decimal_places=None)` —
    locale-agnostic `Decimal` parse with optional max-digit/decimal-place validation.
- `core/common/pagination.py`
  - `paginate(queryset, page, page_size)` — `Page` object for a page/page_size pair.
  - `pagination_meta(page)` — standardized `{count, page, page_size, total_pages,
    next, previous}` dict for list responses.
- `core/common/request_utils.py`
  - `parse_bool(value, default=...)` — tolerant `"1/true/yes/on"` → bool, handles
    `None`/blank/`bool`/`int`/numeric-string.
  - `parse_int(value, default=...)` — int parse with fallback.
  - `parse_json(value)` — `json.loads`, `None`/blank → `None`, raises `ValueError`
    with a clean message otherwise.

Note: `student_app.registration_service`, `teacher_app.assignment_service`, and
`executive_app.course_schedule` re-export `profile_display_name` and their
`get_*_profile` helpers from `core.common.profiles`, so existing import paths still
work. `accountant_app`/`hr_app`/`caterer_app` services re-export their historical
`money`/`display_name`/`student_name` aliases the same way. New code should import
directly from `core.common`.

Related already-shared modules: `core/upload_security.py` (image/file validation),
`core/media_access.py` (protected media URLs), `notifications_package/service.py`
(`notify_profile`, `notify_profiles`, `notify_roles`).

When you find yourself about to write a helper for error formatting, profile
loading/display, money math, pagination, request parsing, or slug/route
normalization, first grep `backend/core/common/` and `backend/core/` — extend the
shared module instead of adding another copy.

## Shared frontend utilities — reuse before you write

The frontend keeps reusable helpers, hooks, and compound UI primitives in
`frontend/lib/`, `frontend/hooks/`, `frontend/components/ui/`, and targeted
shared component folders. **Before creating a new helper or repeating a JSX
block, search for an existing shared implementation and import it.** Do not add
another private copy unless the behavior is truly feature-specific.

Currently available:

- `frontend/lib/fetch-utils.ts`
  - `normalizeApiPath(path)` — normalize API paths while preserving query/hash
    suffixes.
  - `safeJsonParse(text)` — JSON parse with a `null` fallback.
  - `throttledMessage(response, data)` — consistent `429` / `Retry-After`
    messages.
  - `extractErrorMessage(data, fallback)` and `readJsonResponse<T>(...)` —
    standard API error extraction and JSON response handling.
  - `paramsFromFilters(...)`, `queryStringFromFilters(...)`,
    `filenameFromDisposition(...)`, `errorFromResponse(...)` — shared report and
    export helpers.
  - `triggerBlobDownload(blob, filename)` — one browser download trigger.
- `frontend/lib/status-utils.ts`
  - `statusBadgeVariant(status)` and `statusClassName(status)` — shared status
    badge variants and class names.
- `frontend/hooks/use-table-state.ts`
  - `useTableState(...)` — search/filter/sort/page state for table surfaces.
- `frontend/hooks/use-manage-staff.ts`
  - `useManageStaff(...)` — shared load/edit/save flow for admin staff
    management pages.
- `frontend/components/ui/data-table-controls.tsx`
  - `DataTableToolbar` — shared search/filter/sort toolbar controls.
- `frontend/components/admin/manage-page-header.tsx`
  - `ManagePageHeader` — shared admin management page title/action/search row.
- `frontend/components/admin/entity-editor-card.tsx`
  - `EntityEditorCard` — shared add/edit card shell with cancel/save behavior.
- `frontend/components/results/result-display.tsx`
  - `ResultTabsNav`, `ResultSummaryCards`, and `ResultBatchHeader` — shared
    result-workflow navigation, summary cards, and status headers.
- `frontend/components/charts/data-chart.tsx`,
  `frontend/components/charts/chart-utils.ts`, and
  `frontend/components/charts/chart-stat-card.tsx`
  - shared chart canvas, chart math/colors, and stat-card primitives.
- `frontend/components/apply/application-status-steps.tsx`
  - applicant status labels and application-step rendering.

Before writing new frontend code for API parsing, status badges, downloads,
search/filter/sort/pagination state, admin manage headers, result page tabs,
entity editor cards, or chart scaffolding, grep these shared files first. If an
existing helper almost fits, extend it with a narrow optional prop or parameter
instead of copying the code into a page.

## Editing rules for Codex

Before editing:

1. Explain the feature area.
2. List only the files that need inspection.
3. Explain why each file is needed.
4. Ask before touching high-impact shared files.

During editing:

1. Make the smallest working change.
2. Do not refactor unrelated files.
3. Do not rename files unless necessary.
4. Do not modify generated files.
5. Do not edit `node_modules`, `.next`, `graphify-out`, `dist`, `build`, `coverage`, or `__pycache__`.
6. Do not create or edit migrations unless the task changes models and the user expects database changes.
7. Preserve existing API shapes unless the task explicitly requires an API contract change.
8. Before writing any small helper or repeated UI block, check the shared backend
   helpers (`backend/core/common/`, `backend/core/`) and shared frontend helpers
   (`frontend/lib/`, `frontend/hooks/`, `frontend/components/ui/`, and targeted
   shared component folders) for an existing implementation. Import or extend the
   shared module instead of re-defining duplicate code.

After editing:

1. Summarize exactly what changed.
2. List files modified.
3. Provide the command used to test the change.
4. Mention any risk or follow-up needed.
5. Run `graphify update .` after code changes.

## Common feature maps

Use these as starting points, then confirm with `graphify query` before reading files.

### Election feature

Start with:

- `backend/admin_app/election_service.py`
- `backend/admin_app/views/admin_elections.py`
- `backend/student_app/views/student_elections.py`
- `backend/executive_app/views/executive_elections.py`
- `backend/executive_app/views/executive_elections_candidates.py`
- `backend/executive_app/views/executive_elections_results.py`
- `frontend/lib/elections.ts`
- `frontend/components/admin/admin-elections-page.tsx`
- `frontend/components/admin/admin-election-candidates-page.tsx`
- `frontend/components/admin/admin-election-results-page.tsx`
- `frontend/components/student/student-elections-page.tsx`

Avoid starting with `backend/admin_app/models.py` even though election models live there. Open it only if the service/view requires model-level changes.

Useful query:

```bash
graphify query "Which files implement election creation, candidate approval, result publication, student ballot display, and student vote casting?"
```

### Auth, account, login, profile, and API request flow

Start with:

- `backend/admin_app/views/account.py`
- `backend/admin_app/views/admin_create_account.py`
- `backend/applicant_app/views/applicant_auth.py`
- `backend/home_app/views/public_login.py`
- `frontend/components/ui/login-form.tsx`
- `frontend/lib/auth.ts`
- `frontend/app/login/page.tsx`
- `frontend/app/apply/login/page.tsx`
- `frontend/app/profile/page.tsx`

Check token handling, API base URL, authentication headers, refresh behavior, profile fetching, role redirects, and applicant login separately.

Useful query:

```bash
graphify query "Which files handle frontend API authentication, token storage, login, logout, user profile fetching, applicant login, and role redirects?"
```

### Role-zone pages and dashboards

Start with feature-specific route files first, then role-zone helpers if needed:

- `frontend/components/role-zone/create-role-page.tsx`
- `frontend/components/role-zone/role-dashboard.tsx`
- `frontend/components/role-zone/role-zone-page.tsx`
- `frontend/components/role-zone/role-schedule-page.tsx`
- `frontend/components/role-zone/role-schedule-surface.tsx`
- `frontend/lib/dashboard.ts`
- relevant route page under `frontend/app/(admin)`, `frontend/app/(student)`, `frontend/app/(teacher)`, `frontend/app/(executive)`, `frontend/app/(caterer)`, `frontend/app/(librarian)`, or `frontend/app/(technician)`

Do not edit `role-dashboard.tsx` or `create-role-page.tsx` for a one-page UI issue unless the graph shows shared role-zone behavior is the real cause.

Useful query:

```bash
graphify query "Which files implement role dashboard cards, role-zone page creation, dashboard data loading, and role-specific dashboard routes?"
```

### Course schedule and executive scheduling

Start with:

- `backend/executive_app/course_schedule.py`
- `backend/executive_app/views/executive_manage_schedule.py`
- `frontend/lib/schedule-api.ts`
- `frontend/lib/role-schedule.ts`
- `frontend/components/role-zone/role-schedule-page.tsx`
- `frontend/components/role-zone/role-schedule-surface.tsx`
- `frontend/app/(executive)/executive/manage/schedule/page.tsx`

Only open schedule-related models after Graphify confirms the needed model relationship.

Useful query:

```bash
graphify query "Which files implement executive course schedule creation, timetable slots, schedule API calls, and role schedule display?"
```

### Course offerings and student registration

Start with:

- `backend/student_app/registration_service.py`
- `backend/student_app/views/student_registration.py`
- `backend/student_app/views/student_registration_offered_courses.py`
- `backend/student_app/views/student_registration_requests.py`
- `backend/student_app/views/student_registration_history.py`
- `backend/executive_app/views/executive_registrations.py`
- `backend/executive_app/views/executive_registrations_pending.py`
- `backend/executive_app/views/executive_registrations_approved.py`
- `backend/executive_app/views/executive_registrations_history.py`
- `backend/executive_app/views/executive_courses_offer.py`
- `backend/executive_app/views/executive_courses_offered.py`

Useful query:

```bash
graphify query "Which files implement student course registration rules, offered courses, registration requests, executive approval, and registration history?"
```

### Attendance feature

Start with:

- `backend/teacher_app/attendance_service.py`
- `backend/teacher_app/views/teacher_attendance.py`
- `backend/teacher_app/views/teacher_attendance_create.py`
- `backend/teacher_app/views/teacher_attendance_sessions.py`
- `backend/teacher_app/views/teacher_attendance_corrections.py`
- `backend/teacher_app/views/teacher_course_attendance.py`
- `backend/student_app/views/student_attendance.py`
- `backend/student_app/views/student_attendance_code.py`
- `backend/student_app/views/student_attendance_qr.py`
- `backend/student_app/views/student_attendance_report.py`

Useful query:

```bash
graphify query "Which files implement teacher attendance creation, sessions, correction flow, QR/code attendance, and student attendance reports?"
```

### Assignments and course content

Start with:

- `backend/teacher_app/assignment_service.py`
- `backend/teacher_app/course_content_service.py`
- `backend/teacher_app/views/teacher_assignments.py`
- `backend/teacher_app/views/teacher_assignment_create.py`
- `backend/teacher_app/views/teacher_assignment_detail.py`
- `backend/teacher_app/views/teacher_assignment_submissions.py`
- `backend/teacher_app/views/teacher_assignment_feedback.py`
- `backend/teacher_app/views/teacher_course_assignments.py`
- student assignment views under `backend/student_app/views/student_assignments_*.py`
- relevant assignment pages under `frontend/app/(teacher)/teacher/assignments/` and `frontend/app/(student)/student/assignments/`

Useful query:

```bash
graphify query "Which files implement teacher assignment creation, assignment submissions, grading feedback, course content, and student assignment views?"
```

### Applicant and admission feature

Start with:

- `backend/applicant_app/serializers.py`
- `backend/applicant_app/views/applicant_applications.py`
- `backend/applicant_app/views/applicant_documents.py`
- `backend/applicant_app/views/applicant_options.py`
- `backend/applicant_app/views/applicant_staff.py`
- `backend/applicant_app/views/helpers.py`
- `frontend/lib/apply.ts`
- `frontend/lib/admin-applicants.ts`
- `frontend/components/apply/apply-application-form.tsx`
- `frontend/components/apply/apply-dashboard.tsx`
- `frontend/components/admin/admin-manage-applicants-page.tsx`

Useful query:

```bash
graphify query "Which files implement applicant authentication, application form submission, document upload, application status, and admin applicant review?"
```

### Public website and public content management

Start with:

- `backend/home_app/views/public_home.py`
- `backend/home_app/views/public_about.py`
- `backend/home_app/views/public_admissions.py`
- `backend/home_app/views/public_news.py`
- `backend/home_app/views/public_events.py`
- `backend/home_app/views/public_official_links.py`
- `backend/home_app/views/public_programs.py`
- `backend/home_app/views/public_programmes.py`
- `backend/home_app/views/public_schools.py`
- `backend/home_app/views/public_centers.py`
- `backend/home_app/views/public_centres.py`
- `backend/admin_app/views/admin_public_content.py`
- `backend/admin_app/views/admin_public_news.py`
- `backend/admin_app/views/admin_public_events.py`
- `backend/admin_app/views/admin_public_announcements.py`
- `backend/admin_app/views/admin_public_official_links.py`
- `frontend/components/public/public-site.tsx`
- `frontend/lib/aiu-public-data.ts`
- `frontend/lib/public-api.ts`

Useful query:

```bash
graphify query "Which files implement the public website pages, public API data, news, events, admissions, announcements, and official links?"
```

### Academic directory and organization structure

Start with:

- `backend/admin_app/views/admin_academics.py`
- `backend/admin_app/views/admin_academics_schools.py`
- `backend/admin_app/views/admin_academics_centres.py`
- `backend/admin_app/views/admin_academics_departments.py`
- `backend/admin_app/views/admin_academics_programmes.py`
- `backend/admin_app/views/admin_academics_courses.py`
- `backend/admin_app/views/admin_academics_units.py`
- `backend/executive_app/views/executive_organization.py`
- `frontend/components/admin/admin-academic-directory-page.tsx`
- `frontend/components/executive/executive-organization-page.tsx`
- `frontend/components/executive/executive-programs-page.tsx`
- `frontend/lib/admin-directory.ts`

Useful query:

```bash
graphify query "Which files implement schools, centres, departments, programmes, units, academic directory pages, and executive organization views?"
```

### Admin user management and role accounts

Start with the role-specific management file, not the model hub:

- `backend/admin_app/views/admin_manage_students.py`
- `backend/admin_app/views/admin_manage_teachers.py`
- `backend/admin_app/views/admin_manage_executives.py`
- `backend/admin_app/views/admin_manage_applicants.py`
- `backend/admin_app/views/admin_manage_librarians.py`
- `backend/admin_app/views/admin_manage_technicians.py`
- `backend/admin_app/views/admin_create_account.py`
- corresponding frontend pages/components under `frontend/app/(admin)/admin/manage/` and `frontend/components/admin/`

Useful query:

```bash
graphify query "Which files implement admin management of students, teachers, executives, applicants, librarians, technicians, and create-account flows?"
```

### Venue booking feature

Start with:

- `backend/admin_app/venue_booking_service.py`
- `backend/admin_app/views/admin_venues.py`
- `backend/admin_app/views/admin_venue_bookings.py`
- `backend/student_app/views/student_venue_bookings.py`
- `backend/teacher_app/views/teacher_venue_bookings.py`
- `frontend/components/venue-booking/venue-booking-page.tsx`
- route pages under `frontend/app/(admin)/admin/venues/`, `frontend/app/(admin)/admin/venue-bookings/`, `frontend/app/(student)/student/venue-bookings/`, and `frontend/app/(teacher)/teacher/venue-bookings/`

Useful query:

```bash
graphify query "Which files implement venue management, venue booking requests, admin approvals, and student or teacher venue booking pages?"
```

### Hostel feature

Start with:

- `backend/admin_app/views/admin_hostels.py`
- `frontend/app/(admin)/admin/hostels/page.tsx`

Useful query:

```bash
graphify query "Which files implement hostel and hostel room management?"
```

### Canteen feature

Start with:

- `backend/admin_app/views/admin_canteen.py`
- `backend/caterer_app/service.py`
- `backend/caterer_app/views/canteen.py`
- `frontend/components/admin/admin-canteen-page.tsx`
- `frontend/components/caterer/caterer-dashboard-page.tsx`
- `frontend/app/(admin)/admin/canteen/page.tsx`
- `frontend/app/(caterer)/caterer/dashboard/page.tsx`

Useful query:

```bash
graphify query "Which files implement canteen allowances, caterer workflow, student canteen balance, and admin canteen pages?"
```

### Library and librarian feature

Start with:

- `backend/librarian_app/models.py`
- `backend/librarian_app/serializers.py`
- `backend/librarian_app/service.py`
- `backend/librarian_app/views/library.py`
- `backend/student_app/views/student_library.py`
- `backend/admin_app/views/admin_manage_librarians.py`
- `frontend/components/librarian/librarian-dashboard-page.tsx`
- `frontend/components/librarian/librarian-workspace-page.tsx`
- `frontend/components/student/student-library-page.tsx`
- `frontend/components/admin/admin-manage-librarians-page.tsx`

Useful query:

```bash
graphify query "Which files implement library books, copies, loans, laptop lending, librarian workspace, and student library views?"
```

### ICT helpdesk and technician feature

Start with:

- `backend/technician_app/service.py`
- `backend/technician_app/views/helpdesk.py`
- `backend/technician_app/models.py`
- `backend/admin_app/views/admin_manage_technicians.py`
- `frontend/components/student/student-ict-helpdesk-page.tsx`
- `frontend/components/technician/technician-helpdesk-page.tsx`
- `frontend/components/admin/admin-manage-technicians-page.tsx`
- routes under `frontend/app/(student)/student/ict-helpdesk/` and `frontend/app/(technician)/technician/helpdesk/`

Useful query:

```bash
graphify query "Which files implement ICT helpdesk tickets, technician workflow, student ICT helpdesk page, and admin technician management?"
```

### Leave feature

Start with:

- `backend/student_app/leave_service.py`
- `backend/student_app/views/student_leave.py`
- `backend/student_app/views/student_leave_apply.py`
- `backend/student_app/views/student_leave_history.py`
- `backend/teacher_app/views/teacher_leave_requests.py`
- route pages under `frontend/app/(student)/student/leave/` and `frontend/app/(teacher)/teacher/leave-requests/`

Useful query:

```bash
graphify query "Which files implement student leave requests, leave history, and teacher leave approvals?"
```

## Targeted testing guidance

Prefer targeted checks over full-suite runs.

Backend examples:

```bash
cd backend
python manage.py test student_app.tests.CourseRegistrationRuleTests
python manage.py test teacher_app.tests.CourseContentAndAttendanceTests
python manage.py test applicant_app.tests.ApplicantAppApiTests
python manage.py test caterer_app.tests.CanteenWorkflowTests
python manage.py test librarian_app.tests
python manage.py test technician_app.tests
```

Frontend examples:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Before running a frontend command, check `frontend/package.json` if unsure which scripts exist. Do not run expensive full builds unless the change affects shared app routing, auth, layout, role-zone, or shared UI primitives.

## Graphify query examples

Election:

```bash
graphify query "Which files implement election creation, candidate listing, student ballot display, and student vote casting?"
```

Auth/API:

```bash
graphify query "Which files handle frontend API authentication, token storage, login, logout, and user profile fetching?"
```

Student dashboard:

```bash
graphify query "Which files implement the student dashboard frontend and backend API?"
```

Course registration:

```bash
graphify query "Which files implement student course registration rules, offered courses, requests, and approval flow?"
```

Attendance:

```bash
graphify query "Which files implement teacher attendance creation and student attendance viewing?"
```

Public website:

```bash
graphify query "Which files implement the public website pages, public API data, news, events, admissions, and official links?"
```

Library:

```bash
graphify query "Which files implement library circulation, book copies, laptop lending, librarian workspace, and student library display?"
```

ICT helpdesk:

```bash
graphify query "Which files implement student ICT tickets, technician helpdesk workflow, and admin technician management?"
```

Canteen:

```bash
graphify query "Which files implement canteen balance, allowance initialization, caterer workflow, and admin canteen management?"
```

Venue booking:

```bash
graphify query "Which files implement venue booking requests, admin venue approval, student bookings, and teacher bookings?"
```

## Default Codex instruction

For every new task:

Use Graphify first. Do not read `graphify-out/graph.html`. Identify the feature area, query the graph for the smallest relevant files, inspect only those files, explain the plan, then edit only what is necessary. Never open central hub files first. Run a targeted check after editing and then run `graphify update .`.

## Most important project rule

Do not scan the whole backend, whole frontend, or central hub files unless necessary. You can edit the central files if needed, but check the need level and then decide wheather to edit any central file or not.

Examples:

- Election issue: start with `election_service.py`, `admin_elections.py`, `student_elections.py`, `executive_elections*.py`, and `frontend/lib/elections.ts`.
- Attendance issue: start with attendance service/view files.
- Public website issue: start with public API/view and public-site frontend files.
- Login issue: start with account/auth/login files.
- Canteen issue: start with caterer service/view files and admin canteen page.
- Library issue: start with librarian app service/view files and librarian workspace components.
- ICT helpdesk issue: start with technician service/view files and helpdesk components.
- UI issue: start with the exact UI component or route page only.

Open high-impact shared files only after Graphify shows they are directly involved.
