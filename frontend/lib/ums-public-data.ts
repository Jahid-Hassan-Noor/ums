export type PublicLink = {
  label: string
  href: string
  description?: string
}

export type PublicNavGroup = PublicLink & {
  children?: PublicLink[]
}

export type PublicStat = {
  value: string
  label: string
}

export type PublicContentItem = {
  title: string
  summary: string
  meta?: string
  href?: string
}

export type PublicContentSection = {
  eyebrow?: string
  title: string
  body?: string[]
  items?: PublicContentItem[]
  links?: PublicLink[]
}

export type PublicDetailPage = {
  path: string
  active?: string
  eyebrow: string
  title: string
  description: string
  image?: string
  stats?: PublicStat[]
  sections: PublicContentSection[]
}

export const umsContact = {
  address:
    "Jalan Tun Abdul Razak, 05200 Alor Setar, Kedah Darul Aman, Malaysia.",
  phone: "(60) 4774 7300",
  email: "info@aiu.edu.my",
}

export const contactChannels = [
  {
    title: "General Info and Course Inquiry",
    summary: "info@aiu.edu.my",
  },
  {
    title: "Application Status",
    summary: "apply@aiu.edu.my",
  },
  {
    title: "International Student Pass",
    summary: "isu@aiu.edu.my",
  },
  {
    title: "Scholarship",
    summary: "scholarship@aiu.edu.my",
  },
  {
    title: "Admission",
    summary: "admission@aiu.edu.my",
  },
]

export const publicNavGroups: PublicNavGroup[] = [
  {
    label: "About AIU",
    href: "/about",
    children: [
      { label: "Background", href: "/about" },
      { label: "Pro-Chancellor", href: "/about/pro-chancellor" },
      { label: "Board of Governors", href: "/about/board-of-governors" },
      { label: "Senate", href: "/about/senate" },
      {
        label: "University Management Committee",
        href: "/about/university-management-committee",
      },
      {
        label: "Senior Management Committee",
        href: "/about/senior-management-committee",
      },
    ],
  },
  {
    label: "Academics",
    href: "/programmes",
    children: [
      { label: "Academic Programmes", href: "/programmes" },
      { label: "Schools", href: "/schools" },
      { label: "Centres", href: "/centres" },
    ],
  },
  {
    label: "ACE-SEDI",
    href: "/ace-sedi",
    children: [
      { label: "ACE-SEDI", href: "/ace-sedi" },
      {
        label: "Albukhary Social Business Journal",
        href: "/albukhary-social-business-journal",
      },
    ],
  },
  {
    label: "Students",
    href: "/student-life",
    children: [
      { label: "Current Student", href: "/students/current-student" },
      { label: "Student Handbook", href: "/students/student-handbook" },
      { label: "Student Hub", href: "/student-life/student-hub" },
      { label: "AIU Alumni", href: "/alumni" },
      { label: "Wall of Fame", href: "/alumni/wall-of-fame" },
      { label: "Facilities", href: "/student-life/facilities" },
      { label: "Library", href: "/student-life/library" },
      { label: "Student News", href: "/news" },
    ],
  },
  {
    label: "Directories",
    href: "/directories",
    children: [
      { label: "Departments", href: "/departments" },
      { label: "Units", href: "/units" },
    ],
  },
  { label: "Scholarship", href: "/scholarship" },
  { label: "Contact Us", href: "/contact" },
]

export const publicNavLinks = [
  ...publicNavGroups.map(({ label, href }) => ({ label, href })),
  { label: "Portal", href: "/ums-overview" },
]

export const applyLinks = [
  { label: "Apply", href: "/apply" },
  { label: "Applicant Login", href: "/login?next=/apply/dashboard" },
]

export const officialLinks: PublicContentItem[] = [
  {
    title: "Undergraduate Application",
    summary:
      "October 2026 intake guidance, document preparation, and application steps.",
    href: "/apply",
  },
  {
    title: "Postgraduate Application",
    summary:
      "Coursework and research pathways administered by the Centre for Graduate Studies.",
    href: "/apply",
  },
  {
    title: "Student Hub",
    summary:
      "Current student services and resources connected from the public site.",
    href: "/student-life/student-hub",
  },
  {
    title: "Library",
    summary:
      "Library collections, e-resources, operating hours, and learning support.",
    href: "/student-life/library",
  },
  {
    title: "ACE-SEDI",
    summary:
      "AIU Centre of Excellence in Socio-Economic Development and Innovation.",
    href: "/ace-sedi",
  },
  {
    title: "Albukhary Social Business Journal",
    summary:
      "A research publication channel for social business scholarship and innovation.",
    href: "/albukhary-social-business-journal",
  },
  {
    title: "Repository",
    summary:
      "Academic regulations, handbooks, forms, and public university documents.",
    href: "/repository",
  },
  {
    title: "Alumni",
    summary: "AIU alumni community, stories, and wall of fame.",
    href: "/alumni",
  },
  {
    title: "Convocation",
    summary: "Convocation updates and graduate-facing information.",
    href: "/convocation",
  },
]

export const umsValues = [
  {
    title: "Aqidah",
    summary:
      "Faith and spiritual-based excellence, grounding purpose, discipline, and direction.",
  },
  {
    title: "Akhlaq",
    summary:
      "Compassionate character, moral virtues, and internalised personal refinement.",
  },
  {
    title: "Adab",
    summary:
      "Learning excellence, humility, dignity, and respect in academic and social life.",
  },
  {
    title: "Amanah",
    summary:
      "Truthfulness, honesty, integrity, responsibility, and accountable action.",
  },
  {
    title: "Amalan",
    summary:
      "Focused practice, innovation, and the renewal of tradition through purposeful work.",
  },
]

export const schools = [
  {
    code: "SBSS",
    title: "School of Business and Social Sciences",
    href: "/schools/school-of-business-social-sciences",
    image: "/images/aiu/campus-social-business.jpg",
    summary:
      "Social business, management, economics, finance, and social development programmes with applied community engagement.",
    about:
      "SBSS upholds AIU's mission of social business through innovative curriculum and applied learning, including community engagement and leadership experiences grounded in 5A values.",
    vision:
      "To be a centre of excellence in learning social business through an innovative and creative curriculum.",
    mission: [
      "Provide graduates with quality education through innovative curriculum and research experiences.",
      "Disseminate knowledge through teaching, academic publication, and presentation.",
      "Contribute to the academic advancement of business management, development studies, and social business.",
      "Create knowledge through academic research and smart-partnership collaboration.",
    ],
    programmes: [
      "Bachelor of Business Administration (Honours)",
      "Bachelor of Business Administration (Honours) (Marketing)",
      "Bachelor of Business Administration (Honours) (Human Resource Management)",
      "Bachelor of Social Development (Honours)",
      "Bachelor of Economics (Honours)",
      "Bachelor of Finance (Islamic Finance) (Honours)",
      "Bachelor of Politics and International Relations (Honours)",
      "Bachelor of Business Administration with Computer Science (Honours)",
      "Master in Social Business",
      "Master of Business Management (by Research)",
      "Doctor of Philosophy (Management and Administration)",
    ],
  },
  {
    code: "SEHS",
    title: "School of Education and Human Sciences",
    href: "/schools/school-of-education-human-sciences",
    image: "/images/aiu/campus-welcome.jpg",
    summary:
      "Education, early childhood, media and communication, human sciences, and postgraduate education.",
    about:
      "SEHS equips students with knowledge and skills for education, social care, health, media and communication, and public policy through interdisciplinary, technology-driven learning.",
    vision:
      "To be a centre of excellence in learning social business through an innovative and creative curriculum.",
    mission: [
      "Provide graduates with quality education through innovative curriculum and research experiences.",
      "Disseminate knowledge through teaching, academic publication, and presentation.",
      "Contribute to the academic advancement of business management, development studies, and social business.",
      "Create knowledge through academic research and smart-partnership collaboration.",
    ],
    programmes: [
      "Bachelor of Elementary Education (Honours)",
      "Bachelor in Early Childhood Education (Honours)",
      "Bachelor of Media and Communication (Honours)",
      "Master of Education (by Research)",
      "Doctor of Philosophy (Teaching, Training and Education Science)",
    ],
  },
  {
    code: "SCI",
    title: "School of Computing and Informatics",
    href: "/schools/school-of-computing-and-informatics",
    image: "/images/aiu/campus-3zeros.jpg",
    summary:
      "Computing and informatics programmes shaped around technical competence and service to society.",
    about:
      "SCI develops graduates with strong computer science fundamentals, adaptable technical skills, and service-minded leadership grounded in AIU's 5A values.",
    vision:
      "To be the point of reference for computing and informatics in industry and community towards a sustainable world.",
    mission: [
      "Produce global computing and informatics experts and professionals to serve humanity.",
      "Produce adaptable, balanced, and well-rounded graduates with philanthropic attitudes.",
      "Inculcate integrated minds towards social inclusion globally.",
    ],
    programmes: [
      "Bachelor in Computer Science (Honours)",
      "Bachelor in Data Science (Honours)",
      "Bachelor in Information Technology (Cybersecurity) (Honours)",
      "Master of Computing (by Research)",
      "Doctor of Philosophy in Computer Science",
    ],
  },
]

export const centres = [
  {
    code: "CDAE",
    title: "Centre for Development of Academic Excellence",
    href: "/centres/centre-for-development-of-academic-excellence",
    image: "/images/aiu/campus-welcome.jpg",
    summary:
      "Teaching and learning hub supporting faculty development, consultations, SEC/SET, OBE, LMS, and SULAM.",
    about:
      "CDAE partners with AIU staff and students to support excellence and innovation in teaching and learning through orientation, training, mentoring, research, and learning design support.",
    offerings: [
      "Teaching and Delivery Sharing Session (TeDSS)",
      "CDAE Faculty Fellow",
      "Workshops and inductions",
      "Student Evaluation of Course and Teaching (SEC & SET)",
      "Programme management support",
      "Learning management system support",
      "SULAM project support",
    ],
  },
  {
    code: "CFGS",
    title: "Centre for Foundation and General Studies",
    href: "/centres/centre-for-foundation-and-general-studies",
    image: "/images/aiu/campus-social-business.jpg",
    summary:
      "One-year foundation pathways preparing students for undergraduate studies in an international environment.",
    about:
      "CFGS offers a pre-university programme that builds academic knowledge, communication skills, leadership, social responsibility, and AIU's 5A core values.",
    offerings: [
      "Foundation in Computing",
      "Foundation in Arts",
      "Undergraduate readiness",
      "Leadership and social responsibility",
      "Independent learning skills",
    ],
  },
  {
    code: "CGS",
    title: "Centre for Graduate Studies",
    href: "/centres/centre-for-graduate-studies",
    image: "/images/aiu/campus-3zeros.jpg",
    summary:
      "Postgraduate coursework and research connected to social business, sustainable enterprise, and impact research.",
    about:
      "CGS administers postgraduate programmes and student research projects anchored in social business, enterprise solutions, and the Three Zeroes of poverty, unemployment, and net carbon emissions.",
    offerings: [
      "Master in Social Business",
      "Master of Business Management",
      "Master of Education",
      "Doctor of Philosophy",
      "Postgraduate academic guidelines",
    ],
  },
  {
    code: "LC",
    title: "Language Centre",
    href: "/centres/language-centre",
    image: "/images/aiu/campus-welcome.jpg",
    summary:
      "Affordable and accessible language programmes for students, prospective learners, and the wider community.",
    about:
      "The Language Centre prepares learners for international English qualifications and provides language services to schools, higher education institutions, lifelong learners, and the community.",
    offerings: [
      "IELTS preparation",
      "Cambridge Linguaskill preparation",
      "General English",
      "Business English and Professional English",
      "English camps",
      "Creative writing and buddy programmes",
    ],
  },
]

export const departments = [
  "Vice Chancellor's Office",
  "Deputy Vice Chancellor (Academic)'s Office",
  "Deputy Vice Chancellor (Research and Innovation)'s Office",
  "Registry Department",
  "Academic Management Department (AMD)",
  "Centre for Student Affairs and Alumni (CSAA)",
  "Information, Communication and Technology Centre (ICT)",
  "Centre for Corporate Planning and Communication (CPC)",
  "Centre of Reference (Library)",
  "Human Resource Department",
  "Finance Department",
  "Centre for Quality Assurance and Accreditation (CQAA)",
]

export const units = [
  "Procurement Unit",
  "Admission Unit",
  "Student Recruitment Unit",
  "Scholarship Unit",
  "Facility Management Unit",
  "International Student Unit",
  "Examination and Records Unit",
]

export const latestNews = [
  {
    title:
      "AIU Programmatix 3ZERO Club Conducted Power BI Workshop in Collaboration with SCI Committee and KhitTa",
    date: "April 13, 2026",
    category: "News and Event",
    href: "/news/aiu-programmatix-3zero-club-conducted-power-bi-workshop-in-collaboration-with-sci-committee-and-khitta",
    summary:
      "A student-led workshop connected Programmatix 3ZERO Club, the SCI Committee, and KhitTa to strengthen Power BI and data literacy skills.",
  },
  {
    title:
      "AIU Lecturer Selected for International Writing Workshop for Early Career Researchers from the Global South",
    date: "April 13, 2026",
    category: "News and Event",
    href: "/news/aiu-lecturer-selected-for-international-writing-workshop",
    summary:
      "An AIU academic was selected to join an international writing workshop supporting early career researchers from the Global South.",
  },
  {
    title:
      "AIU SCI Committee Organises Three-Day Data Analytics Bootcamp in Collaboration with KhitTa and Programmatix 3ZERO Clubs",
    date: "April 13, 2026",
    category: "News and Event",
    href: "/news/aiu-sci-committee-organises-three-day-data-analytics-bootcamp",
    summary:
      "The School of Computing and Informatics community supported a practical bootcamp focused on data analytics exposure and collaboration.",
  },
  {
    title:
      "AIU Bachelor of Economics Conducts Sinar Harapan Program at Taman Sinar Harapan Jitra",
    date: "April 13, 2026",
    category: "News and Event",
    href: "/news/aiu-bachelor-of-economics-conducts-sinar-harapan-program",
    summary:
      "Bachelor of Economics students engaged with the Taman Sinar Harapan Jitra community through a service-oriented programme.",
  },
  {
    title: "CSAA AIU Organises Medical Insurance Briefing for Local Students",
    date: "April 13, 2026",
    category: "News and Event",
    href: "/news/csaa-aiu-organises-medical-insurance-briefing-for-local-students",
    summary:
      "The Centre for Student Affairs and Alumni organised a briefing to help local students understand medical insurance matters.",
  },
  {
    title: "Raya Celebration 2026 Unites AIU Students from Over 60 Countries",
    date: "April 13, 2026",
    category: "News and Event",
    href: "/news/raya-celebration-2026-unites-aiu-students-from-over-60-countries",
    summary:
      "The university community celebrated cultural diversity and togetherness with students representing more than 60 nationalities.",
  },
]

export const monthlyHighlights = [
  {
    title: "Monthly Event Highlights - December 2025",
    summary:
      "A monthly publication collecting recent university events, student activities, and campus life highlights.",
    href: "/aiunique",
  },
]

export const intakeNotice = {
  intake: "October 2026 Intake",
  status: "Application Open",
  deadline: "31 July 2026",
  href: "/apply",
}

export const scholarshipCriteria = [
  "Local applicants: 17 to 22 years old; international applicants: 17 to 20 years old.",
  "Single marital status.",
  "Household income below AIU's scholarship thresholds for the applicant category and state or region.",
  "No family member previously sponsored by Albukhary Foundation.",
]

export const scholarshipAssessment = [
  { label: "Socio Economic Status", value: "40%" },
  { label: "Communication Skills", value: "25%" },
  { label: "Personality and Attitude", value: "20%" },
  { label: "Defence of Personal Statement", value: "15%" },
]

export const scholarshipStaff = [
  "Nur Khalida Rahayu Binti Zainon",
  "Nur Zarifah Haifa Binti Mohamad Zakaria",
  "Nur Wahida Binti Azizan",
  "Amirul Bahrain Bin Shamsul Bahrain",
]

export const scholarshipContact = {
  phone: "+604-774 7331",
  whatsapp: "+6011-2414 1208",
  email: "scholarship@aiu.edu.my",
}

export const governanceGroups = {
  boardOfGovernors: [
    { title: "Syed Mohamad Albukhary", summary: "Chairman" },
    {
      title: "Professor Dato' Ir. Dr. Mohd Saleh Bin Jaafar",
      summary: "Member",
    },
    { title: "Dato' Mohammad Zainal Bin Shaari", summary: "Member" },
    { title: "Professor Dr. Rosna Binti Awang Hashim", summary: "Member" },
    { title: "Sharifah Sofia Binti Syed Mokhtar Shah", summary: "Member" },
    { title: "Syed Danial Bin Syed Mokhtar Shah", summary: "Member" },
    {
      title: "Professor Dr. Abdul Malek Bin Abdul Karim",
      summary: "Member",
    },
    { title: "Norpisah Binti Mat Isa", summary: "Secretary" },
    {
      title: "Professor Dr. Hj. Mohamad Abdullah Bin Hemdi",
      summary: "Ex-Officio",
    },
    { title: "Professor Dr. Khalid Hussain", summary: "Member" },
  ],
  universityManagementCommittee: [
    {
      title: "Professor Dato' Ir. Dr. Mohd Saleh Bin Jaafar",
      summary: "Vice Chancellor and President (Chairman)",
    },
    {
      title: "Professor Dr. Hj. Mohamad Abdullah Bin Hemdi",
      summary: "Deputy Vice Chancellor (Academic)",
    },
    { title: "Norpisah Binti Mat Isa", summary: "Registrar" },
    { title: "Rafilah Binti Abd Aziz", summary: "Financial Controller" },
    { title: "Ts. Sahrulnizam Bin Doni", summary: "Director, ICT Centre" },
    {
      title: "Abdul Shakur Bin Abdullah",
      summary:
        "Deputy Registrar / Director, Centre for Corporate Planning and Communication (Secretary)",
    },
  ],
  seniorManagementCommittee: [
    {
      title: "Professor Dato' Ir. Dr. Mohd Saleh Bin Jaafar",
      summary: "Vice Chancellor and President",
    },
    {
      title: "Professor Dr. Hj. Mohamad Abdullah Bin Hemdi",
      summary: "Deputy Vice Chancellor (Academic)",
    },
    {
      title: "Associate Professor Dr. Suraya Hanim Binti Mokhtar",
      summary:
        "Director, AIU Centre of Excellence in Socio-Economic Development and Innovation",
    },
    { title: "Norpisah Binti Mat Isa", summary: "Registrar" },
    { title: "Rafilah Binti Abd Aziz", summary: "Financial Controller" },
    { title: "Ts. Sahrulnizam Bin Doni", summary: "Director, ICT Centre" },
    {
      title: "Abdul Shakur Bin Abdullah",
      summary:
        "Deputy Registrar / Director, Centre for Corporate Planning and Communication",
    },
    {
      title: "Professor Dr. Annuar Bin Md Nassir",
      summary: "Acting Dean, School of Business and Social Sciences",
    },
    {
      title: "Professor Dr. Abdul Malek Bin Abdul Karim",
      summary: "Dean, School of Education and Human Sciences",
    },
    {
      title: "Associate Professor Dr. Basheer Riskhan",
      summary: "Dean, School of Computing and Informatics",
    },
    {
      title: "Alia Hanim Binti Zainal Abidin",
      summary: "Director, Centre for Foundation and General Studies",
    },
    {
      title: "Professor Dr. Yusnidah Binti Ibrahim",
      summary: "Director, Centre for Graduate Studies",
    },
  ],
  senate: [
    {
      title: "Professor Dato' Ir. Dr. Mohd Saleh Bin Jaafar",
      summary: "Vice Chancellor and President (Chairman)",
    },
    {
      title: "Professor Dr. Hj. Mohamad Abdullah Bin Hemdi",
      summary: "Deputy Vice Chancellor (Academic)",
    },
    {
      title: "Professor Dr. Annuar Bin Md Nassir",
      summary: "Acting Dean, School of Business and Social Sciences",
    },
    {
      title: "Professor Dr. Abdul Malek Bin Abdul Karim",
      summary: "Dean, School of Education and Human Sciences",
    },
    {
      title: "Associate Professor Dr. Basheer Riskhan",
      summary: "Dean, School of Computing and Informatics",
    },
    {
      title: "Professor Dr. Yusnidah Binti Ibrahim",
      summary: "Director, Centre for Graduate Studies",
    },
    {
      title: "Alia Hanim Binti Zainal Abidin",
      summary: "Director, Centre for Foundation and General Studies",
    },
    {
      title: "Sherina Shahnaz Binti Mohamed Fauzi",
      summary: "Director, Language Centre",
    },
    {
      title: "Ildefonso Halipa Jr.",
      summary: "Director, Centre for Development of Academic Excellence",
    },
    {
      title: "Norpisah Binti Mat Isa",
      summary: "Registrar (Secretary)",
    },
  ],
}

export const umsModules = [
  "Course registration",
  "Current and completed courses",
  "Attendance",
  "Assignments",
  "Result submission and publication",
  "Student elections",
  "Academic setup",
  "Statistics and audit logs",
]

export const umsRoles: { title: string; summary?: string }[] = []

const academicDetailPages: PublicDetailPage[] = [
  ...schools.map((school) => ({
    path: school.href,
    active: "/programmes",
    eyebrow: school.code,
    title: school.title,
    description: school.about,
    image: school.image,
    stats: [
      { value: school.code, label: "School code" },
      { value: String(school.programmes.length), label: "Programmes" },
      { value: "5A", label: "Core values" },
      { value: "AIU", label: "Academic school" },
    ],
    sections: [
      {
        eyebrow: "About",
        title: "Academic identity",
        body: [school.about],
      },
      {
        eyebrow: "Vision",
        title: school.vision,
        body: school.mission,
      },
      {
        eyebrow: "Programmes Offered",
        title: "Programmes under this school",
        items: school.programmes.map((programme) => ({
          title: programme,
          summary:
            "Programme listed under the current AIU academic programme structure.",
          href: "/programmes",
        })),
      },
    ],
  })),
  ...centres.map((centre) => ({
    path: centre.href,
    active: "/programmes",
    eyebrow: centre.code,
    title: centre.title,
    description: centre.about,
    image: centre.image,
    stats: [
      { value: centre.code, label: "Centre code" },
      { value: String(centre.offerings.length), label: "Key services" },
      { value: "AIU", label: "Academic support" },
      { value: "5A", label: "Core values" },
    ],
    sections: [
      {
        eyebrow: "About",
        title: "Centre overview",
        body: [centre.about],
      },
      {
        eyebrow: "Programmes and Services",
        title: "What this centre supports",
        items: centre.offerings.map((offering) => ({
          title: offering,
          summary:
            "Service, programme, or learning support area listed for this AIU centre.",
        })),
      },
      {
        eyebrow: "Related",
        title: "Academic directory connection",
        links: [
          { label: "All Centres", href: "/centres" },
          { label: "Academic Programmes", href: "/programmes" },
        ],
      },
    ],
  })),
]

const publicServiceDetailPages: PublicDetailPage[] = [
  {
    path: "/academics",
    active: "/programmes",
    eyebrow: "Academics",
    title: "SBSS, SEHS, SCI, and AIU academic centres.",
    description:
      "AIU's academic structure is organised around three schools and specialist centres for foundation, graduate studies, academic excellence, and language learning.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Schools",
        title: "Academic schools",
        items: schools.map((school) => ({
          title: school.title,
          summary: school.summary,
          meta: school.code,
          href: school.href,
        })),
      },
      {
        eyebrow: "Centres",
        title: "Academic and support centres",
        items: centres.map((centre) => ({
          title: centre.title,
          summary: centre.summary,
          meta: centre.code,
          href: centre.href,
        })),
      },
    ],
  },
  {
    path: "/academic-programmes",
    active: "/programmes",
    eyebrow: "Academic Programmes",
    title: "Lists of programmes and academic calendars.",
    description:
      "The programme directory follows AIU's current public structure for schools, foundation studies, and academic calendar references.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Programmes",
        title: "Programmes by school and centre",
        items: [
          ...schools.flatMap((school) =>
            school.programmes.map((programme) => ({
              title: programme,
              summary: school.title,
              meta: school.code,
              href: school.href,
            }))
          ),
          ...centres
            .filter((centre) => centre.code === "CFGS")
            .flatMap((centre) =>
              centre.offerings.slice(0, 2).map((programme) => ({
                title: programme,
                summary: centre.title,
                meta: centre.code,
                href: centre.href,
              }))
            ),
        ],
      },
      {
        eyebrow: "Academic Calendar",
        title: "Session 2025/2026 references",
        body: [
          "Foundation Studies Programme calendar: Centre for Foundation and General Studies.",
          "Undergraduate Programmes calendar: School of Business and Social Sciences, School of Education and Human Sciences, and School of Computing and Informatics.",
        ],
      },
    ],
  },
  {
    path: "/admissions/undergraduate",
    active: "/admissions",
    eyebrow: "Undergraduate Program",
    title: "October 2026 intake application guidance.",
    description:
      "AIU's October 2026 undergraduate intake is open with an application deadline of 31 July 2026.",
    image: "/images/aiu/campus-welcome.jpg",
    stats: [
      { value: "Oct", label: "2026 intake" },
      { value: "31 Jul", label: "Deadline" },
      { value: "UG", label: "Pathway" },
      { value: "AIU", label: "Application" },
    ],
    sections: [
      {
        eyebrow: "Apply Now",
        title: "Application flow",
        body: [
          "Prepare identity documents, academic transcripts, English proficiency evidence, and scholarship documents where relevant.",
          "Check age, academic, English language, and scholarship requirements before submission.",
          "Eligible applicants may be invited for scholarship interview assessment.",
        ],
      },
      {
        eyebrow: "Helpful Pages",
        title: "Continue inside this website",
        links: [
          { label: "Scholarship", href: "/scholarship" },
          { label: "Academic Programmes", href: "/programmes" },
          { label: "Contact Admissions", href: "/contact" },
        ],
      },
    ],
  },
  {
    path: "/admissions/postgraduate",
    active: "/admissions",
    eyebrow: "Postgraduate Program",
    title: "Coursework and research pathways at AIU.",
    description:
      "Postgraduate study at AIU is administered through the Centre for Graduate Studies and anchored in social business, research, and enterprise solutions.",
    image: "/images/aiu/campus-3zeros.jpg",
    stats: [
      { value: "CGS", label: "Centre" },
      { value: "5", label: "Programmes" },
      { value: "5.0", label: "IELTS minimum" },
      { value: "MUET 4", label: "Local requirement" },
    ],
    sections: [
      {
        eyebrow: "Programmes Offered",
        title: "Postgraduate options",
        items: [
          {
            title: "Master in Social Business",
            summary:
              "Coursework pathway with a typical full-time duration of 1.5 to 2 years.",
          },
          {
            title: "Master of Business Management",
            summary:
              "Research pathway with full-time and Malaysian part-time options.",
          },
          {
            title: "Master of Education",
            summary:
              "Research pathway connected to education and human sciences.",
          },
          {
            title: "Doctor of Philosophy (Business Management)",
            summary: "Research doctorate under business management.",
          },
          {
            title: "Doctor of Philosophy (Education)",
            summary: "Research doctorate under education.",
          },
        ],
      },
      {
        eyebrow: "Entry Requirements",
        title: "Core postgraduate requirements",
        body: [
          "Master's degree entry generally requires a recognised bachelor's degree with a minimum CGPA of 2.75 or equivalent.",
          "PhD entry generally requires a recognised master's degree or equivalent experience accepted by the AIU Senate.",
          "International applicants need English language evidence such as IELTS or TOEFL; Malaysian applicants may use MUET.",
        ],
      },
    ],
  },
  {
    path: "/apply-now",
    active: "/admissions",
    eyebrow: "Apply Now",
    title: "Choose your AIU application pathway.",
    description:
      "Start from the undergraduate or postgraduate route, then continue through programmes, scholarship, and contact guidance inside this replacement website.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Applications",
        title: "Application pathways",
        items: [
          {
            title: "Undergraduate",
            summary:
              "October 2026 intake, scholarship review, and applicant guidance.",
            href: "/apply",
          },
          {
            title: "Postgraduate",
            summary: "Coursework and research routes administered by CGS.",
            href: "/apply",
          },
        ],
      },
    ],
  },
  {
    path: "/students/current-student",
    active: "/student-life",
    eyebrow: "Current Student",
    title: "Current student resources and portal access.",
    description:
      "Current students can use this website as the main entry point for student services and authenticated academic workflows.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Student Services",
        title: "Public resources",
        items: [
          {
            title: "Student Handbook",
            summary: "Academic and student guidance documents.",
            href: "/students/student-handbook",
          },
          {
            title: "Student Hub",
            summary: "Student services and campus resource gateway.",
            href: "/student-life/student-hub",
          },
          {
            title: "Library",
            summary: "Learning resources and academic support.",
            href: "/student-life/library",
          },
        ],
      },
      {
        eyebrow: "Portal",
        title: "Authenticated academic services",
        links: [
          { label: "Student Login", href: "/login" },
          { label: "Portal Overview", href: "/ums-overview" },
        ],
      },
    ],
  },
  {
    path: "/students/student-handbook",
    active: "/student-life",
    eyebrow: "Student Handbook",
    title: "Student handbook and academic regulations.",
    description:
      "A public gateway for AIU student handbooks, academic regulations, and repository documents.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Repository",
        title: "Academic references",
        body: [
          "Student handbooks, academic regulations, programme guides, and policy documents should be managed through this website as public repository records.",
        ],
        links: [{ label: "Repository", href: "/repository" }],
      },
    ],
  },
  {
    path: "/student-life/student-hub",
    active: "/student-life",
    eyebrow: "Student Hub",
    title: "Student services hub.",
    description:
      "The Student Hub entry point is represented here as an internal public page so the replacement website keeps visitors inside the new experience.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Student Support",
        title: "Hub areas",
        items: [
          {
            title: "Academic services",
            summary:
              "Registration, courses, attendance, assignments, and results continue inside the authenticated portal.",
            href: "/login",
          },
          {
            title: "Campus services",
            summary:
              "Facilities, library, alumni, and student news remain accessible from Student Life.",
            href: "/student-life",
          },
        ],
      },
    ],
  },
  {
    path: "/student-life/facilities",
    active: "/student-life",
    eyebrow: "Facilities",
    title: "Residential and campus life facilities.",
    description:
      "AIU's fully residential campus supports learning, belonging, and self-discovery through academic, residential, and student-life facilities.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Campus Life",
        title: "Facilities focus",
        body: [
          "Campus facilities should be managed here as public records for accommodation, learning spaces, student activity areas, and visitor guidance.",
        ],
        links: [
          { label: "Student Life", href: "/student-life" },
          { label: "Contact", href: "/contact" },
        ],
      },
    ],
  },
  {
    path: "/student-life/library",
    active: "/student-life",
    eyebrow: "Library",
    title: "Centre of Reference and library services.",
    description:
      "The AIU library supports learning through collections, e-resources, operating information, and student research assistance.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Learning Support",
        title: "Library services",
        items: [
          {
            title: "Collections and e-resources",
            summary: "Academic resources for students, staff, and researchers.",
          },
          {
            title: "Research support",
            summary: "Reference, reading, and academic discovery support.",
          },
          {
            title: "Centre of Reference",
            summary:
              "Listed in AIU's public directory as a core university department.",
            href: "/departments",
          },
        ],
      },
    ],
  },
  {
    path: "/alumni",
    active: "/student-life",
    eyebrow: "Alumni",
    title: "AIU alumni community.",
    description:
      "The alumni page connects graduates, achievements, stories, and community updates inside the replacement public site.",
    image: "/images/aiu/campus-3zeros.jpg",
    sections: [
      {
        eyebrow: "Community",
        title: "Alumni links",
        items: [
          {
            title: "Wall of Fame",
            summary: "Graduate stories and recognition.",
            href: "/alumni/wall-of-fame",
          },
          {
            title: "News",
            summary: "Alumni-related news and student activities.",
            href: "/news",
          },
        ],
      },
    ],
  },
  {
    path: "/alumni/wall-of-fame",
    active: "/student-life",
    eyebrow: "Wall of Fame",
    title: "AIU alumni wall of fame.",
    description:
      "A public recognition page for outstanding alumni stories and achievements.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Recognition",
        title: "Future managed content",
        body: [
          "This page is ready for managed alumni profiles, achievements, and graduate stories.",
        ],
      },
    ],
  },
  {
    path: "/repository",
    active: "/student-life",
    eyebrow: "Repository",
    title: "Public AIU documents and references.",
    description:
      "A repository area for student handbooks, regulations, calendars, forms, publications, and public lecture materials.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Documents",
        title: "Document categories",
        items: [
          {
            title: "Student Handbook",
            summary: "Student guidance and academic expectations.",
            href: "/students/student-handbook",
          },
          {
            title: "Academic Calendar",
            summary: "Foundation and undergraduate session references.",
            href: "/academic-programmes",
          },
          {
            title: "Public Lecture Series",
            summary: "Public lectures and academic engagement materials.",
            href: "/public-lecture-series",
          },
        ],
      },
    ],
  },
  {
    path: "/ace-sedi",
    active: "/ace-sedi",
    eyebrow: "ACE-SEDI",
    title:
      "AIU Centre of Excellence in Socio-Economic Development and Innovation.",
    description:
      "ACE-SEDI connects AIU's social business identity, research, development, and innovation work around socio-economic impact.",
    image: "/images/aiu/campus-3zeros.jpg",
    sections: [
      {
        eyebrow: "Social Business",
        title: "Socio-economic development and innovation",
        body: [
          "ACE-SEDI is represented as a full local page so social business, research, and community impact can be published without sending users away from the replacement site.",
        ],
        links: [
          {
            label: "Albukhary Social Business Journal",
            href: "/albukhary-social-business-journal",
          },
          { label: "Programmes", href: "/programmes" },
        ],
      },
    ],
  },
  {
    path: "/albukhary-social-business-journal",
    active: "/ace-sedi",
    eyebrow: "ASBJ",
    title: "Albukhary Social Business Journal.",
    description:
      "A publication gateway for AIU research, social business scholarship, and innovation stories.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Research",
        title: "Journal focus",
        body: [
          "The journal page can host issues, calls for papers, editorial information, and research highlights connected to AIU's social business mission.",
        ],
      },
    ],
  },
  {
    path: "/aiunique",
    active: "/news",
    eyebrow: "Monthly Event Highlights",
    title: "AIUNIQUE monthly highlights.",
    description:
      "Monthly highlights collect university events, student activities, and campus life into a public publication stream.",
    image: "/images/aiu/campus-3zeros.jpg",
    sections: [
      {
        eyebrow: "Latest",
        title: "Monthly highlights",
        items: monthlyHighlights,
      },
    ],
  },
  {
    path: "/career",
    active: "/about",
    eyebrow: "Career",
    title: "Join AIU.",
    description:
      "A local public career page for future vacancies, application guidance, and staff recruitment information.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Careers",
        title: "Future managed content",
        body: [
          "Career listings can be managed here so the replacement site keeps visitors inside the new AIU public experience.",
        ],
      },
    ],
  },
  {
    path: "/publications",
    active: "/news",
    eyebrow: "Publications",
    title: "AIU publications.",
    description:
      "A local publication index for reports, magazines, journals, public documents, and campaign materials.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Publications",
        title: "Publication types",
        items: [
          {
            title: "Monthly Highlights",
            summary: "Student and campus activity publication stream.",
            href: "/aiunique",
          },
          {
            title: "Repository",
            summary: "Regulations, forms, and handbooks.",
            href: "/repository",
          },
        ],
      },
    ],
  },
  {
    path: "/press-release",
    active: "/news",
    eyebrow: "Press Release",
    title: "AIU press releases.",
    description:
      "A local page for official public statements, announcements, and media-facing releases.",
    image: "/images/aiu/campus-3zeros.jpg",
    sections: [
      {
        eyebrow: "Media",
        title: "Future managed content",
        body: [
          "Press releases can be published here with categories, dates, and newsroom ownership.",
        ],
      },
    ],
  },
  {
    path: "/public-lecture-series",
    active: "/news",
    eyebrow: "Public Lecture Series",
    title: "AIU public lecture series.",
    description:
      "A public academic engagement page for lectures, recordings, posters, and speaker information.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Academic Engagement",
        title: "Lecture archive",
        body: [
          "This page is ready for managed public lecture entries and academic outreach content.",
        ],
      },
    ],
  },
  {
    path: "/convocation",
    active: "/student-life",
    eyebrow: "Convocation",
    title: "AIU convocation information.",
    description:
      "A local convocation page for graduate notices, ceremony guidance, and celebration updates.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Graduates",
        title: "Future managed content",
        body: [
          "Convocation updates can be managed here with ceremony schedules, forms, robe collection guidance, and graduate announcements.",
        ],
      },
    ],
  },
  {
    path: "/admissions-and-applications",
    active: "/admissions",
    eyebrow: "Admissions and Applications",
    title: "Undergraduate and postgraduate applications.",
    description:
      "A local replacement for the admissions and applications page, covering October 2026 undergraduate intake and postgraduate pathways.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Choose Pathway",
        title: "Application pages",
        items: [
          {
            title: "Undergraduate Program",
            summary:
              "October 2026 intake is open with a 31 July 2026 deadline.",
            href: "/apply",
          },
          {
            title: "Postgraduate Program",
            summary: "Research and coursework pathways through CGS.",
            href: "/apply",
          },
          {
            title: "Scholarship",
            summary:
              "Criteria, interview assessment, and Scholarship Unit contacts.",
            href: "/scholarship",
          },
        ],
      },
    ],
  },
]

const governanceDetailPages: PublicDetailPage[] = [
  {
    path: "/about/pro-chancellor",
    active: "/about",
    eyebrow: "Pro-Chancellor",
    title: "Sonny Bill Williams",
    description:
      "AIU's Pro-Chancellor brings global leadership, sports excellence, humanitarian advocacy, and youth empowerment into the university's values-driven public identity.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Leadership",
        title: "Pro-Chancellor profile",
        body: [
          "Sonny Bill Williams is recognised globally for elite sport, humanitarian causes, cultural integration, and youth empowerment.",
          "AIU positions his leadership presence around the 5A core values, the university's 8-Hour Rule, student engagement, community outreach, and the mission of nurturing globally competitive and socially responsible graduates.",
        ],
      },
    ],
  },
  {
    path: "/about/board-of-governors",
    active: "/about",
    eyebrow: "Board of Governors",
    title: "Meet Our Board of Governors.",
    description:
      "The Board of Governors monitors and reviews AIU's overall operations, strategic direction, educational character, mission, constitution, rules, and policies.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Governance",
        title: "Board members",
        items: governanceGroups.boardOfGovernors,
      },
    ],
  },
  {
    path: "/about/senate",
    active: "/about",
    eyebrow: "Senate",
    title: "Meet Our Senate Members.",
    description:
      "AIU Senate membership brings together university leadership, deans, directors, professors, registrar, and ex-officio representatives for academic governance.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Academic Governance",
        title: "Senate members",
        items: governanceGroups.senate,
      },
    ],
  },
  {
    path: "/about/university-management-committee",
    active: "/about",
    eyebrow: "University Management Committee",
    title: "Meet Our University Management Committee.",
    description:
      "The University Management Committee coordinates senior operational leadership across the Vice Chancellor's office, registry, finance, ICT, and corporate planning.",
    image: "/images/aiu/campus-3zeros.jpg",
    sections: [
      {
        eyebrow: "Management",
        title: "Committee members",
        items: governanceGroups.universityManagementCommittee,
      },
    ],
  },
  {
    path: "/about/senior-management-committee",
    active: "/about",
    eyebrow: "Senior Management Committee",
    title: "Meet Our Senior Management Committee.",
    description:
      "The Senior Management Committee includes university executives, deans, centre directors, quality, research, library, finance, ICT, HR, and academic operations leaders.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Senior Management",
        title: "Committee members",
        items: governanceGroups.seniorManagementCommittee,
      },
    ],
  },
]

const newsDetailPages: PublicDetailPage[] = latestNews.map((item) => ({
  path: item.href,
  active: "/news",
  eyebrow: item.category,
  title: item.title,
  description: item.summary,
  image: "/images/aiu/campus-3zeros.jpg",
  stats: [
    { value: "AIU", label: "News" },
    { value: item.date.split(" ")[0], label: "Month" },
    { value: "2026", label: "Year" },
    { value: "3ZERO", label: "Campus life" },
  ],
  sections: [
    {
      eyebrow: item.date,
      title: "News summary",
      body: [item.summary],
      links: [
        { label: "All News", href: "/news" },
        { label: "Monthly Highlights", href: "/aiunique" },
      ],
    },
  ],
}))

export const publicDetailPages: PublicDetailPage[] = [
  ...academicDetailPages,
  ...publicServiceDetailPages,
  ...governanceDetailPages,
  ...newsDetailPages,
]

export const publicDetailPageMap = new Map(
  publicDetailPages.map((page) => [page.path.replace(/\/+$/, ""), page])
)

export function getPublicDetailPage(slug: string[]) {
  const path = `/${slug.join("/")}`.replace(/\/+$/, "")

  return publicDetailPageMap.get(path)
}
