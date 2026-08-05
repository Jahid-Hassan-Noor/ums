# Universal University Portal Roadmap

This document turns the current AIU-specific portal into a reusable university
portal platform. It is written as an implementation roadmap: each section names
the pipeline or functionality to change, why it matters, where the risk is, and
how to know the change is complete.

The goal is not to remove the existing AIU demo/test data from the repository.
The goal is to ensure no university-specific information is required by the
runtime codebase. AIU-specific details may remain only in disposable test files,
demo fixtures, or clearly named seed packs that can be deleted without breaking
the system.

---

## 1. Core Universality Rule

The system should run for any university through configuration and data entry,
without editing source code.

### Hardcoding Policy

Allowed:

- AIU details in test fixtures.
- AIU details in clearly named demo seed files.
- AIU details in documentation that describes previous examples or migration
  context.

Not allowed:

- AIU name, abbreviation, emails, URLs, addresses, school codes, centre codes,
  programme names, intake dates, scholarship text, policy text, currency, or
  timezone inside reusable runtime code.
- AIU-specific fallback content in frontend pages.
- Backend logic that requires AIU-specific organization codes such as `COR`,
  `CSAA`, `ICT`, `LC`, `CGS`, `CFGS`, `SBSS`, `SEHS`, or `SCI`.
- API serializers or services that silently assign users to AIU-specific
  centers, departments, units, or schools.
- Navigation, role dashboards, public website copy, or operational workflows
  that assume one university's structure.

### Target Runtime Principle

Every institution-specific value should come from one of these sources:

1. System settings.
2. Public CMS content.
3. Academic organization records.
4. Module-specific policy records.
5. Tenant/demo seed data loaded intentionally.
6. Environment variables for deployment-only values.

If a value can vary between universities, it should not be embedded directly in
runtime code.

---

## 2. Current Strengths To Preserve

The project already has several pieces that make the universal goal realistic.

### Existing Configuration Foundation

The backend has a settings registry in:

- `backend/admin_app/settings_registry.py`
- `backend/admin_app/views/admin_settings.py`
- `backend/home_app/views/public_settings.py`

The frontend already has a public settings consumer in:

- `frontend/lib/ums-settings.ts`

This should become the central contract for institution identity, locale,
currency, branding, terminology, enabled modules, and default policies.

### Existing Public CMS Foundation

The backend already has public content models and admin/public views for:

- Public pages.
- News.
- Events.
- Official links.
- Public helper payloads.

Relevant files:

- `backend/home_app/models.py`
- `backend/home_app/views/public_helpers.py`
- `backend/home_app/views/public_home.py`
- `backend/admin_app/views/admin_public_content.py`
- `backend/admin_app/views/public_content_utils.py`

This CMS foundation should replace static public website content.

### Existing Flexible Academic Organization Foundation

The academic organization model already supports:

- Schools.
- Centers.
- Departments.
- Units.
- Programs.
- Semester groups.
- Centers with academic or non-academic type.
- Centers with semester-based or whole-year academic modes.

Relevant files:

- `backend/admin_app/models.py`
- `backend/admin_app/views/admin_academics.py`
- `backend/admin_app/views/admin_academics_centres.py`
- `backend/admin_app/views/admin_semesters.py`
- `frontend/components/admin/admin-academic-directory-page.tsx`
- `frontend/lib/admin-directory.ts`

The remaining work is to remove old assumptions around names, codes, and
special session types.

---

## 3. Highest Priority Implementation Phases

Recommended order:

1. Establish the universal configuration contract.
2. Replace public website static data with CMS/settings-driven content.
3. Split generic bootstrap data from AIU demo/test data.
4. Generalize academic sessions and organization setup.
5. Remove hardcoded role-to-center/unit mappings.
6. Localize currency, timezone, and payment settings.
7. Make operational modules policy-driven and optional.
8. Add a non-AIU readiness test matrix.

This order gives the biggest visible and architectural shift first.

---

## 4. Phase 1: Universal Institution Configuration

### Goal

Create one authoritative configuration layer for institution-level identity and
policy. The frontend and backend should both read from this layer instead of
local static defaults.

### What To Configure

Institution identity:

- University name.
- Short name.
- Legal name.
- Tagline.
- Address.
- Phone.
- General email.
- Admissions email.
- Website URL.
- Logo URL.
- Hero image URL.

Localization:

- Timezone.
- Locale.
- Currency code.
- Currency symbol.
- Number format.
- Date format.
- Time format.

Terminology:

- School label.
- Centre/center label.
- Department label.
- Unit label.
- Program/programme label.
- Course label.
- Semester label.
- Academic year label.
- Student ID label.
- Staff ID label.
- Applicant label.

Branding:

- Primary color.
- Secondary color.
- Accent color.
- Logo.
- Public hero image.
- Login image.
- Favicon.

Feature flags:

- Admissions.
- Public website.
- Canteen.
- Library.
- Hostel.
- Venue booking.
- ICT/helpdesk.
- Elections.
- Finance.
- Attendance.
- Evaluations.
- Leave.
- Notifications.

Default policies:

- Password policy.
- Upload limits.
- Attendance threshold.
- Leave notice period.
- Default academic calendar type.
- Default application number prefix.
- Default payment gateway provider.

### Current Risk

Some settings already exist, but many modules still define their own defaults.
Examples include static public content, Malaysian timezone, `MYR`, `RM`,
AIU-specific labels, and module-specific defaults.

### Implementation Steps

1. Audit `backend/admin_app/settings_registry.py` and decide which settings
   belong in the universal contract.
2. Extend public settings payloads so frontend can access all institution-level
   values.
3. Normalize all frontend defaults in `frontend/lib/ums-settings.ts` to generic
   values.
4. Add backend helper functions for common config reads.
5. Replace module-level hardcoded locale, currency, timezone, and labels with
   settings lookups.
6. Add admin UI fields for the new settings.
7. Add validation for required settings.
8. Add a setup completeness endpoint or checklist.

### Acceptance Criteria

- Changing university name in admin settings updates public pages, dashboard
  labels, page titles, and email-visible text where applicable.
- Changing timezone affects canteen, semester, attendance, event, and finance
  date handling.
- Changing currency affects every money display and backend finance payload.
- No reusable frontend default contains AIU/Albukhary-specific text.
- No reusable backend default requires AIU-specific organization codes.

---

## 5. Phase 2: Public Website CMS Migration

### Goal

Make the public website fully driven by public settings and CMS content.

### Current Risk

The public website has the highest amount of visible AIU-specific content in
runtime code. Static fallback data includes AIU identity, AIU schools, AIU
centers, AIU admissions copy, AIU news, AIU values, AIU governance, AIU campus
details, and AIU-specific metadata.

High-risk files:

- `frontend/lib/ums-public-data.ts`
- `frontend/lib/public-api.ts`
- `frontend/components/public/public-site.tsx`
- `frontend/app/page.tsx`
- `frontend/app/about/page.tsx`
- `frontend/app/admissions/page.tsx`
- `frontend/app/programmes/page.tsx`
- `frontend/app/schools/page.tsx`
- `frontend/app/centres/page.tsx`
- `frontend/app/news/page.tsx`
- `frontend/app/services/page.tsx`
- `frontend/app/student-life/page.tsx`
- `frontend/app/[...slug]/page.tsx`

### Implementation Steps

1. Treat backend CMS content as the primary source for public pages.
2. Treat institution public settings as the primary source for institution
   identity, hero images, metadata, contact details, and labels.
3. Replace static page metadata with dynamic metadata from CMS/settings.
4. Replace static route page content with fetched public page content.
5. Replace AIU static fallback data with neutral fallback data.
6. Add CMS records for common pages:
   - Home.
   - About.
   - Admissions.
   - Programs.
   - Schools.
   - Centers.
   - News.
   - Events.
   - Services.
   - Student life.
   - Directories.
7. Make public navigation configurable through CMS or settings.
8. Ensure missing CMS content shows neutral setup guidance to admins and a clean
   empty state to public users.
9. Add admin controls for ordering, publishing, hiding, and linking public pages.
10. Ensure static fallback images are generic, not AIU campus images.

### Acceptance Criteria

- Deleting all AIU seed/demo content does not break public routes.
- A new university can set name, logo, hero, pages, news, schools, centers, and
  admissions copy without source edits.
- Public route metadata no longer mentions AIU unless CMS data explicitly does.
- `frontend/lib/ums-public-data.ts` contains only neutral schema/default helpers
  or is replaced by API-backed content.
- Public pages work when no school, center, or programme has been created yet.

---

## 6. Phase 3: Seed Data And Demo Pack Separation

### Goal

Separate generic installation/bootstrap data from AIU-specific demo data.

### Current Risk

Current seed commands create AIU organization structures, users, school codes,
center codes, rooms, emails, public content, and system settings. This is useful
for testing, but dangerous if it is treated as the default setup path.

High-risk files:

- `backend/admin_app/management/commands/seed_ums_organisation.py`
- `backend/admin_app/management/commands/seed_all_data.py`
- AIU-specific test seed files.

### Implementation Steps

1. Create a generic bootstrap command that creates only required system defaults:
   - Admin role support.
   - Required settings keys.
   - Empty/default feature flags.
   - Optional generic sample records.
2. Move AIU-specific organization data into a clearly named demo command, such
   as `seed_aiu_demo_data`.
3. Move AIU public content into an AIU demo content pack.
4. Move AIU users/emails into AIU test/demo fixtures only.
5. Make demo commands opt-in.
6. Rename command help text so it is clear when a command seeds demo data.
7. Document how to delete demo data safely.
8. Add a second non-AIU demo pack for universal testing.

### Acceptance Criteria

- Fresh setup can run without creating AIU data.
- Removing AIU demo seed files does not break migrations, app startup, tests
  unrelated to AIU fixtures, or frontend builds.
- Demo files are named clearly enough that future maintainers know they are not
  platform requirements.
- CI can run against a neutral university fixture.

---

## 7. Phase 4: Academic Organization And Calendar Generalization

### Goal

Allow any university to model its academic structure without code edits.

### Required Flexibility

Schools:

- Optional.
- Configurable name, code, slug, dean/lead, public visibility.

Centers:

- Academic or non-academic.
- Semester-based or whole-year/annual/continuous.
- Optional parent/owner relationships if needed later.
- Configurable public visibility.

Departments:

- Can belong to a school or center.
- Can be academic or administrative depending on institution needs.

Units:

- Can belong to a school, center, department, or administrative area.
- Should not require hardcoded codes for special roles.

Programs:

- Can belong to schools or academic centers.
- Can be semester-based or whole-year depending on owner.
- Can have configurable levels, duration, credit model, and public visibility.

Calendars:

- Multiple calendar groups.
- Semester-based groups.
- Annual/whole-year groups.
- Custom session names.
- Active/inactive calendars.

### Current Risk

The center flexibility exists, but old naming remains around `IELTSSession`.
Whole-year center logic should not be IELTS-specific.

High-risk files:

- `backend/admin_app/models.py`
- `backend/admin_app/views/admin_semesters.py`
- `backend/executive_app/course_schedule.py`
- `backend/executive_app/views/executive_courses_offer.py`
- `frontend/components/admin/admin-semesters-page.tsx`
- `frontend/components/role-zone/academic-calendar-surface.tsx`

### Implementation Steps

1. Rename/generalize `IELTSSession` concept to an institution-neutral session
   model, such as `AnnualAcademicSession` or `AcademicSession`.
2. Update admin semester/session APIs to use neutral names.
3. Preserve migration compatibility for existing AIU demo data.
4. Ensure centers can be created as:
   - Non-academic.
   - Academic semester-based.
   - Academic whole-year.
5. Ensure public and internal pages display center academic mode correctly.
6. Generalize course offering eligibility beyond schools.
7. Allow courses/programs to be associated with academic centers where relevant.
8. Ensure schedule/attendance/results logic works for center-owned programs.
9. Add admin UI warnings when an academic center has no configured calendar.

### Acceptance Criteria

- Admin can create a non-academic center with no academic calendar.
- Admin can create an academic center with semesters.
- Admin can create an academic center with whole-year sessions.
- Course offerings can target the correct academic owner.
- No user-facing label says IELTS unless the configured program/session is
  actually IELTS.
- Removing LC/IELTS demo data does not break whole-year center support.

---

## 8. Phase 5: Role, Permission, Navigation, And Module Ownership

### Goal

Keep role-based access, but remove institution-specific assumptions about where
roles belong and which modules they manage.

### Current Risk

Roles are fixed across backend and frontend. That can be acceptable for a first
universal version, but hardcoded role placement is not acceptable.

Examples of risky assumptions:

- Librarian assigned to a specific center/unit code.
- Caterer assigned to a specific center/unit code.
- Technician assigned to ICT by code.
- Frontend navigation assumes specific module names and ownership.
- Middleware/proxy route rules assume fixed role home paths.

High-risk files:

- `backend/auth_app/models.py`
- `backend/auth_app/serializers.py`
- `backend/auth_app/permissions.py`
- `frontend/lib/ums-roles.ts`
- `frontend/proxy.ts`

### Implementation Steps

1. Define the difference between core platform roles and institution-defined
   staff placement.
2. Keep core roles if needed:
   - Admin.
   - Student.
   - Teacher.
   - Executive.
   - Applicant.
   - Accountant.
   - HR.
   - Librarian.
   - Caterer.
   - Technician.
3. Move role display labels and descriptions into settings/config.
4. Move module visibility into settings/config.
5. Move role-to-module permissions into a configurable matrix.
6. Move role-to-unit/department/center default placement into admin-selectable
   setup records.
7. Replace hardcoded special role organization lookup by code with configured
   ownership records.
8. Make route guards read the effective role/module matrix where practical.
9. Add clear admin errors when a role requires module ownership but no owner is
   configured.

### Acceptance Criteria

- A librarian role can be assigned to any configured library unit or center.
- A caterer role can be assigned to any configured dining/canteen unit.
- A technician role can be assigned to any configured service desk/IT unit.
- Disabling a module hides its routes and dashboard cards.
- No backend account creation flow requires `COR`, `CSAA`, or `ICT`.
- Navigation labels can be changed without editing `frontend/lib/ums-roles.ts`.

---

## 9. Phase 6: Admissions Pipeline Configuration

### Goal

Make admissions reusable for universities with different application forms,
document requirements, workflows, scholarship policies, and application number
formats.

### Current Strength

There is already a configurable admissions setup helper.

Relevant file:

- `backend/applicant_app/admissions_setup.py`

### Current Risk

Several admissions assumptions still appear fixed:

- Application number prefix.
- Status pipeline.
- Document type choices.
- Scholarship/review labels.
- Some applicant identity fields.
- Public admissions page copy and deadlines.

High-risk files:

- `backend/applicant_app/models.py`
- `backend/applicant_app/serializers.py`
- `backend/applicant_app/admissions_setup.py`
- `frontend/components/apply/apply-application-form.tsx`
- `frontend/components/apply/application-status-steps.tsx`
- `frontend/app/admissions/page.tsx`

### Implementation Steps

1. Make application number prefix configurable.
2. Make application number format configurable enough for common patterns.
3. Move document types into admissions setup.
4. Move required/optional document rules into admissions setup.
5. Move custom applicant fields into admissions setup.
6. Move workflow steps/status labels into admissions setup.
7. Make scholarship sections optional and label-configurable.
8. Allow workflows with no scholarship stage.
9. Allow workflows with or without interview stages.
10. Move intake deadlines and public admissions copy to CMS/settings.
11. Ensure programme-specific admissions requirements can override global rules.

### Acceptance Criteria

- A university can use its own application prefix without code edits.
- A university can remove scholarship review from the applicant journey.
- A university can add or remove document types from admin settings.
- Public admissions copy is editable from CMS/admin.
- Applicant status UI is generated from configured workflow labels.

---

## 10. Phase 7: Finance, Currency, And Payment Gateway Localization

### Goal

Support institutions outside Malaysia and institutions with different payment
providers.

### Current Risk

Finance code and UI contain Malaysian assumptions:

- `MYR`.
- `RM`.
- `en-MY`.
- ToyyibPay/DuitNow terminology.
- Malaysian payment gateway assumptions.

High-risk files:

- `backend/accountant_app/models.py`
- `backend/accountant_app/service.py`
- `frontend/components/utils/format.ts`
- `frontend/components/finance/subscriptions-page.tsx`
- `frontend/components/student/student-fines-page.tsx`
- `frontend/components/accountant/accountant-workspace-page.tsx`
- `frontend/components/accountant/accountant-canteen-page.tsx`

### Implementation Steps

1. Add institution currency settings.
2. Add institution locale settings.
3. Replace hardcoded money formatting with shared currency formatter.
4. Replace backend default currency literals with settings-derived defaults.
5. Make payment provider labels configurable.
6. Keep provider adapters modular.
7. Support a disabled/manual payment mode.
8. Ensure invoices, fines, subscriptions, canteen balances, ledger entries, and
   reports all use the same currency source.
9. Add migration strategy for existing `MYR` demo records.

### Acceptance Criteria

- Setting currency to `USD`, `EUR`, `BDT`, or another code changes all money UI.
- No user-facing frontend text says `RM` unless currency settings say so.
- Backend APIs do not assume `MYR` for new records unless configured.
- Payment gateway UI can show a generic/manual provider.
- Existing AIU/MYR demo data remains valid as demo data.

---

## 11. Phase 8: Canteen/Dining Module Policy

### Goal

Make the canteen module optional and policy-driven.

### Current Risk

The canteen module assumes:

- Malaysian timezone.
- `RM` display.
- Monthly allowance model.
- Specific eligibility logic.
- One canteen workflow.

High-risk files:

- `backend/caterer_app/models.py`
- `backend/caterer_app/service.py`
- `backend/caterer_app/views/canteen.py`
- `frontend/components/caterer/caterer-dashboard-page.tsx`
- `frontend/components/accountant/accountant-canteen-page.tsx`

### Implementation Steps

1. Add canteen/dining feature settings.
2. Configure monthly allowance amount and currency through finance settings.
3. Configure allowance reset timezone and month boundary.
4. Configure eligible student statuses.
5. Configure whether allowance depends on scholarship/cohort/program.
6. Configure whether canteen balance syncs to student profile.
7. Replace hardcoded `RM` strings with shared money formatting.
8. Allow the module to be disabled cleanly.
9. Rename UI labels from canteen to configured dining label if needed.

### Acceptance Criteria

- A university can disable the canteen module.
- A university can use a different currency.
- A university can set allowance amount and eligibility rules.
- No canteen code assumes `Asia/Kuala_Lumpur`.
- No canteen user-facing text assumes `RM`.

---

## 12. Phase 9: Library Module Policy

### Goal

Make library services configurable by institution.

### Current Risk

Library already has some feature flags, but borrowing limits, asset types, loan
periods, laptop/room assumptions, and fine policies need stronger configuration.

Relevant files:

- `backend/librarian_app/models.py`
- `backend/librarian_app/serializers.py`
- `backend/librarian_app/service.py`
- `backend/librarian_app/views/library.py`
- `frontend/components/librarian/librarian-workspace-page.tsx`
- `frontend/components/student/student-library-page.tsx`

### Implementation Steps

1. Add configurable library service types:
   - Books.
   - Laptops.
   - Rooms.
   - Other assets.
2. Add configurable loan limits per asset type.
3. Add configurable loan periods per asset type.
4. Add configurable fine rules.
5. Add configurable renewal rules.
6. Add configurable reservation rules.
7. Replace hardcoded laptop/room limits with settings.
8. Ensure disabled services disappear from student and librarian views.

### Acceptance Criteria

- A university can run books only.
- A university can disable laptop lending.
- A university can set loan limits and loan periods.
- Student views reflect the enabled services and limits.
- Librarian views do not show disabled services.

---

## 13. Phase 10: Helpdesk And Technician Module Generalization

### Goal

Turn ICT helpdesk into a configurable service desk module.

### Current Risk

The current module assumes ICT-specific categories and reference prefixes.

High-risk files:

- `backend/technician_app/models.py`
- `backend/technician_app/service.py`
- `backend/technician_app/views/helpdesk.py`
- `frontend/components/student/student-ict-helpdesk-page.tsx`
- `frontend/components/technician/technician-helpdesk-page.tsx`

### Implementation Steps

1. Create configurable helpdesk/service desk categories.
2. Make reference prefix configurable.
3. Make display label configurable:
   - ICT Helpdesk.
   - IT Service Desk.
   - Facilities Helpdesk.
   - Student Support Desk.
4. Make ticket statuses configurable or at least label-configurable.
5. Configure assignment rules by category.
6. Configure SLA/priority rules if needed.
7. Remove hardcoded external/manual form links from runtime defaults.
8. Allow multiple service desks later if required.

### Acceptance Criteria

- A university can rename ICT Helpdesk without code changes.
- Ticket categories can be added/removed by admin.
- Ticket reference prefix is not fixed to `ICT-`.
- Technician ownership does not require an `ICT` department code.

---

## 14. Phase 11: Hostel Module Policy

### Goal

Support different residence models and room policies.

### Current Risk

Hostel logic assumes male/female hostel types, default capacities, and room code
patterns.

Relevant files:

- `backend/admin_app/models.py`
- `backend/admin_app/views/admin_hostels.py`
- `frontend/app/(admin)/admin/hostels/page.tsx`

### Implementation Steps

1. Configure allowed residence types.
2. Support gender-specific, mixed, family, staff, or custom labels if needed.
3. Configure default room capacity.
4. Configure max room capacity.
5. Configure room code generation format.
6. Configure bed assignment rules.
7. Configure hostel eligibility rules.
8. Ensure frontend selects use configured labels.

### Acceptance Criteria

- A university can define custom residence type labels.
- Room capacity defaults come from settings.
- Hostels are not limited to only male/female labels.
- Room code format can be changed or manually overridden.

---

## 15. Phase 12: Elections Module Generalization

### Goal

Make elections configurable for different universities and governance models.

### Current Risk

Election terminology assumes specific student representative and school
committee concepts.

Relevant files:

- `backend/admin_app/election_service.py`
- `backend/admin_app/views/admin_elections.py`
- `backend/student_app/views/student_elections.py`
- `backend/executive_app/views/executive_elections.py`
- `backend/technician_app/models.py`
- `frontend/lib/elections.ts`
- `frontend/components/admin/admin-elections-page.tsx`
- `frontend/components/student/student-elections-page.tsx`

### Implementation Steps

1. Make election types configurable.
2. Make constituencies configurable:
   - University-wide.
   - School.
   - Center.
   - Department.
   - Program.
   - Cohort.
3. Make seat labels configurable.
4. Make nomination rules configurable.
5. Make voter eligibility configurable.
6. Make result publication rules configurable.
7. Remove hardcoded SRC/school committee assumptions from user-facing text.

### Acceptance Criteria

- A university can create a generic student council election.
- A university can create department-level elections.
- Election labels do not assume AIU governance terms.
- Eligibility is based on configured constituency rules.

---

## 16. Phase 13: Venue Booking Module Policy

### Goal

Make venues and booking approval rules reusable across institutions.

### Relevant Files

- `backend/admin_app/venue_booking_service.py`
- `backend/admin_app/views/admin_venues.py`
- `backend/admin_app/views/admin_venue_bookings.py`
- `backend/student_app/views/student_venue_bookings.py`
- `backend/teacher_app/views/teacher_venue_bookings.py`
- `frontend/components/venue-booking/venue-booking-page.tsx`

### Implementation Steps

1. Configure venue categories.
2. Configure booking requester roles.
3. Configure approval workflow.
4. Configure blackout dates.
5. Configure booking duration limits.
6. Configure required fields per booking type.
7. Ensure disabled venue booking routes are hidden.

### Acceptance Criteria

- A university can disable venue booking.
- A university can define its own venue categories.
- Approval workflow can be changed without code edits.

---

## 17. Phase 14: Academic Policy Workflows

### Goal

Make academic policies configurable enough for different universities.

### Areas To Review

Attendance:

- Attendance threshold.
- QR/session validity.
- Late/present/absent statuses.
- Excuse/correction policy.
- Minimum warning classes.
- Program-specific rules.

Leave:

- Minimum notice period.
- Required approvers.
- Approval order.
- Dean/teacher/executive role mapping.
- Auto-approval/rejection rules.

Evaluations:

- Survey title and branding.
- Required survey gates.
- Question templates.
- Who can create/publish surveys.
- Whether incomplete evaluations block registration.

Results and grading:

- Grade scale.
- GPA rules.
- Final exam rules.
- Retake rules.
- Transcript labels.
- Academic standing policy.

Course registration:

- Credit limits.
- Prerequisites.
- Repeat rules.
- Academic hold rules.
- Eligible owner rules for schools/centers/programs.

### High-Risk Files To Review

- `backend/teacher_app/attendance_service.py`
- `backend/student_app/leave_service.py`
- `backend/student_app/views/student_leave_apply.py`
- `backend/student_app/views/student_evaluations.py`
- `backend/executive_app/views/executive_evaluations.py`
- `backend/student_app/registration_service.py`
- `backend/executive_app/views/executive_courses_offer.py`
- `frontend/components/role-zone/academic-calendar-surface.tsx`
- `frontend/components/role-zone/role-schedule-page.tsx`

### Acceptance Criteria

- Attendance QR validity can be changed by settings.
- Leave approvers are configured, not discovered by designation text.
- Evaluation titles do not hardcode a university-specific survey name.
- Registration policies can vary by program/calendar group.
- Grade/GPA labels are institution-configurable where displayed.

---

## 18. Phase 15: Frontend Navigation And Dashboard Configuration

### Goal

Make role navigation and dashboards reflect enabled modules and configured
institution terminology.

### Current Risk

Frontend navigation is one of the places where module assumptions become visible
to users. If a university does not use canteen, ICT, hostel, or elections, those
routes should not appear.

High-risk files:

- `frontend/lib/ums-roles.ts`
- `frontend/proxy.ts`
- `frontend/components/role-zone/role-dashboard.tsx`
- `frontend/components/role-zone/create-role-page.tsx`
- Role route pages under `frontend/app/(admin)`, `frontend/app/(student)`,
  `frontend/app/(teacher)`, `frontend/app/(executive)`, and other role groups.

### Implementation Steps

1. Define a route/module registry.
2. Map routes to feature flags.
3. Map dashboard cards to feature flags.
4. Map role nav labels to configurable terminology.
5. Hide disabled module routes in navigation.
6. Guard disabled module routes at page/API level.
7. Ensure proxy/middleware supports disabled modules cleanly.
8. Add empty/setup states for modules that are enabled but not configured.

### Acceptance Criteria

- Disabled modules do not show in sidebars or dashboards.
- Direct visits to disabled module routes show a controlled unavailable page.
- Role descriptions do not mention AIU-specific departments or offices.
- Navigation can use configured labels for center/centre, programme/program, and
  module names.

---

## 19. Phase 16: Backend API And Serializer Cleanup

### Goal

Remove hardcoded institution assumptions from API behavior.

### What To Look For

- Code-based organization lookups.
- Hardcoded email domains.
- Hardcoded public identifiers.
- Hardcoded timezone/currency.
- Hardcoded labels in API responses.
- Hardcoded statuses that should be configured.
- Business rules tied to AIU structure.

### Priority Areas

Account creation:

- Remove special handling based on `COR`, `CSAA`, and `ICT`.
- Let admin choose placement or let module ownership config decide.

Academic APIs:

- Generalize whole-year sessions.
- Generalize eligibility beyond school-only assumptions.

Applicant APIs:

- Configurable application prefix.
- Configurable documents/status labels.

Finance APIs:

- Configurable currency and payment provider.

Operational APIs:

- Configurable helpdesk categories.
- Configurable canteen/library/hostel/election policies.

### Acceptance Criteria

- API responses do not expose AIU-specific labels unless they came from database
  content or settings.
- Serializers validate against configured policy, not hardcoded AIU structure.
- Reusable backend code can run with a blank generic university setup.

---

## 20. Phase 17: Data Model And Migration Strategy

### Goal

Introduce universality without breaking existing data.

### Strategy

1. Prefer additive fields and neutral aliases first.
2. Keep existing fields during transition.
3. Create data migrations only when model changes require them.
4. Preserve AIU demo data as data, not runtime logic.
5. Avoid destructive renames until API/frontend compatibility is ready.
6. Use compatibility serializers if old frontend code needs transition support.

### Special Case: IELTS/Whole-Year Session

If `IELTSSession` already has real/demo data:

1. Add a neutral model or neutral API representation.
2. Migrate existing IELTS records to the neutral representation.
3. Keep a compatibility alias if needed.
4. Remove user-facing generic usage of the IELTS name.
5. Let IELTS be only a program/session name in data.

### Acceptance Criteria

- Existing demo data still loads.
- New non-AIU data can be created without AIU-specific fields.
- Renamed concepts have compatibility coverage.
- Migrations are reversible where practical.

---

## 21. Phase 18: Universal Setup Wizard

### Goal

Give administrators a clear setup flow for a new institution.

### Suggested Wizard Steps

1. Institution profile:
   - Name.
   - Short name.
   - Legal name.
   - Contact details.
   - Website.

2. Branding:
   - Logo.
   - Favicon.
   - Primary colors.
   - Public hero image.

3. Localization:
   - Timezone.
   - Locale.
   - Currency.
   - Date/time format.

4. Terminology:
   - School/center labels.
   - Program/programme preference.
   - Semester/session labels.

5. Academic structure:
   - Schools.
   - Centers.
   - Departments.
   - Units.
   - Programs.

6. Academic calendars:
   - Semester groups.
   - Whole-year/session groups.
   - Active academic periods.

7. Enabled modules:
   - Admissions.
   - Finance.
   - Canteen/dining.
   - Library.
   - Hostel.
   - Helpdesk.
   - Elections.
   - Venue booking.

8. Role ownership:
   - Library owner.
   - Dining/canteen owner.
   - Helpdesk owner.
   - Finance owner.
   - Academic executive owners.

9. Admissions:
   - Application prefix.
   - Required documents.
   - Workflow stages.
   - Intake periods.

10. Public website:
    - Home page.
    - About page.
    - Admissions page.
    - Academic pages.
    - News/events.

### Acceptance Criteria

- A new university can complete setup from admin UI.
- Setup completeness can be checked programmatically.
- Missing setup shows actionable admin messages.
- Public users never see raw configuration errors.

---

## 22. Phase 19: Testing And Verification Matrix

### Goal

Prevent AIU-specific assumptions from returning later.

### Required Test Profiles

AIU demo profile:

- Allowed only in demo/test seed scope.
- Verifies existing demo data still works.

Neutral university profile:

- Example name: Example Metropolitan University.
- Non-Malaysian timezone.
- Non-MYR currency.
- Different school/center codes.
- At least one academic center with semesters.
- At least one academic center with whole-year sessions.
- At least one non-academic center.
- Optional canteen disabled.
- Optional hostel disabled.
- Custom helpdesk category names.

Minimal university profile:

- Institution settings only.
- No public content yet.
- No optional modules enabled.
- No academic data yet.

### Automated Checks

Backend:

- Settings API returns configured identity.
- Public settings API contains no AIU fallback.
- Account creation works without AIU organization codes.
- Academic center creation supports all center modes.
- Admissions application numbers use configured prefix.
- Finance records use configured currency.
- Disabled modules reject or hide actions cleanly.

Frontend:

- Public home renders configured university name.
- Public route metadata uses configured/CMS data.
- Navigation hides disabled modules.
- Money formatting uses configured currency.
- Center/centre/programme labels follow terminology settings.
- Apply form follows configured admissions setup.

Static search checks:

- Fail CI when AIU terms appear in runtime files.
- Allow AIU terms in test/demo seed paths.
- Scan for:
  - `AIU`
  - `Albukhary`
  - `aiu.edu`
  - `SBSS`
  - `SEHS`
  - `SCI`
  - `LC`
  - `CGS`
  - `CFGS`
  - `COR`
  - `CSAA`
  - `ICT`
  - `MYR`
  - `RM`
  - `Asia/Kuala_Lumpur`

### Suggested Allowlist

AIU terms should be allowed only under paths like:

- `backend/**/tests/**`
- `backend/**/test_*.py`
- `backend/admin_app/management/commands/*aiu*seed*.py`
- `backend/admin_app/management/commands/*demo*.py`
- `docs/**`

Do not allow AIU terms in:

- Runtime views.
- Runtime serializers.
- Runtime services.
- Frontend route pages.
- Frontend components.
- Frontend libraries used by production pages.
- Generic seed/bootstrap commands.

---

## 23. Suggested Work Breakdown

### Milestone 1: Configuration Contract

Deliverables:

- Expanded institution settings.
- Public settings API updated.
- Frontend settings type updated.
- Neutral defaults.
- Static search guard drafted.

Definition of done:

- Public settings can describe a non-AIU university.
- No frontend fallback identity uses AIU.

### Milestone 2: Public Website Neutralization

Deliverables:

- Public pages use CMS/settings.
- Static AIU public data removed from runtime.
- Metadata is dynamic.
- Neutral empty states.

Definition of done:

- The public website can be rebranded from admin/CMS only.

### Milestone 3: Seed Separation

Deliverables:

- Generic bootstrap command.
- AIU demo seed command.
- Optional non-AIU demo seed command.
- Seed documentation.

Definition of done:

- Fresh setup does not create AIU data unless explicitly requested.

### Milestone 4: Academic Generalization

Deliverables:

- Neutral whole-year academic session model/API naming.
- Academic center UI complete.
- Course eligibility generalized.
- Calendar/session displays neutralized.

Definition of done:

- A university can configure school-based, center-based, semester-based, and
  whole-year academic programs.

### Milestone 5: Role And Module Config

Deliverables:

- Configurable module visibility.
- Configurable role labels.
- Configurable special-role ownership.
- Navigation route registry.

Definition of done:

- No account creation logic depends on AIU center/unit codes.

### Milestone 6: Finance And Operations

Deliverables:

- Shared currency formatter everywhere.
- Payment provider abstraction improved.
- Canteen/library/helpdesk/hostel/election policies configurable.

Definition of done:

- Optional modules can be disabled cleanly and enabled with custom labels.

### Milestone 7: Universal Readiness Tests

Deliverables:

- Neutral university fixture.
- Minimal university fixture.
- Static hardcode scan.
- Backend and frontend targeted tests.

Definition of done:

- CI catches accidental AIU hardcoding in runtime files.

---

## 24. Recommended Static Hardcode Guard

Add a script or CI check that scans runtime files for university-specific terms.

### Search Terms

Start with:

```text
AIU
Albukhary
aiu.edu
SBSS
SEHS
SCI
LC
CGS
CFGS
COR
CSAA
CQAA
CDAE
ICT
MYR
RM
Asia/Kuala_Lumpur
en-MY
ToyyibPay
DuitNow
```

### Runtime Paths To Scan

Scan:

- `backend/*_app/**/*.py`
- `backend/core/**/*.py`
- `frontend/app/**/*`
- `frontend/components/**/*`
- `frontend/lib/**/*`
- `frontend/hooks/**/*`

Exclude:

- Migrations if they preserve old data.
- Tests.
- Demo seed commands.
- Documentation.
- Generated/dependency folders.

### Expected Outcome

The guard should fail if a hardcoded institution-specific value appears in
runtime code. It should pass when the same value appears in an allowed test/demo
file.

---

## 25. Practical Definition Of Universal

The portal can be considered universal when this scenario works without source
edits:

1. Fresh database is created.
2. Generic bootstrap is run.
3. Admin logs in.
4. Admin enters institution profile and branding.
5. Admin chooses timezone, locale, and currency.
6. Admin configures terminology.
7. Admin enables/disables modules.
8. Admin creates schools, centers, departments, units, and programs.
9. Admin configures academic calendars.
10. Admin configures admissions workflow.
11. Admin creates public website pages.
12. Admin creates staff/student accounts.
13. Public site, login, dashboards, admissions, academic pages, finance, and
    enabled modules all show the configured institution's identity.
14. No AIU data appears unless the admin intentionally loaded AIU demo content.

---

## 26. Final Recommendation

Do not start by changing every module at once. Start by making the configuration
contract strong and then force public website/runtime pages to consume it. After
that, split AIU demo data from generic bootstrap. Those three steps will reveal
the remaining hardcoded assumptions naturally and make later module cleanup much
safer.

The best first implementation target is:

1. Universal institution settings contract.
2. CMS/settings-driven public website.
3. Generic bootstrap plus AIU demo seed separation.
4. Static hardcode guard with test/demo allowlist.

Once these are in place, the remaining module-by-module changes can be completed
with far less risk.
