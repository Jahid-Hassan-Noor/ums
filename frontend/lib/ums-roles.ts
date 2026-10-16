export const UMS_ROLES = ["applicant", "student", "teacher", "executive", "librarian", "caterer", "technician", "accountant", "hr", "admin"] as const

export type UserRole = (typeof UMS_ROLES)[number]

export type UmsIconKey =
  | "academic"
  | "assignments"
  | "attendance"
  | "calendar"
  | "courses"
  | "dashboard"
  | "elections"
  | "hostels"
  | "imports"
  | "leave"
  | "notifications"
  | "palette"
  | "records"
  | "results"
  | "semesters"
  | "settings"
  | "statistics"
  | "users"

export type UmsNavItem = {
  title: string
  url: string
  icon: UmsIconKey
  description?: string
  items?: Array<{
    title: string
    url: string
    description?: string
  }>
}

export type UmsMetric = {
  title: string
  value: string
  subtitle: string
  icon: UmsIconKey
}

export type UmsZone = {
  role: UserRole
  label: string
  shortLabel: string
  basePath: string
  dashboardPath: string
  headline: string
  description: string
  scope: string
  metrics: UmsMetric[]
  priorities: string[]
  navMain: UmsNavItem[]
  navSecondary: UmsNavItem[]
}

const sharedSecondaryNav: UmsNavItem[] = [
  {
    title: "Profile",
    url: "/profile",
    icon: "settings",
    description: "Review your account details and preferences.",
  },
]

export const ROLE_ZONES: Record<UserRole, UmsZone> = {
  applicant: {
    role: "applicant",
    label: "Applicant",
    shortLabel: "Applicant",
    basePath: "/apply",
    dashboardPath: "/apply/dashboard",
    headline: "Application Dashboard",
    description:
      "A guided admissions workspace for programme selection, scholarship details, document upload, and application status.",
    scope: "Own admission and scholarship applications only.",
    metrics: [
      {
        title: "Applications",
        value: "0",
        subtitle: "Draft and submitted applications appear here.",
        icon: "records",
      },
      {
        title: "Scholarship",
        value: "Optional",
        subtitle: "Scholarship review is linked to the admission application.",
        icon: "academic",
      },
      {
        title: "Documents",
        value: "0",
        subtitle: "Uploaded documents are reviewed by admission staff.",
        icon: "imports",
      },
    ],
    priorities: [
      "Create an applicant account and keep one active application per intake.",
      "Complete programme selection, personal details, academic background, scholarship details, documents, and statement of truth.",
      "Track admission and scholarship decisions after submission.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/apply/dashboard",
        icon: "dashboard",
        description: "Application overview, next actions, and status summary.",
      },
      {
        title: "Statistics",
        url: "/apply/statistics",
        icon: "statistics",
        description: "Application progress, document activity, and status analytics.",
      },
      {
        title: "Application Form",
        url: "/apply/application",
        icon: "records",
        description: "Complete the six-section admission application.",
      },
      {
        title: "Documents",
        url: "/apply/documents",
        icon: "imports",
        description: "Upload passport, transcript, certificate, scholarship, and reference files.",
      },
      {
        title: "Status",
        url: "/apply/status",
        icon: "notifications",
        description: "Review submission status and staff updates.",
      },
      {
        title: "Notifications",
        url: "/apply/notifications",
        icon: "notifications",
        description: "Review application alerts and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  student: {
    role: "student",
    label: "Student",
    shortLabel: "Student",
    basePath: "/student",
    dashboardPath: "/student/dashboard",
    headline: "Student Dashboard",
    description:
      "A focused student workspace for registration, attendance, assignments, published results, and active elections.",
    scope: "Own academic record and active student workflows only.",
    metrics: [
      {
        title: "Registered Courses",
        value: "0",
        subtitle: "Backend data will populate current enrollments.",
        icon: "courses",
      },
      {
        title: "Attendance",
        value: "0%",
        subtitle: "Visible once attendance records are connected.",
        icon: "attendance",
      },
      {
        title: "Open Assignments",
        value: "0",
        subtitle: "Student submissions will appear here.",
        icon: "assignments",
      },
    ],
    priorities: [
      "Register directly for eligible offered courses during admin-defined registration periods.",
      "View attendance and assignment status for enrolled course offerings.",
      "View only executive-published results and vote once in active elections.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/student/dashboard",
        icon: "dashboard",
        description: "Student overview and academic activity summary.",
      },
      {
        title: "Statistics",
        url: "/student/statistics",
        icon: "statistics",
        description: "Attendance, assignments, registration, canteen, and support analytics.",
      },
      {
        title: "Courses",
        url: "/student/courses",
        icon: "courses",
        items: [
          {
            title: "Course Registration",
            url: "/student/courses/register",
            description: "Register directly for eligible offered courses during the open period.",
          },
          {
            title: "Current Courses",
            url: "/student/courses/current",
            description: "View enrolled courses for the active semester.",
          },
          {
            title: "Completed Courses",
            url: "/student/courses/completed",
            description: "Review courses completed in previous semesters.",
          },
        ],
      },
      {
        title: "Course Evaluations",
        url: "/student/evaluations",
        icon: "records",
        description: "Complete required course evaluation feedback for current courses.",
      },
      {
        title: "Schedule",
        url: "/student/timetable",
        icon: "calendar",
        description: "View today's and weekly schedule for classes and activities.",
        items: [
          {
            title: "Today's schedule",
            url: "/student/timetable/today",
            description: "See today's class blocks and schedule items.",
          },
          {
            title: "Weekly schedule",
            url: "/student/timetable/weekly",
            description: "Review the full weekly class schedule.",
          },
        ],
      },
      {
        title: "Calendar",
        url: "/student/calendar",
        icon: "calendar",
        description: "Combine classes, assignments, exams, leave, and events.",
      },
      {
        title: "Venue Bookings",
        url: "/student/venue-bookings",
        icon: "calendar",
        description: "Request a university venue for an event or personal use.",
      },
      {
        title: "Service Desk",
        url: "/student/ict-helpdesk",
        icon: "records",
        description: "Submit support issues and track their progress.",
      },
      {
        title: "Attendance",
        url: "/student/attendance",
        icon: "attendance",
        description: "View your attendance records by course offering.",
        items: [
          {
            title: "Code Entry",
            url: "/student/attendance/code",
            description: "Submit an attendance code from class.",
          },
          {
            title: "Attendance Report",
            url: "/student/attendance/report",
            description: "Review attendance by course and semester.",
          },
          {
            title: "QR Attendance",
            url: "/student/attendance/qr",
            description: "Placeholder for QR-based attendance check-in.",
          },
        ],
      },
      {
        title: "Assignments",
        url: "/student/assignments",
        icon: "assignments",
        description: "Submit assignments and track submission status.",
      },
      {
        title: "Quizzes",
        url: "/student/quizzes",
        icon: "assignments",
        description: "Take online quizzes and review submitted attempts.",
      },
      {
        title: "Gradebook",
        url: "/student/gradebook",
        icon: "results",
        description: "Review released formative grades for current course offerings.",
      },
      {
        title: "Registration",
        url: "/student/registration",
        icon: "courses",
        description: "Browse eligible offered courses, register, and view history.",
        items: [
          {
            title: "Offered Courses",
            url: "/student/registration/offered-courses",
            description: "Browse courses available in the registration period.",
          },
          {
            title: "My Registrations",
            url: "/student/registration/requests",
            description: "Review your current semester registrations.",
          },
          {
            title: "History",
            url: "/student/registration/history",
            description: "Review previous registration records.",
          },
        ],
      },
      {
        title: "Results",
        url: "/student/results",
        icon: "results",
        description: "View results after executive publication.",
        items: [
          {
            title: "Semester Results",
            url: "/student/results/semester",
            description: "Filter published completed-semester results or view all published results together.",
          },
          {
            title: "Transcript",
            url: "/student/results/transcript",
            description: "Review structured transcript records.",
          },
          {
            title: "Course Works",
            url: "/student/results/course-works",
            description: "View current-semester course work marks published by teachers.",
          },
          {
            title: "Exam Slip",
            url: "/student/results/exam-slip",
            description: "Download the final exam slip after schedule publication.",
          },
        ],
      },
      {
        title: "Leave",
        url: "/student/leave",
        icon: "leave",
        description: "Apply for leave and track approval status.",
        items: [
          {
            title: "Leave Requests",
            url: "/student/leave",
            description: "Apply for leave and track approval status.",
          },
          {
            title: "Apply Leave",
            url: "/student/leave/apply",
            description: "Create a new student leave request.",
          },
          {
            title: "Leave History",
            url: "/student/leave/history",
            description: "Review previous leave applications.",
          },
        ],
      },
      {
        title: "Student Affairs",
        url: "/student/emergency-contacts",
        icon: "hostels",
        description: "Emergency contacts and warden schedule references.",
        items: [
          {
            title: "Emergency Contacts",
            url: "/student/emergency-contacts",
            description: "Privacy-aware emergency and support contacts.",
          },
          {
            title: "Warden Schedule",
            url: "/student/warden-schedule",
            description: "View warden or security schedule information.",
          },
        ],
      },
      {
        title: "Canteen",
        url: "/student/canteen",
        icon: "records",
        description: "Check your monthly meal allowance, available balance, and canteen purchases.",
      },
      {
        title: "Subscriptions",
        url: "/student/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Fines & Charges",
        url: "/student/fines",
        icon: "records",
        description: "View and pay outstanding fines or issued charges.",
      },
      {
        title: "Library",
        url: "/student/library/books",
        icon: "records",
        description: "Search books, browse available laptops or discussion rooms, and track requests.",
        items: [
          {
            title: "Books",
            url: "/student/library/books",
            description: "Search by title or author, borrow a copy, or request a new book.",
          },
          {
            title: "Laptops",
            url: "/student/library/laptops",
            description: "View and request laptops currently available to borrow.",
          },
          {
            title: "Discussion Rooms",
            url: "/student/library/rooms",
            description: "Reserve an available room and collect its key from library reception.",
          },
        ],
      },
      {
        title: "Elections",
        url: "/student/elections",
        icon: "elections",
        description: "Vote in active elections and view published outcomes.",
      },
      {
        title: "Notifications",
        url: "/student/notifications",
        icon: "notifications",
        description: "Review course, result, assignment, and election alerts.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  teacher: {
    role: "teacher",
    label: "Teacher",
    shortLabel: "Teacher",
    basePath: "/teacher",
    dashboardPath: "/teacher/dashboard",
    headline: "Teacher Dashboard",
    description:
      "A teaching workspace limited to assigned course offerings, attendance, assignments, and result submissions.",
    scope: "Assigned course offerings only.",
    metrics: [
      {
        title: "Assigned Courses",
        value: "0",
        subtitle: "Current teaching assignments will appear here.",
        icon: "courses",
      },
      {
        title: "Pending Results",
        value: "0",
        subtitle: "Result submissions awaiting completion.",
        icon: "results",
      },
      {
        title: "Assignments",
        value: "0",
        subtitle: "Active assignment workflows for assigned offerings.",
        icon: "assignments",
      },
    ],
    priorities: [
      "Record attendance for assigned course offerings.",
      "Create assignments and review student submissions for assigned offerings.",
      "Submit results for executive review without access to unrelated courses.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/teacher/dashboard",
        icon: "dashboard",
        description: "Teacher overview and assigned course activity.",
      },
      {
        title: "Statistics",
        url: "/teacher/statistics",
        icon: "statistics",
        description: "Teaching workload, attendance sessions, assignments, and result analytics.",
      },
      {
        title: "Courses",
        url: "/teacher/courses",
        icon: "courses",
        items: [
          {
            title: "Current Courses",
            url: "/teacher/courses/current",
            description: "Manage active course offerings assigned to you.",
          },
          {
            title: "Previous Courses",
            url: "/teacher/courses/previous",
            description: "Review completed teaching assignments.",
          },
        ],
      },
      {
        title: "Schedule",
        url: "/teacher/timetable",
        icon: "calendar",
        description: "View today's and weekly schedule for assigned teaching slots.",
        items: [
          {
            title: "Today's schedule",
            url: "/teacher/timetable/today",
            description: "See today's teaching slots and related items.",
          },
          {
            title: "Weekly schedule",
            url: "/teacher/timetable/weekly",
            description: "Review the full weekly teaching schedule.",
          },
        ],
      },
      {
        title: "Calendar",
        url: "/teacher/calendar",
        icon: "calendar",
        description: "Teaching calendar with classes, assignments, and deadlines.",
      },
      {
        title: "Venue Bookings",
        url: "/teacher/venue-bookings",
        icon: "calendar",
        description: "Request a university venue for an event or personal use.",
      },
      {
        title: "Attendance",
        url: "/teacher/attendance",
        icon: "attendance",
        description: "Manage class sessions and attendance records.",
        items: [
          {
            title: "Sessions",
            url: "/teacher/attendance/sessions",
            description: "View attendance sessions for assigned offerings.",
          },
          {
            title: "Create Session",
            url: "/teacher/attendance/create",
            description: "Generate class codes or QR attendance sessions.",
          },
          {
            title: "Corrections",
            url: "/teacher/attendance/corrections",
            description: "Review and correct attendance records.",
          },
        ],
      },
      {
        title: "Assignments",
        url: "/teacher/assignments",
        icon: "assignments",
        description: "Create assignments and review student submissions.",
        items: [
          {
            title: "All Assignments",
            url: "/teacher/assignments",
            description: "Manage assignment workflows for assigned courses.",
          },
          {
            title: "Create Assignment",
            url: "/teacher/assignments/create",
            description: "Draft and publish a new assignment.",
          },
          {
            title: "Submissions",
            url: "/teacher/assignments/submissions",
            description: "Review submitted work awaiting grading.",
          },
          {
            title: "Feedback Queue",
            url: "/teacher/assignments/feedback",
            description: "Track grading and feedback follow-up.",
          },
        ],
      },
      {
        title: "Quizzes",
        url: "/teacher/quizzes",
        icon: "assignments",
        description: "Create online quizzes, monitor attempts, and grade responses.",
        items: [
          {
            title: "All Quizzes",
            url: "/teacher/quizzes",
            description: "Create quizzes and review attempts.",
          },
          {
            title: "Question Bank",
            url: "/teacher/quizzes/question-bank",
            description: "Manage reusable questions, categories, and versions.",
          },
        ],
      },
      {
        title: "Gradebook",
        url: "/teacher/gradebook",
        icon: "results",
        description: "Maintain formative categories, items, grades, and course totals.",
      },
      {
        title: "Results",
        url: "/teacher/results",
        icon: "results",
        items: [
          {
            title: "Draft Results",
            url: "/teacher/results/draft",
            description: "Prepare result records before submission.",
          },
          {
            title: "Result Submission",
            url: "/teacher/results/submit",
            description: "Submit results for assigned course offerings.",
          },
          {
            title: "Completed Results",
            url: "/teacher/results/completed",
            description: "Review previously submitted result records.",
          },
        ],
      },
      {
        title: "Leave Requests",
        url: "/teacher/leave-requests",
        icon: "records",
        description: "Review student leave approvals for affected classes.",
      },
      {
        title: "Subscriptions",
        url: "/teacher/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Notifications",
        url: "/teacher/notifications",
        icon: "notifications",
        description: "Review teaching workflow alerts and result updates.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  executive: {
    role: "executive",
    label: "Executive",
    shortLabel: "Executive",
    basePath: "/executive",
    dashboardPath: "/executive/dashboard",
    headline: "Executive Dashboard",
    description:
      "A school or centre workspace for academic workflows, offered courses, result publication, and people management.",
    scope: "Assigned school or centre only.",
    metrics: [
      {
        title: "School Workflows",
        value: "0",
        subtitle: "Pending academic workflow items.",
        icon: "academic",
      },
      {
        title: "Results To Review",
        value: "0",
        subtitle: "Teacher submissions awaiting executive review.",
        icon: "results",
      },
      {
        title: "Calendar Items",
        value: "0",
        subtitle: "Upcoming academic calendar items to coordinate.",
        icon: "calendar",
      },
    ],
    priorities: [
      "Manage students, teachers, and course offerings for the assigned unit.",
      "Review teacher result submissions and publish approved semester results.",
      "Coordinate calendar events and notifications for the assigned unit.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/executive/dashboard",
        icon: "dashboard",
        description: "Executive overview for the assigned school or centre.",
      },
      {
        title: "Statistics",
        url: "/executive/statistics",
        icon: "statistics",
        description: "School or centre level operational statistics.",
      },
      {
        title: "Reports",
        url: "/executive/reports",
        icon: "records",
        description: "Export scoped student, teacher, and published final-result records.",
      },
      {
        title: "Manage",
        url: "/executive/manage",
        icon: "users",
        items: [
          {
            title: "Manage Students",
            url: "/executive/manage/students",
            description: "Maintain student records for your school or centre.",
          },
          {
            title: "Manage Teachers",
            url: "/executive/manage/teachers",
            description: "Maintain teacher records for your school or centre.",
          },
          {
            title: "Schedule",
            url: "/executive/manage/schedule",
            description: "Review class schedules and edit single-week classes.",
          },
        ],
      },
      {
        title: "Organisation",
        url: "/executive/organization",
        icon: "academic",
        description: "Maintain details and programmes for your assigned school or centre.",
        items: [
          {
            title: "Details",
            url: "/executive/organization",
            description: "Edit the public details for your assigned school or centre.",
          },
          {
            title: "Programmes",
            url: "/executive/programs",
            description: "Add and maintain programmes under your assigned school or centre.",
          },
        ],
      },
      {
        title: "Audit Log",
        url: "/executive/audit-log",
        icon: "settings",
        description: "Review executive changes within your assigned school or centre.",
      },
      {
        title: "Results",
        url: "/executive/results",
        icon: "results",
        items: [
          {
            title: "Semester Results",
            url: "/executive/results/semester",
            description: "Review and publish current semester results.",
          },
          {
            title: "Previous Results",
            url: "/executive/results/previous",
            description: "Review historical published result records.",
          },
          {
            title: "Review Results",
            url: "/executive/results/review",
            description: "Approve, reject, return, or publish teacher submissions.",
          },
          {
            title: "Publication",
            url: "/executive/results/publication",
            description: "Publish approved results after review.",
          },
        ],
      },
      {
        title: "Courses",
        url: "/executive/courses",
        icon: "courses",
        items: [
          {
            title: "Offered Courses",
            url: "/executive/courses/offered",
            description: "Manage courses offered for the current semester.",
          },
          {
            title: "Offer Courses",
            url: "/executive/courses/offer",
            description: "Create a new course offering.",
          },
          {
            title: "Add Courses",
            url: "/executive/courses/add",
            description: "Add a course under your assigned school or centre.",
          },
          {
            title: "All Courses",
            url: "/executive/courses/all",
            description: "Review available courses within your unit.",
          },
        ],
      },
      {
        title: "Course Evaluations",
        url: "/executive/evaluations",
        icon: "records",
        description: "Launch course evaluation surveys, monitor completion, and analyze responses.",
      },
      {
        title: "Calendar",
        url: "/executive/calendar",
        icon: "calendar",
        description: "Review academic events for the assigned school or centre.",
      },
      {
        title: "Subscriptions",
        url: "/executive/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Notifications",
        url: "/executive/notifications",
        icon: "notifications",
        description: "Review alerts for results, elections, and academic updates.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  librarian: {
    role: "librarian",
    label: "Librarian",
    shortLabel: "Librarian",
    basePath: "/librarian",
    dashboardPath: "/librarian/dashboard",
    headline: "Librarian Dashboard",
    description:
      "A library operations workspace for inventory, room reservations, borrowing requests, and timed allocations.",
    scope: "Configured library inventory and circulation ownership.",
    metrics: [
      {
        title: "Available Books",
        value: "0",
        subtitle: "Physical copies ready for student borrowing.",
        icon: "courses",
      },
      {
        title: "Pending Requests",
        value: "0",
        subtitle: "Student book, laptop, and room requests awaiting action.",
        icon: "records",
      },
      {
        title: "Active Loans",
        value: "0",
        subtitle: "Items currently assigned to students.",
        icon: "users",
      },
    ],
    priorities: [
      "Maintain book titles, physical copies, shelves, and precise shelf locations.",
      "Maintain university laptops available for student borrowing.",
      "Maintain reservable discussion rooms and their reception keys.",
      "Fulfil student requests or assign assets and rooms with due times and record returns.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/librarian/dashboard",
        icon: "dashboard",
        description: "Library inventory and circulation summary.",
      },
      {
        title: "Statistics",
        url: "/librarian/statistics",
        icon: "statistics",
        description: "Inventory, circulation, pending request, and overdue loan analytics.",
      },
      {
        title: "Books",
        url: "/librarian/books",
        icon: "courses",
        description: "Manage book titles, physical copies, shelves, and locations.",
      },
      {
        title: "Laptops",
        url: "/librarian/laptops",
        icon: "records",
        description: "Manage university laptops available for borrowing.",
      },
      {
        title: "Discussion Rooms",
        url: "/librarian/rooms",
        icon: "records",
        description: "Manage reservable rooms, capacities, facilities, keys, and standard time limits.",
      },
      {
        title: "Circulation",
        url: "/librarian/circulation",
        icon: "users",
        description: "Fulfil requests, allocate timed loans or room keys, and record returns.",
      },
      {
        title: "Settings",
        url: "/librarian/settings",
        icon: "settings",
        description: "Manage library service availability for students.",
      },
      {
        title: "Subscriptions",
        url: "/librarian/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Notifications",
        url: "/librarian/notifications",
        icon: "notifications",
        description: "Review library workflow alerts and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  caterer: {
    role: "caterer",
    label: "Caterer",
    shortLabel: "Caterer",
    basePath: "/caterer",
    dashboardPath: "/caterer/dashboard",
    headline: "Caterer Dashboard",
    description:
      "A simple canteen checkout workspace for student card lookup, bill deduction, and current-month transaction history.",
    scope: "Current-month canteen allowance and purchases for eligible active students.",
    metrics: [
      {
        title: "Eligible Students",
        value: "0",
        subtitle: "Active students with a current monthly allowance.",
        icon: "users",
      },
      {
        title: "Monthly Allocation",
        value: "0.00",
        subtitle: "Configured monthly allowance including extras.",
        icon: "records",
      },
      {
        title: "Transactions",
        value: "0",
        subtitle: "Canteen purchases completed this month.",
        icon: "statistics",
      },
    ],
    priorities: [
      "Search for the student using the ID printed on the student card.",
      "Confirm the bill amount and deduct it from the current monthly balance.",
      "Show the updated balance and all transactions for the current allowance month.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/caterer/dashboard",
        icon: "dashboard",
        description: "Student card lookup, bill deduction, and monthly transactions.",
      },
      {
        title: "Statistics",
        url: "/caterer/statistics",
        icon: "statistics",
        description: "Current-month canteen allowance, spending, and checkout analytics.",
      },
      {
        title: "Subscriptions",
        url: "/caterer/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Notifications",
        url: "/caterer/notifications",
        icon: "notifications",
        description: "Review canteen workflow alerts and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  technician: {
    role: "technician",
    label: "Technician",
    shortLabel: "Technician",
    basePath: "/technician",
    dashboardPath: "/technician/dashboard",
    headline: "Technician Dashboard",
    description:
      "A focused operations workspace for service desk support, venue decisions, and election management.",
    scope: "Technician-owned operational workflows and student election maintenance.",
    metrics: [
      {
        title: "Submitted",
        value: "0",
        subtitle: "New student service issues awaiting attention.",
        icon: "records",
      },
      {
        title: "In Progress",
        value: "0",
        subtitle: "Issues currently being handled by the service team.",
        icon: "statistics",
      },
      {
        title: "Solved",
        value: "0",
        subtitle: "Issues completed by the service desk.",
        icon: "notifications",
      },
    ],
    priorities: [
      "Review newly submitted student service issues.",
      "Record addressed and in-progress updates for students.",
      "Mark resolved tickets as solved with a clear resolution note.",
      "Create elections, maintain candidates, and publish election outcomes.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/technician/dashboard",
        icon: "dashboard",
        description: "Service desk ticket summary and work queue.",
      },
      {
        title: "Statistics",
        url: "/technician/statistics",
        icon: "statistics",
        description: "Ticket status, category demand, and open workload analytics.",
      },
      {
        title: "Venue Booking Requests",
        url: "/technician/venue-bookings",
        icon: "calendar",
        description: "Approve or reject student and teacher venue booking requests.",
      },
      {
        title: "Elections",
        url: "/technician/elections",
        icon: "elections",
        description: "Create elections, manage candidates, and publish outcomes.",
        items: [
          {
            title: "Election Setup",
            url: "/technician/elections",
            description: "Create elections and define voting phases.",
          },
          {
            title: "Candidates",
            url: "/technician/elections/candidates",
            description: "Manage candidates for active elections.",
          },
          {
            title: "Election Results",
            url: "/technician/elections/results",
            description: "Publish or review election outcomes.",
          },
        ],
      },
      {
        title: "Subscriptions",
        url: "/technician/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Helpdesk",
        url: "/technician/helpdesk",
        icon: "records",
        description: "Review and update all student service desk tickets.",
      },
      {
        title: "Notifications",
        url: "/technician/notifications",
        icon: "notifications",
        description: "Review new helpdesk ticket alerts and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  accountant: {
    role: "accountant",
    label: "Accountant",
    shortLabel: "Accounts",
    basePath: "/accountant",
    dashboardPath: "/accountant/dashboard",
    headline: "Finance Dashboard",
    description:
      "A finance operations workspace for subscription plans, payment gateway settings, payment records, and subscription cards.",
    scope: "Finance department subscription and payment operations.",
    metrics: [
      {
        title: "Active Subscriptions",
        value: "0",
        subtitle: "Paid subscription options currently valid.",
        icon: "records",
      },
      {
        title: "Pending Payments",
        value: "0",
        subtitle: "Checkout sessions waiting for gateway confirmation.",
        icon: "statistics",
      },
      {
        title: "Gateway",
        value: "Setup",
        subtitle: "Payment gateway and manual payment settings are managed here.",
        icon: "settings",
      },
    ],
    priorities: [
      "Maintain payment gateway details without hard-coding credentials in the backend.",
      "Create and maintain subscription options, prices, durations, and role availability.",
      "Monitor successful payments and subscription card issuance.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/accountant/dashboard",
        icon: "dashboard",
        description: "Finance payment and subscription overview.",
      },
      {
        title: "Statistics",
        url: "/accountant/statistics",
        icon: "statistics",
        description: "Ledger, canteen, subscription, and compensation approval analytics.",
      },
      {
        title: "Canteen Allowance",
        url: "/accountant/canteen",
        icon: "records",
        description: "Manage student canteen allowance, monthly extras, and manual balance additions.",
      },
      {
        title: "Compensation Requests",
        url: "/accountant/compensation-requests",
        icon: "records",
        description: "Approve or reject HR salary and bonus change requests.",
      },
      {
        title: "Gateway Settings",
        url: "/accountant/gateway",
        icon: "settings",
        description: "Maintain payment gateway endpoint, mode, and credentials.",
      },
      {
        title: "Manage Subscriptions",
        url: "/accountant/plans",
        icon: "records",
        description: "Create, edit, or remove subscription options.",
      },
      {
        title: "Subscription Records",
        url: "/accountant/subscriptions",
        icon: "statistics",
        description: "Review payment status and active subscription records.",
      },
      {
        title: "Student Ledgers",
        url: "/accountant/ledger",
        icon: "records",
        description: "Post student charges, review balances, and manage finance holds.",
        items: [
          { title: "Overview", url: "/accountant/ledger" },
          { title: "Fines & Charges", url: "/accountant/ledger/fines" },
          { title: "Finance Holds", url: "/accountant/ledger/holds" },
          { title: "Bulk Charge", url: "/accountant/ledger/bulk-charge" },
          { title: "Payment Plans", url: "/accountant/ledger/payment-plans" },
        ],
      },
      {
        title: "Subscriptions",
        url: "/accountant/my-subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Notifications",
        url: "/accountant/notifications",
        icon: "notifications",
        description: "Review finance workflow alerts and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  hr: {
    role: "hr",
    label: "Human Resources",
    shortLabel: "HR",
    basePath: "/hr",
    dashboardPath: "/hr/dashboard",
    headline: "HR Dashboard",
    description:
      "A human-resources workspace for employee master records, positions, staff lifecycle status, and HR self-service.",
    scope: "Employee master, position, and HR staff operations.",
    metrics: [
      {
        title: "Employees",
        value: "0",
        subtitle: "Unified employee records linked to portal profiles.",
        icon: "users",
      },
      {
        title: "Positions",
        value: "0",
        subtitle: "University job roles, employment types, and grades.",
        icon: "records",
      },
      {
        title: "Lifecycle",
        value: "Active",
        subtitle: "Draft, probation, active, suspended, resigned, and retired statuses.",
        icon: "statistics",
      },
    ],
    priorities: [
      "Maintain a unified employee master without removing role-specific teacher, executive, librarian, caterer, technician, or accountant records.",
      "Create position definitions before assigning staff to employee records.",
      "Track employment status changes as auditable personnel events.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/hr/dashboard",
        icon: "dashboard",
        description: "Employee and position overview.",
      },
      {
        title: "Statistics",
        url: "/hr/statistics",
        icon: "statistics",
        description: "Visualize employee salary, bonus, status, and leave placeholder stats.",
      },
      {
        title: "Employees",
        url: "/hr/employees",
        icon: "users",
        description: "Create and maintain unified employee master records.",
      },
      {
        title: "Staff Onboarding",
        url: "/hr/onboarding",
        icon: "records",
        description: "Track staff applications and onboarding work.",
      },
      {
        title: "Positions",
        url: "/hr/positions",
        icon: "records",
        description: "Maintain HR positions, employment types, and grades.",
      },
      {
        title: "My HR Profile",
        url: "/hr/my-profile",
        icon: "settings",
        description: "Review your own employee master record.",
      },
      {
        title: "Subscriptions",
        url: "/hr/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "Notifications",
        url: "/hr/notifications",
        icon: "notifications",
        description: "Review HR workflow alerts and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
  admin: {
    role: "admin",
    label: "Administrator",
    shortLabel: "Admin",
    basePath: "/admin",
    dashboardPath: "/admin/dashboard",
    headline: "Admin Dashboard",
    description:
      "A global administration workspace for accounts, academic structure, semesters, and system-wide statistics.",
    scope: "System-wide configuration and reporting.",
    metrics: [
      {
        title: "Accounts",
        value: "0",
        subtitle: "Students, teachers, executives, and admins.",
        icon: "users",
      },
      {
        title: "Schools",
        value: "0",
        subtitle: "Academic schools and their leadership teams.",
        icon: "academic",
      },
      {
        title: "Centres",
        value: "0",
        subtitle: "Academic and support centres across the institution.",
        icon: "academic",
      },
    ],
    priorities: [
      "Create and manage accounts across student, teacher, and executive roles.",
      "Maintain schools and centres while executives handle departmental structure.",
      "Monitor system-wide statistics, reports, and academic term setup.",
    ],
    navMain: [
      {
        title: "Dashboard",
        url: "/admin/dashboard",
        icon: "dashboard",
        description: "Global portal health and administration overview.",
      },
      {
        title: "Statistics",
        url: "/admin/statistics",
        icon: "statistics",
        description: "System-wide statistics across the portal.",
      },
      {
        title: "Create Account",
        url: "/admin/create-account",
        icon: "users",
        description: "Create role-specific portal accounts.",
        items: [
          {
            title: "Create Student",
            url: "/admin/create-account/student",
            description: "Create a student account with a student ID.",
          },
          {
            title: "Create Teacher",
            url: "/admin/create-account/teacher",
            description: "Create a teacher account with a staff ID.",
          },
          {
            title: "Create Executive",
            url: "/admin/create-account/executive",
            description: "Create an executive account with a staff ID.",
          },
          {
            title: "Create Librarian",
            url: "/admin/create-account/librarian",
            description: "Create a librarian account assigned to a configured library owner.",
          },
          {
            title: "Create Caterer",
            url: "/admin/create-account/caterer",
            description: "Create a dining or canteen worker account assigned to a configured owner.",
          },
          {
            title: "Create Technician",
            url: "/admin/create-account/technician",
            description: "Create a service desk technician account.",
          },
          {
            title: "Create Accountant",
            url: "/admin/create-account/accountant",
            description: "Create a finance department accountant account.",
          },
          {
            title: "Create HR",
            url: "/admin/create-account/hr",
            description: "Create a human resources staff account.",
          },
        ],
      },
      {
        title: "Manage",
        url: "/admin/manage",
        icon: "users",
        items: [
          {
            title: "Manage Applicants",
            url: "/admin/manage/applicants",
            description: "Review applicant accounts and application history.",
          },
          {
            title: "Manage Students",
            url: "/admin/manage/students",
            description: "Create and maintain student accounts.",
          },
          {
            title: "Manage Teachers",
            url: "/admin/manage/teachers",
            description: "Create and maintain teacher accounts.",
          },
          {
            title: "Manage Executives",
            url: "/admin/manage/executives",
            description: "Create and maintain executive accounts.",
          },
          {
            title: "Manage Librarians",
            url: "/admin/manage/librarians",
            description: "Maintain librarian accounts assigned to configured library owners.",
          },
          {
            title: "Manage Caterers",
            url: "/admin/manage/caterers",
            description: "Maintain dining or canteen worker accounts assigned to configured owners.",
          },
          {
            title: "Manage Technicians",
            url: "/admin/manage/technicians",
            description: "Maintain service desk technician accounts assigned to configured owners.",
          },
          {
            title: "Manage Accountants",
            url: "/admin/manage/accountants",
            description: "Maintain finance department accountant accounts.",
          },
          {
            title: "Manage HR",
            url: "/admin/manage/hr",
            description: "Maintain human resources staff accounts.",
          },
        ],
      },

      {
        title: "Academic Structure",
        url: "/admin/academics",
        icon: "academic",
        description: "Manage schools, centres, departments, units, programmes, and semesters.",
        items: [
          {
            title: "Schools",
            url: "/admin/schools",
            description: "Add, update, and retire academic schools and their details.",
          },
          {
            title: "Centres",
            url: "/admin/centres",
            description: "Add, update, and retire academic and support centres.",
          },
          {
            title: "Departments",
            url: "/admin/academics/departments",
            description: "Manage departments and their school or centre placement.",
          },
          {
            title: "Units",
            url: "/admin/academics/units",
            description: "Manage administrative units and assigned executives.",
          },
          {
            title: "Programmes",
            url: "/admin/academics/programmes",
            description: "Manage academic and centre programmes shown on public pages.",
          },
          {
            title: "Semesters",
            url: "/admin/semesters",
            description: "Create and manage academic semesters.",
          },
        ],
      },
      {
        title: "Gradebook Criteria",
        url: "/admin/gradebook",
        icon: "results",
        description: "Manage institution grade scales and grade-point criteria.",
      },
      {
        title: "Venues",
        url: "/admin/venues",
        icon: "academic",
        description: "Create and manage campus buildings and venues.",
      },
      {
        title: "Venue Requests",
        url: "/admin/venue-bookings",
        icon: "calendar",
        description: "Review venue booking requests when admin approval is configured.",
      },
      {
        title: "Hostels",
        url: "/admin/hostels",
        icon: "hostels",
        description: "Create and manage residential hostels, rooms, wardens, and student assignments.",
      },
      {
        title: "Public Content",
        url: "/admin/public-content",
        icon: "records",
        description: "Manage public website content and authenticated announcements.",
        items: [
          {
            title: "News",
            url: "/admin/public-content/news",
            description: "Manage public news items.",
          },
          {
            title: "Events",
            url: "/admin/public-content/events",
            description: "Manage event listings and monthly highlights.",
          },
          {
            title: "Announcements",
            url: "/admin/public-content/announcements",
            description: "Manage targeted portal announcements.",
          },
          {
            title: "Official Links",
            url: "/admin/public-content/official-links",
            description: "Manage public and authenticated resource links.",
          },
        ],
      },
      {
        title: "Reports",
        url: "/admin/reports",
        icon: "statistics",
        description: "Export tables and review operational reports.",
        items: [
          {
            title: "People",
            url: "/admin/reports/people",
            description: "Filtered student, teacher, executive, and applicant XLSX reports.",
          },
          {
            title: "Academic",
            url: "/admin/reports/academic",
            description: "Academic directory, registration, attendance, and leave reports.",
          },
          {
            title: "Operations",
            url: "/admin/reports/operations",
            description: "Campus operations, support, governance, and audit reports.",
          },
          {
            title: "Export History",
            url: "/admin/reports/exports",
            description: "Review, redownload, and remove generated report files.",
          },
        ],
      },
      {
        title: "Subscriptions",
        url: "/admin/subscriptions",
        icon: "records",
        description: "Buy available subscriptions or print active subscription cards.",
      },
      {
        title: "UI Customization",
        url: "/admin/ui-customization",
        icon: "palette",
        description: "Customize the portal appearance in real time.",
      },
      {
        title: "Setup Wizard",
        url: "/admin/setup-wizard",
        icon: "settings",
        description: "Complete the guided universal setup checklist for a new institution.",
      },
      {
        title: "Settings",
        url: "/admin/settings",
        icon: "settings",
        description: "Configure portal settings and operational defaults.",
      },
      {
        title: "Backup and Restore",
        url: "/admin/backup-restore",
        icon: "records",
        description: "Download backups, restore data, and manage monthly backup emails.",
      },
      {
        title: "Audit Log",
        url: "/admin/audit-log",
        icon: "settings",
        description: "Review privileged administrative activity.",
      },
      {
        title: "Notifications",
        url: "/admin/notifications",
        icon: "notifications",
        description: "Review approvals, system alerts, and portal notices.",
      },
    ],
    navSecondary: sharedSecondaryNav,
  },
}

const ROLE_ALIASES: Record<string, UserRole> = {
  administrator: "admin",
  admin: "admin",
  executive: "executive",
  staff: "executive",
  teacher: "teacher",
  lecturer: "teacher",
  chef: "teacher",
  librarian: "librarian",
  library: "librarian",
  caterer: "caterer",
  canteen: "caterer",
  technician: "technician",
  ict: "technician",
  accountant: "accountant",
  accounts: "accountant",
  finance: "accountant",
  hr: "hr",
  "human resources": "hr",
  humanresources: "hr",
  "human-resources": "hr",
  human_resources: "hr",
  applicant: "applicant",
  admissions: "applicant",
  student: "student",
  user: "student",
}

export function parseUmsRole(role: string | null | undefined): UserRole | null {
  const value = String(role ?? "").trim().toLowerCase()
  return ROLE_ALIASES[value] ?? null
}

export function normalizeUmsRole(role: string | null | undefined): UserRole {
  return parseUmsRole(role) ?? "student"
}

export function isUmsRole(role: string | null | undefined): role is UserRole {
  return UMS_ROLES.includes(String(role ?? "").toLowerCase() as UserRole)
}

export function defaultUmsRouteForRole(role: UserRole): string {
  return ROLE_ZONES[role].dashboardPath
}

export function roleForUmsPath(pathname: string): UserRole | null {
  const normalizedPath = pathname.replace(/\/+$/, "") || "/"

  for (const role of UMS_ROLES) {
    const basePath = ROLE_ZONES[role].basePath
    if (normalizedPath === basePath || normalizedPath.startsWith(`${basePath}/`)) {
      return role
    }
  }

  return null
}

export function getUmsNavItemByUrl(role: UserRole, url: string) {
  const zone = ROLE_ZONES[role]
  const allItems = [...zone.navMain, ...zone.navSecondary]

  for (const item of allItems) {
    if (item.url === url) {
      return item
    }

    const subItem = item.items?.find((candidate) => candidate.url === url)
    if (subItem) {
      return {
        ...subItem,
        icon: item.icon,
      }
    }
  }

  return null
}
