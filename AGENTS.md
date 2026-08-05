# AGENTS.md - Rules For AI Agents Working On This Project

## Project Context

This repository is a full-stack university management portal:

- Backend: Django and Django REST Framework in `backend/`
- Frontend: Next.js and React in `frontend/`
- Runtime: Docker containers
- Knowledge graph: Graphify output in `graphify-out/`

Use Docker for backend and frontend commands. Do not introduce or rely on local
virtual environments for normal project work. Do not change Docker, Compose, or
Nginx configuration unless the user explicitly asks for infrastructure changes.

## Core Principles

1. Preserve existing behavior unless the user asks to change it.
2. Make the smallest working change that solves the task.
3. Prefer existing project patterns over new abstractions.
4. Search for existing helpers, functions, hooks, services, components, and UI
   blocks before creating new ones.
5. Keep runtime code configurable and data-driven where values can vary between
   universities.
6. Do not hardcode institution-specific names, emails, domains, codes, currency,
   timezone, policy copy, or public website content in reusable runtime code.
7. Never revert user changes unless the user explicitly asks.

## Graphify First

Before reading many files or editing code, use Graphify as the first navigation
layer.

Do not open `graphify-out/graph.html` unless the user explicitly asks for the
visual graph.

Preferred order:

1. `graphify query "<specific question>"`
2. `graphify explain "<feature or concept>"`
3. `graphify path "<source>" "<target>"`
4. `graphify-out/wiki/index.md` only for broad navigation, if it exists
5. `graphify-out/GRAPH_REPORT.md` only for broad architecture review

After code changes, run:

```bash
graphify update .
```

Dirty `graphify-out/` files are expected after updates. Do not revert them
unless the user asks.

## Standard Task Workflow

For every task:

1. Identify the feature area.
2. Run a targeted Graphify query.
3. Inspect only the smallest relevant file set.
4. Check existing shared code before creating new code.
5. List affected files before editing and explain why each file is needed.
6. Edit only the files needed for the task.
7. Run targeted verification in Docker.
8. Run `graphify update .` after code changes.
9. Summarize what changed, which files were modified, what checks ran, and any
   remaining risk.

Avoid broad scans of `backend/`, `frontend/app`, `frontend/components`, or large
generated outputs unless the request genuinely requires a repository-wide audit.

## Reuse Before Creating Anything

Before adding a new helper, function, hook, formatter, parser, component,
service method, or repeated UI block, search for an existing implementation.

Examples:

- Need percentage, currency, or date formatting? Search existing formatting
  helpers first.
- Need API error handling? Check shared fetch utilities first.
- Need pagination or request parsing? Check backend common helpers first.
- Need a table toolbar, entity editor, status badge, chart, or admin page shell?
  Check shared frontend components first.
- Need profile names or identifiers? Use shared profile helpers.

If an existing helper almost fits, extend it with a narrow optional parameter
instead of copying similar logic into a feature file.

## Shared Backend Code To Check First

Look in `backend/core/common/` and `backend/core/` before writing small backend
utilities.

Common helpers include:

- `core.common.errors`: `first_error`, `validation_error_response`
- `core.common.profiles`: profile display, identifiers, and role profile loading
- `core.common.money`: money formatting and decimal parsing
- `core.common.pagination`: pagination helpers
- `core.common.request_utils`: boolean, integer, and JSON parsing
- `core.common.academic_policy`: academic policy helpers
- `core/upload_security.py`: upload validation
- `core/media_access.py`: protected/public media URL helpers
- `notifications_package/service.py`: notification dispatch helpers

New backend code should import shared helpers directly when possible.

## Shared Frontend Code To Check First

Look in these areas before creating new frontend utilities or UI blocks:

- `frontend/lib/fetch-utils.ts`
- `frontend/lib/status-utils.ts`
- `frontend/lib/ums-settings.ts`
- `frontend/lib/public-api.ts`
- `frontend/components/utils/format.ts`
- `frontend/hooks/use-table-state.ts`
- `frontend/hooks/use-manage-staff.ts`
- `frontend/hooks/use-public-ums-settings.ts`
- `frontend/components/ui/`
- `frontend/components/admin/manage-page-header.tsx`
- `frontend/components/admin/entity-editor-card.tsx`
- `frontend/components/results/result-display.tsx`
- `frontend/components/charts/`
- Feature folders under `frontend/components/`

Use the settings contract for institution identity, terminology, locale,
currency, role labels, module labels, and feature visibility.

## High-Impact Files

Do not start with central hub files. Start with feature-specific views,
services, components, route pages, or API libraries.

Open or edit these files only when Graphify or the task clearly shows they are
needed:

- `backend/admin_app/models.py`
- `backend/admin_app/serializers.py`
- `backend/admin_app/settings_registry.py`
- `backend/admin_app/urls.py`
- `backend/auth_app/models.py`
- `backend/auth_app/permissions.py`
- `backend/core/settings.py`
- `frontend/lib/auth.ts`
- `frontend/lib/ums-settings.ts`
- `frontend/lib/ums-roles.ts`
- `frontend/proxy.ts`
- `frontend/components/layout/header.tsx`
- `frontend/components/role-zone/role-dashboard.tsx`
- `frontend/components/role-zone/create-role-page.tsx`
- `frontend/components/ui/button.tsx`
- `frontend/components/ui/card.tsx`
- `frontend/components/ui/sidebar.tsx`
- `frontend/components/public/public-site.tsx`

## Feature Entry Points

Confirm with Graphify, then start near the relevant feature:

- Public site/CMS: `backend/home_app/views/public_*`,
  `backend/admin_app/views/admin_public_*`, `frontend/lib/public-api.ts`,
  `frontend/components/public/`
- Settings/setup: `backend/admin_app/settings_registry.py`,
  `backend/admin_app/setup_wizard.py`, `backend/admin_app/views/admin_settings.py`,
  `frontend/lib/ums-settings.ts`
- Auth/account: `backend/auth_app/views/account.py`,
  `backend/admin_app/views/admin_create_account.py`,
  `frontend/components/ui/login-form.tsx`, `frontend/lib/auth.ts`
- Academic directory: `backend/admin_app/views/admin_academics_*`,
  `frontend/lib/admin-directory.ts`
- Academic calendar/schedule: `backend/admin_app/views/admin_semesters.py`,
  `backend/executive_app/course_schedule.py`,
  `frontend/components/admin/admin-semesters-page.tsx`,
  `frontend/components/role-zone/`
- Course registration: `backend/student_app/registration_service.py`,
  `backend/student_app/views/student_registration*`,
  `backend/executive_app/views/executive_registrations*`
- Attendance: `backend/teacher_app/attendance_service.py`,
  `backend/teacher_app/views/teacher_attendance*`,
  `backend/student_app/views/student_attendance*`
- Assignments/content: `backend/teacher_app/assignment_service.py`,
  `backend/teacher_app/course_content_service.py`, assignment pages and views
- Admissions: `backend/applicant_app/admissions_setup.py`,
  `backend/applicant_app/serializers.py`, `frontend/lib/apply.ts`,
  `frontend/components/apply/`
- Finance/accountant: `backend/accountant_app/service.py`,
  `backend/accountant_app/ledger_service.py`, `frontend/components/accountant/`,
  `frontend/components/finance/`
- Dining/canteen: `backend/caterer_app/service.py`,
  `backend/caterer_app/views/canteen.py`, `frontend/components/caterer/`
- Library: `backend/librarian_app/service.py`,
  `backend/librarian_app/views/library.py`, `frontend/components/librarian/`,
  `frontend/components/student/student-library-page.tsx`
- Helpdesk: `backend/technician_app/service.py`,
  `backend/technician_app/views/helpdesk.py`,
  `frontend/components/student/student-ict-helpdesk-page.tsx`,
  `frontend/components/technician/technician-helpdesk-page.tsx`
- Hostel: `backend/admin_app/views/admin_hostels.py`,
  `frontend/app/(admin)/admin/hostels/page.tsx`
- Elections: election services/views, `frontend/lib/elections.ts`, election
  components
- Venue booking: venue booking services/views,
  `frontend/components/venue-booking/venue-booking-page.tsx`
- Leave: `backend/student_app/leave_service.py`, leave views and pages

## Backend Rules

- Keep serializers, services, and views aligned with existing API shapes unless
  the user requests an API contract change.
- Prefer service-layer logic for reusable business rules.
- Use `select_related` / `prefetch_related` when adding list/detail endpoints
  that touch related records.
- Use shared error responses and request parsing helpers.
- Do not add migrations unless model changes require them or an existing model
  change is missing a migration.
- Do not edit migration files that have already been applied in shared
  environments unless the user explicitly asks and the migration strategy is
  clear.

## Frontend Rules

- Match existing design patterns and component conventions.
- Use shared settings, role, formatting, API, and status utilities.
- Keep UI state local unless existing shared hooks fit the workflow.
- Hide or guard disabled modules through the existing settings/module utilities.
- Avoid large duplicated JSX blocks; extract or reuse existing components when
  repetition becomes meaningful.
- Ensure text fits on mobile and desktop.

## Testing And Verification

Use targeted checks before broad checks.

Backend examples:

```bash
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend python manage.py test student_app.tests.CourseRegistrationRuleTests --keepdb
docker compose exec -T backend python manage.py test teacher_app.tests.CourseContentAndAttendanceTests --keepdb
docker compose exec -T backend python manage.py test applicant_app.tests.ApplicantAppApiTests --keepdb
```

Frontend examples:

```bash
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run build
```

Run full frontend builds only when shared routing, auth, layout, settings,
role-zone, or build-time behavior changes.

## Git And Filesystem Rules

- Do not revert changes you did not make.
- Do not use destructive git commands unless the user explicitly asks.
- Do not edit generated or dependency folders:
  `node_modules`, `.next`, `graphify-out`, `dist`, `build`, `coverage`,
  `__pycache__`.
- Do not rename files unless necessary.
- Keep unrelated refactors out of task-focused changes.
- Preserve existing formatting style in touched files.

## Final Response Requirements

When finishing a task, report:

- What changed
- Files modified
- Checks run and whether they passed
- Any known risks, skipped checks, or follow-ups

Keep the final answer concise and focused on the user's request.
