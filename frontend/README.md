# AIU Unified Portal

A unified academic platform that consolidates the AIU student, teacher, executive, and administrative experience into a single, seamless system. Replaces fragmented access across Moodle, Student Hub, AIU SMS, and the public website.

## Overview

**Portal** is the daily academic operating system for Africa International University (AIU). It combines the strongest workflows from existing systems:

- **Moodle** → Course content, assignments, deadlines, learning progress
- **Student Hub** → Registration, attendance, exams, elections
- **AIU SMS** → Academic records, GPA/CGPA, leave, emergency contacts
- **AIU Website** → Institutional content, academic structure, official links
- **Timetable Spreadsheet** → Structured calendar data and scheduling

The result: **one platform, one login, one dashboard, one calendar, one notification stream**.

## Key Features

### For Students
- **Dashboard** – upcoming assignments, courses, attendance, notifications
- **Courses** – current, completed, and registration with course details and resources
- **Assignments** – submit work, track grading, view feedback
- **Attendance** – code and QR submission, attendance reports
- **Academic Records** – results, GPA, transcripts, exam slips
- **Registration & Elections** – course registration, exam exemptions, SRC voting
- **Calendar & Timetable** – unified schedule view
- **Leave Management** – apply for and track leave requests

### For Teachers
- **Course Management** – roster, resources, assignments
- **Attendance** – create sessions, record attendance, corrections
- **Assignment Grading** – manage submissions, provide feedback
- **Results** – draft, submit, and finalize grades
- **Calendar & Timetable** – unified schedule

### For Executives
- **Course Offerings** – view, create, and manage course offerings
- **Student Management** – view and manage student records
- **Registration Approval** – approve/reject pending registrations
- **Results Publication** – review and publish semester results
- **Elections** – manage candidate nominations and voting
- **Reporting** – statistics and insights

### For Administrators
- **Academic Structure** – manage schools and centres (programmes, units, and departments are managed by executives)
- **User Management** – create and manage students, teachers, executives
- **Semester Management** – configure academic periods
- **Content Management** – manage public announcements, events, news
- **Audit Logs** – system activity tracking
- **Settings** – system configuration

## Tech Stack

**Frontend:**
- **Next.js 16** – React framework with App Router
- **TypeScript** – type-safe development
- **Tailwind CSS** – utility-first styling
- **shadcn/ui** – accessible component library
- **React 19** – latest React features

**Backend:**
- **Django** – Python web framework
- **Django REST Framework** – REST API
- **JWT Authentication** – secure token-based auth
- **PostgreSQL** – primary database (assumed)

## Project Structure

```
portal/
├── frontend/                    # Next.js application (this directory)
│   ├── app/                    # Next.js app directory
│   │   ├── (admin)/           # Admin role routes
│   │   ├── (student)/         # Student role routes
│   │   ├── (teacher)/         # Teacher role routes
│   │   ├── (executive)/       # Executive role routes
│   │   └── (public)/          # Public routes
│   ├── components/             # Reusable React components
│   │   ├── ui/                # Base UI components (shadcn)
│   │   ├── layout/            # Layout components
│   │   ├── sidebar/           # Navigation
│   │   ├── charts/            # Data visualization
│   │   └── modals/            # Modal dialogs
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utilities and helpers
│   └── public/                 # Static assets
├── backend/                    # Django REST API
│   ├── core/                  # Django project settings
│   ├── admin_app/             # Admin endpoints
│   ├── student_app/           # Student endpoints
│   ├── teacher_app/           # Teacher endpoints
│   ├── executive_app/         # Executive endpoints
│   ├── home_app/              # Public endpoints
│   └── notifications_package/  # Notifications service
└── docs/                       # Documentation
    └── PLAN.md                # Project plan and route inventory
```

## Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+ and pip (for backend)
- Git

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

## Development

### Run Frontend

```bash
cd frontend
npm run dev
```

The app opens at `http://localhost:3000`.

### Run Linter & Type Checker

```bash
npm run lint       # ESLint
npm run typecheck  # TypeScript
npm run format     # Prettier
```

### Build for Production

```bash
npm run build
npm start
```

## API Routes

The backend exposes API endpoints grouped by role:

### Authentication (Root)
- `POST /auth/login` – user login
- `POST /auth/register` – user registration
- `POST /auth/verify-email` – email verification
- `POST /auth/forgot-password` – password reset request
- `POST /auth/reset-password` – confirm password reset
- `GET /auth/token/refresh` – refresh JWT token

### Student API
- `GET /student/dashboard` – dashboard summary
- `GET /student/courses` – enrolled courses
- `GET /student/assignments` – assignments
- `POST /student/assignments/{id}/submit` – submit assignment
- `GET /student/attendance` – attendance records
- `GET /student/results` – academic results
- `POST /student/registration` – course registration
- And more...

### Teacher API
- `GET /teacher/dashboard` – teaching dashboard
- `GET /teacher/courses` – assigned courses
- `POST /teacher/assignments/create` – create assignment
- `GET /teacher/assignments/{id}/submissions` – student submissions
- `POST /teacher/attendance/sessions` – create attendance session
- And more...

### Executive & Admin APIs
- See `docs/PLAN.md` for full endpoint list

## Route Inventory

See `docs/PLAN.md` for the complete frontend and backend route trees. Key patterns:

- **Dynamic Routes**: `/student/courses/[courseId]`, `/student/assignments/[assignmentId]`
- **Nested Routes**: `/admin/schools`, `/admin/centres`, `/teacher/courses/[courseId]/assignments`
- **Trailing Slashes**: Backend supports both with/without trailing slashes for compatibility

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit: `git commit -m "Add feature"`
3. Push to branch: `git push origin feature/your-feature`
4. Open a pull request

## Design Principles

1. **User-Centric** – Design for the actual daily workflows of students, teachers, and staff
2. **Unified Experience** – One system, one login, one dashboard
3. **Role-Specific** – Different interfaces for different roles
4. **Information Priority** – Show urgent items (overdue work, pending approvals) first
5. **Accessibility** – Follow WCAG guidelines for inclusive design
6. **Performance** – Fast load times and smooth interactions

## License

Private repository. All rights reserved to Africa International University.

## Support

For issues, questions, or contributions, contact the development team.
