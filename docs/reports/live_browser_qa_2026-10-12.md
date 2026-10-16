# Live Chrome browser QA — 2026-10-12

## Diagnosis at a glance — 2026-10-14

The original Compose failure was the bind-mounted backend entrypoint lacking execute permission. PostgreSQL and Redis were healthy; the backend could not run its script and failed its health check. Restoring the executable bit fixed startup. A separate host port-3000 conflict was resolved through the local Compose override. Backend, frontend, Nginx, PostgreSQL, and Redis now report healthy.

One synthetic admin, two accounts for each of the eight admin-creatable roles, two applicants, four centre-scoped academic accounts, and three hostel students were created: **26 accounts total**. Real Chrome cross-role workflows passed for account creation, applicant drafts, registration, teaching content, assignments, quizzes, grading and published results, evaluations, attendance and corrections, helpdesk, venue booking, library, dining, elections, HR, hostel administration, CMS publication, audit logs, and report generation. The dated observations below specify the exact actions and evidence; route rendering alone is not counted as a full feature pass.

Confirmed defects fixed during the audit: helpdesk and evaluation form buttons that did not submit; individual-assignment validation and post-submit reset; mobile sidebar persistence and Semester Results overflow; hostel room over-capacity creation/capacity reduction; CMS local date/time conversion; and historical attendance times changing when the weekly meeting was edited. The backend entrypoint and local port conflict were also fixed.

Open findings: rapid anonymous requests can hit the shared 20/minute throttle, and a centre lookup's HTTP 429 becomes a misleading 404; the ordinary 346-test Django run had four 429 failures, although the affected classes passed 9/9 in isolation. The Next.js development server restarted near its memory threshold during broad navigation and briefly returned 502. Pending library requests are labeled as already allocated/on loan. The UI allowed final results publication before the synthetic semester start; whether that is permitted needs an academic policy decision. Hostel capacity validation counts existing residents but has not been tested under concurrent account creation.

The audit is **not complete**. The 193 role navigation URLs below are an inventory, not 193 verified workflows. Uploads/imports and document-dependent submissions are blocked by Chrome's file-URL permission; browser download completion was not observed even where generated XLSX files were validated in Docker. External payment checkout, backup restore, and other high-impact or unconfigured flows were not exercised. Remaining work is listed after the dated progress updates.

## Progress update — 2026-10-13

This audit is in progress. The inventory below is not a claim that all functionality passed.

- Docker startup fixed: restored executable mode on `backend/docker/entrypoint.sh` (100644 → 100755). The bind-mounted script previously failed with `permission denied`.
- Port conflict fixed: `docker-compose.override.yml` now publishes `${UMS_FRONTEND_PORT:-3001}:3000`, because another project owned port 3000. Main portal: `http://localhost:8080`.
- Created one admin `qa_admin_20261012`, then two accounts per admin-creatable role through real Chrome: `qa_<role>_<1|2>_20261012` for student, teacher, executive, librarian, caterer, technician, accountant, hr. Created two applicants through public registration with the same naming pattern. Four further centre-scoped executive, teacher, and student accounts were created for academic QA, followed by three hostel-scoped students. **26 new accounts total.** All use synthetic `example.test` emails; administrator email: `qa.admin.20261012@example.test`. Passwords intentionally excluded.
- School-scoped roles use DEMO-SCI; students use DEMO-BCOMP; executives use DEMO-SCI-ADMIN. Account credentials emails use the console backend, verified before creation.
- Chrome PASS: admin login and logout; successful account creation for all eight roles; both HR records displayed in Manage HR; password length validation; applicant registration, draft save with four programme choices, incomplete-submission rejection, draft timeline, own statistics, notifications empty state, profile details.
- Chrome defect FIXED: student helpdesk submit button was `type="button"`, so clicking did nothing. Added explicit `type="submit"` in `frontend/components/student/student-ict-helpdesk-page.tsx`; retest created **SD-00003**, subject `QA 20261012 Wi-Fi connection test`, with submitted progress history.
- Chrome PASS: book search empty result; book addition request `QA Browser Workflow Testing`; laptop borrowing request for CODEX-AUDIT-LAPTOP-001; duplicate borrowing request rejected; venue request `QA 20261012 workshop` for 2026-10-15 14:00–15:00 submitted for technician review; leave on 2026-10-20 submitted and automatically approved with the displayed reason that no approvers were required.
- Chrome PASS, cross-role: technician changed SD-00003 through In progress to Solved with visible progress history; student saw the final status and both notes. Technician approved the venue request; student saw Approved. Technician notification Mark all read updated 2 unread to 0; statistics reflected 2 solved of 3 tickets.
- Chrome PASS, library: librarian created `QA Browser Workflow Testing`, shelf `QA-SHELF-20261012`, copy `QA-COPY-20261012-1`, then marked the student's addition request Added. Student saw the reply and catalog link. Librarian created laptop `QA-LAPTOP-20261012-1` and room `QA-ROOM-20261012`; student 1 reserved the room, student 2 separately requested the laptop. Both requests were fulfilled by librarian 2; timed room allocation enforced the two-hour limit. Key and both laptop returns were confirmed; active allocation count returned to zero. A second laptop request while holding one was rejected by the server. Pending library requests are counted in the student UI as "on loan"/"allocated" before fulfilment; this is confusing copy, although limits were enforced.
- Chrome PASS, isolation: student 2 had no access to student 1's ticket, venue request, laptop loan, or room reservation in their own lists. Direct navigation to `/admin/dashboard` redirected student 2 to `/student/dashboard`.
- Chrome PASS, elections: technician 1 created active synthetic election `QA 20261012 Council Workflow`; technician 2 linked and approved both QA students as candidates. Student 1 and student 2 each submitted a distinct ballot; repeat submit controls became disabled and the live tally showed 2 votes, 1 per candidate. This synthetic ballot remains Active until its configured end and is visible to eligible students.
- The existing Demo Semester registration phase is closed; its Register controls correctly disabled. An independent active `QA Foundation Browser Semester 2026` was created in DEMO-FND so academic workflows could be tested without closing or altering the existing semester.
- Upload BLOCKER: Chrome extension lacks “Allow access to file URLs.” The file chooser opened, but setting a synthetic PNG failed. User was asked to enable permission. Uploads, imports and document-dependent submission remain blocked pending that action.
- Runtime finding: after navigating several previously uncompiled routes, Next.js reported “Server is approaching the used memory threshold, restarting...” and Chrome briefly showed 502. Container was not OOM-killed; the development server restarted and recovered.
- Supplemental verification: Django system check PASS; migration drift check PASS; frontend typecheck PASS and frontend lint PASS after the helpdesk and assignment fixes. Full Django run: **346 tests, 4 failures**, all anonymous public-content/media expectations receiving HTTP 429. Rerun of both affected classes: **9/9 PASS**. Shared Redis throttling/cache is not isolated by the ordinary test command; full-suite failure is not a clean pass and needs test isolation work.
- Live evidence is saved under `/tmp/ums-live-qa-evidence/`, including `browser-observations.json`, per-page DOM snapshots, `applicant-draft-status.jpg`, and `student-helpdesk-created.jpg`. Automated test output: `/tmp/ums-full-tests-20261013.log` and `/tmp/ums-targeted-tests-20261013.log`.

## Progress update — 2026-10-14

- Chrome PASS, academic setup: admin created programme `QA-FND-20261013`, active independent foundation semester, and centre-scoped executive, teacher, and two student accounts. The executive created catalog course `QA-FND101`, published section QA1 with capacity 2 and a Wednesday 09:00–10:30 timetable, and assigned the centre teacher. The teacher published `QA Course Outline` and `QA Welcome Announcement`.
- Chrome defect FIXED: individual assignment creation sent `group_rules: null` although the field is hidden in Individual mode, causing backend validation failure. The first successful request then displayed a false error because it called `event.currentTarget.reset()` after awaiting. `frontend/components/teacher/teacher-assignments-page.tsx` now sends an empty rules string and captures the form element before the request. Retest created the separate draft `QA Assignment Form Regression` with a success message and cleared form. The earlier published `QA Browser Reflection` was also visible on the teacher and enrolled student pages with its rubric.
- Chrome PASS, enrollment and capacity: both QA centre students registered for `QA-FND101` during pre-registration, each receiving Approved status and 3/21 credits. The section moved from 0/2 to 2/2 seats, leaving 0 remaining. Student 1's current course showed the teacher, outline, announcement, and assignment.
- Chrome PASS, assessment: each enrolled student submitted a separate text assignment attempt; second submissions were disabled as configured. Student 2 initially saw 0 submissions and no access to student 1's response. Teacher's queue showed two submissions and returned rubric-linked grades and distinct feedback: 10/10 for student 1, 8/10 for student 2. Student 1 answered the published `QA Browser Knowledge Check` correctly and received 1/1; student 2 answered incorrectly and received 0/1. Student 1's gradebook showed the quiz score.
- Chrome PASS, HR: QA HR user created position `QA-HR-POS-20261013` and a zero-salary synthetic employee record for their own profile; My HR Profile showed the linked record. Created synthetic onboarding card `QA Browser Staff Applicant`, moved it New applicant → In review → Getting started, and verified timestamped history. Employee linking remains untested because the card has no corresponding portal profile.
- Chrome PASS, finance controls: QA accountant signed in, searched for a synthetic student ledger, placed then released a temporary finance hold on QA Center Student 1; the active-hold count returned to zero. Fines and charges list rendered existing records. A PDF export endpoint returned HTTP 200 in the frontend log, but Chrome did not expose a completed download; file contents remain unverified. No payment or nonzero charge was submitted.
- Chrome PASS, final results: teacher gradebook calculated 100.00/A+ and 72.73/B+ from the two assignment and quiz scores, then copied both totals to an editable two-record result draft. Teacher submitted the synthetic batch; the center executive reviewed and approved it, then published it. Student 1 saw A+ and a 4.00 CGPA in Semester Results and Transcript; student 2 independently saw B+ and a 3.33 CGPA. The teacher's result form became read-only while under review. The UI allowed publication before this QA semester's scheduled start date; that timing rule should be reviewed against academic policy.
- Chrome PASS, dining: both caterer accounts signed in. Caterer 1 found QA Center Student 1's $50.00 monthly allowance and completed a $1.25 synthetic lunch deduction; balance became $48.75 and the transaction appeared in history. A $100.00 attempted deduction was rejected for insufficient funds without changing that balance. Caterer 2 found the same $48.75 balance and transaction. Caterer statistics showed $1.25 spent and one transaction. Student 2's own dining page still showed a separate $50.00 balance with no transactions. Student 1's post-purchase dining page was not rechecked in this pass.
- Chrome defects FIXED, evaluations: the executive launch button in `frontend/app/(executive)/executive/evaluations/page.tsx` and student submit button in `frontend/app/(student)/student/evaluations/[surveyId]/page.tsx` rendered as `type="button"` inside forms, leaving clicks inert. Both now use `type="submit"`. Chrome retest launched `QA Foundation Course Browser Evaluation` for `QA-FND101` with 34 required questions and two pending students. Student 1's empty submission focused the first required answer; after completing 31 scale and three written answers, submission succeeded, duplicate response entry became a view-only state, and the student's next-semester evaluation hold cleared. Student 2 independently had a pending requirement, then completed all 34 answers. Executive analytics showed 2 submitted, 0 pending, 100% completion, 62 scale answers, distinct response distributions, and both sets of written comments. The XLSX export click produced no completed Chrome download event, so exported file contents remain unverified.
- Chrome PASS, public page rendering: signed out, the home, about, admissions, programmes, scholarship, schools, centres, departments, units, directories, news, events, services, student life, contact, official links, UMS overview, apply landing, and applicant registration routes rendered. The home Apply and Start Application links reached the expected pages. A published news card and school card opened their detail pages. Several sections displayed empty published-content states; this sweep established page rendering and navigation only.
- Chrome finding, public throttling: after rapid anonymous navigation, the DEMO-FND centre card led to a branded 404. Backend logs showed HTTP 429 for its public centre lookup. The shared DRF anonymous limit is configured at 20 requests/minute; `getPublicCentre` catches the non-404 error and returns `null`, which the detail route converts to `notFound()`. After the throttle window, the same card opened `/centres/demo-foundation-center` and rendered the correct centre and QA Foundation programme. This is a misleading transient error state, not a missing centre. No rate-limit or public API behavior was changed in this pass.
- Chrome PASS, focused mobile layout: at 390 × 844, the public centre and About pages rendered without document-level horizontal overflow; the public mobile menu navigated from the centre detail to About and closed. Student 1 signed in at that width, opened the mobile sidebar, and reached Dining. Their own page confirmed the caterer's earlier $1.25 purchase and $48.75 balance. The sidebar initially stayed open over the destination after navigation. `frontend/components/sidebar/app-sidebar.tsx` now closes the mobile sheet when the route changes; retests of both a direct Dining link and nested Semester Results link ended with the sheet closed.
- Chrome defect FIXED, Semester Results mobile width: the long native semester option made its filter row 483px wide at a 390px viewport, clipping controls and causing page-level horizontal scrolling. `frontend/components/student/student-results-page.tsx` now stacks and constrains the filter on narrow screens. Chrome measured document width 390px at a 390px viewport after a fresh frontend bundle, and 1470px at the normal 1470px viewport. The results table and tab strip retain their local horizontal scrolling.
- Chrome PASS, public news CMS: QA admin created `QA Browser Public News 20261014` as Draft; the anonymous `/news` listing showed only the seeded published item. Admin edited the same synthetic record to Published, and its anonymous detail URL `/news/qa-browser-public-news-20261014` rendered the title, summary, body, and publication date. The listing initially remained stale during its 300-second revalidation window; a later Chrome recheck showed the new card, and clicking it opened the correct detail page. The synthetic published item remains in the local demo database.
- Chrome PASS, audit and report generation: admin Audit Log showed the synthetic news create/update entries with the QA administrator as actor; searching `public content news` returned those two entries, and Reset restored 46 entries. People Reports exported a Students XLSX filtered by `QA Center Student 1`; Export History showed Completed with one row. Academic Reports exported Course Offerings filtered by `QA-FND101`, also Completed with one row. Operations Reports exported Canteen Transactions filtered by that student, Completed with the one synthetic lunch row. Direct read-only inspection of all three stored XLSX files in Docker verified valid ZIP workbooks with their respective single QA data rows; the earlier course evaluation export was also valid with two data rows and 39 columns. Chrome's download event did not fire for export buttons or Export History Download, so saving the file through Chrome itself remains unverified.
- Chrome PASS, report notifications: the two export-completed notifications appeared for the QA admin. Mark all read changed the page from 2 unread to 0, and Refresh retained that state. The global header badge initially lagged but later updated to 0 on its periodic refresh.
- Chrome PASS, hostel administration and student information: admin created synthetic residence `QA-HOSTEL-20261014`, room `QA-HOSTEL-20261014-1-01` initially with capacity 2, emergency contact `QA Residence Desk`, and a Wednesday 09:00–10:00 warden schedule. A centre student saw the contact and warden details on the two Student Affairs pages. Admin created `qa_hostel_student_1_20261014` with that room; the hostel occupancy changed from 0/2 to 1/2 and listed the student. The new student signed in and opened Profile successfully. Profile has no room field; a resident-facing room page remains untested.
- Chrome defect FIXED, hostel capacity: a second QA resident filled the room to 2/2, but creation of a third succeeded and admin showed 3/2 occupied. `backend/auth_app/serializers.py` now rejects student assignments to a full managed room, including room-section suffixes; `backend/admin_app/serializers.py` also rejects reducing capacity below the number of current residents. Chrome confirmed the capacity-edit error, then raised this synthetic room to a valid 3/3. A fourth account attempt returned `Hostel room QA-HOSTEL-20261014-1-01 is full`; read-only database verification confirmed that fourth account does not exist and occupancy remains 3/3. The focused account-creation class passed 7/7 tests.
- Chrome PASS, public events: admin created `QA Browser Public Event 20261014` as Draft, edited it to Published for October 20, 14:00–15:00 at QA Browser Residence, and saw it in the admin list. Its public detail page rendered immediately; after the public cache revalidated, the Events listing showed the card and clicking it opened the correct detail. The event remains published in the local demo database.
- Chrome defect FIXED, CMS date/time: the public-content editor treated `datetime-local` input as UTC, so its default clock was eight hours behind Malaysia local time and an entered event time represented the wrong instant. `frontend/components/admin/admin-public-content-page.tsx` now displays API timestamps in browser local time and submits timezone-aware ISO timestamps for page/news publication, events, and announcements. Chrome showed the corrected local default and round-tripped the event at 14:00–15:00; Django stores the matching 06:00–07:00 UTC. Direct Chrome automation `fill()` did not fire React's change handling for native date fields, so the retest used a native keyboard change before save.
- Chrome PASS, announcements and official links: admin created a public announcement as Draft, then published and pinned it. After cache revalidation, `/news` showed its title and body alongside the published news cards. Admin created a synthetic official link inactive, activated it, and later saw it on `/official-links` and in the public footer. The link was deactivated after that check because its `example.test` destination is intentionally non-resolving. A later anonymous Chrome visit showed the official-links empty state and no QA link in the footer, confirming removal after cache refresh. Evidence: `public-official-link-deactivated.jpg`.
- Chrome PASS, attendance: the centre executive temporarily moved only the synthetic QA-FND101 meeting to Wednesday 14:00–16:00, when the backend clock was inside that window. The teacher's Open QR control became available and opened a session with a rotating 60-second code. QA Center Student 1 submitted the displayed code successfully; a repeat attempt returned "Attendance already submitted." Their report showed 1/1 and 100%, while the teacher's roster showed Student 1 at 1/1 and Student 2 at 0/1. The teacher closed the session, and the executive restored the original Wednesday 09:00–10:30 meeting, confirmed in the offering list. QR scanning and expired/wrong-course code rejection remain untested. Evidence: `teacher-attendance-open.jpg`, `student-attendance-submitted.jpg`, `student-attendance-report.jpg`, and `teacher-attendance-closed.jpg`.
- Chrome PASS, attendance correction: the teacher marked synthetic Student 2 "Absent with reason" on the closed QA-FND101 session. The correction saved, and Student 2's own report showed 0/1, the status, and the entered note. Medical-certificate upload and other correction statuses remain untested. Evidence: `teacher-attendance-correction.jpg`.
- Chrome PASS, invalid attendance code: Student 2 entered a random six-character code and a previously displayed code from the now closed session. Both returned "Attendance code is invalid or has already been replaced" without a new attendance record. This does not separately prove expiry timing or wrong-course enrollment behavior. Evidence: `student-attendance-invalid-code.jpg`.
- Chrome defect FIXED, attendance history: after the executive restored the weekly meeting to 09:00, Student 2's history incorrectly relabelled the already held 14:00 session as 09:00. `backend/teacher_app/attendance_service.py` now uses the session's captured actual start/end values for report and session payloads; the student code lookup and teacher QR/course history display those values. A regression test changes the meeting after opening a session and checks that history retains its original time. Chrome retest showed 14:00 in both Student 2's report and the teacher's course attendance history after the schedule restoration. Evidence: `student-attendance-history-time-fixed.jpg`, `teacher-attendance-history-time-fixed.jpg`.
- Graphify refresh after the frontend code changes completed. Frontend typecheck and lint both passed, including after the CMS date/time fix. Chrome evidence now includes registration, assignment submission, quiz results, teacher grades, HR onboarding, result publication, student transcripts, caterer checkout, evaluation submission and analytics, CMS publication, and form-fix screenshots under `/tmp/ums-live-qa-evidence/`.

Remaining: more accountant, executive, admin, and public CMS actions; QR scan, attendance expiry/wrong-course cases and medical-certificate correction; evaluation control changes; same-role isolation beyond tested records; responsive checks; upload-dependent tests; Chrome file downloads; resident-facing room workflows; additional dining allocation/adjustment controls; and public 429 error handling. Preserve all existing user changes and test records.

## Audit context

- Environment: local university management portal, Docker runtime, real Chrome linked to Codex.
- Requested scope: bootstrap one admin, create multiple accounts for each available role through supported user flows, and exercise website functionality.
- Parent-reported setup: Docker backend is healthy; bootstrap administrator `qa.admin.20261012@example.test` exists. These are setup notes, not browser test passes.
- Coverage inventory: 193 unique role navigation URLs, plus shared/public routes and detail workflows. Parent/alias navigation URLs are retained; dynamic detail URLs are covered by workflow checks below.
- Inventory source: `frontend/lib/ums-roles.ts`, checked against account creation and ownership validators. Actual visible navigation depends on module settings and executive scope.
- Checklist status: entries below were initially inventoried as untested and remain unmarked until each full item is annotated with per-action evidence. The dated progress updates above record observed passes and limits. A rendered page alone does not establish that its mutations, validation, permissions, downloads, or cross-role workflow pass.

## Result recording

Replace `[ ]` only after observed verification. Append `PASS`, `FAIL`, `BLOCKED`, or `SKIPPED` with a short observation, account, and evidence reference; retain unexplored subflows explicitly as untested. Record defects and retests in the observation log. Do not put passwords, access tokens, or real personal data in this report.

| Status | Meaning |
| --- | --- |
| UNTESTED | No live browser evidence recorded |
| PASS | Specified action and resulting state verified in Chrome |
| FAIL | Reproducible behavior disagrees with expected workflow |
| BLOCKED | Prerequisite or external dependency prevents exercising the action |
| SKIPPED | Explicitly omitted, with reason recorded |

## Account and data prerequisites — UNTESTED

- [ ] Sign in to the bootstrap admin and verify admin dashboard and session behavior.
- [ ] Prepare two distinct synthetic accounts for each admin-creatable role: student, teacher, executive, librarian, caterer, technician, accountant, HR. Record identifiers and ownership scopes without passwords.
- [ ] Create two applicant accounts through `/apply/register`; applicant creation is not offered by the admin Create Account UI.
- [ ] Confirm credentials email delivery uses the intended local/test backend before account submissions; account creation refuses to save when credential delivery fails.
- [ ] Create or select active schools/centres, departments, units, and programmes needed by test profiles.
- [ ] Student: exactly one school/centre; programme belongs to the same scope where selected.
- [ ] Teacher: one or more school/centre assignments; use a second teacher/scope to check isolation.
- [ ] Executive: unit with exactly one school/centre parent; include academic scope for academic workflows.
- [ ] Librarian/caterer: selected school/centre/unit owner or configured role default; technician may also use a department owner.
- [ ] Accountant/HR: create supported profiles and verify access without requiring an academic owner.
- [ ] Applicant: unique username/email/identity, names, phone, nationality, residence, password confirmation.
- [ ] Academic workflow: active semester, open registration/offering dates, programme/course, course offering, assigned teacher, capacity, timetable/venue, grade scale.
- [ ] Operational workflow: book/laptop/room stock, canteen allocation, helpdesk configuration, venue approval route, election dates/candidates, finance plans, HR position.
- [ ] Document enabled/disabled modules and available external integrations before interpreting unavailable pages.

## Coverage totals

| Role | Unique navigation URLs |
| --- | ---: |
| admin | 49 |
| applicant | 6 |
| student | 42 |
| teacher | 28 |
| executive | 24 |
| librarian | 9 |
| caterer | 4 |
| technician | 9 |
| accountant | 14 |
| hr | 8 |
| **Total** | **193** |

## Shared session, UI, and permissions — UNTESTED

- [ ] `/login`: valid/invalid credentials, username/email handling, role destination, validation, server error feedback.
- [ ] `/apply/login` and `/apply/register`: applicant authentication, duplicate identity/email, invalid/mismatched passwords, dashboard redirect.
- [ ] `/forgot-password` and the resulting reset link: form feedback and usable password change through the intended test email channel.
- [ ] `/profile`: profile display/edit, image upload validation, change password, persistence after refresh.
- [ ] Logout, reload, unauthenticated protected-route access, session expiry/refresh, and browser Back behavior.
- [ ] Cross-role denial and same-role record isolation using the second synthetic account; restricted actions and direct detail URLs.
- [ ] Sidebar groups, breadcrumbs, header/profile menu, empty states, loading/error states, and visible module guards.
- [ ] Desktop and narrow/mobile layouts: labels, controls, tables, dialogs, menus, keyboard focus, horizontal overflow.
- [ ] Lists: search/filter/sort/pagination, details, reset controls, persistence after permitted create/edit/delete actions.
- [ ] Notifications: creation from workflow, recipient isolation, read state, links, and count updates.
- [ ] Reports/downloads/uploads: file contents, expected format, permission checks, validation, and failed operation feedback.

## Public website — UNTESTED

Confirm each route is enabled/configured, then verify page rendering and relevant links/detail pages. Public content is data-driven; empty or disabled states require separate observations.

- [ ] `/` — UNTESTED
- [ ] `/about` — UNTESTED
- [ ] `/admissions` — UNTESTED
- [ ] `/scholarship` — UNTESTED
- [ ] `/schools` — UNTESTED
- [ ] `/centres` — UNTESTED
- [ ] `/programmes` — UNTESTED
- [ ] `/departments` — UNTESTED
- [ ] `/units` — UNTESTED
- [ ] `/directories` — UNTESTED
- [ ] `/news` — UNTESTED
- [ ] `/events` — UNTESTED
- [ ] `/services` — UNTESTED
- [ ] `/student-life` — UNTESTED
- [ ] `/contact` — UNTESTED
- [ ] `/official-links` — UNTESTED
- [ ] `/ums-overview` — UNTESTED
- [ ] `/apply` — UNTESTED
- [ ] Configured CMS navigation/pages and dynamic public detail links — UNTESTED
- [ ] Public search/filter controls, application links, contact/resource links, media, and responsive navigation — UNTESTED

## Cross-role functional workflows — UNTESTED

- [ ] Admin: single account creation, CSV/XLSX import and error rows, duplicate/invalid input, people edit/status, scope management.
- [ ] Administration: school/centre/department/unit/programme, semester/date rules, grading criteria, venue/building, hostel/room/resident/warden workflows.
- [ ] Setup/settings: wizard steps, identity/terminology/localization/module options, role ownership, saved settings reflected in their consuming pages.
- [ ] CMS: news/event/announcement/official link create/edit/visibility, public rendering, notification targeting.
- [ ] Reports/audit: filtered export, export history, privileged action entries, authorized backup download. Restore needs a safe test data boundary before execution; do not replace existing user data merely to mark this item complete.
- [ ] Applicant → admin: application draft/validation/programme/intake, six sections, scholarship, files, statement of truth, submission, staff review, decision/status visibility.
- [ ] Executive → teacher/student: course catalog/prerequisites/offering, teacher/group assignment, calendar/timetable/exam schedule, publication visibility.
- [ ] Student registration: eligibility/capacity/date/credit/prerequisite validation, register/drop/group change, duplicate registration, history.
- [ ] Teacher content → student: content visibility/download, assigned offering isolation, announcements, assignment create/edit/submission/late rule/feedback.
- [ ] Teacher attendance → student: session create/open/close, code/QR entry, duplicate/expired/wrong-course validation, corrections, reports.
- [ ] Teacher quiz → student: question bank, quiz setup/publication, attempt/submission/deadline, marking and visibility.
- [ ] Gradebook/results: teacher drafts/release/submission, executive review/rejection/publication, student current work/semester results/transcript/exam slip.
- [ ] Student evaluation → executive: submission, duplicate constraints, reporting, result access policy where configured.
- [ ] Student leave → approver: submit/cancel, routing/decision, comments, history and affected calendar state.
- [ ] Student venue request → technician/admin: availability/conflict, approval/rejection/cancellation, requester visibility.
- [ ] Student helpdesk → technician: ticket create/attachment/category, assignment/status/response, requester visibility and notifications.
- [ ] Librarian → student: catalog/inventory, book/laptop/room request, approval/issue/return/cancel, availability/conflict/due-state behavior.
- [ ] Accountant → caterer/student: allocation/adjustment/compensation, purchase validation/receipt, balance and transaction visibility.
- [ ] Finance: subscription plan/record/card, checkout/manual test payment where configured, fines/charges/waivers, holds, bulk charge, ledger/payment plan.
- [ ] Technician → student: election setup, candidate application/approval, voting eligibility/one-vote rule, results visibility.
- [ ] HR: positions, employee lifecycle/profile changes, onboarding board/tasks, own HR profile and permission boundaries.
- [ ] Shared calendar/statistics/notifications reflect the synthetic records created in their source workflows.

## Role navigation checklist — UNTESTED

Each entry initially means only that its URL is inventoried. Record page-load and functional verification separately when their scope differs.

### Admin — 49 URLs

- [ ] `/admin/dashboard` — Dashboard — UNTESTED
- [ ] `/admin/statistics` — Statistics — UNTESTED
- [ ] `/admin/create-account` — Create Account — UNTESTED
- [ ] `/admin/create-account/student` — Create Student — UNTESTED
- [ ] `/admin/create-account/teacher` — Create Teacher — UNTESTED
- [ ] `/admin/create-account/executive` — Create Executive — UNTESTED
- [ ] `/admin/create-account/librarian` — Create Librarian — UNTESTED
- [ ] `/admin/create-account/caterer` — Create Caterer — UNTESTED
- [ ] `/admin/create-account/technician` — Create Technician — UNTESTED
- [ ] `/admin/create-account/accountant` — Create Accountant — UNTESTED
- [ ] `/admin/create-account/hr` — Create HR — UNTESTED
- [ ] `/admin/manage` — Manage — UNTESTED
- [ ] `/admin/manage/applicants` — Manage Applicants — UNTESTED
- [ ] `/admin/manage/students` — Manage Students — UNTESTED
- [ ] `/admin/manage/teachers` — Manage Teachers — UNTESTED
- [ ] `/admin/manage/executives` — Manage Executives — UNTESTED
- [ ] `/admin/manage/librarians` — Manage Librarians — UNTESTED
- [ ] `/admin/manage/caterers` — Manage Caterers — UNTESTED
- [ ] `/admin/manage/technicians` — Manage Technicians — UNTESTED
- [ ] `/admin/manage/accountants` — Manage Accountants — UNTESTED
- [ ] `/admin/manage/hr` — Manage HR — UNTESTED
- [ ] `/admin/academics` — Academic Structure — UNTESTED
- [ ] `/admin/schools` — Schools — UNTESTED
- [ ] `/admin/centres` — Centres — UNTESTED
- [ ] `/admin/academics/departments` — Departments — UNTESTED
- [ ] `/admin/academics/units` — Units — UNTESTED
- [ ] `/admin/academics/programmes` — Programmes — UNTESTED
- [ ] `/admin/semesters` — Semesters — UNTESTED
- [ ] `/admin/gradebook` — Gradebook Criteria — UNTESTED
- [ ] `/admin/venues` — Venues — UNTESTED
- [ ] `/admin/venue-bookings` — Venue Requests — UNTESTED
- [ ] `/admin/hostels` — Hostels — UNTESTED
- [ ] `/admin/public-content` — Public Content — UNTESTED
- [ ] `/admin/public-content/news` — News — UNTESTED
- [ ] `/admin/public-content/events` — Events — UNTESTED
- [ ] `/admin/public-content/announcements` — Announcements — UNTESTED
- [ ] `/admin/public-content/official-links` — Official Links — UNTESTED
- [ ] `/admin/reports` — Reports — UNTESTED
- [ ] `/admin/reports/people` — People — UNTESTED
- [ ] `/admin/reports/academic` — Academic — UNTESTED
- [ ] `/admin/reports/operations` — Operations — UNTESTED
- [ ] `/admin/reports/exports` — Export History — UNTESTED
- [ ] `/admin/subscriptions` — Subscriptions — UNTESTED
- [ ] `/admin/ui-customization` — UI Customization — UNTESTED
- [ ] `/admin/setup-wizard` — Setup Wizard — UNTESTED
- [ ] `/admin/settings` — Settings — UNTESTED
- [ ] `/admin/backup-restore` — Backup and Restore — UNTESTED
- [ ] `/admin/audit-log` — Audit Log — UNTESTED
- [ ] `/admin/notifications` — Notifications — UNTESTED

### Applicant — 6 URLs

- [ ] `/apply/dashboard` — Dashboard — UNTESTED
- [ ] `/apply/statistics` — Statistics — UNTESTED
- [ ] `/apply/application` — Application Form — UNTESTED
- [ ] `/apply/documents` — Documents — UNTESTED
- [ ] `/apply/status` — Status — UNTESTED
- [ ] `/apply/notifications` — Notifications — UNTESTED

### Student — 42 URLs

- [ ] `/student/dashboard` — Dashboard — UNTESTED
- [ ] `/student/statistics` — Statistics — UNTESTED
- [ ] `/student/courses` — Courses — UNTESTED
- [ ] `/student/courses/register` — Course Registration — UNTESTED
- [ ] `/student/courses/current` — Current Courses — UNTESTED
- [ ] `/student/courses/completed` — Completed Courses — UNTESTED
- [ ] `/student/evaluations` — Course Evaluations — UNTESTED
- [ ] `/student/timetable` — Schedule — UNTESTED
- [ ] `/student/timetable/today` — Today's schedule — UNTESTED
- [ ] `/student/timetable/weekly` — Weekly schedule — UNTESTED
- [ ] `/student/calendar` — Calendar — UNTESTED
- [ ] `/student/venue-bookings` — Venue Bookings — UNTESTED
- [ ] `/student/ict-helpdesk` — Service Desk — UNTESTED
- [ ] `/student/attendance` — Attendance — UNTESTED
- [ ] `/student/attendance/code` — Code Entry — UNTESTED
- [ ] `/student/attendance/report` — Attendance Report — UNTESTED
- [ ] `/student/attendance/qr` — QR Attendance — UNTESTED
- [ ] `/student/assignments` — Assignments — UNTESTED
- [ ] `/student/quizzes` — Quizzes — UNTESTED
- [ ] `/student/gradebook` — Gradebook — UNTESTED
- [ ] `/student/registration` — Registration — UNTESTED
- [ ] `/student/registration/offered-courses` — Offered Courses — UNTESTED
- [ ] `/student/registration/requests` — My Registrations — UNTESTED
- [ ] `/student/registration/history` — History — UNTESTED
- [ ] `/student/results` — Results — UNTESTED
- [ ] `/student/results/semester` — Semester Results — UNTESTED
- [ ] `/student/results/transcript` — Transcript — UNTESTED
- [ ] `/student/results/course-works` — Course Works — UNTESTED
- [ ] `/student/results/exam-slip` — Exam Slip — UNTESTED
- [ ] `/student/leave` — Leave — UNTESTED
- [ ] `/student/leave/apply` — Apply Leave — UNTESTED
- [ ] `/student/leave/history` — Leave History — UNTESTED
- [ ] `/student/emergency-contacts` — Student Affairs — UNTESTED
- [ ] `/student/warden-schedule` — Warden Schedule — UNTESTED
- [ ] `/student/canteen` — Canteen — UNTESTED
- [ ] `/student/subscriptions` — Subscriptions — UNTESTED
- [ ] `/student/fines` — Fines & Charges — UNTESTED
- [ ] `/student/library/books` — Library — UNTESTED
- [ ] `/student/library/laptops` — Laptops — UNTESTED
- [ ] `/student/library/rooms` — Discussion Rooms — UNTESTED
- [ ] `/student/elections` — Elections — UNTESTED
- [ ] `/student/notifications` — Notifications — UNTESTED

### Teacher — 28 URLs

- [ ] `/teacher/dashboard` — Dashboard — UNTESTED
- [ ] `/teacher/statistics` — Statistics — UNTESTED
- [ ] `/teacher/courses` — Courses — UNTESTED
- [ ] `/teacher/courses/current` — Current Courses — UNTESTED
- [ ] `/teacher/courses/previous` — Previous Courses — UNTESTED
- [ ] `/teacher/timetable` — Schedule — UNTESTED
- [ ] `/teacher/timetable/today` — Today's schedule — UNTESTED
- [ ] `/teacher/timetable/weekly` — Weekly schedule — UNTESTED
- [ ] `/teacher/calendar` — Calendar — UNTESTED
- [ ] `/teacher/venue-bookings` — Venue Bookings — UNTESTED
- [ ] `/teacher/attendance` — Attendance — UNTESTED
- [ ] `/teacher/attendance/sessions` — Sessions — UNTESTED
- [ ] `/teacher/attendance/create` — Create Session — UNTESTED
- [ ] `/teacher/attendance/corrections` — Corrections — UNTESTED
- [ ] `/teacher/assignments` — Assignments — UNTESTED
- [ ] `/teacher/assignments/create` — Create Assignment — UNTESTED
- [ ] `/teacher/assignments/submissions` — Submissions — UNTESTED
- [ ] `/teacher/assignments/feedback` — Feedback Queue — UNTESTED
- [ ] `/teacher/quizzes` — Quizzes — UNTESTED
- [ ] `/teacher/quizzes/question-bank` — Question Bank — UNTESTED
- [ ] `/teacher/gradebook` — Gradebook — UNTESTED
- [ ] `/teacher/results` — Results — UNTESTED
- [ ] `/teacher/results/draft` — Draft Results — UNTESTED
- [ ] `/teacher/results/submit` — Result Submission — UNTESTED
- [ ] `/teacher/results/completed` — Completed Results — UNTESTED
- [ ] `/teacher/leave-requests` — Leave Requests — UNTESTED
- [ ] `/teacher/subscriptions` — Subscriptions — UNTESTED
- [ ] `/teacher/notifications` — Notifications — UNTESTED

### Executive — 24 URLs

- [ ] `/executive/dashboard` — Dashboard — UNTESTED
- [ ] `/executive/statistics` — Statistics — UNTESTED
- [ ] `/executive/reports` — Reports — UNTESTED
- [ ] `/executive/manage` — Manage — UNTESTED
- [ ] `/executive/manage/students` — Manage Students — UNTESTED
- [ ] `/executive/manage/teachers` — Manage Teachers — UNTESTED
- [ ] `/executive/manage/schedule` — Schedule — UNTESTED
- [ ] `/executive/organization` — Organisation — UNTESTED
- [ ] `/executive/programs` — Programmes — UNTESTED
- [ ] `/executive/audit-log` — Audit Log — UNTESTED
- [ ] `/executive/results` — Results — UNTESTED
- [ ] `/executive/results/semester` — Semester Results — UNTESTED
- [ ] `/executive/results/previous` — Previous Results — UNTESTED
- [ ] `/executive/results/review` — Review Results — UNTESTED
- [ ] `/executive/results/publication` — Publication — UNTESTED
- [ ] `/executive/courses` — Courses — UNTESTED
- [ ] `/executive/courses/offered` — Offered Courses — UNTESTED
- [ ] `/executive/courses/offer` — Offer Courses — UNTESTED
- [ ] `/executive/courses/add` — Add Courses — UNTESTED
- [ ] `/executive/courses/all` — All Courses — UNTESTED
- [ ] `/executive/evaluations` — Course Evaluations — UNTESTED
- [ ] `/executive/calendar` — Calendar — UNTESTED
- [ ] `/executive/subscriptions` — Subscriptions — UNTESTED
- [ ] `/executive/notifications` — Notifications — UNTESTED

### Librarian — 9 URLs

- [ ] `/librarian/dashboard` — Dashboard — UNTESTED
- [ ] `/librarian/statistics` — Statistics — UNTESTED
- [ ] `/librarian/books` — Books — UNTESTED
- [ ] `/librarian/laptops` — Laptops — UNTESTED
- [ ] `/librarian/rooms` — Discussion Rooms — UNTESTED
- [ ] `/librarian/circulation` — Circulation — UNTESTED
- [ ] `/librarian/settings` — Settings — UNTESTED
- [ ] `/librarian/subscriptions` — Subscriptions — UNTESTED
- [ ] `/librarian/notifications` — Notifications — UNTESTED

### Caterer — 4 URLs

- [ ] `/caterer/dashboard` — Dashboard — UNTESTED
- [ ] `/caterer/statistics` — Statistics — UNTESTED
- [ ] `/caterer/subscriptions` — Subscriptions — UNTESTED
- [ ] `/caterer/notifications` — Notifications — UNTESTED

### Technician — 9 URLs

- [ ] `/technician/dashboard` — Dashboard — UNTESTED
- [ ] `/technician/statistics` — Statistics — UNTESTED
- [ ] `/technician/venue-bookings` — Venue Booking Requests — UNTESTED
- [ ] `/technician/elections` — Elections — UNTESTED
- [ ] `/technician/elections/candidates` — Candidates — UNTESTED
- [ ] `/technician/elections/results` — Election Results — UNTESTED
- [ ] `/technician/subscriptions` — Subscriptions — UNTESTED
- [ ] `/technician/helpdesk` — Helpdesk — UNTESTED
- [ ] `/technician/notifications` — Notifications — UNTESTED

### Accountant — 14 URLs

- [ ] `/accountant/dashboard` — Dashboard — UNTESTED
- [ ] `/accountant/statistics` — Statistics — UNTESTED
- [ ] `/accountant/canteen` — Canteen Allowance — UNTESTED
- [ ] `/accountant/compensation-requests` — Compensation Requests — UNTESTED
- [ ] `/accountant/gateway` — Gateway Settings — UNTESTED
- [ ] `/accountant/plans` — Manage Subscriptions — UNTESTED
- [ ] `/accountant/subscriptions` — Subscription Records — UNTESTED
- [ ] `/accountant/ledger` — Student Ledgers — UNTESTED
- [ ] `/accountant/ledger/fines` — Fines & Charges — UNTESTED
- [ ] `/accountant/ledger/holds` — Finance Holds — UNTESTED
- [ ] `/accountant/ledger/bulk-charge` — Bulk Charge — UNTESTED
- [ ] `/accountant/ledger/payment-plans` — Payment Plans — UNTESTED
- [ ] `/accountant/my-subscriptions` — Subscriptions — UNTESTED
- [ ] `/accountant/notifications` — Notifications — UNTESTED

### Hr — 8 URLs

- [ ] `/hr/dashboard` — Dashboard — UNTESTED
- [ ] `/hr/statistics` — Statistics — UNTESTED
- [ ] `/hr/employees` — Employees — UNTESTED
- [ ] `/hr/onboarding` — Staff Onboarding — UNTESTED
- [ ] `/hr/positions` — Positions — UNTESTED
- [ ] `/hr/my-profile` — My HR Profile — UNTESTED
- [ ] `/hr/subscriptions` — Subscriptions — UNTESTED
- [ ] `/hr/notifications` — Notifications — UNTESTED

## Observation and defect log

This table was part of the initial inventory. Browser observations and retests are recorded in the dated progress updates above; unmarked checklist items below those updates do not override their findings.

| ID | Area / URL | Account / scope | Action and expected outcome | Observed result / evidence | Status / retest |
| --- | --- | --- | --- | --- | --- |

## Supplemental automated verification

The initial inventory task executed no checks. Subsequent Docker and Chrome verification is recorded in the dated progress updates above. Automated checks supplement browser evidence and are not labeled as live Chrome tests. Existing frontend scripts are `typecheck`, `lint`, and `build`; no dedicated browser/e2e suite was found in the project inventory.

Useful targeted suites: `admin_app.test_route_permissions`, `applicant_app.tests.PortalRoleAccessTests`, `student_app.tests.CourseRegistrationRuleTests`, `teacher_app.test_learning_management_portal`, `executive_app.test_results_workflow`, and operational app workflow tests.

## Inventory sources and limits

- `frontend/lib/ums-roles.ts`: role/navigation contract, 193 distinct URLs after deduplicating within each role.
- `frontend/components/sidebar/app-sidebar.tsx`: module visibility and executive scope filtering.
- `frontend/components/admin/admin-create-account-page.tsx` and `backend/admin_app/views/admin_create_account.py`: eight admin-creatable roles, single/import flow, credentials email prerequisite.
- `backend/auth_app/serializers.py` and `backend/admin_app/role_config.py`: profile/ownership prerequisites.
- `backend/admin_app/management/commands/bootstrap_university.py`: generic bootstrap and admin synchronization.
- `frontend/app/apply/register/page.tsx` and `backend/applicant_app/serializers.py`: separate applicant registration and required fields.
- Public page coverage was identified through Graphify; configurable CMS/detail routes are not exhaustively enumerable from the static role map.
- The student QR attendance URL routes to code entry with optional initial code; its navigation description's placeholder wording is not proof of missing implementation.
- No pass claims, code fixes, external payment execution, destructive restore, or browser actions are established by this inventory alone.
