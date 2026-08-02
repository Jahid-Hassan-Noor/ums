# Moodle vs AIU Portal Functionality Comparison

Generated: 2026-07-04

Source folders reviewed:

- Moodle: `/Users/mac/Desktop/moodle-main/public`
- AIU Portal: `/Users/mac/Documents/venv/portal`

This document compares the local open-source Moodle checkout against the local AIU Portal project. The Moodle checkout identifies itself as `5.3dev (Build: 20260630)` in `public/version.php`. The portal review used Graphify first for navigation, then verified current functionality from the live Django/Next.js source tree because the existing Graphify report was built from an older commit.

No source code, Docker configuration, database schema, or generated Graphify output was modified for this report.

## Executive Summary

Moodle is a mature learning management system. Its biggest strengths are deep LMS primitives: courses, enrolment plugins, activity modules, quizzes, question banks, forums, gradebook, completion tracking, competencies, badges, repositories, web services, mobile support, reporting, backups, privacy tooling, accessibility tooling, and a large plugin architecture.

The AIU Portal is broader as a university operations portal. It includes learning workflows, but it also covers admissions, public website content, role dashboards, academic administration, student registration, executive result publication, library operations, canteen balances, venue booking, hostel management, ICT helpdesk, elections, accountant/finance workflows, fines, subscriptions, and institutional reporting.

In short:

- Moodle is deeper in LMS/course delivery mechanics.
- AIU Portal is broader in institution administration and role-specific operational workflows.
- The two overlap around courses, users, assignments, files/resources, grades/results, notifications, calendars, reports, and role-based access.
- Moodle has many LMS capabilities that the portal does not currently implement, especially quizzes/question banks, discussion forums, SCORM/H5P/LTI, gradebook, completion/availability rules, badges, competencies, advanced enrolment/auth plugins, repositories, and backup/restore.
- AIU Portal has many university-business capabilities that Moodle core does not provide as first-class workflows, such as admissions, canteen, library circulation, venue booking, hostels, ICT helpdesk, elections, and finance subscriptions/fines.

## Methodology

The comparison was built from local source evidence rather than marketing descriptions.

For Moodle, the primary evidence was:

- Core version file: `public/version.php`
- Plugin folders with `version.php`
- Moodle activity modules under `public/mod`
- Authentication plugins under `public/auth`
- Enrolment plugins under `public/enrol`
- Blocks, filters, repositories, reports, data formats, course formats, question types, grade plugins, admin tools, AI providers, SMS gateways, communication providers, web service protocols, availability conditions, media players, assignment subplugins, quiz access rules, quiz reports, and workshop subplugins
- Core database install schema in `public/lib/db/install.xml`
- Web service declarations in `db/services.php` files

For AIU Portal, the primary evidence was:

- Graphify query output as the first navigation layer
- Django app models under `backend/*_app/models.py`
- Django app URL declarations under `backend/*_app/urls.py` and `backend/core/urls.py`
- Django service/view files under feature apps
- Next.js App Router pages under `frontend/app/**/page.tsx`
- Backend settings and dependency files for Celery, Redis, DRF, JWT, media, email, chatbot, and payment-related settings

Current portal inventory observed during the review:

- 227 frontend `page.tsx` routes
- 277 first-party backend app route declarations across the major Django apps
- 30 public frontend pages
- 56 admin pages
- 54 student pages
- 32 teacher pages
- 26 executive pages
- 8 librarian pages
- 8 accountant pages
- 5 applicant pages
- 5 technician pages
- 3 caterer pages

## Moodle Functional Inventory

### 1. Core LMS Platform

Moodle provides a full LMS foundation:

- Course sites
- Course categories
- Course sections
- Course modules
- Activity/resource placement inside courses
- Course formats
- User enrolments
- Groups and groupings
- Cohorts
- Roles, contexts, permissions, capabilities
- Activity completion
- Course completion
- Conditional access
- Gradebook
- Calendar
- Notifications
- Messaging
- File storage
- Backup/restore
- Reporting
- Web services
- Mobile integration support
- Plugin lifecycle and installer tooling

The core database schema includes major platform entities such as:

- `course`
- `course_categories`
- `course_modules`
- `course_sections`
- `enrol`
- `user_enrolments`
- `user`
- `role`
- `context`
- `role_assignments`
- `role_capabilities`
- `groups`
- `groupings`
- `cohort`
- `files`
- `repository`
- `backup_controllers`
- `task_scheduled`
- `task_adhoc`
- `grade_items`
- `grade_grades`
- `question`
- `question_attempts`
- `badge`
- `competency`
- `analytics_models`
- `reportbuilder_report`
- `payment_accounts`
- `payments`
- `ai_providers`
- `sms_messages`

### 2. Moodle Activity and Resource Modules

Moodle includes 23 main activity/resource modules:

| Module | Functionality |
| --- | --- |
| Assignment | Coursework submission, grading, feedback, file/text submissions |
| BigBlueButton | Virtual classroom/meeting integration |
| Book | Multi-page structured learning resource |
| Choice | Single-question polling/choice activity |
| Database | User-contributed structured records |
| Feedback | Survey/feedback collection |
| Folder | Grouped downloadable files |
| Forum | Discussion boards and course communication |
| Glossary | Course glossary/knowledge base entries |
| H5P activity | Interactive H5P learning content |
| IMS content package | IMS-packaged learning content |
| Label/Text and media area | Inline text/media in course sections |
| Lesson | Branching lesson paths and question pages |
| LTI external tool | External tool integration |
| Page | HTML/content page resource |
| Question bank | Question management surface |
| Quiz | Online quizzes/exams with attempts and grading |
| File/resource | Downloadable file resource |
| SCORM package | SCORM e-learning package support |
| Subsection | Nested/structured course section support |
| URL | External link resource |
| Wiki | Collaborative course wiki |
| Workshop | Peer assessment workflow |

This is the largest Moodle advantage over the portal. The portal has assignments, resources, attendance, results, and study guides, but Moodle has a broad reusable activity system.

### 3. Assignment Features

Moodle assignment support includes:

- File submissions
- Online text submissions
- Submission comments
- Feedback comments
- Feedback files
- PDF annotation
- Offline grading worksheet
- Late submission penalties
- Grading panels
- Rubric and marking guide integration
- Overrides
- Submission lifecycle APIs

AIU Portal has assignment creation, submissions, attachments, comments, feedback, and rubrics. Moodle is still deeper in generalized assignment subplugins and grading integrations.

### 4. Quiz and Assessment Engine

Moodle has a full quiz engine:

- Quiz activity
- Attempts
- Attempt summaries
- Attempt review
- Saving and processing attempts
- Best-grade calculation
- Manual grading
- Quiz statistics
- Response reports
- Question versioning
- Random questions
- Overrides
- Grade item creation/update
- Access controls

Quiz access rules include:

- Delay between attempts
- IP address restriction
- Number of attempts
- Offline attempts
- Open/close dates
- Password
- Safe Exam Browser
- Secure window
- Time limit

AIU Portal currently has exam slips, final exam scheduling/result workflows, attendance, assignments, and a `quiz` activity/announcement label, but it does not have a Moodle-style quiz engine with question bank, attempts, question types, randomization, automatic grading, and quiz reports.

### 5. Question Bank and Question Types

Moodle includes 18 question types:

| Question type | Functionality |
| --- | --- |
| Calculated | Formula-based numeric questions |
| Calculated multichoice | Formula-driven multiple-choice questions |
| Calculated simple | Simpler calculated questions |
| Drag and drop onto image | Place labels/items on images |
| Drag and drop markers | Marker placement on image |
| Drag and drop into text | Fill text by dragging answers |
| Description | Non-graded prompt/instruction |
| Essay | Long-form written answer |
| Select missing words | Dropdown/gap selection |
| Matching | Match prompts to answers |
| Missing question type placeholder | Placeholder for unavailable types |
| Embedded answers/Cloze | Mixed embedded question formats |
| Multiple choice | Single/multiple answer choices |
| Numerical | Numeric answer questions |
| Ordering | Sequence/order questions |
| Random short-answer matching | Randomized matching from short answers |
| Short answer | Text answer |
| True/False | Binary answer |

AIU Portal does not currently expose this question-bank/question-type infrastructure.

### 6. Gradebook

Moodle has a full gradebook subsystem:

- Grade items
- Grade categories
- Grade grades
- Grade history
- Scales
- Outcomes
- Grade letters
- Grade imports
- Grade exports
- Grader report
- User report
- Overview report
- Single view
- Summary report
- Grade history report
- Outcomes report
- Rubric and marking guide forms

AIU Portal has results, GPA, transcript, exam slip, result submission/review/publication, and course-work/final-exam percentages. That is strong for institutional academic records, but it is not equivalent to Moodle's generalized gradebook.

### 7. Course Completion, Availability, and Learning Progress

Moodle has:

- Activity completion
- Course completion
- Completion aggregation criteria
- Self-completion block
- Completion status block
- Conditional availability by:
  - Completion
  - Date
  - Grade
  - Group
  - Grouping
  - User profile
- Progress reports
- Participation reports
- Course completion reports

AIU Portal tracks course registration, enrollment, attendance, assignments, and results, but it does not appear to implement Moodle-style completion rules and conditional activity access.

### 8. Competencies, Learning Plans, and Badges

Moodle includes:

- Competency frameworks
- Course competencies
- User competencies
- Learning plans
- Templates
- Evidence
- Competency reports
- Badges
- Badge criteria
- Badge issuing
- Badge backpack integrations
- Badge endorsements/alignments/related badges

AIU Portal does not currently expose a competency, learning-plan, or badge system.

### 9. Authentication Plugins

Moodle authentication plugins include:

| Plugin | Functionality |
| --- | --- |
| External database | Authenticate from external DB |
| Email-based self-registration | User self-registration by email |
| LDAP server | LDAP authentication |
| LTI | LTI-based authentication |
| Manual accounts | Locally managed accounts |
| No login | Disabled login accounts |
| No authentication | Accounts without authentication enforcement |
| OAuth 2 | OAuth2 providers |
| Shibboleth | Shibboleth SSO |
| Web services authentication | Web service auth |

AIU Portal has JWT-based portal authentication, applicant auth, role-based access, email verification, forgot/reset password, change password, and admin-created account flows. It does not currently have Moodle's broad authentication plugin ecosystem.

### 10. Enrolment Plugins

Moodle enrolment plugins include:

| Plugin | Functionality |
| --- | --- |
| Category enrolments | Enrol by category relationship |
| Cohort sync | Sync cohort members into courses |
| External database | Enrol from external DB |
| Enrolment on payment | Payment-based enrolment |
| Flat file/CSV | Enrolment from CSV file |
| Guest access | Course guest access |
| IMS Enterprise file | IMS enrolment import |
| LDAP enrolments | LDAP-backed enrolment |
| Publish as LTI tool | Publish course/activity as LTI |
| Manual enrolments | Manual enrolment |
| Course meta link | Link enrolments from another course |
| PayPal | PayPal enrolment payment |
| Self enrolment | Student self-enrolment |

AIU Portal has a custom student course registration and executive approval workflow. It does not have Moodle's enrolment plugin model.

### 11. Blocks and Dashboard Widgets

Moodle includes 40 block plugins, including:

- Accessibility review
- Activity results
- Admin bookmarks
- Latest badges
- Blog menu/recent/blog tags
- Calendar
- Upcoming events
- Comments
- Course completion status
- Courses
- Course/site summary
- Feedback
- Global search
- Random glossary entry
- Text/HTML
- Login
- Learning plans
- Mentees
- Course overview
- Logged-in user profile
- Navigation
- Latest announcements
- Online users
- Private files
- Recent activity
- Recently accessed courses/items
- RSS feeds
- Search forums
- Self completion
- Administration/settings
- Social activities
- Starred courses
- Tags
- Timeline

AIU Portal has role dashboards and page-specific cards, but not Moodle's configurable block ecosystem.

### 12. Filters, Editors, and Media

Moodle text/content filters include:

- Activity names auto-linking
- Algebra
- Code highlighting
- Database auto-linking
- H5P display
- Email protection
- Emoticons
- Glossary auto-linking
- MathJax
- Media plugin
- Multilang
- TeX
- URL auto-linking

Moodle editor support includes:

- Plain textarea
- TinyMCE
- TinyMCE accessibility checker
- TinyMCE AI placement
- TinyMCE autosave
- TinyMCE equation editor
- TinyMCE H5P insertion
- TinyMCE HTML/link/media support
- TinyMCE RecordRTC

Media players include:

- HTML5 audio
- HTML5 video
- VideoJS
- Vimeo
- YouTube

AIU Portal has a modern React UI and file/media uploads for its workflows, but it does not include Moodle's generalized content filter/editor/media plugin layer.

### 13. File Repositories and Portfolios

Moodle repository plugins include:

- Embedded files
- Content bank
- Course files
- Dropbox
- EQUELLA
- File system
- Flickr
- Flickr public
- Google Drive
- Local server files
- Merlot.org
- Nextcloud
- Microsoft OneDrive
- Recent files
- Amazon S3
- File upload
- URL downloader
- Private files
- WebDAV
- Wikimedia
- YouTube videos

Portfolio plugins include:

- File download
- Flickr
- Google Drive

AIU Portal stores and serves files for specific workflows such as applicant documents, course resources, assignment attachments, study guides, reports, and generated PDFs. It does not currently have Moodle's pluggable repository/portfolio system.

### 14. Reporting and Analytics

Moodle reports include:

- Backups report
- Competency breakdown
- Course completion
- Config changes
- Course overview
- Events list
- Infected files
- Insights
- Logs
- Live logs
- Activity report
- Course participation
- Performance overview
- Activity completion progress
- Question instances
- Security checks
- Statistics
- System status
- Theme usage
- User sessions

Moodle also includes report builder tables and analytics tables for predictions, training samples, analysables, indicators, and actions.

AIU Portal has reports and exports for academic, people, operational, student, teacher, and final result data, plus audit logs and statistics. It does not currently match Moodle's LMS analytics/report-builder breadth.

### 15. Web Services and Mobile/API Ecosystem

Moodle includes:

- REST protocol
- SOAP protocol
- External service declarations
- External functions
- Tokens
- Web service users
- Mobile app tooling
- Many core and module-specific web service APIs

Examples include APIs for:

- Badges
- Blog
- Calendar
- Course formats
- Enrolment user search
- Grades
- Groups
- Messaging
- Search
- Assignments
- BigBlueButton
- Forum
- Glossary
- H5P
- Quiz
- PayPal
- Question bank

AIU Portal exposes DRF APIs for its Next.js frontend, but it does not currently expose a Moodle-style external service registry for third-party clients/mobile plugins.

### 16. Administration, Security, Privacy, and Operations

Moodle admin tools include:

- Site admin presets
- Analytics models
- Availability condition management
- Acceptance testing tools
- Accessibility toolkit
- Capability overview
- Cohort roles management
- UI component library
- Custom language
- Data privacy
- Database transfer
- File types
- Development data generator
- HTTPS conversion
- Plugin installer
- Language packs
- Licence manager
- Log store manager
- Learning plans
- Competency import/migration
- Inbound message configuration
- Multi-factor authentication
- Moodle app tools
- Event monitor
- OAuth2 services
- PHPUnit tools
- Policies
- Profiling
- Recycle bin
- Database search/replace
- Spam cleaner
- Scheduled task configuration
- Template library
- Unsupported role assignments
- Course upload
- User upload
- User tours
- XMLDB editor

AIU Portal has settings, audit logs, route permission tests, Celery scheduled tasks, notifications, reports, and account management. It does not include the same mature admin/plugin/privacy/accessibility operations suite as Moodle.

### 17. Payments, AI, SMS, and Communication Providers

Moodle includes:

- PayPal payment gateway
- Payment accounts/gateways/payments schema
- AI providers:
  - Amazon Bedrock
  - Azure AI
  - DeepSeek
  - Gemini
  - Ollama
  - OpenAI
- SMS gateways:
  - AWS
  - Modica
- Communication providers:
  - Custom link
  - Matrix
- Message outputs:
  - Mobile
  - Email
  - Popup/web
  - SMS

AIU Portal has ToyyibPay/DuitNow-compatible finance configuration, payment attempts, webhooks, subscriptions, fines, email delivery, in-app notifications, and chatbot settings for Ollama. Moodle's payment/AI/SMS approach is pluginized; AIU Portal's approach is custom and institution-specific.

## AIU Portal Functional Inventory

### 1. Architecture and Roles

AIU Portal is a Django/DRF backend plus Next.js/React frontend. It is organized around role apps and role-specific frontends.

Primary roles and areas:

- Public website user
- Applicant
- Student
- Teacher
- Executive
- Administrator
- Librarian
- Caterer
- Technician
- Accountant

Backend apps reviewed:

- `admin_app`
- `student_app`
- `teacher_app`
- `executive_app`
- `applicant_app`
- `home_app`
- `librarian_app`
- `caterer_app`
- `technician_app`
- `accountant_app`
- `notifications_package`
- `chatbot_app`

Key platform features:

- JWT authentication
- Email verification
- Forgot/reset password
- Change password
- Role-based routing
- Role-specific dashboards
- Admin-created role accounts
- Applicant-specific authentication
- DRF APIs
- Next.js frontend pages
- Media uploads
- PDF generation via ReportLab
- Celery with Redis
- Email backend configuration
- Notifications
- Chatbot endpoint

### 2. Public Website and CMS

The portal includes a public-facing university website and admin-managed public content.

Public pages include:

- Home
- About
- Admissions
- Apply
- Applicant login/register
- Centers/centres
- Contact
- Departments
- Directories
- Events
- Forgot/reset/recover account
- Login
- News
- Notifications
- Official links
- Payment return
- Portal overview
- Profile
- Programmes/programs
- Scholarship
- Schools
- Services
- Student life
- Units
- Catch-all slug page

Public content models include:

- `PublicPage`
- `PublicAnnouncement`
- `PublicNews`
- `PublicEvent`
- `OfficialLink`
- `PublicDirectoryEntry`
- `PublicInquiry`

Admin public content management includes:

- Public content pages
- Announcements
- Events
- News
- Official links

This is a portal strength. Moodle can host course/site pages, but it is not primarily a university public CMS.

### 3. Authentication and Account Management

Portal auth includes:

- Main login
- Applicant login
- User profile
- Email verification
- Forgot password
- Reset password
- Change password
- Token refresh
- Current user lookup
- Role-based frontend routing
- Admin-created accounts
- Role-specific create-account pages
- Role-specific account management pages

Admin can create/manage:

- Students
- Teachers
- Executives
- Applicants
- Librarians
- Technicians
- Caterers
- Accountants

Compared with Moodle:

- Portal is stronger for institution-defined staff/student/applicant account flows.
- Moodle is stronger for pluggable authentication providers and external identity integrations.

### 4. Academic Directory and Organization

Portal academic structure models include:

- `School`
- `Center`
- `Department`
- `Unit`
- `Program`
- `Semester`
- `SemesterHoliday`
- `IELTSSession`
- `Course`
- `CourseOffering`
- `CourseTutorialGroup`
- `CourseLabGroup`
- `ClassGroup`
- `Room`
- `Building`
- `Venue`

Admin academic pages cover:

- Schools
- Centres
- Departments
- Units
- Programmes
- Courses
- Semesters

Executive organization pages cover:

- Organization
- Programs
- Executive management of students/teachers

Compared with Moodle:

- Moodle has course categories and courses.
- Portal has a richer university administrative directory around schools, centres, departments, units, programmes, buildings, venues, and semesters.

### 5. Course Offering and Scheduling

Portal course/schedule features include:

- Course catalog management
- Course offering
- Offered course listings
- Teacher assignment to offerings
- Class meetings
- Tutorial/lab groups
- Executive schedule management
- Student timetable
- Teacher timetable
- Calendar pages
- Final exam schedule logic

Frontend pages include:

- Executive courses/add/all/offer/offered
- Executive manage schedule
- Student timetable/today/weekly
- Teacher timetable/today/weekly
- Student courses/current/completed/detail
- Teacher courses/current/previous/detail

Compared with Moodle:

- Moodle has course shells, sections, activities, and enrolments.
- Portal has more institution-specific scheduling, timetable, final exam, and offering workflows.

### 6. Student Course Registration

Portal registration features include:

- Registration periods
- Offered course list
- Student course registration requests
- Registration history
- Backend registration rules
- Executive approval/review paths
- Enrollment records
- Duplicate/retake/timetable rule enforcement in service logic

Models include:

- `RegistrationPeriod`
- `CourseRegistration`
- `Enrollment`

Compared with Moodle:

- Moodle supports enrolment plugins and self/manual/cohort/guest enrolment.
- Portal supports a university-style registration approval process.

### 7. Course Content and Study Guides

Portal course content features include:

- Course sections
- Resource folders
- Course resources
- Course announcements
- Course activities
- Study-guide upload/display
- Assessment-plan settings per course offering
- Teacher course resource workspace
- Student course detail page with course content

Models include:

- `CourseResourceFolder`
- `CourseSection`
- `CourseAnnouncement`
- `CourseAnnouncementSlot`
- `CourseAnnouncementSlotSelection`
- `CourseResource`
- `CourseActivity`

Compared with Moodle:

- Portal has useful teacher/student course-resource workflows.
- Moodle is much deeper in reusable activity/resource types, filters, content bank, H5P, LTI, SCORM, lesson, page, book, URL, folder, wiki, forum, and glossary.

### 8. Assignments

Portal assignment features include:

- Teacher assignment creation
- Assignment detail
- Assignment submissions
- Student submission
- Assignment feedback
- Assignment comments
- Assignment attachments
- Assignment groups
- Group membership/invitations
- Rubrics
- Upcoming/submitted/graded/overdue student views

Models include:

- `Assignment`
- `AssignmentGroup`
- `AssignmentGroupMembership`
- `AssignmentGroupInvitation`
- `AssignmentRubric`
- `AssignmentSubmission`
- `AssignmentAttachment`
- `AssignmentFeedback`
- `AssignmentComment`

Compared with Moodle:

- Common area: assignments, submissions, feedback, rubrics.
- Moodle has more assignment subplugins and gradebook integration.
- Portal has a custom assignment workflow tuned to the AIU portal roles.

### 9. Attendance

Portal attendance features include:

- Teacher attendance sessions
- Attendance creation
- Attendance corrections
- Course attendance
- Student attendance view
- Attendance code submission
- QR attendance
- Attendance reports

Models include:

- `AttendanceSession`
- `AttendanceRecord`
- `AttendanceCodeSubmission`

This is a portal strength relative to Moodle core. Moodle can support attendance via plugins, but the reviewed Moodle core activity list does not show the portal's exact QR/code attendance workflow as a first-class core module.

### 10. Results, GPA, Transcript, and Exam Slip

Portal academic records features include:

- Teacher result drafts
- Teacher result submission
- Completed results
- Executive result review
- Executive result publication
- Semester results
- Previous results
- GPA
- Transcript
- Course-work results
- Exam slip
- Exam slip PDF
- Semester result PDF
- Final result exports

Models include:

- `Exam`
- `ExamVenueAllocation`
- `ExamSlip`
- `TranscriptRecord`
- `ResultPublication`
- `ResultBatch`
- `ResultRecord`
- `ResultApproval`
- `ResultReviewNote`
- `ResultSubmission`

Compared with Moodle:

- Moodle has a strong gradebook.
- Portal has stronger institution-specific result approval, publication, transcript, and exam-slip workflows.

### 11. Evaluations and Surveys

Portal evaluation features include:

- Evaluation templates
- Course evaluation surveys
- Student evaluation responses
- Executive survey management
- Survey detail
- Survey export

Models include:

- `EvaluationTemplate`
- `CourseEvaluationSurvey`
- `CourseEvaluationResponse`

Moodle has Feedback activity and survey-like workflows. Portal's evaluation workflow is more institution-specific and tied to executive/course operations.

### 12. Applicant and Admissions

Portal applicant/admission features include:

- Applicant registration/login
- Applicant profile/me
- Application options
- Application creation
- Application detail
- Application submission
- Applicant documents
- Staff application listing
- Staff status review
- Scholarship review
- Document review

Models include:

- `Applicant`
- `ApplicationIntake`
- `ApplicationProgramme`
- `AdmissionApplication`
- `ScholarshipApplication`
- `ApplicationDocument`
- `ApplicationStatusEvent`

This is a major portal-only area. Moodle does not provide this admissions pipeline as a core LMS function.

### 13. Library and Librarian Workspace

Portal library features include:

- Librarian dashboard
- Books
- Book detail
- Book acquisition requests
- Book copies
- Shelves
- Laptops
- Library rooms
- Students lookup
- Borrow requests
- Loans
- Loan return
- Loan renewal
- Apply/waive fine
- Mark lost
- Student library views
- Student book requests
- Student room reservation cancellation

Models include:

- `Librarian`
- `Shelf`
- `Book`
- `BookAcquisitionRequest`
- `BookCopy`
- `Laptop`
- `LibraryRoom`
- `BorrowRequest`
- `Loan`
- `Fine`
- `WaitlistEntry`
- `InventoryAudit`
- `InventoryAuditItem`
- `AcquisitionBudget`

This is a portal-only operational domain compared with Moodle core.

### 14. Canteen

Portal canteen features include:

- Caterer dashboard
- Student canteen account lookup
- Canteen transactions
- Admin canteen page
- Canteen settings
- Monthly allowance initialization
- Bonus/allowance handling
- Balance adjustment

Models include:

- `Caterer`
- `CanteenSetting`
- `CanteenMonthlyBonus`
- `StudentCanteenAccount`
- `CanteenTransaction`
- `CanteenBalanceAdjustment`

Scheduled task:

- `initialize-canteen-allowances-monthly`

This is not a Moodle core domain.

### 15. Finance, Subscriptions, Fines, and Payments

Portal finance/accountant features include:

- Accountant dashboard
- Finance gateway settings
- Subscription plans
- My subscriptions
- Accountant subscription view
- Subscription purchase
- Subscription card generation
- Payment return
- Payment webhook
- Student list for fines
- Accountant fine list/detail
- Fine deduction
- Student fine list
- Student fine payment initiation
- Overdue fine escalation

Models include:

- `Accountant`
- `FinanceGatewayConfig`
- `SubscriptionPlan`
- `Subscription`
- `PaymentAttempt`
- `Fine`

Scheduled task:

- `mark-overdue-fines-hourly`

Compared with Moodle:

- Moodle has PayPal/payment-gateway infrastructure for enrolments/payments.
- Portal has custom institution finance workflows: subscriptions, fines, cards, ToyyibPay/DuitNow-compatible gateway settings, webhooks, and accountant role pages.

### 16. Venue Booking and Hostel

Portal venue features include:

- Venue management
- Building management
- Venue CRUD
- Booking requests
- Admin approval/rejection
- Student venue booking
- Teacher venue booking
- Owner cancellation

Models include:

- `Venue`
- `Building`
- `VenueBookingRequest`

Portal hostel features include:

- Hostels
- Hostel rooms
- Hostel export
- Student-life hostel content

Models include:

- `Hostel`
- `HostelRoom`

These are portal-only campus operations areas.

### 17. ICT Helpdesk

Portal ICT helpdesk features include:

- Student ticket creation/listing
- Technician dashboard
- Technician ticket detail
- Ticket categories
- Status updates
- Ticket update history

Models include:

- `Technician`
- `HelpdeskTicket`
- `HelpdeskTicketUpdate`

This is a portal-only operational workflow compared with Moodle core.

### 18. Student Services

Portal student services include:

- Student dashboard
- Courses
- Assignments
- Attendance
- Calendar
- Elections
- Emergency contacts
- Evaluations
- Exam slip
- Fines
- ICT helpdesk
- Leave apply/history
- Library
- Notifications
- Registration
- Results
- Subscriptions
- Timetable
- Venue bookings
- Warden schedule

Models include:

- `Student`
- `LeaveRequest`
- `LeaveApproval`
- `StudentAffairsContact`
- `EmergencyContact`
- `WardenSchedule`

Moodle has student dashboards, course overview, grades, calendar, messages, and activities. Portal adds campus-service workflows.

### 19. Teacher Services

Portal teacher services include:

- Teacher dashboard
- Assignments
- Assignment submissions and feedback
- Attendance
- Calendar
- Course detail
- Course assignments
- Course attendance
- Course resources
- Course roster
- Leave requests
- Notifications
- Results draft/submission/completed
- Timetable
- Venue bookings

Models include:

- `Teacher`
- `TeacherScopeAssignment`
- Teacher-side assignment/content/attendance/result models

Moodle has teacher/course editing and grading concepts. Portal has custom teacher role pages aligned with AIU workflows.

### 20. Executive Services

Portal executive features include:

- Executive dashboard
- Audit log
- Calendar
- Courses
- Course offering
- Course schedule management
- Student/teacher management
- Organization
- Programs
- Reports
- Statistics
- Results review/publication
- Evaluations

Models include:

- `Executive`
- `ExecutiveUnitAssignment`
- `CourseOfferProposal`
- `TimetableSlot`
- Result/evaluation models

Moodle has admin/manager roles, but the reviewed portal has a distinct executive academic administration domain.

### 21. Elections

Portal elections include:

- Election creation/management
- School election seats
- Candidate management/approval
- Student ballot display
- Student vote casting
- Result snapshots/publication

Models include:

- `Election`
- `SchoolElectionSeat`
- `ElectionCandidate`
- `Vote`
- `ElectionResultSnapshot`

Moodle does not provide this as a core workflow.

### 22. Notifications, Audit Logs, Reports, and Scheduled Tasks

Portal system support includes:

- Notifications list/read/read-all/delete/delete-read
- Due reminder processing
- Email notifications
- Audit logs
- Admin reports
- Report exports
- Executive reports
- Statistics pages
- Celery worker and Redis broker

Scheduled tasks configured:

- Process due reminders every minute
- Mark overdue fines hourly
- Initialize canteen allowances monthly

Moodle has a mature task/log/report/notification subsystem. Portal has a more focused custom implementation for its role workflows.

### 23. Chatbot

Portal includes:

- Chatbot query endpoint
- Ollama base URL setting
- Configurable model and fast model
- Feature flag for LLM enablement

Moodle has pluginized AI provider infrastructure. Portal has a simpler custom chatbot integration.

## Common Functionality Between Moodle and AIU Portal

| Functional Area | Moodle | AIU Portal | Comparison |
| --- | --- | --- | --- |
| Users/accounts | Core users, roles, contexts, capabilities | Profiles, role-specific users, admin-created accounts | Common, but Moodle has deeper permission context system |
| Authentication | Many auth plugins | JWT, email verification, reset/change password, applicant auth | Common login/account need; Moodle has more external auth options |
| Courses | Course/category/section/module system | Course, offering, teacher assignment, registration, timetable | Common course concept; portal is more university-schedule oriented |
| Enrolment/registration | Enrolment plugins | Student registration requests and executive approval | Common student-course relationship; implementation differs |
| Course resources | Resource/page/book/folder/URL/H5P/etc. | Course resources, folders, sections, study guides | Common; Moodle much broader |
| Assignments | Assignment module with submissions/feedback/rubrics | Assignment workflows with submissions/feedback/rubrics | Strong overlap |
| Grading/results | Gradebook, reports, outcomes | Results, GPA, transcript, exam slip, publication workflow | Common assessment record need; portal stronger in institutional records |
| Calendar | Core calendar | Student/teacher/executive calendars | Common |
| Notifications | Message/notification subsystem | Notification package and role notification pages | Common |
| Reports/logs | Many reports, logs, report builder | Reports, exports, audit log, statistics | Common; Moodle broader LMS analytics |
| Payments | PayPal/payment gateway support | ToyyibPay/DuitNow-compatible finance, subscriptions, fines | Common payment concept; portal more campus-finance specific |
| Evaluations/feedback | Feedback module | Course evaluation surveys/templates | Common feedback/survey domain |
| Files/uploads | File API, repositories, private files | Media uploads, applicant docs, resources, PDFs | Common, but Moodle has repository abstraction |
| Admin tools | Extensive site admin tools | Admin dashboards/settings/manage pages | Common administrative need; Moodle has more platform tooling |

## Moodle Functionality Missing or Not Yet Equivalent in AIU Portal

The items below are the main Moodle capabilities not currently present in the portal as equivalent systems.

### 1. Full Quiz Engine - Implemented

Moodle has a mature online quiz/exam engine. The local Moodle implementation is mainly under `public/mod/quiz`, with reusable question state stored through the core question engine under `public/question/engine`.

Moodle source evidence reviewed:

- `public/mod/quiz/db/install.xml` defines the quiz delivery schema: `quiz`, `quiz_grade_items`, `quiz_slots`, `quiz_sections`, `quiz_feedback`, `quiz_overrides`, `quiz_attempts`, `quiz_grades`, and `quiz_reports`.
- `public/mod/quiz/attempt.php` handles an in-progress attempt page, capability checks, access-rule checks, page navigation, autosave setup, and attempt rendering.
- `public/mod/quiz/review.php` handles post-attempt review for students and teachers, including review permissions and display options.
- `public/mod/quiz/classes/access_manager.php` aggregates quiz access-rule plugins from `public/mod/quiz/accessrule/*`.
- `public/mod/quiz/classes/grade_calculator.php` recalculates attempt totals and final quiz grades using highest, average, first-attempt, or last-attempt methods.
- Quiz report plugins exist under `public/mod/quiz/report`: grading, overview, responses, and statistics.
- Quiz access rules exist for delay between attempts, IP address, number of attempts, offline attempts, open/close dates, password, Safe Exam Browser, secure window, and time limit.

Moodle functionality to add to the portal:

- Teacher/executive quiz authoring tied to a `CourseOffering`.
- Quiz metadata: title, description/instructions, total marks, publication status, visible-from/visible-until, review policy, grade method, pass mark, and optional result-workflow mapping.
- Quiz structure: sections, ordered slots, per-question marks, required previous-question rules, page breaks, shuffle questions, shuffle answers, and random-question slots.
- Attempt access controls: open/close windows, time limit, max attempts, password, IP allow-list, per-student or per-group overrides, and late/overdue handling.
- Student attempt flow: start attempt, resume attempt, answer autosave, navigation, flag question, submit page, final submit, timeout submit, and attempt state transitions.
- Attempt review: teacher review, student review, configurable answer visibility, correctness visibility, marks visibility, feedback visibility, and right-answer visibility.
- Grading: automatic grading for objective types, manual grading queue for essays and flagged short answers, grade recalculation, final grade selection across attempts, and grade history.
- Reports: attempt overview, responses report, manual grading report, per-question statistics, item difficulty/facility, discrimination indicators, and exportable CSV/PDF summaries.
- Security controls: backend-enforced eligibility, time-window checks on every attempt request, server-side timer authority, answer visibility rules, and audit events for attempt start/submit/regrade/reopen.
- Optional high-security layer later: Safe Exam Browser style config, secure-window mode, screenshot/proctoring policy hooks, and device/IP/session anomaly logging.

Portal gap:

- Graphify did not surface any existing `Quiz`, `QuestionBank`, `QuestionAttempt`, quiz attempt, random-question, or online-exam engine. The only explicit quiz-adjacent portal hit was the existing `Exam` academic-record model.
- Portal currently has assignments, rubrics, study guides, course resources, attendance, exam slips, final-exam scheduling, result submission/review/publication, GPA, and transcript workflows.
- Those workflows are important, but they are not a Moodle-style online quiz/exam engine with reusable questions, attempts, automatic grading, review policies, randomization, and quiz analytics.

Suggested portal data model:

- `QuestionBank`: owned by a school, department, programme, course, or course offering.
- `QuestionCategory`: hierarchical grouping inside a bank.
- `Question`: stable logical question record.
- `QuestionVersion`: immutable authored version with status such as draft, ready, archived.
- `QuestionChoice`: answer options and feedback for objective question types.
- `Quiz`: published assessment linked to `CourseOffering`, with timing, attempt, grading, review, and security settings.
- `QuizSection`: optional section heading and shuffle setting.
- `QuizQuestionSlot`: ordered quiz slot with mark, page, display number, required-previous flag, and fixed question/version reference.
- `QuizRandomRule`: random-question slot or section rule that selects from categories, tags, difficulty, or type.
- `QuizAccessOverride`: per-student or per-group overrides for time window, time limit, attempts, and password.
- `QuizAttempt`: one student's attempt, with attempt number, state, start/finish times, current page, score, and overdue handling.
- `QuestionAttempt`: snapshot of the question version, slot, max mark, selected variant, response summary, right-answer summary, and awarded fraction/mark.
- `QuestionAttemptStep`: autosave and submit history for each question attempt.
- `QuizGrade`: final calculated grade for a student on a quiz.
- `QuizManualGrade`: manual grading records, grader notes, rubric-like judgement fields, and regrade audit.
- `QuizReportSnapshot`: cached report/statistics output for expensive analytics.

Recommended first implementation slice:

1. Add backend models/services for `QuestionBank`, `QuestionCategory`, `Question`, `QuestionVersion`, `QuestionChoice`, `Quiz`, `QuizQuestionSlot`, `QuizAttempt`, `QuestionAttempt`, `QuestionAttemptStep`, and `QuizGrade`.
2. Support multiple choice, true/false, short answer, and essay first.
3. Add teacher APIs to create questions, create quizzes, add questions to slots, publish/unpublish quizzes, and preview a quiz.
4. Add student APIs to list available quizzes for enrolled offerings, start/resume attempts, autosave answers, submit attempts, and view allowed review data.
5. Add grading services for objective auto-grading and essay/manual grading.
6. Add teacher reports for attempts, responses, manual grading, and quiz grade export.
7. Keep quiz grades separate from official result publication initially; add an optional reviewed mapping into the existing result workflow only after the quiz engine is stable.

Implementation cautions:

- Do not fold this into assignment rubrics. Assignment rubrics evaluate submitted work; quiz questions need reusable versions, attempt snapshots, answer validation, grading behavior, and review policies.
- Do not trust frontend timers. The backend must enforce open/close times, time limit, attempt count, ownership, and submit deadlines on every attempt mutation.
- Snapshot the question version into each `QuestionAttempt`; otherwise later question edits can change the meaning of old attempts.
- Treat random questions as a slot-selection rule that resolves to concrete question attempts at attempt start.
- Start without Safe Exam Browser/proctoring. Add those only after core attempt integrity, autosave, review, and grading are reliable.

### 2. Question Bank and Question Types - Implemented

Moodle has 18 question types and a versioned question-bank infrastructure that is shared by the quiz engine and other question-using activities.

Moodle source evidence reviewed:

- `public/question/type/*` contains 18 question-type plugins: calculated, calculated multichoice, calculated simple, drag-and-drop onto image, drag-and-drop markers, drag-and-drop into text, description, essay, select missing words, matching, missing type placeholder, embedded answers/Cloze, multiple choice, numerical, ordering, random short-answer matching, short answer, and true/false.
- `public/lib/db/install.xml` defines reusable question-bank tables: `question_categories`, `question`, `question_bank_entries`, `question_versions`, `question_references`, `question_set_references`, `question_answers`, and `question_hints`.
- The same schema defines runtime question-attempt tables: `question_usages`, `question_attempts`, `question_attempt_steps`, and `question_attempt_step_data`.
- The same schema defines analytics tables: `question_statistics`, `question_response_analysis`, and `question_response_count`.
- `public/question/engine/questionusage.php` models a set of questions being attempted by an activity such as a quiz.
- `public/question/engine/questionattempt.php` models one question inside a larger attempt, including slot, variant, max mark, state steps, response summary, right answer, and flags.
- `public/question/bank/*` includes bank features for editing, category management, import, export, history/version display, preview, statistics, tagging, usage tracking, creator columns, question-name/text/type views, and bulk movement/deletion.

Moodle functionality to add to the portal:

- Bank ownership by course, course offering, department, programme, or school.
- Hierarchical question categories.
- Question versioning with draft, ready, archived, and hidden states.
- Reusable question metadata: name, text, type, default mark, penalty, general feedback, created by, modified by, tags, difficulty, learning outcome, and usage count.
- Question references so quizzes point either to a fixed version or the latest ready version.
- Random question set references that select questions by category, tag, difficulty, type, and count.
- Preview tooling so teachers can test how a question renders and grades before publishing.
- Import/export later, preferably CSV/QTI/GIFT-like formats after the first internal format is stable.
- Usage tracking so teachers can see where a question is used before editing or archiving it.
- Response analytics that support question improvement: answer distribution, facility/difficulty, discrimination, most common wrong answers, and manual-review flags.

Recommended first question types:

| Question type | First portal behavior |
| --- | --- |
| Multiple choice | Single-answer first, then multi-answer; shuffle choices; per-choice feedback |
| True/False | Binary choice; auto-grade; feedback for both options |
| Short answer | Exact/case-insensitive match first; manual override support |
| Essay | Manual grading only; optional file attachment later |

Recommended later question types:

| Question type | Reason to defer |
| --- | --- |
| Numerical | Needs tolerance/units rules |
| Matching | Needs paired answer modeling and shuffle behavior |
| Ordering | Needs sequence scoring logic |
| Calculated | Needs variables, datasets, formulas, and validation tooling |
| Cloze/embedded answers | Needs parser and rich rendering rules |
| Drag-and-drop/image questions | Needs media hotspot/coordinate UI |

Suggested portal roadmap:

1. Build a teacher/executive question bank per course/offering first, with category and tag filters.
2. Add immutable `QuestionVersion` records before attempts exist, so old attempts remain auditable after edits.
3. Add question preview and validation before quiz publication.
4. Connect quiz slots to question versions through explicit references.
5. Add random-question rules only after fixed-question quizzes work.
6. Add import/export after internal authoring, attempts, and reports are stable.
7. Add response analytics after there is enough attempt data to make the reports useful.

Implementation cautions:

- Keep question-bank permissions backend-enforced. A teacher should only author against assigned offerings/courses, while executives/admins can manage broader banks according to academic scope.
- Do not reuse `AssignmentRubric` for question scoring. Rubrics can help manual essay grading later, but objective question grading needs deterministic answer keys and per-attempt snapshots.
- Do not let a question edit mutate published attempts. Edits should create a new version and leave existing `QuestionAttempt` rows tied to the old version.
- Do not expose correct answers through APIs unless the quiz review settings allow it for that student and attempt state.

### 3. Forums and Course Discussions

Moodle has a mature forum activity with discussions, posts, subscriptions, read tracking, digests, grading, reports, and web-service support.

Moodle source evidence reviewed:

- `public/mod/forum/db/install.xml` defines `forum`, `forum_discussions`, `forum_posts`, `forum_queue`, `forum_subscriptions`, `forum_digests`, `forum_read`, `forum_track_prefs`, `forum_discussion_subs`, and `forum_grades`.
- `public/mod/forum/db/access.php` defines forum capabilities.
- `public/mod/forum/db/services.php` exposes forum web-service functions.
- `public/mod/forum/lib.php` contains the module integration points.
- `public/mod/forum/report/*` shows that forum analytics/reporting is treated as a first-class concern.

Moodle functionality to add to the portal:

- Course-offering discussion boards.
- Discussion threads with title, body, author, status, pinned/locked state, and last activity.
- Replies with nesting or flat chronological display.
- Read/unread tracking per user.
- Thread subscription and notification preferences.
- Teacher moderation: pin, lock, hide, restore, delete, move, and mark answer.
- Optional grading/rating later, separate from official result publication.
- Reports for participation count, inactive students, unanswered threads, and moderation activity.

Portal gap:

- No Moodle-style course discussion forum.
- Portal course pages have resources, announcements, assignments, attendance, study guides, and activities, but not persistent course discussions with read tracking and subscriptions.

Suggested portal roadmap:

1. Add `CourseDiscussionBoard`, `CourseDiscussionThread`, `CourseDiscussionPost`, `CourseDiscussionReadState`, and `CourseDiscussionSubscription` models tied to `CourseOffering`.
2. Add teacher APIs for board settings, moderation, thread pinning, locking, and deletion.
3. Add student/teacher APIs for listing discussions, creating threads, replying, marking read, and subscription toggles.
4. Add notifications for new replies, mentions, pinned announcements, and teacher answers.
5. Add role-aware frontend pages inside the existing student/teacher course detail surfaces.
6. Add participation exports only after the discussion workflow is stable.

Implementation cautions:

- Keep board access backend-enforced through enrollment and teacher assignment checks.
- Do not reuse course announcements for discussions. Announcements are broadcast content; forums need conversation state.
- Start with simple moderation and read tracking before adding grading or rich analytics.

### 4. Wiki, Glossary, Lesson, Book, Database, Choice, Workshop

Moodle includes several course activity types that go beyond file resources and assignments.

Moodle source evidence reviewed:

- `public/mod/wiki/db/install.xml`, `db/access.php`, and `db/services.php` implement collaborative wiki pages.
- `public/mod/glossary/db/install.xml` defines glossaries, entries, aliases, categories, entry-category links, and display formats.
- `public/mod/lesson/db/install.xml` defines lesson pages, answers, attempts, grades, timers, branches, and overrides.
- `public/mod/book/db/install.xml` defines books and chapters.
- `public/mod/data/db/install.xml` defines database activities, fields, records, and per-field content.
- `public/mod/choice/db/install.xml` defines choices, options, and student answers.
- `public/mod/workshop/db/install.xml` defines workshop settings, submissions, assessments, grades, and aggregated peer-assessment grades.
- `public/mod/workshop/form/*` and `public/mod/workshop/allocation/*` show Moodle's workshop subplugin model for grading strategies and reviewer allocation.

Moodle activity types not currently equivalent in the portal:

- Wiki
- Glossary
- Lesson
- Book
- Database activity
- Choice/poll
- Workshop peer assessment

Portal gap:

- Portal course content is useful but not modular at Moodle's level.
- Portal has course resources, folders, sections, announcements, activities, assignments, rubrics, and study guides, but it does not expose separate authoring/runtime models for these activity types.

Suggested portal roadmap:

1. Keep the existing `CourseActivity` concept as the user-facing course activity surface, but add type-specific tables/services only where the type needs real behavior.
2. Add `ChoicePoll` first if teachers need quick single-question polling.
3. Add `CoursePage` or `CourseBook` for structured teacher-authored content that is richer than uploaded PDFs.
4. Add `Lesson` only if AIU needs branching paths, page-by-page progress, and embedded questions.
5. Add `Glossary` if programmes need shared terminology, auto-linking, or student-contributed terms.
6. Add `Wiki` only if collaborative course authoring is a real teaching requirement.
7. Add `Workshop` last because peer assessment needs submission allocation, reviewer anonymity rules, assessment forms, calibration, and appeals.

Suggested portal data models by priority:

- `ChoicePoll`, `ChoicePollOption`, `ChoicePollResponse`
- `CourseBook`, `CourseBookChapter`
- `Lesson`, `LessonPage`, `LessonBranch`, `LessonAttempt`
- `Glossary`, `GlossaryEntry`, `GlossaryCategory`, `GlossaryAlias`
- `CourseWiki`, `WikiPage`, `WikiRevision`
- `PeerWorkshop`, `WorkshopSubmission`, `WorkshopReview`, `WorkshopAllocation`, `WorkshopGrade`

Implementation cautions:

- Do not create one huge generic JSON activity table for everything. Use a light registry plus type-specific models for workflows that have state.
- Keep teacher authoring simple at first. Moodle's module set is broad because it is a platform; the portal should add only the activities AIU will actually use.
- Prioritize forums, quizzes, lessons/pages, and polls before lower-frequency tools.

### 5. SCORM, IMS, H5P, and LTI

Moodle supports packaged learning content and external learning-tool launch standards.

Moodle source evidence reviewed:

- `public/mod/scorm/db/install.xml` defines SCORM packages, SCOes, SCO data, sequencing rules, AICC sessions, SCORM attempts, tracked elements, and SCO values.
- `public/mod/scorm/report/*` shows SCORM-specific reporting.
- `public/mod/imscp/db/install.xml` defines IMS content package resources.
- `public/mod/h5pactivity/db/install.xml` defines H5P activities, attempts, and attempt results.
- `public/mod/lti/db/install.xml` defines LTI activity instances, tool proxies, tool types, tool settings, submissions, access tokens, category visibility, and course visibility.
- `public/mod/lti/services.php` and `public/mod/lti/db/services.php` expose LTI service integration.

Moodle supports:

- SCORM packages
- IMS content packages
- H5P content/activity
- LTI external tools

Portal gap:

- No equivalent package/runtime/tool integration layer.
- Portal supports file/resource uploads and course content, but not package runtime tracking, H5P attempts, SCORM sequencing, or LTI launches.

Suggested portal roadmap:

1. Add LTI 1.3 first if AIU needs external learning tools such as proctoring, simulations, or publisher content.
2. Add H5P integration if teachers need interactive content that can report attempt results.
3. Treat IMS content package support as static content rendering unless tracking is required.
4. Defer SCORM until there is a specific compliance requirement or a large existing SCORM content library.
5. Keep external tool results separate from official result publication until reviewed by teachers/executives.

Suggested portal data models:

- `ExternalToolProvider`: issuer/client/deployment/JWKS/tool settings for LTI providers.
- `ExternalToolLink`: course/offering-level launch configuration.
- `ExternalToolLaunch`: audit record of launches by student/user.
- `ExternalToolResult`: score/result callback records.
- `InteractiveContentPackage`: uploaded H5P/IMS/SCORM package metadata.
- `InteractiveContentAttempt`: student attempt/progress record.

Implementation cautions:

- LTI needs careful signing, nonce/state validation, key rotation, and launch context enforcement.
- Do not build SCORM from scratch unless necessary. SCORM runtime and sequencing are deceptively deep.
- For H5P, prefer a maintained renderer/runtime integration rather than a custom partial implementation.
- Keep tool launch permissions tied to enrollment, teacher assignment, and course-offering publication.

### 6. Full Gradebook  - Implemented

Moodle has a flexible gradebook independent of any one activity.

Moodle source evidence reviewed:

- `public/lib/db/install.xml` defines `grade_outcomes`, `grade_outcomes_courses`, `grade_categories`, `grade_items`, `grade_grades`, grade history tables, import staging tables, `grade_letters`, and `grade_settings`.
- `public/grade/lib.php`, `public/grade/querylib.php`, and `public/lib/grade/*` implement gradebook logic.
- `public/grade/report/*` implements gradebook reports.
- `public/grade/import/*` and `public/grade/export/*` support grade movement.
- `public/grade/grading/*` supports advanced grading workflows.

Moodle feature coverage includes:

- Grade categories
- Grade items
- Grade history
- Scales
- Outcomes
- Grade import/export
- Per-user and grader views

Portal gap:

- Portal has academic results and transcripts, but not a flexible gradebook across arbitrary activities.
- Portal result flows are official academic-record workflows: teacher result drafts/submissions, executive review/publication, GPA, transcript, exam slip, result PDFs, and exports.
- That is not the same as a teacher-maintained formative gradebook that can collect grades from assignments, quizzes, discussions, attendance, and external tools.

Suggested portal roadmap:

1. Add a course-offering gradebook that is separate from official results.
2. Add `GradebookCategory`, `GradebookItem`, `GradebookGrade`, `GradebookGradeHistory`, and `GradebookScale`.
3. Let assignments and future quizzes publish grade items into the gradebook.
4. Add teacher views for grade entry, grade override, feedback, import/export, and grade history.
5. Add student views for released formative grades only.
6. Add category weighting and aggregation after the basic gradebook is reliable.
7. Add an explicit "send to result draft" action that copies reviewed totals into the existing result workflow.

Implementation cautions:

- Keep formative gradebook grades separate from official transcript/result records.
- Preserve auditability: grade overrides, recalculations, imports, and final result mapping should be logged.
- Do not let every activity write official results directly. Route official grades through existing teacher/executive review.
- Avoid building full Moodle-scale gradebook complexity until the portal has quizzes and more activity types producing grades.

### 7. Completion and Conditional Availability

Moodle supports activity completion, course completion, and conditional availability.

Moodle source evidence reviewed:

- `public/lib/db/install.xml` defines `course_completion_aggr_methd`, `course_completion_criteria`, `course_completion_crit_compl`, `course_completions`, `course_modules_completion`, and `course_completion_defaults`.
- `public/completion/classes/api.php`, `manager.php`, and `progress.php` implement completion APIs and progress logic.
- `public/completion/criteria/*` defines criteria such as activity, course, date, duration, grade, role, self-completion, and unenrolment.
- `public/availability/classes/*` implements availability trees, conditions, capability checks, module/section info, and result evaluation.
- `public/availability/condition/*` includes completion, date, grade, group, grouping, and profile conditions.

Moodle feature coverage includes:

- Activity completion
- Course completion
- Conditional access by date, grade, group, grouping, profile, completion

Portal gap:

- No general completion/availability engine for course activities.
- Portal tracks enrollment, attendance, assignments, course resources, and results, but does not have a reusable rule engine for "activity complete" or "unlock this item when conditions are met."

Suggested portal roadmap:

1. Add `ActivityCompletionRule`, `StudentActivityCompletion`, and `ActivityAvailabilityRule`.
2. Start with manual completion and simple automatic completion for viewed resource, submitted assignment, submitted quiz, and attended session.
3. Add availability conditions for date/time, enrolled group, prior activity completion, and minimum grade.
4. Add teacher UI to set completion and unlock rules per activity.
5. Add student progress indicators on course detail pages.
6. Add course completion aggregation only after activity completion data is reliable.

Implementation cautions:

- Avoid overbuilding this until quizzes/forums/resources have enough meaningful activities to unlock.
- Keep rule evaluation backend-side so hidden activities cannot be accessed through direct API calls.
- Cache carefully but invalidate on enrollment, grade, completion, and schedule changes.

### 8. Competencies, Learning Plans, and Badges

Moodle supports outcomes-oriented learning structures and badge issuing.

Moodle source evidence reviewed:

- `public/lib/db/install.xml` defines competency tables: `competency`, `competency_framework`, `competency_coursecomp`, `competency_plan`, `competency_template`, `competency_usercomp`, `competency_usercompcourse`, `competency_usercompplan`, `competency_evidence`, `competency_userevidence`, and module competency links.
- `public/competency/classes/*` implements frameworks, plans, templates, evidence, related competencies, user competencies, and course/module competency mappings.
- `public/admin/tool/lp/*` exposes learning-plan UI and services.
- `public/lib/db/install.xml` defines badge tables: `badge`, `badge_criteria`, `badge_issued`, backpack, endorsement, alignment, and related-badge tables.
- `public/badges/*` implements badge issuing, criteria, recipients, backpack connection, endorsements, alignments, and external badge metadata.

Moodle feature coverage includes:

- Competency frameworks
- Learning plans
- Evidence
- Badges and badge backpacks

Portal gap:

- No competency/badge/learning-plan system.
- Portal has programme/course structures and result records, but not explicit learning outcomes, evidence mapping, learner plans, or badge issuance.

Suggested portal roadmap:

1. Start with `ProgrammeOutcome`, `CourseOutcome`, and `CourseOutcomeMapping` tied to courses and offerings.
2. Add outcome mapping to assignments and future quizzes before building full learning plans.
3. Add `StudentOutcomeEvidence` from graded activities, manual evidence, or result records.
4. Add executive reports for outcome coverage and attainment.
5. Add `LearningPlan` only if advisors need individual student plans.
6. Add badges only when AIU has a real policy for issuing micro-credentials or student-life achievements.

Implementation cautions:

- Do not add badges as decoration. They need issuer policy, criteria, expiry, revocation, and evidence.
- Keep outcome evidence auditable and tied to the original assessment artifact.
- Competency mapping can become administrative overhead; start with programme/course outcomes if accreditation needs it.

### 9. Pluggable Authentication and Enrolment Ecosystem

Moodle has plugin ecosystems for authentication and enrolment.

Moodle source evidence reviewed:

- `public/auth/*` contains auth plugins: database, email, LDAP, LTI, manual, no-login, none, OAuth2, Shibboleth, and webservice.
- `public/auth/classes/external.php` and `public/auth/classes/validate_user.php` support auth APIs and validation.
- `public/enrol/*` contains enrolment plugins: category, cohort, database, fee, flatfile, guest, IMS Enterprise, LDAP, LTI, manual, meta, PayPal, and self.
- `public/enrol/externallib.php` exposes enrolment web services.
- `public/lib/db/install.xml` includes external service/token tables used by integrations.

Moodle feature coverage includes:

- LDAP
- OAuth2
- Shibboleth
- External database auth
- LTI auth
- Cohort sync
- Flat-file enrolments
- IMS Enterprise
- Guest/self enrolment
- PayPal enrolment

Portal gap:

- Portal uses custom auth and registration, not pluggable external identity/enrolment providers.
- Portal auth is institution-specific: JWT login, applicant auth, email verification, forgot/reset password, profile, role redirects, and admin-created accounts.
- Portal course registration is also institution-specific: registration requests, rules, executive approval, enrollment, and timetable conflict checks.

Suggested portal roadmap:

1. Add SSO/OAuth2 only if AIU has a real identity provider.
2. Add LDAP/SAML/Shibboleth only if campus IT requires it.
3. Add bulk user import/export and account reconciliation before a plugin-style auth framework.
4. Keep applicant login separate from staff/student login unless policy changes.
5. Keep student course registration approval separate from Moodle-style self-enrolment.
6. Add cohort/batch assignment tools only if executives/admins need bulk course assignment.

Implementation cautions:

- Do not weaken role/account policy while adding SSO. External identity should prove identity; portal backend should still own role authorization.
- Enrolment plugins are not a drop-in fit because the portal has academic registration rules and executive approval.
- Treat external identities, student IDs, applicant IDs, and staff records as separate reconciliation concerns.

### 10. Repository and Portfolio Integrations

Moodle has pluggable repository/file-picker integrations and portfolio export targets.

Moodle source evidence reviewed:

- `public/repository/*` contains repository plugins: area files, content bank, course files, Dropbox, EQUELLA, filesystem, Flickr, Flickr public, Google Docs, local, Merlot, Nextcloud, OneDrive, recent, S3, upload, URL, user/private files, WebDAV, Wikimedia, and YouTube.
- `public/repository/lib.php`, `filepicker.php`, and `repository_ajax.php` implement the repository picker flow.
- `public/lib/db/install.xml` defines repository tables: `repository`, `repository_instances`, and `repository_instance_config`.
- `public/portfolio/*` contains portfolio plugins for download, Flickr, and Google Docs.
- `public/lib/db/install.xml` defines portfolio tables: `portfolio_instance`, `portfolio_instance_config`, `portfolio_instance_user`, `portfolio_log`, and `portfolio_tempdata`.

Moodle repository providers include:

- Google Drive
- OneDrive
- Dropbox
- Nextcloud
- S3
- WebDAV
- YouTube
- Wikimedia

Portal gap:

- Portal file handling is workflow-specific.
- Portal stores files for specific workflows such as applicant documents, course resources, assignment attachments, study guides, library assets, generated PDFs, public content, and reports.
- It does not have a shared cloud-file picker or portfolio export layer.

Suggested portal roadmap:

1. Keep direct upload as the default because it is simpler and matches current portal workflows.
2. Add an internal `ManagedFile` abstraction only if duplicate file logic grows across course resources, assignments, applicant documents, and reports.
3. Add Google Drive/OneDrive picker support only if teachers/admins repeatedly need cloud-file selection.
4. Add S3-compatible storage backend only if deployment/storage requirements demand it.
5. Add portfolio export only if students need to export coursework/evidence outside the portal.

Implementation cautions:

- External repositories add OAuth scopes, token storage, revocation, file-permission drift, and data-retention concerns.
- Do not expose private applicant, result, finance, or library records through a general file picker.
- Keep per-workflow file authorization even if a shared file abstraction is added.

### 11. Backup, Restore, Recycle Bin, and Plugin Installer

Moodle has course backup/restore infrastructure, recycle bins, and plugin installation tooling.

Moodle source evidence reviewed:

- `public/backup/*` implements backup and restore controllers, course/activity/section/block tasks, import/copy flows, logs, and Common Cartridge conversion.
- `public/lib/db/install.xml` defines `backup_courses`, `backup_controllers`, and `backup_logs`.
- Activity modules include `backup/moodle2/*` implementations, for example forum, quiz, assignment, SCORM, H5P, LTI, and workshop.
- `public/admin/tool/recyclebin/*` implements course and category recycle bins, with tables `tool_recyclebin_course` and `tool_recyclebin_category`.
- `public/admin/tool/installaddon/*` implements plugin installation from zip, permission checks, and installer tests.

Moodle feature coverage includes:

- Course backups
- Backup reports
- Restore infrastructure
- Recycle bin
- Plugin installer
- XMLDB editor

Portal gap:

- No Moodle-style course backup/restore/plugin lifecycle.
- Portal has generated exports and reports, but not portable course/offering backups, restore previews, recycle-bin recovery, or a plugin installer.

Suggested portal roadmap:

1. Add export/import for course content before full backup/restore.
2. Start with `CourseOfferingExport` for sections, resources, announcements, study guide metadata, assignments, and future quizzes.
3. Add import preview with validation before writing into a target course offering.
4. Add soft-delete/recycle-bin behavior for course content, discussions, assignments, and quizzes before building full restore.
5. Keep plugin installation out of scope unless the portal becomes a platform product for third-party extensions.

Implementation cautions:

- Full backup/restore must preserve ownership, files, dates, grades, attempts, and permissions. It is large and easy to get wrong.
- Do not allow restore to overwrite official results, transcripts, finance records, or audit logs.
- Plugin installers are high-risk in a custom Django portal; prefer normal deployment/release processes.

### 12. Advanced Reporting and Analytics  - Implemented

Moodle has fixed reports, report builder, analytics models, predictions, and insights.

Moodle source evidence reviewed:

- `public/report/*` includes backups, competency, completion, config log, course overview, event list, infected files, insights, log, live log, outline, participation, performance, progress, question instances, security, stats, status, theme usage, and user sessions.
- `public/reportbuilder/*` implements report definitions, columns, filters, audiences, downloads, and custom report editing.
- `public/lib/db/install.xml` defines report-builder tables: `reportbuilder_report`, `reportbuilder_column`, `reportbuilder_filter`, `reportbuilder_user_filter`, `reportbuilder_audience`, and `reportbuilder_schedule`.
- `public/analytics/classes/*` implements models, analysables, analysis, indicators, predictions, actions, dataset management, classifiers, regressors, and insights.
- `public/lib/db/install.xml` defines analytics tables: `analytics_models`, `analytics_models_log`, `analytics_predictions`, `analytics_train_samples`, `analytics_predict_samples`, `analytics_used_files`, `analytics_indicator_calc`, `analytics_prediction_actions`, and `analytics_used_analysables`.

Moodle feature coverage includes:

- Report builder
- Analytics models
- Predictions
- Insights
- Security/performance/status reports
- Activity participation/progress reports

Portal gap:

- Portal has custom reports/exports/statistics but not a general report builder or predictive analytics layer.
- Portal reporting is institution-specific across academics, students, teachers, operations, public content, finance, audit logs, and statistics. It does not expose a configurable report-builder layer or Moodle-like learning analytics predictions.

Suggested portal roadmap:

1. Improve existing report filters, saved views, exports, and scheduled delivery before building a general report builder.
2. Add `SavedReportDefinition`, `ReportColumn`, `ReportFilter`, `ReportAudience`, and `ScheduledReport` only after report requirements repeat across roles.
3. Add role-aware report permissions so users can only report on records they are allowed to see.
4. Add analytics snapshots for stable metrics such as attendance risk, assignment overdue rate, course registration bottlenecks, and support ticket aging.
5. Add predictive analytics only after there is enough clean historical data and a clear intervention workflow.

Implementation cautions:

- Report builder is a data-exposure risk. Permission filters must be enforced in the backend query layer, not just in the UI.
- Do not train/publish predictions without explainability, staff workflow, and false-positive handling.
- Keep operational reports separate from official academic records unless explicitly reviewed.

### 13. Privacy, Policy, Accessibility, MFA, User Tours

Moodle includes mature governance and user-experience admin tools.

Moodle source evidence reviewed:

- `public/admin/tool/dataprivacy/*` implements data requests, data registry, purposes, categories, expired context handling, metadata registry, and privacy APIs.
- `public/admin/tool/dataprivacy/db/install.xml` defines request, purpose, category, context, context list, and request-context tables.
- `public/admin/tool/policy/*` implements policy documents, versions, acceptance tracking, and policy services.
- `public/admin/tool/policy/db/install.xml` defines `tool_policy`, `tool_policy_versions`, and `tool_policy_acceptances`.
- `public/admin/tool/brickfield/*` implements accessibility checks, content analysis, scheduling, results, errors, and summaries.
- `public/admin/tool/brickfield/db/install.xml` defines accessibility check, process, area, content, result, error, summary, cache, and schedule tables.
- `public/admin/tool/mfa/*` implements MFA factor management, secrets, auth state, reset, reports, and settings.
- `public/admin/tool/mfa/db/install.xml` defines `tool_mfa`, `tool_mfa_secrets`, and `tool_mfa_auth`.
- `public/admin/tool/usertours/*` implements tours, steps, targeting, cache, and configuration.

Moodle feature coverage includes:

- Data privacy request tooling
- Policy acceptance tooling
- Accessibility toolkit
- MFA tool
- User tours
- Capability overview

Portal gap:

- Portal has route permissions and audit logs, but not these mature platform governance tools.
- Portal has authentication, role permissions, audit logs, and settings, but not formal data-subject request workflows, policy acceptance versions, accessibility scan dashboards, MFA factor management, or guided tours.

Suggested portal roadmap:

1. Add MFA first if production security policy requires it, starting with TOTP and recovery codes.
2. Add `PolicyDocument`, `PolicyVersion`, and `PolicyAcceptance` for terms, privacy notices, and student/staff policies.
3. Add data export/delete request tracking only if compliance obligations require it.
4. Add accessibility checks to CI and page-level audits before building an in-app accessibility dashboard.
5. Add lightweight user tours only for complex workflows such as registration, result submission, public content management, and finance setup.

Implementation cautions:

- MFA must include recovery and admin reset flows, or it can lock out legitimate users.
- Policy acceptance should be versioned; accepting an old version should not count for a new one.
- Data deletion is complicated in a university portal because academic, finance, audit, and legal records often cannot be deleted outright.
- Accessibility tooling should first prevent regressions in the frontend build pipeline.

### 14. Global Search and Solr - Implemented

Moodle has a global search framework with pluggable search engines.

Moodle source evidence reviewed:

- `public/search/classes/*` implements search areas, documents, document factory, engines, manager, external API, and indexing helpers.
- `public/search/cli/indexer.php` provides CLI indexing.
- `public/search/engine/simpledb` and `public/search/engine/solr` provide search engines.
- `public/lib/db/install.xml` defines `search_index_requests`.
- Search areas exist for course content, messages, users, and other Moodle components under paths such as `course/classes/search`, `message/classes/search`, and `user/classes/search`.

Moodle feature coverage includes:

- Simple DB search
- Solr search
- Search blocks and APIs

Portal gap:

- No equivalent global search engine across courses, resources, public content, library, and records.
- Portal has many searchable domains, but search is page/workflow-specific rather than one role-aware index.

Suggested portal roadmap:

1. Add a role-aware global search endpoint with strict domain filters.
2. Start with simple PostgreSQL search for public content, courses, course resources, assignments, library books, helpdesk tickets, and venue records.
3. Add an index table such as `SearchDocument` with source model, object ID, title, summary, keywords, visibility scope, and last indexed time.
4. Add background indexing through existing Celery/Redis if content volume grows.
5. Move to OpenSearch/Solr only if database search is too slow or ranking requirements become complex.

Implementation cautions:

- Search must never bypass role permissions. Index results should be filtered by the user's actual backend access.
- Separate public search from authenticated role search.
- Do not index sensitive values from applicant documents, finance records, private results, audit logs, or helpdesk details unless there is a clear permission model.

### 15. Moodle Mobile and External Web Service Ecosystem

Moodle has a formal external service and mobile ecosystem.

Moodle source evidence reviewed:

- `public/lib/db/install.xml` defines `external_services`, `external_functions`, `external_services_functions`, `external_services_users`, and `external_tokens`.
- `public/webservice/*` implements external token UI, uploads, documentation, REST and SOAP protocols, simple servers, and web-service helpers.
- `public/webservice/rest/*` and `public/webservice/soap/*` provide protocol-specific servers.
- `public/admin/webservice/*` provides web-service administration.
- `public/admin/tool/mobile/*` implements mobile app APIs, autologin, launch/logout flows, manifest, settings, subscription, tasks, services, and external functions.
- `public/auth/webservice` provides web-service authentication.
- Many Moodle modules include `db/services.php` files that register external functions.

Moodle feature coverage includes:

- REST/SOAP protocols
- External function registry
- Mobile app tools
- Token-based web services

Portal gap:

- Portal APIs serve the first-party Next.js frontend but are not packaged as a Moodle-like third-party API ecosystem.
- Portal already exposes DRF endpoints for the Next.js app, but it does not have external application registration, scoped API tokens, versioned public API contracts, mobile-specific service bundles, or developer documentation comparable to Moodle's service registry.

Suggested portal roadmap:

1. Stabilize DRF API contracts and add OpenAPI documentation first.
2. Add API versioning before third-party clients depend on the portal.
3. Add `ExternalApplication`, `ApiToken`, `ApiScope`, `ApiTokenAudit`, and rate limiting if external clients are approved.
4. Add mobile-oriented endpoints only for workflows that need mobile UX: notifications, timetable, attendance, assignments, library, helpdesk, payments, and profile.
5. Add OAuth2/OIDC client credentials or authorization-code flow only if there are real third-party integrations.
6. Keep admin controls for token revocation, scope changes, client status, and usage logs.

Implementation cautions:

- Do not expose all internal DRF endpoints as public APIs. Create a supported external API surface.
- Use scoped tokens, rate limits, audit logs, and least-privilege permissions.
- Mobile APIs must preserve the same backend policy as the web frontend.
- Keep third-party/mobile access separate from staff impersonation or internal admin actions.

## AIU Portal Functionality Not Present as Moodle Core Workflows

The portal has several workflows that Moodle does not provide as core LMS features.

### 1. Admissions and Applicants

Portal has:

- Applicant registration/login
- Application form
- Application status
- Document upload/review
- Scholarship review
- Staff admission review

Moodle does not provide this as a native admissions pipeline.

### 2. Public University CMS

Portal has:

- Public website pages
- News
- Events
- Announcements
- Official links
- Public directories
- Academic organization pages

Moodle can publish pages, but it is not structured as a university public website CMS.

### 3. Executive Academic Administration

Portal has:

- Executive dashboards
- Organization management
- Course offering
- Schedule management
- Result review/publication
- Evaluation management
- Executive reports/statistics

Moodle manager/admin roles do not map exactly to this institutional executive workflow.

### 4. Library Operations

Portal has:

- Books/copies/shelves
- Loans
- Borrow requests
- Laptop lending
- Library room reservations
- Acquisition requests
- Inventory audits
- Library fines

Moodle does not provide library circulation as core.

### 5. Canteen Operations

Portal has:

- Canteen accounts
- Allowances
- Bonuses
- Transactions
- Monthly initialization task

Moodle does not provide canteen operations as core.

### 6. Campus Venue and Hostel Management

Portal has:

- Venue booking
- Venue approvals
- Booking cancellation
- Buildings
- Hostels
- Hostel rooms

Moodle does not provide campus venue/hostel operations as core.

### 7. ICT Helpdesk

Portal has:

- Student helpdesk tickets
- Technician dashboard
- Technician ticket updates

Moodle does not provide ICT helpdesk as core.

### 8. Finance Subscriptions and Fines

Portal has:

- Accountant role
- Subscription plans
- Payment attempts
- Subscription cards
- Fines
- Fine payment/deduction
- Payment webhooks

Moodle has payment infrastructure, but not this specific campus finance workflow.

### 9. Elections

Portal has:

- Elections
- Candidates
- Voting
- Result snapshots

Moodle does not provide student elections as core.

### 10. Leave, Emergency Contacts, Warden Schedule

Portal has:

- Student leave applications
- Teacher leave approvals
- Emergency contacts
- Warden schedule

Moodle does not provide these student affairs workflows as core.

## Functional Coverage Matrix

Legend:

- Strong: first-class or mature implementation in the reviewed source
- Partial: related functionality exists, but not equivalent
- Missing: no clear equivalent found in the reviewed source

| Area | Moodle | AIU Portal | Notes |
| --- | --- | --- | --- |
| Course shells | Strong | Strong | Moodle LMS-native; portal offering/schedule-native |
| Course categories/organization | Strong | Strong | Portal uses schools/centres/departments/programmes |
| Course sections | Strong | Partial | Portal has course sections/resources, less LMS-module depth |
| Assignments | Strong | Strong | Both support submissions/feedback/rubrics |
| Assignment PDF annotation | Strong | Missing | Moodle has editpdf feedback |
| Online quiz engine | Strong | Missing | Major Moodle-only capability |
| Question bank | Strong | Missing | Major Moodle-only capability |
| Question types | Strong | Missing | Major Moodle-only capability |
| Gradebook | Strong | Partial | Portal has official results, not flexible gradebook |
| Transcripts/exam slips | Partial | Strong | Portal-specific academic records |
| Course registration approval | Partial | Strong | Moodle enrolment differs |
| Enrolment plugins | Strong | Missing | Moodle plugin ecosystem |
| Attendance QR/code | Partial/plugin-dependent | Strong | Portal first-class workflow |
| Forums | Strong | Missing | Moodle activity module |
| Wiki/glossary/book/lesson | Strong | Missing | Moodle activity modules |
| SCORM/IMS/H5P/LTI | Strong | Missing | Moodle package/tool ecosystem |
| Completion tracking | Strong | Partial | Portal has progress-like records, not rule engine |
| Conditional availability | Strong | Missing | Moodle availability plugins |
| Competencies | Strong | Missing | Moodle competency subsystem |
| Badges | Strong | Missing | Moodle badge subsystem |
| Calendar | Strong | Strong | Both have calendar/timetable concepts |
| Notifications | Strong | Strong | Both support notification workflows |
| Messaging | Strong | Partial | Portal notifications, not Moodle-style messaging |
| Public website CMS | Partial | Strong | Portal is stronger |
| Admissions | Missing | Strong | Portal-only domain |
| Library circulation | Missing | Strong | Portal-only domain |
| Canteen | Missing | Strong | Portal-only domain |
| Venue booking | Missing | Strong | Portal-only domain |
| Hostel | Missing | Strong | Portal-only domain |
| ICT helpdesk | Missing | Strong | Portal-only domain |
| Student elections | Missing | Strong | Portal-only domain |
| Finance subscriptions/fines | Partial | Strong | Portal-specific business workflow |
| Payment gateway | Strong | Strong | Moodle PayPal; portal ToyyibPay/DuitNow-compatible |
| Reports | Strong | Strong | Moodle LMS reports; portal institutional reports |
| Report builder | Strong | Missing | Moodle-only platform tool |
| Analytics/insights | Strong | Partial | Portal statistics/reports, not predictive analytics |
| Audit logs | Strong | Strong | Both have log/audit concepts |
| Backup/restore | Strong | Missing | Moodle-only platform tool |
| Recycle bin | Strong | Missing | Moodle admin tool |
| Plugin installer | Strong | Missing | Moodle platform capability |
| Web services registry | Strong | Partial | Portal has DRF APIs, not Moodle service registry |
| Mobile app tooling | Strong | Missing | Moodle app tooling |
| External repositories | Strong | Missing | Moodle repository plugins |
| AI provider framework | Strong | Partial | Portal chatbot/Ollama settings only |
| SMS gateways | Strong | Missing | Moodle SMS plugins |
| MFA | Strong | Missing | Moodle admin tool |
| Data privacy tools | Strong | Missing | Moodle admin tool |
| Accessibility toolkit | Strong | Missing | Moodle admin tool |

## Recommended Portal Roadmap Based on Moodle Gap Analysis

This roadmap assumes AIU wants to move the portal closer to Moodle's LMS depth while preserving the portal's university operations strengths.

### Phase 1: High-Value LMS Gaps

1. Add course discussion forums.
2. Add a basic quiz engine.
3. Add a question bank with a small set of question types.
4. Add a course-level gradebook that stays separate from official results at first.
5. Add activity completion tracking.

Why this phase first:

- These are the largest practical learning gaps.
- They directly improve teacher/student course delivery.
- They can integrate with existing course offerings, assignments, notifications, and results later.

### Phase 2: Content and Activity Expansion

1. Add lesson/page/book-style content modules.
2. Add poll/choice activities.
3. Add glossary or shared course terminology.
4. Add H5P support if interactive content is important.
5. Add LTI support if external tools are required.

Why this phase second:

- It builds on a generic course activity model.
- It avoids overcommitting to complex standards before the core LMS workflow is mature.

### Phase 3: Progress, Rules, and Learning Outcomes

1. Add activity completion rules.
2. Add conditional availability rules.
3. Add programme/course outcomes.
4. Add competency mapping if required.
5. Add badges only if they support a real academic/student-life policy.

Why this phase third:

- Completion and outcome systems become useful once there are enough activities to track.

### Phase 4: Platform Integrations

1. Add OAuth2/SSO if AIU has an identity provider.
2. Add OpenAPI documentation for portal APIs.
3. Add cloud file repository integrations only if staff request them.
4. Add role-aware global search.
5. Add SMS gateway support only if notification policy requires it.

Why this phase fourth:

- These are valuable but should follow stabilization of core learning features.

### Phase 5: Governance and Operations Hardening

1. Add MFA.
2. Add policy acceptance tracking.
3. Add privacy/data export/delete request workflows if compliance requires them.
4. Add accessibility checks to CI.
5. Add richer report definitions and scheduled report delivery.

Why this phase fifth:

- These features support production governance and compliance after the product surface stabilizes.

## Implementation Cautions

Do not copy Moodle's architecture directly into the portal. Moodle is a plugin platform written around its own PHP subsystem. AIU Portal is a Django/DRF and Next.js product with role-specific workflows. The right strategy is to borrow Moodle's product concepts, not its implementation shape.

Recommended portal design principles:

- Keep official transcripts/results separate from formative gradebook activity.
- Keep course registration separate from LMS enrolment mechanics unless policy changes.
- Add LMS features through portal-native Django services and DRF endpoints.
- Reuse existing role dashboards and course pages.
- Keep backend enforcement for academic rules.
- Avoid frontend-only policy checks.
- Avoid building a plugin system unless there is a real need for third-party extension.
- Start with a small, stable course activity abstraction before adding many activity types.

## Bottom Line

Moodle is substantially ahead as a learning management system. It has mature quiz, question bank, gradebook, course activity, completion, competency, repository, reporting, web service, backup, privacy, accessibility, and plugin systems.

AIU Portal is substantially broader as a university portal. It handles admissions, public content, academic administration, student registration, timetables, results publication, library, canteen, venue booking, hostels, helpdesk, finance, fines, subscriptions, elections, leave, emergency contacts, and role-specific dashboards.

The best future direction is not to replace the portal with Moodle-like structure. The best direction is to selectively add Moodle-inspired LMS depth to the portal's existing role-based university operations foundation.
