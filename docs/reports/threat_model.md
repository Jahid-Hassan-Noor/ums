# AIU Portal Repository Threat Model

## Overview

This repository implements the AIU Portal, a full-stack university portal with a Django / Django REST Framework backend and a Next.js / React frontend. The deployed product surface is split between a JWT-authenticated DRF API under `backend/` and role-specific frontend routes under `frontend/`. The backend exposes authentication endpoints in `backend/core/urls.py`, role modules for admin, student, teacher, executive, applicant, caterer, librarian, technician, accountant, notifications, chatbot, and unauthenticated public-site content endpoints. The frontend stores and refreshes sessions in `frontend/lib/auth.ts` and uses `frontend/proxy.ts` to protect role route trees by revalidating the access token against `/auth/me`.

The system handles sensitive university data and workflows: identities, role assignments, academic structures, applicant records, uploaded admissions documents, student registrations, attendance, results, assignments, leave requests, elections, venue bookings, hostel data, canteen balances, library circulation, ICT helpdesk tickets, public website content, notifications, exports, administrative audit logs, quizzes, question banks, gradebooks, quiz attempts, chatbot interactions, finance subscriptions, payment transactions, fines, and subscription cards. The primary security objective is to prevent one actor from reading or changing another actor's records or privileged workflows unless the backend has explicitly authorized that role and object relationship.

Important runtime controls already visible at repository scope include Django's authentication middleware, DRF JWT authentication, a default `admin_app.permissions.IsActivePortalUser` permission in `backend/core/settings.py`, a portal policy middleware, an audit action middleware, short-lived access tokens, role-aware frontend routing, and separate URL modules for public, applicant, student, teacher, executive, admin, caterer, librarian, technician, accountant, chatbot, and notification APIs. These controls are useful but must not be treated as sufficient without endpoint-level object authorization, because frontend route checks and client-side storage are not trust boundaries.

## Threat Model, Trust Boundaries, and Assumptions

Trust boundaries:

- Public internet or campus clients to the Next.js frontend and public DRF endpoints. Public pages, admissions options, login, password reset, applicant registration/login, news/events, contact, public content, and static/media resources may be reached by unauthenticated users.
- Browser to backend API. Any request body, path parameter, query parameter, file upload, cookie, localStorage value, and JWT presented by the browser is attacker-controlled until validated server-side.
- Frontend route proxy to backend authorization. `frontend/proxy.ts` can improve navigation and session refresh behavior, but backend API views must enforce role, active-account, and object-level access independently.
- JWT verification boundary. Access and refresh tokens signed with `SECRET_KEY` grant API access. Production secrecy and rotation of `DJANGO_SECRET_KEY` matter because the SimpleJWT signing key is the Django secret key.
- Role boundary. Admin, executive, teacher, student, applicant, caterer, librarian, technician, accountant, and public users have materially different capabilities. Role-specific endpoints under `backend/*_app/urls.py` must prevent confused deputy access and horizontal access between users of the same role.
- Object ownership boundary. Student records, applicant applications, uploaded documents, assignment submissions, leave requests, attendance records, helpdesk tickets, venue bookings, library loans, canteen accounts, notifications, quiz attempts, question bank content, gradebook grades, finance records, payment transactions, and chatbot queries must be scoped to the authenticated user's profile or authorized administrative scope.
- Staff delegation boundary. Executive users can have a school/center/unit scope; staff applicant review endpoints and executive academic workflows must enforce that scope server-side.
- File and media boundary. Applicant documents, profile pictures, quiz attachments, chatbot uploaded files, and media URLs are displayed through API/base URL composition. User-controlled file names, image URLs, or file uploads must not create XSS, mixed-content, SSRF-like fetches, or open redirect behavior.
- Operator/developer boundary. Environment variables, Docker configuration, Celery/Redis, PostgreSQL credentials, email settings, and deployment settings are operator-controlled inputs. Source code, migrations, and fixtures are developer-controlled.
- Background task boundary. Celery jobs process reminders, canteen allowances, quiz grading, overdue fines, search indexing, and chatbot vector updates. Task names and task inputs must be treated as privileged internal control data, not user-selected execution.
- Public content boundary. Admin-managed public content may be rendered to unauthenticated visitors; stored HTML, links, slugs, and media references require XSS and content integrity consideration.
- AI/Chatbot boundary. Chatbot queries, vector search, and LLM interactions process user input and may expose sensitive data if not properly scoped to tenant and user permissions.

Attacker-controlled inputs include login credentials, password reset identifiers, registration data, uploaded files, applicant application JSON fields, public query strings, pagination/search/export filters, course/assignment/attendance IDs, voting and registration choices, booking request data, helpdesk ticket content, notification read IDs, quiz responses, question bank content, gradebook scores, payment webhook data, chatbot queries, and all role-specific API path parameters. Operator-controlled inputs include allowed hosts, CORS origins, frontend/backend base URLs, email backend settings, database settings, Celery broker URLs, token lifetimes, LLM provider settings, and payment gateway credentials. Developer-controlled inputs include code, migrations, test fixtures, static assets, and build configuration.

Assumptions for severity calibration:

- The repository is intended to run as a networked web application, not as a purely local tool.
- The backend API is the authoritative security boundary; frontend role routing and localStorage/cookies are defense-in-depth only.
- A malicious authenticated low-privilege user is in scope, including students, applicants, teachers, caterers, librarians, technicians, accountants, and executives with limited academic scope.
- A malicious unauthenticated public visitor is in scope for public endpoints, authentication flows, applicant registration/login, password reset, and uploaded/static/media access.
- A compromised admin or server operator is largely out of scope for ordinary application bugs, except where code makes accidental privilege escalation, credential exposure, or blast-radius expansion more likely.

## Attack Surface, Mitigations, and Attacker Stories

Authentication and session management:

- `backend/core/urls.py` exposes `/auth/login`, `/auth/me`, email verification, forgot/reset/change password, and token refresh. Weak reset-token validation, token leakage, account-state bypass, or missing active/banned checks could allow account takeover or persistent unauthorized access.
- `frontend/lib/auth.ts` stores JWTs in localStorage and mirrored cookies so the Next proxy can route users. Any XSS in the frontend or public content can therefore become token theft.
- `frontend/proxy.ts` revalidates role by calling `/auth/me` and refreshes access tokens with refresh cookies. The proxy must not be treated as backend authorization, and cookies should be protected in production with secure deployment settings.
- New `backend/core/upload_security.py` provides centralized image validation for uploads across applicant, public content, teacher assignment/content, attendance, profile, and related upload paths.

Authorization and object access:

- Admin management endpoints can create and modify accounts, academic hierarchy, public content, elections, hostels, venues, reports, imports, and audit-log access. Missing `IsAdmin` checks or weak object scoping would be high impact.
- Student endpoints cover assignments, submissions, attendance code/QR flows, leave, registration, elections/voting, library, venue bookings, results, exam slips, transcripts, notifications, quizzes, quiz attempts, and gradebook. IDOR or broken ownership checks can expose records or mutate grades, attendance, votes, bookings, or academic requests.
- Teacher endpoints cover assignment creation/grading, attendance creation/corrections, results, course rosters, resources, leave approvals, venue bookings, quiz creation/grading, question bank management, and gradebook entry. Teacher authorization must be tied to assigned courses and students, not merely the teacher role.
- Executive endpoints cover schedule management, courses, offerings, registration approvals, student/teacher management, survey exports, results publication, reports, and organization data. Executive scope must be enforced for school/center/unit boundaries.
- Applicant endpoints cover application creation/update/submission, documents, scholarship data, and staff review. Applicant object ownership and staff review authorization are central because applicant records contain identity documents and sensitive personal/financial data.
- Caterer, librarian, technician, accountant, and notifications endpoints have smaller but still sensitive object boundaries: balances/transactions, book/laptop/room loans, helpdesk tickets, per-user notification states, finance subscriptions, fines, payment attempts, and subscription cards.
- Chatbot endpoints process user queries with vector search and LLM interactions. Query permissions must enforce tenant isolation and user role boundaries.
- Gradebook endpoints allow teachers to enter grades and students to view released grades. Grade overrides and history must be audited and role-scoped.

Files, uploads, and exports:

- Applicant document upload paths in `backend/applicant_app/models.py` include the original filename under application and document-type directories. Upload handling should validate type/size, avoid executable content exposure, prevent path traversal via storage normalization, and avoid public unauthenticated document access.
- Profile pictures and media URLs are displayed through API/base URL composition. User-controlled file names or image URLs must not create XSS, mixed-content, SSRF-like fetches, or open redirect behavior.
- Export endpoints for applicants, students, teachers, executives, reports, surveys, hostels, and PDFs can expose bulk PII. Export authorization and filtering are high-value review targets.
- Chatbot vector search index updates and document processing must not leak cross-tenant data.
- Quiz attempt exports and gradebook exports must be tenant-scoped and role-authorized.

Public website and content:

- `backend/home_app/urls.py` marks many public endpoints `AllowAny`: news, events, pages, admissions, schools, departments, official links, contact, directories, and portal overview. Public content should be read-only to unauthenticated users, avoid leaking unpublished/admin-only data, and sanitize rich text or URLs that render in the frontend.
- Public login/profile/notification routes are not all `AllowAny`, so permission overrides and default permissions matter.

Injection and server-side operations:

- Search, filtering, report generation, imports, schedule generation, evaluation exports, quiz question imports, chatbot vector indexing, and dynamic public page lookup are natural places to review for ORM bypass, unsafe raw SQL, path construction, CSV formula injection, HTML injection, command execution, and excessive resource use.
- The codebase uses PostgreSQL, Redis/Celery, email backends, media storage, vector databases, and LLM providers. User-controlled values must not decide task names, email headers, backend URLs, file paths, or database identifiers.
- Quiz grading logic and answer validation must be server-side enforced; client-side timers and validation cannot be trusted.

Existing mitigations and robustness signals:

- DRF defaults to JWT authentication and an active-user permission.
- Django CSRF, clickjacking, authentication, security, and session middleware are enabled.
- The frontend proxy revalidates role with the backend rather than trusting a role cookie alone.
- Access tokens are short-lived, with refresh flow separated.
- Role-specific URL modules make it possible to review and enforce boundary-specific permissions.
- Audit middleware and audit-log endpoints indicate intent to capture privileged actions.
- Centralized upload security validation in `backend/core/upload_security.py` reduces file upload risk surface.
- Quiz engine enforces backend-side time limits, attempt counts, IP allow-lists, and Safe Exam Browser configuration keys.
- Gradebook maintains audit history for grade changes and overrides.

## Severity Calibration (Critical, High, Medium, Low)

Critical findings in this repository would usually involve unauthenticated or low-privilege compromise of administrative power, token signing secrets, arbitrary file read/write or code execution on the backend, mass access to admissions/student records, arbitrary grade/result/vote manipulation, password reset/account takeover, or cross-tenant data leakage in multi-tenant deployments. Examples: forging JWTs due to exposed production `SECRET_KEY`; an unauthenticated upload path that writes executable files or exposes arbitrary media; public endpoint that returns all applicant documents; student-controlled ID parameter that changes another student's vote or result; quiz engine bypass allowing unauthorized attempt access or grade manipulation; gradebook override without audit trail; chatbot vector search leaking cross-tenant document content.

High findings include authenticated cross-role or horizontal access to sensitive records or workflows, missing role checks on admin/executive/staff endpoints, unsafe bulk export exposure, stored XSS where JWTs in localStorage can be stolen, document upload bypass exposing PII, or teacher/executive scope bypass affecting grades, attendance, schedules, registrations, or admissions. Examples: applicant can access another applicant's document by UUID; teacher can grade courses not assigned to them; executive can export all students outside their scope; stored public news content executes script for portal users; quiz attempt access without proper enrollment; gradebook grade entry by unauthorized teacher; chatbot query accessing another tenant's indexed content.

Medium findings include limited object leaks, weaker session hardening that requires another bug to exploit, CSV injection in exports, insufficient file type validation where files remain non-executable and access-controlled, rate-limit gaps on login/reset flows, and public content integrity issues without credential theft. Examples: helpdesk ticket metadata visible across students; password reset endpoint leaks whether an email exists; report export formula injection affects staff opening spreadsheets; quiz review settings misconfiguration exposing answers prematurely; gradebook scale misconfiguration allowing score inflation; chatbot rate limiting gaps.

Low findings include defense-in-depth hardening, production configuration footguns that are safe when correctly overridden, missing security headers already covered elsewhere, verbose non-sensitive errors, or UI-only route guard inconsistencies where backend authorization is sound. Examples: default `DEBUG=True` or `ALLOWED_HOSTS=*` in settings is low in local development but can become high if deployed unchanged; frontend role cookie can be tampered with but backend rejects unauthorized API calls; unauthenticated public endpoint exposes only already-public published content; quiz settings UI shows options not yet enforced by backend; gradebook category weight validation warnings.