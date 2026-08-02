import re

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from admin_app import models
from executive_app.models import Executive
from teacher_app.models import Teacher


SCHOOLS = [
    {
        "code": "SBSS",
        "name": "School of Business and Social Sciences",
        "slug": "school-of-business-social-sciences",
        "description": (
            "Academic school for social business, management, economics, finance, "
            "politics, international relations, and social development."
        ),
        "about": (
            "The School of Business and Social Sciences upholds AIU's educational "
            "mission through innovative curricula and practical social-business "
            "learning. Its programmes combine discipline-specific knowledge with "
            "community engagement, leadership, and AIU's 5A core values."
        ),
        "vision": (
            "To be a centre of excellence in learning social business through an "
            "innovative and creative curriculum."
        ),
        "mission": [
            "Provide graduates with quality education through innovative curriculum and research experiences.",
            "Disseminate knowledge through teaching, academic publication, and presentation.",
            "Contribute to the academic advancement of business management, development studies, and social business.",
            "Create knowledge through academic research and smart-partnership collaboration.",
        ],
    },
    {
        "code": "SEHS",
        "name": "School of Education and Human Sciences",
        "slug": "school-of-education-human-sciences",
        "description": (
            "Academic school for education, early childhood education, media and "
            "communication, and human sciences."
        ),
        "about": (
            "The School of Education and Human Sciences equips students for work in "
            "education, social care, health, media and communication, and public "
            "policy through interdisciplinary, technology-driven learning."
        ),
        "vision": (
            "To be a centre of excellence in learning social business through an "
            "innovative and creative curriculum."
        ),
        "mission": [
            "Provide graduates with quality education through innovative curriculum and research experiences.",
            "Disseminate knowledge through teaching, academic publication, and presentation.",
            "Contribute to academic advancement through interdisciplinary education and human sciences.",
            "Create knowledge through academic research and smart-partnership collaboration.",
        ],
    },
    {
        "code": "SCI",
        "name": "School of Computing and Informatics",
        "slug": "school-of-computing-and-informatics",
        "description": (
            "Academic school for computer science, data science, cybersecurity, "
            "computing research, and informatics."
        ),
        "about": (
            "The School of Computing and Informatics develops technically competent, "
            "adaptable, and service-minded computing professionals grounded in AIU's "
            "social-business mission and 5A core values."
        ),
        "vision": (
            "To be the point of reference for computing and informatics in industry "
            "and community towards a sustainable world."
        ),
        "mission": [
            "Produce global computing and informatics experts and professionals to serve humanity.",
            "Produce adaptable, balanced, and well-rounded graduates with philanthropic attitudes.",
            "Inculcate integrated minds towards social inclusion globally.",
        ],
    },
]


CENTERS = [
    {
        "code": "CDAE",
        "name": "Centre for Development of Academic Excellence",
        "slug": "centre-for-development-of-academic-excellence",
        "description": (
            "AIU's teaching and learning hub for academic development, teaching "
            "quality, learning technology, and curriculum support."
        ),
        "about": (
            "CDAE partners with academic and non-academic staff and students to "
            "support excellence and innovation in teaching and learning through "
            "orientation, training, mentorship, research, and innovation."
        ),
        "offerings": [
            "Teaching and Delivery Sharing Session (TeDSS)",
            "CDAE Faculty Fellow",
            "Workshops and inductions",
            "Student Evaluation of Course and Teaching (SEC and SET)",
            "Programme management support",
            "Learning management system support",
            "SULAM project support",
        ],
    },
    {
        "code": "CFGS",
        "name": "Centre for Foundation and General Studies",
        "slug": "centre-for-foundation-and-general-studies",
        "description": (
            "Academic centre providing one-year pre-university pathways and general "
            "studies for undergraduate readiness."
        ),
        "about": (
            "CFGS prepares students for undergraduate study in an international "
            "learning environment while developing communication, leadership, social "
            "responsibility, independent learning, and AIU's 5A core values."
        ),
        "offerings": [
            "Foundation in Computing",
            "Foundation in Arts",
            "General studies",
            "Undergraduate readiness",
            "Leadership and social responsibility",
        ],
    },
    {
        "code": "CGS",
        "name": "Centre for Graduate Studies",
        "slug": "centre-for-graduate-studies",
        "description": (
            "Academic centre administering postgraduate coursework, research "
            "programmes, and student research projects."
        ),
        "about": (
            "CGS administers AIU's postgraduate study and research projects, anchored "
            "in social business, sustainable enterprise solutions, and research with "
            "social and environmental impact."
        ),
        "offerings": [
            "Master in Social Business",
            "Master of Business Management",
            "Master of Education",
            "Master of Computing",
            "Doctor of Philosophy",
            "Postgraduate research administration",
        ],
    },
    {
        "code": "LC",
        "name": "Language Centre",
        "slug": "language-centre",
        "description": (
            "Academic language centre providing accessible language programmes for "
            "students, prospective learners, institutions, and the community."
        ),
        "about": (
            "AIU Language Centre prepares learners for international English "
            "qualifications and provides engaging language programmes and services "
            "for schools, higher education institutions, lifelong learners, and the "
            "wider community."
        ),
        "offerings": [
            "IELTS preparation",
            "General English",
            "Business English and Professional English",
            "English camps and creative writing",
            "Buddy programmes",
        ],
    },
    {
        "code": "CSAA",
        "name": "Centre for Student Affairs and Alumni",
        "slug": "centre-for-student-affairs-and-alumni",
        "description": (
            "Student-support centre for welfare, counselling, residential life, "
            "career development, student activities, and alumni engagement."
        ),
        "about": (
            "CSAA supports students throughout university life by coordinating "
            "wellbeing, counselling, residence, career, co-curricular, and alumni "
            "services."
        ),
        "offerings": [
            "Student affairs",
            "Counselling and wellbeing",
            "Residential support",
            "Career development",
            "Alumni engagement",
        ],
    },
    {
        "code": "ICT",
        "name": "Information, Communication and Technology Centre",
        "slug": "information-communication-and-technology-centre",
        "description": (
            "Technology centre delivering ICT operations, systems, programming, "
            "technical support, and digital services."
        ),
        "about": (
            "The ICT Centre supports university learning and operations through "
            "reliable infrastructure, systems, technical support, programming, and "
            "technology project delivery."
        ),
        "offerings": [
            "ICT operations",
            "Systems and programming",
            "Technical support",
            "Technology projects",
        ],
    },
    {
        "code": "CPC",
        "name": "Centre for Corporate Planning and Communication",
        "slug": "centre-for-corporate-planning-and-communication",
        "description": (
            "Corporate centre for institutional planning, communications, events, "
            "publications, stakeholder messaging, and student recruitment."
        ),
        "about": (
            "CPC coordinates strategic corporate planning and communication so that "
            "the university presents clear, consistent information to prospective "
            "students, partners, and the wider public."
        ),
        "offerings": [
            "Corporate planning",
            "Corporate communication",
            "Events and publications",
            "Student recruitment",
        ],
    },
    {
        "code": "COR",
        "name": "Centre of Reference (Library)",
        "slug": "centre-of-reference-library",
        "description": (
            "Library and reference centre providing learning resources, research "
            "support, information services, and study spaces."
        ),
        "about": (
            "The Centre of Reference supports teaching, learning, and research with "
            "library collections, reference services, learning resources, and access "
            "to information."
        ),
        "offerings": [
            "Library services",
            "Reference services",
            "Learning resources",
            "Research support",
        ],
    },
    {
        "code": "CQAA",
        "name": "Centre for Quality Assurance and Accreditation",
        "slug": "centre-for-quality-assurance-and-accreditation",
        "description": (
            "Quality centre overseeing institutional quality assurance, programme "
            "accreditation, policy, and continuous improvement."
        ),
        "about": (
            "CQAA coordinates quality-management and accreditation processes to "
            "support compliance, programme quality, and continuous institutional "
            "improvement."
        ),
        "offerings": [
            "Quality assurance",
            "Programme accreditation",
            "Quality policy support",
            "Continuous improvement",
        ],
    },
    {
        "code": "ACE-SEDI",
        "name": "AIU Centre of Excellence in Socio-Economic Development and Innovation",
        "slug": "aiu-centre-of-excellence-in-socio-economic-development-and-innovation",
        "description": (
            "Research centre advancing socio-economic development, social business, "
            "innovation, and impact-focused knowledge."
        ),
        "about": (
            "ACE-SEDI is one of the specialist centres under the research and "
            "innovation portfolio, connecting AIU's social-business mission with "
            "socio-economic development and innovation."
        ),
        "offerings": [
            "Socio-economic development research",
            "Social-business innovation",
            "Impact initiatives",
            "Knowledge exchange",
        ],
    },
    {
        "code": "CRIM",
        "name": "Centre for Research and Innovation Management",
        "slug": "centre-for-research-and-innovation-management",
        "description": (
            "Research centre coordinating research governance, innovation management, "
            "and support for university research activity."
        ),
        "about": (
            "CRIM supports the planning, governance, administration, and development "
            "of research and innovation across the university."
        ),
        "offerings": [
            "Research management",
            "Innovation management",
            "Research governance",
            "Researcher support",
        ],
    },
    {
        "code": "CCIE",
        "name": "Centre for Community and Industry Engagement",
        "slug": "centre-for-community-and-industry-engagement",
        "description": (
            "Engagement centre connecting AIU with communities, industry partners, "
            "and collaborative impact initiatives."
        ),
        "about": (
            "CCIE builds relationships and coordinates engagement between the "
            "university, communities, and industry to support collaboration and "
            "social impact."
        ),
        "offerings": [
            "Community engagement",
            "Industry engagement",
            "Partnership development",
            "Collaborative impact initiatives",
        ],
    },
]


DEPARTMENTS = [
    {
        "code": "VCO",
        "name": "Vice Chancellor's Office",
        "description": (
            "University leadership office responsible for strategic direction, "
            "corporate governance, official duties, and coordination across schools, "
            "departments, sections, and units."
        ),
    },
    {
        "code": "DVCA",
        "name": "Deputy Vice Chancellor (Academic)'s Office",
        "description": (
            "Academic leadership office responsible for academic matters, student "
            "affairs, scholarship access, and a respectful learning environment."
        ),
    },
    {
        "code": "DVCRI",
        "name": "Deputy Vice Chancellor (Research and Innovation)'s Office",
        "description": (
            "Research and innovation leadership office overseeing socio-economic "
            "development, research management, and community and industry engagement."
        ),
    },
    {
        "code": "REG",
        "name": "Registry Department",
        "description": (
            "Department supporting university governance, regulatory compliance, "
            "administration, policy, and official records."
        ),
    },
    {
        "code": "AMD",
        "name": "Academic Management Department (AMD)",
        "description": (
            "Department supporting admissions, academic administration, examinations, "
            "student records, and international student services."
        ),
    },
    {
        "code": "HRD",
        "name": "Human Resource Department",
        "description": (
            "Department responsible for recruitment, appointments, staff welfare, "
            "professional development, and human-resource records."
        ),
    },
    {
        "code": "FIN",
        "name": "Finance Department",
        "description": (
            "Department managing university finance, accounting, budgeting, payments, "
            "financial controls, and related services."
        ),
    },
]


UNITS = [
    {
        "code": "PROC",
        "name": "Procurement Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "FIN",
        "description": "Procurement services, purchasing coordination, and supplier administration.",
    },
    {
        "code": "ADM",
        "name": "Admission Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "AMD",
        "description": "Offer, enrolment, registration, clearance, and admission-record support.",
    },
    {
        "code": "SRU",
        "name": "Student Recruitment Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CPC",
        "description": "Prospective-student engagement and student recruitment support.",
    },
    {
        "code": "SCHOL",
        "name": "Scholarship Unit",
        "unit_type": models.Unit.UNIT_STUDENT_AFFAIRS,
        "center": "CSAA",
        "description": "Scholarship assessment, interviews, awards, and student scholarship support.",
    },
    {
        "code": "FMU",
        "name": "Facility Management Unit",
        "unit_type": models.Unit.UNIT_SERVICE,
        "department": "VCO",
        "description": "Campus facilities coordination, maintenance, and infrastructure services.",
    },
    {
        "code": "ISU",
        "name": "International Student Unit",
        "unit_type": models.Unit.UNIT_STUDENT_AFFAIRS,
        "department": "AMD",
        "description": "Visa, student-pass, immigration, and international-student support.",
    },
    {
        "code": "ERU",
        "name": "Examination and Records Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "AMD",
        "description": "Examination operations and official academic student records.",
    },
    {
        "code": "SBSS-ADMIN",
        "name": "SBSS Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "school": "SBSS",
        "description": "Administrative coordination and operational support for SBSS.",
    },
    {
        "code": "SEHS-ADMIN",
        "name": "SEHS Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "school": "SEHS",
        "description": "Administrative coordination and operational support for SEHS.",
    },
    {
        "code": "SCI-ADMIN",
        "name": "SCI Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "school": "SCI",
        "description": "Administrative coordination and operational support for SCI.",
    },
    {
        "code": "CDAE-ADMIN",
        "name": "CDAE Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CDAE",
        "description": "Administrative coordination and operational support for CDAE.",
    },
    {
        "code": "CFGS-ADMIN",
        "name": "CFGS Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CFGS",
        "description": "Administrative coordination and operational support for foundation and general studies.",
    },
    {
        "code": "CGS-ADMIN",
        "name": "CGS Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CGS",
        "description": "Administrative coordination and operational support for graduate studies.",
    },
    {
        "code": "LC-ADMIN",
        "name": "Language Centre Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "LC",
        "description": "Administrative coordination and operational support for the Language Centre.",
    },
    {
        "code": "ICT-ADMIN",
        "name": "ICT Centre Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "ICT",
        "description": "Administrative and technical support for the ICT Centre.",
    },
    {
        "code": "CPC-ADMIN",
        "name": "CPC Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CPC",
        "description": "Administrative coordination and operational support for the Centre for Corporate Planning and Communication.",
    },
    {
        "code": "COR-ADMIN",
        "name": "Library Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "COR",
        "description": "Administrative and library support services.",
    },
    {
        "code": "CQAA-ADMIN",
        "name": "CQAA Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CQAA",
        "description": "Administrative coordination and operational support for quality assurance and accreditation.",
    },
    {
        "code": "CSAA-ADMIN",
        "name": "CSAA Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CSAA",
        "description": "Administrative and student-welfare support for the Centre for Student Affairs and Alumni.",
    },
    {
        "code": "CTN-ADMIN",
        "name": "Canteen Admin",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CSAA",
        "description": "Canteen administration and student meal allowance operations.",
    },
    {
        "code": "ACE-SEDI-ADMIN",
        "name": "ACE-SEDI Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "ACE-SEDI",
        "description": "Administrative support for AIU Centre of Excellence in Socio-Economic Development and Innovation.",
    },
    {
        "code": "CRIM-ADMIN",
        "name": "CRIM Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CRIM",
        "description": "Administrative support for the Centre for Research and Innovation Management.",
    },
    {
        "code": "CCIE-ADMIN",
        "name": "CCIE Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "center": "CCIE",
        "description": "Administrative support for the Centre for Community and Industry Engagement.",
    },
    {
        "code": "VCO-ADMIN",
        "name": "Vice Chancellor's Office Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "VCO",
        "description": "Administrative support for the Vice Chancellor's Office.",
    },
    {
        "code": "DVCA-ADMIN",
        "name": "DVCA Office Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "DVCA",
        "description": "Administrative support for the Deputy Vice Chancellor (Academic)'s Office.",
    },
    {
        "code": "DVCRI-ADMIN",
        "name": "DVCRI Office Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "DVCRI",
        "description": "Administrative support for the Deputy Vice Chancellor (Research and Innovation)'s Office.",
    },
    {
        "code": "REG-ADMIN",
        "name": "Registry Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "REG",
        "description": "Administrative support for the Registry Department.",
    },
    {
        "code": "AMD-ADMIN",
        "name": "AMD Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "AMD",
        "description": "Administrative support for the Academic Management Department.",
    },
    {
        "code": "HRD-ADMIN",
        "name": "HR Department Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "HRD",
        "description": "Administrative support for the Human Resource Department.",
    },
    {
        "code": "FIN-ADMIN",
        "name": "Finance Department Administrative Unit",
        "unit_type": models.Unit.UNIT_ADMINISTRATIVE,
        "department": "FIN",
        "description": "Administrative support for the Finance Department.",
    },
]


SCHOOL_PROGRAMMES = {
    "SBSS": [
        ("SBSS-BBA", "Bachelor of Business Administration (Honours)", "Bachelor", 3),
        ("SBSS-BBAM", "Bachelor of Business Administration (Honours) (Marketing)", "Bachelor", 3),
        ("SBSS-BBAHRM", "Bachelor of Business Administration (Honours) (Human Resource Management)", "Bachelor", 3),
        ("SBSS-BSD", "Bachelor of Social Development (Honours)", "Bachelor", 3),
        ("SBSS-BECO", "Bachelor of Economics (Honours)", "Bachelor", 3),
        ("SBSS-BFIN", "Bachelor of Finance (Islamic Finance) (Honours)", "Bachelor", 3),
        ("SBSS-BPIR", "Bachelor of Politics and International Relations (Honours)", "Bachelor", 3),
        ("SBSS-BBACS", "Bachelor of Business Administration with Computer Science (Honours)", "Bachelor", 3),
        ("SBSS-MSB", "Master in Social Business", "Master", None),
        ("SBSS-MBM", "Master of Business Management (by Research)", "Master", None),
        ("SBSS-PHD", "Doctor of Philosophy (Management and Administration)", "Doctorate", None),
    ],
    "SEHS": [
        ("SEHS-BEE", "Bachelor of Elementary Education (Honours)", "Bachelor", None),
        ("SEHS-BECE", "Bachelor in Early Childhood Education (Honours)", "Bachelor", None),
        ("SEHS-BMC", "Bachelor of Media and Communication (Honours)", "Bachelor", None),
        ("SEHS-MED", "Master of Education (by Research)", "Master", None),
        ("SEHS-PHD", "Doctor of Philosophy (Teaching, Training and Education Science)", "Doctorate", None),
    ],
    "SCI": [
        ("SCI-BCS", "Bachelor in Computer Science (Honours)", "Bachelor", 3),
        ("SCI-BDS", "Bachelor in Data Science (Honours)", "Bachelor", None),
        ("SCI-BITC", "Bachelor in Information Technology (Cybersecurity) (Honours)", "Bachelor", None),
        ("SCI-MCOMP", "Master of Computing (by Research)", "Master", None),
        ("SCI-PHD", "Doctor of Philosophy in Computer Science", "Doctorate", None),
    ],
}


CENTER_PROGRAMMES = {
    "CDAE": [
        ("CDAE-TEDSS", "Teaching and Delivery Sharing Session (TeDSS)", models.Program.PROGRAM_CENTER),
        ("CDAE-FELLOW", "CDAE Faculty Fellow", models.Program.PROGRAM_CENTER),
        ("CDAE-WS", "Academic Development Workshops and Inductions", models.Program.PROGRAM_CENTER),
        ("CDAE-SULAM", "SULAM Project Support", models.Program.PROGRAM_CENTER),
    ],
    "CFGS": [
        ("CFGS-FC", "Foundation in Computing", models.Program.PROGRAM_ACADEMIC),
        ("CFGS-FA", "Foundation in Arts", models.Program.PROGRAM_ACADEMIC),
    ],
    "CGS": [
        ("CGS-MSB", "Master in Social Business", models.Program.PROGRAM_ACADEMIC),
        ("CGS-MBM", "Master of Business Management (by Research)", models.Program.PROGRAM_ACADEMIC),
        ("CGS-MED", "Master of Education (by Research)", models.Program.PROGRAM_ACADEMIC),
        ("CGS-MCOMP", "Master of Computing (by Research)", models.Program.PROGRAM_ACADEMIC),
        ("CGS-PHD", "Doctor of Philosophy", models.Program.PROGRAM_ACADEMIC),
    ],
    "LC": [
        ("LC-IELTS", "Preparatory Course for International English Language Testing System (IELTS)", models.Program.PROGRAM_ACADEMIC),
        ("LC-GE", "General English", models.Program.PROGRAM_ACADEMIC),
        ("LC-BE", "Business English and Professional English", models.Program.PROGRAM_ACADEMIC),
        ("LC-CW", "English Camps and Creative Writing", models.Program.PROGRAM_CENTER),
        ("LC-BUDDY", "Buddy Programmes", models.Program.PROGRAM_CENTER),
    ],
}


TEACHERS = [
    # SBSS - School of Business and Social Sciences
    {"email": "annuar.nassir@aiu.edu.my", "name": "Professor Dr. Annuar Bin Md Nassir", "designation": "Acting Dean, School of Business and Social Sciences", "school": "SBSS"},
    {"email": "mohamad.mokhlis@aiu.edu.my", "name": "Mohamad Mokhlis Bin Ahmad Fuad", "designation": "Deputy Dean, School of Business and Social Sciences", "school": "SBSS"},
    {"email": "yusnidah.ibrahim@aiu.edu.my", "name": "Professor Dr. Yusnidah Binti Ibrahim", "designation": "Professor / Director, Centre for Graduate Studies", "school": "SBSS"},
    {"email": "nor.azilah@aiu.edu.my", "name": "Professor Dr. Nor Azilah Binti Husin", "designation": "Professor / Coordinator of Master in Business Management & PhD in Management", "school": "SBSS"},
    {"email": "sofri.yahya@aiu.edu.my", "name": "Professor Dr. Sofri Bin Yahya", "designation": "Professor / Coordinator of Master in Social Business", "school": "SBSS"},
    {"email": "noor.jannah@aiu.edu.my", "name": "Noor Jannah Binti Afi", "designation": "Lecturer / Head of Programme, Bachelor of Business Administration (Honours)", "school": "SBSS"},
    {"email": "siti.maizalaizzah@aiu.edu.my", "name": "Siti Maizalaizzah Akma Binti Adnan", "designation": "Lecturer / Head of Programme, BBA with Computer Science / Acting HoP, BBA (Marketing)", "school": "SBSS"},
    {"email": "aliaa.diyana@aiu.edu.my", "name": "Aliaa Diyana Binti Zamri", "designation": "Lecturer / Head of Programme, BBA (Human Resource Management)", "school": "SBSS"},
    {"email": "osaid.abdaljawwad@aiu.edu.my", "name": "Osaid N.A. Abdaljawwad", "designation": "Lecturer / Head of Programme, Bachelor of Economics (Honours)", "school": "SBSS"},
    {"email": "farah.syazwani@aiu.edu.my", "name": "Farah Syazwani Binti Hayrol Aziz", "designation": "Lecturer / Head of Programme, Bachelor of Social Development (Honours)", "school": "SBSS"},
    {"email": "noorul.hafidzah@aiu.edu.my", "name": "Dr. Noorul Hafidzah Binti Zawawi", "designation": "Senior Lecturer / Head of Programme, Bachelor of Politics and International Relations (Honours)", "school": "SBSS"},
    {"email": "salfarina.gapor@aiu.edu.my", "name": "Professor Dr. Salfarina Binti Abdul Gapor", "designation": "Professor / Director, Centre for Research and Innovation Management (CRIM)", "school": "SBSS"},
    {"email": "suraya.mokhtar@aiu.edu.my", "name": "Associate Professor Dr. Suraya Hanim Binti Mokhtar", "designation": "Associate Professor / Director, ACE-SEDI", "school": "SBSS"},
    {"email": "ayesah.abubakar@aiu.edu.my", "name": "Associate Professor Dr. Ayesah Uy Abubakar", "designation": "Associate Professor", "school": "SBSS"},
    {"email": "norizan.azizan@aiu.edu.my", "name": "Associate Professor Dr. Norizan Binti Azizan", "designation": "Associate Professor", "school": "SBSS"},
    {"email": "mikio.oishi@aiu.edu.my", "name": "Associate Professor Dr. Mikio Oishi", "designation": "Associate Professor", "school": "SBSS"},
    {"email": "reazul.islam@aiu.edu.my", "name": "Dr. Reazul Islam", "designation": "Senior Lecturer", "school": "SBSS"},
    {"email": "noorasyikin.mohdnoh@aiu.edu.my", "name": "Dr. Noorasyikin Binti Mohd Noh", "designation": "Senior Lecturer / Director, Centre for Quality Assurance and Accreditation", "school": "SBSS"},
    {"email": "ravindran.raman@aiu.edu.my", "name": "Ravindran A/L Raman", "designation": "Senior Lecturer", "school": "SBSS"},
    {"email": "hamid.alwesabi@aiu.edu.my", "name": "Dr. Hamid Abdulkhaleq Hassan Al-Wesabi", "designation": "Lecturer", "school": "SBSS"},
    {"email": "hla.theingi@aiu.edu.my", "name": "Hla Theingi Win", "designation": "Lecturer", "school": "SBSS"},
    {"email": "abdul.wafi@aiu.edu.my", "name": "Abdul Wafi Bin Samsurrijal", "designation": "Lecturer / Coordinator Internship", "school": "SBSS"},
    {"email": "nur.arfah@aiu.edu.my", "name": "Nur Arfah Binti Abdul Sabian", "designation": "Lecturer / Head of Programme, Bachelor of Finance (Islamic Finance) (Honours)", "school": "SBSS"},
    {"email": "amirul.syafiq@aiu.edu.my", "name": "Amirul Syafiq Bin Mohd Ghazali", "designation": "Lecturer", "school": "SBSS"},
    {"email": "ammar.alqolaq@aiu.edu.my", "name": "Dr. Ammar J. K. Alqolaq", "designation": "Lecturer", "school": "SBSS"},
    {"email": "afifi.nordin@aiu.edu.my", "name": "Afifi Bin Nordin", "designation": "Lecturer", "school": "SBSS"},
    {"email": "aiman.muqri@aiu.edu.my", "name": "Aiman Muqri Bin Ahmad Shukri", "designation": "Lecturer / Deputy Director, Centre for Community and Industry Engagement", "school": "SBSS"},
    {"email": "nur.jazanadia@aiu.edu.my", "name": "Nur Jazanadia Binti Jamaludin", "designation": "Lecturer", "school": "SBSS"},
    {"email": "mohd.faiz.fansuri@aiu.edu.my", "name": "Mohd Faiz Fansuri Bin Mohd Affandy", "designation": "Lecturer", "school": "SBSS"},
    {"email": "emily.rogos@aiu.edu.my", "name": "Emily Anak Rogos", "designation": "Lecturer", "school": "SBSS"},
    {"email": "nurzalyna.zaki@aiu.edu.my", "name": "Nurzalyna Binti Mohamed Zaki", "designation": "Lecturer", "school": "SBSS"},

    # SCI - School of Computing and Informatics
    {"email": "basheer.riskhan@aiu.edu.my", "name": "Associate Professor Dr. Basheer Riskhan", "designation": "Dean, School of Computing and Informatics", "school": "SCI"},
    {"email": "nadiah.arsat@aiu.edu.my", "name": "Nadiah Binti Arsat", "designation": "Deputy Dean, School of Computing and Informatics", "school": "SCI"},
    {"email": "khalid.hussain@aiu.edu.my", "name": "Professor Dr. Khalid Hussain", "designation": "Professor", "school": "SCI"},
    {"email": "zurinahni.zainol@aiu.edu.my", "name": "Professor Dr. Zurinahni Binti Zainol", "designation": "Professor / Coordinator, Master of Computing & PhD in Computer Science", "school": "SCI"},
    {"email": "leelavathi.rajamanickam@aiu.edu.my", "name": "Associate Professor Ts. Dr. Leelavathi Rajamanickam", "designation": "Associate Professor", "school": "SCI"},
    {"email": "abu.bakar.ngah@aiu.edu.my", "name": "Ts. Abu Bakar Bin Ngah", "designation": "Lecturer / Director, Centre for Community and Industry Engagement", "school": "SCI"},
    {"email": "mohd.zulkifli@aiu.edu.my", "name": "Ts. Mohd Zulkifli Bin Mohd Zaki", "designation": "Lecturer", "school": "SCI"},
    {"email": "nor.haniza@aiu.edu.my", "name": "Dr. Nor Haniza Binti Mohd Khir", "designation": "Lecturer", "school": "SCI"},

    # SEHS - School of Education and Human Sciences
    {"email": "abdul.malek@aiu.edu.my", "name": "Professor Dr. Abdul Malek Bin Abdul Karim", "designation": "Dean, School of Education and Human Sciences", "school": "SEHS"},
    {"email": "munirah.ghazali@aiu.edu.my", "name": "Professor Dr. Munirah Binti Ghazali", "designation": "Professor", "school": "SEHS"},
    {"email": "nor.hashimah@aiu.edu.my", "name": "Professor Dr. Nor Hashimah Binti Hashim", "designation": "Professor", "school": "SEHS"},
    {"email": "tengku.shahrom@aiu.edu.my", "name": "Associate Professor Dr. Tengku Shahrom Bin Tengku Shahdan", "designation": "Associate Professor", "school": "SEHS"},
    {"email": "kalthom.husain@aiu.edu.my", "name": "Associate Professor Dr. Kalthom Binti Husain", "designation": "Associate Professor", "school": "SEHS"},
    {"email": "bakare.kayode@aiu.edu.my", "name": "Associate Professor Dr. Bakare Kazeem Kayode", "designation": "Associate Professor / Postgraduate Coordinator", "school": "SEHS"},
    {"email": "adhara.ahmad@aiu.edu.my", "name": "Adhara Binti Ahmad", "designation": "Senior Lecturer / Deputy Registrar", "school": "SEHS"},
    {"email": "ildefonso.halipa@aiu.edu.my", "name": "Ildefonso Halipa Jr.", "designation": "Senior Lecturer / Director, Centre for Development of Academic Excellence", "school": "SEHS"},
    {"email": "sitinurbayu.yusoff@aiu.edu.my", "name": "Dr. Sitinurbayu Binti Mohd Yusoff", "designation": "Senior Lecturer", "school": "SEHS"},
    {"email": "amani.mubarak@aiu.edu.my", "name": "Dr. Amani Binti Abdullah Mubarak", "designation": "Senior Lecturer", "school": "SEHS"},
    {"email": "mohamad.nor.hisyam@aiu.edu.my", "name": "Mohamad Nor Hisyam Bin Musa", "designation": "Lecturer / Head of Programme, Bachelor of Media and Communication / Warden", "school": "SEHS"},
    {"email": "nidhoil.ibrahim@aiu.edu.my", "name": "Nidhoil Mohamed Ibrahim", "designation": "Lecturer / Deputy Director, Centre for Student Affairs and Alumni", "school": "SEHS"},
    {"email": "alia.hanim@aiu.edu.my", "name": "Alia Hanim Binti Zainal Abidin", "designation": "Lecturer / Director, Centre for Foundation and General Studies", "school": "SEHS"},
    {"email": "nurul.huda.bakri@aiu.edu.my", "name": "Nurul Huda Binti Hassan Bakri", "designation": "Lecturer / Deputy Director, Centre for Student Affairs and Alumni", "school": "SEHS"},
    {"email": "nur.faridatul@aiu.edu.my", "name": "Nur Faridatul Jamalia Binti Radzali", "designation": "Lecturer / Deputy Director, Centre for Quality Assurance", "school": "SEHS"},
    {"email": "samihah.mahamud@aiu.edu.my", "name": "Samihah Binti Mahamud", "designation": "Lecturer / Head of Programme, Bachelor in Early Childhood Education", "school": "SEHS"},
    {"email": "hisham.barbhuiya@aiu.edu.my", "name": "Dr. Hisham Anand Barbhuiya", "designation": "Lecturer", "school": "SEHS"},
    {"email": "rubini.radza@aiu.edu.my", "name": "Rubini A/P Radza", "designation": "Lecturer", "school": "SEHS"},
    {"email": "nur.syaheera@aiu.edu.my", "name": "Nur Syaheera Binti Zaifuddin", "designation": "Lecturer / Warden", "school": "SEHS"},
    {"email": "faeizaratul.fazeila@aiu.edu.my", "name": "Faeizaratul Fazeila Binti Isa", "designation": "Lecturer", "school": "SEHS"},

    # CFGS - Centre for Foundation and General Studies
    {"email": "irdayu.ibrahim@aiu.edu.my", "name": "Irdayu Binti Ibrahim", "designation": "Head of Programme for Foundation in Computing", "center": "CFGS"},
    {"email": "abu.dzarr@aiu.edu.my", "name": "Abu Dzarr Bin Muhammad Rus", "designation": "Head of Programme for Foundation in Arts", "center": "CFGS"},
    {"email": "syaza.lyana@aiu.edu.my", "name": "Syaza Lyana Binti Mahadzir", "designation": "Lecturer", "center": "CFGS"},
    {"email": "mohd.fadli.zakaria@aiu.edu.my", "name": "Mohd Fadli Bin Zakaria", "designation": "Lecturer", "center": "CFGS"},
    {"email": "farah.nadiah.kudus@aiu.edu.my", "name": "Farah Nadiah Binti Abdul Kudus", "designation": "Lecturer / Warden", "center": "CFGS"},

    # LC - Language Centre
    {"email": "sherina.shahnaz@aiu.edu.my", "name": "Sherina Shahnaz Binti Mohamed Fauzi", "designation": "Director, Language Centre", "center": "LC"},
    {"email": "mubarak.ali@aiu.edu.my", "name": "Mubarak Ali Bin Rakhir Mohamed", "designation": "Teacher, Language Centre", "center": "LC"},
    {"email": "nurul.hamidah@aiu.edu.my", "name": "Nurul Hamidah Binti Mohd Hamdi", "designation": "Senior Teacher, Language Centre", "center": "LC"},
    {"email": "nur.darina@aiu.edu.my", "name": "Nur Darina Binti Ibrahim", "designation": "Teacher, Language Centre", "center": "LC"},
    {"email": "khairunnisha.redzzuan@aiu.edu.my", "name": "Khairunnisha Binti Redzzuan", "designation": "Teacher, Language Centre", "center": "LC"},
    {"email": "ilyas.adam@aiu.edu.my", "name": "Ilyas Bin Adam", "designation": "Teacher, Language Centre", "center": "LC"},
    {"email": "zulaikha.zulkifli@aiu.edu.my", "name": "Zulaikha Binti Zulkifli", "designation": "Teacher, Language Centre", "center": "LC"},
    {"email": "nurfarinaa.firdaus@aiu.edu.my", "name": "Nurfarinaa Binti Mohd Firdaus", "designation": "Teacher, Language Centre", "center": "LC"},
    {"email": "nurulathirah.rusli@aiu.edu.my", "name": "Nurulathirah Fatma Binti Rusli", "designation": "Teacher, Language Centre", "center": "LC"},
]


EXECUTIVES = [
    # SBSS-ADMIN
    {"email": "aina.syafiqah@aiu.edu.my", "name": "Aina Syafiqah Binti Razali", "designation": "Executive", "school": "SBSS", "unit": "SBSS-ADMIN"},
    {"email": "nurul.fatihah.zainudin@aiu.edu.my", "name": "Nurul Fatihah Binti Zainudin", "designation": "Assistant Executive", "school": "SBSS", "unit": "SBSS-ADMIN"},

    # SCI-ADMIN
    {"email": "liliana.rofiki@aiu.edu.my", "name": "Liliana Mas Aliza Binti Rofiki", "designation": "Executive", "school": "SCI", "unit": "SCI-ADMIN"},
    {"email": "fatin.nurin.rahwani@aiu.edu.my", "name": "Fatin Nurin Rahwani Binti Razak", "designation": "Executive", "school": "SCI", "unit": "SCI-ADMIN"},
    {"email": "muhammad.adam.rahman@aiu.edu.my", "name": "Muhammad Adam Bin A. Rahman", "designation": "IT Lab Assistant", "school": "SCI", "unit": "SCI-ADMIN"},

    # SEHS-ADMIN
    {"email": "tun.nazhatul@aiu.edu.my", "name": "Tun Nazhatul Syima Binti Wan Mohd", "designation": "Executive", "school": "SEHS", "unit": "SEHS-ADMIN"},

    # CDAE-ADMIN
    {"email": "nurul.munirah.azam@aiu.edu.my", "name": "Nurul Munirah Binti Md Azam", "designation": "Executive", "center": "CDAE", "unit": "CDAE-ADMIN"},
    {"email": "muhammad.arif.nurhan@aiu.edu.my", "name": "Muhammad Arif Nurhan Bin Mohd Nazri", "designation": "Executive", "center": "CDAE", "unit": "CDAE-ADMIN"},
    {"email": "mifzal.aqmar@aiu.edu.my", "name": "Mifzal Aqmar Bin Mohamad Azhar", "designation": "Moodle LMS Administrator", "center": "CDAE", "unit": "CDAE-ADMIN"},

    # CFGS-ADMIN
    {"email": "siti.nur.sarah@aiu.edu.my", "name": "Siti Nur Sarah Binti Farizal", "designation": "Executive", "center": "CFGS", "unit": "CFGS-ADMIN"},

    # CGS-ADMIN
    {"email": "nor.shahidatul.umairah@aiu.edu.my", "name": "Nor Shahidatul Umairah Binti Muhammad Fisal", "designation": "Executive", "center": "CGS", "unit": "CGS-ADMIN"},

    # LC-ADMIN
    {"email": "fatin.nur.elleina@aiu.edu.my", "name": "Fatin Nur Elleina Binti Asmira Helmy", "designation": "Executive", "center": "LC", "unit": "LC-ADMIN"},

    # VCO-ADMIN
    {"email": "siti.balqis@aiu.edu.my", "name": "Siti Balqis Binti Nor Jasni", "designation": "Executive", "department": "VCO", "unit": "VCO-ADMIN"},

    # DVCA-ADMIN
    {"email": "syifaa.hafizah@aiu.edu.my", "name": "Syifaa Hafizah Binti Soib", "designation": "Assistant Executive", "department": "DVCA", "unit": "DVCA-ADMIN"},

    # DVCRI-ADMIN
    {"email": "nur.ilani@aiu.edu.my", "name": "Nur Ilani Binti Rusli", "designation": "Senior Executive", "department": "DVCRI", "unit": "DVCRI-ADMIN"},

    # ACE-SEDI
    {"email": "masrani.awang@aiu.edu.my", "name": "Masrani Bin Awang", "designation": "Executive (ACE-SEDI)", "center": "ACE-SEDI", "unit": "ACE-SEDI-ADMIN"},
    {"email": "nurul.alia.atiqah@aiu.edu.my", "name": "Nurul Alia Atiqah Binti Mohamad Rosli", "designation": "Executive (ACE-SEDI)", "center": "ACE-SEDI", "unit": "ACE-SEDI-ADMIN"},

    # CRIM
    {"email": "anis.roslan@aiu.edu.my", "name": "Anis Binti Roslan", "designation": "Executive (CRIM)", "center": "CRIM", "unit": "CRIM-ADMIN"},

    # CCIE
    {"email": "mohd.yusof.izzuddin@aiu.edu.my", "name": "Mohd Yusof Izzuddin Bin Abu Bakar", "designation": "Executive (CCIE)", "center": "CCIE", "unit": "CCIE-ADMIN"},

    # REG-ADMIN
    {"email": "halina.abdol.hamid@aiu.edu.my", "name": "Halina Binti Abdol Hamid", "designation": "Executive", "department": "REG", "unit": "REG-ADMIN"},
    {"email": "nur.atiqah.rozali@aiu.edu.my", "name": "Nur Atiqah Binti Rozali", "designation": "Executive", "department": "REG", "unit": "REG-ADMIN"},

    # AMD-ADMIN
    {"email": "sarina.bachok@aiu.edu.my", "name": "Sarina Binti Bachok", "designation": "Senior Executive, Academic Management Department", "department": "AMD", "unit": "AMD-ADMIN"},
    {"email": "nur.fatimah.azzahra@aiu.edu.my", "name": "Nur Fatimah Az-Zahra Binti Azhar", "designation": "Senior Executive", "department": "AMD", "unit": "AMD-ADMIN"},

    # ADM - Admission Unit
    {"email": "jessica.ong@aiu.edu.my", "name": "Jessica Ong Mei Chen", "designation": "Senior Executive, Admission Unit", "department": "AMD", "unit": "ADM"},
    {"email": "anis.wahdah@aiu.edu.my", "name": "Anis Wahdah Binti Mahamd Razaed", "designation": "Executive", "department": "AMD", "unit": "ADM"},
    {"email": "muhammad.alif.afiq@aiu.edu.my", "name": "Muhammad Alif Afiq Bin Raidzan", "designation": "Assistant Executive", "department": "AMD", "unit": "ADM"},

    # ISU - International Student Unit
    {"email": "nur.syafiqah.nazary@aiu.edu.my", "name": "Nur Syafiqah Binti Nazary", "designation": "Senior Executive, International Student Unit", "department": "AMD", "unit": "ISU"},
    {"email": "ahmad.muaz@aiu.edu.my", "name": "Ahmad Muaz Bin Azizan", "designation": "Senior Executive, International Student Unit", "department": "AMD", "unit": "ISU"},
    {"email": "siti.nur.aisyah@aiu.edu.my", "name": "Siti Nur Aisyah Binti Nor Azman", "designation": "Executive", "department": "AMD", "unit": "ISU"},
    {"email": "nurul.shazwani@aiu.edu.my", "name": "Nurul Shazwani Binti Mohd Fahmi", "designation": "Executive", "department": "AMD", "unit": "ISU"},

    # ERU - Examination and Records Unit
    {"email": "sofia.amir@aiu.edu.my", "name": "Sofia Binti Amir", "designation": "Executive, Examination and Records Unit", "department": "AMD", "unit": "ERU"},
    {"email": "nur.nazhifa@aiu.edu.my", "name": "Nur Nazhifa Binti Shuhaimi", "designation": "Executive, Examination and Records Unit", "department": "AMD", "unit": "ERU"},

    # SRU - Student Recruitment Unit
    {"email": "anis.nabilah@aiu.edu.my", "name": "Anis Nabilah Binti Muuti", "designation": "Senior Executive, Student Recruitment Unit", "center": "CPC", "unit": "SRU"},
    {"email": "maisarah.abdul.hamid@aiu.edu.my", "name": "Maisarah Binti Abdul Hamid", "designation": "Executive, Student Recruitment Unit", "center": "CPC", "unit": "SRU"},

    # CPC-ADMIN
    {"email": "noorarneena.zulaziz@aiu.edu.my", "name": "Noorarneena Binti Zul Aziz", "designation": "Senior Executive", "center": "CPC", "unit": "CPC-ADMIN"},
    {"email": "nur.lina.qaleeda@aiu.edu.my", "name": "Nur Lina Qaleeda Binti Abd Halim", "designation": "Executive", "center": "CPC", "unit": "CPC-ADMIN"},
    {"email": "muhammad.syafiq.ariff@aiu.edu.my", "name": "Muhammad Syafiq Ariff Bin Kamal Ariffin", "designation": "Assistant Executive", "center": "CPC", "unit": "CPC-ADMIN"},

    # HRD-ADMIN
    {"email": "masliza.zanol@aiu.edu.my", "name": "Masliza Binti Zanol", "designation": "Manager, Human Resource Department", "department": "HRD", "unit": "HRD-ADMIN"},
    {"email": "siti.nur.ashikin@aiu.edu.my", "name": "Siti Nur Ashikin Binti Mohd Jiwa", "designation": "Executive", "department": "HRD", "unit": "HRD-ADMIN"},
    {"email": "nur.alia.yusini@aiu.edu.my", "name": "Nur Alia Binti Yusini", "designation": "Executive", "department": "HRD", "unit": "HRD-ADMIN"},
    {"email": "mohammad.shahmi@aiu.edu.my", "name": "Mohammad Shahmi Bin Ab Majid", "designation": "Executive", "department": "HRD", "unit": "HRD-ADMIN"},

    # FIN-ADMIN
    {"email": "chong.chew.lee@aiu.edu.my", "name": "Chong Chew Lee", "designation": "Chief Financial Officer", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "rafilah.abdaziz@aiu.edu.my", "name": "Rafilah Binti Abd Aziz", "designation": "Financial Controller", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "tan.kai.shing@aiu.edu.my", "name": "Tan Kai Shing", "designation": "Assistant Financial Controller", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "hazrini.hanafiah@aiu.edu.my", "name": "Hazrini Binti Hanafiah", "designation": "Senior Executive", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "nurul.sharifah@aiu.edu.my", "name": "Nurul Sharifah Binti Azman", "designation": "Executive", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "nurul.zalikha@aiu.edu.my", "name": "Nurul Zalikha Binti Zubaidi", "designation": "Executive", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "farah.nadia.md.isa@aiu.edu.my", "name": "Farah Nadia Binti Md Isa", "designation": "Assistant Executive", "department": "FIN", "unit": "FIN-ADMIN"},
    {"email": "ching.chia.chee@aiu.edu.my", "name": "Ching Chia Chee", "designation": "Assistant Executive", "department": "FIN", "unit": "FIN-ADMIN"},

    # PROC - Procurement Unit
    {"email": "nurul.syamimi@aiu.edu.my", "name": "Nurul Syamimi Binti Zakari", "designation": "Assistant Executive, Procurement Unit", "department": "FIN", "unit": "PROC"},

    # FMU - Facility Management Unit
    {"email": "mohammad.shafiq.zainul@aiu.edu.my", "name": "Mohammad Shafiq Bin Zainul Abidin", "designation": "Senior Executive, Facility Management Unit", "department": "VCO", "unit": "FMU"},
    {"email": "razuan.mahmud@aiu.edu.my", "name": "Razuan Bin Mahmud", "designation": "Driver cum Despatch", "department": "VCO", "unit": "FMU"},
    {"email": "razis.awang@aiu.edu.my", "name": "Razis Bin Awang", "designation": "Driver cum Management Services", "department": "VCO", "unit": "FMU"},
    {"email": "muhammad.aizat.noordin@aiu.edu.my", "name": "Muhammad Aizat Bin Noordin", "designation": "Driver cum Management Services", "department": "VCO", "unit": "FMU"},
    {"email": "mohd.zakihafiz@aiu.edu.my", "name": "Mohd Zakihafiz Bin Che Ahmad", "designation": "Driver", "department": "VCO", "unit": "FMU"},

    # SCHOL - Scholarship Unit
    {"email": "nur.khalida.rahayu@aiu.edu.my", "name": "Nur Khalida Rahayu Binti Zainon", "designation": "Executive, Scholarship Unit", "center": "CSAA", "unit": "SCHOL"},
    {"email": "nur.zarifah.haifa@aiu.edu.my", "name": "Nur Zarifah Haifa Binti Mohamad Zakaria", "designation": "Executive, Scholarship Unit", "center": "CSAA", "unit": "SCHOL"},
    {"email": "nur.wahida.azizan@aiu.edu.my", "name": "Nur Wahida Binti Azizan", "designation": "Executive, Scholarship Unit", "center": "CSAA", "unit": "SCHOL"},
    {"email": "amirul.bahrain@aiu.edu.my", "name": "Amirul Bahrain Bin Shamsul Bahrain", "designation": "Executive, Scholarship Unit", "center": "CSAA", "unit": "SCHOL"},

    # CSAA-ADMIN
    {"email": "fazlia.azhari@aiu.edu.my", "name": "Fazlia Binti Azhari", "designation": "Counsellor", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "mohammad.hafis.shafiq@aiu.edu.my", "name": "Mohammad Hafis Shafiq Bin Mohammad Sopian", "designation": "Counsellor", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "atiqah.che.sulaiman@aiu.edu.my", "name": "'Atiqah Binti Che Sulaiman", "designation": "Senior Executive", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "hazween.eyzwann@aiu.edu.my", "name": "Hazween Eyzwann Bin Sharif", "designation": "Executive cum Warden", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "nurul.izzati.ramli@aiu.edu.my", "name": "Nurul Izzati Binti Ramli", "designation": "Executive cum Warden", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "ainun.nadiah@aiu.edu.my", "name": "Ainun Nadiah Binti Samsudin", "designation": "Executive (Career & Alumni)", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "mohammad.ariff.musthapa@aiu.edu.my", "name": "Mohammad Ariff Bin Musthapa Kamal", "designation": "Executive cum Warden", "center": "CSAA", "unit": "CSAA-ADMIN"},
    {"email": "muhammad.faiz.jelani@aiu.edu.my", "name": "Muhammad Faiz Bin Jelani", "designation": "Executive", "center": "CSAA", "unit": "CSAA-ADMIN"},

    # ICT-ADMIN
    {"email": "sahrulnizam.doni@aiu.edu.my", "name": "Ts. Sahrulnizam Bin Doni", "designation": "Director, ICT Centre", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "ammar.ihsan@aiu.edu.my", "name": "Ammar Ihsan Bin Saiful Anuar", "designation": "Technology Operations Lead", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "anwar.feisal@aiu.edu.my", "name": "Anwar Feisal Bin Mohd Hussain", "designation": "Assistant Manager, IT Technical Project Coordinator", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "nursyarmiza.rodzi@aiu.edu.my", "name": "Nursyarmiza Binti Rodzi", "designation": "IT Executive", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "mohammad.aiman.ahmad.zaki@aiu.edu.my", "name": "Mohammad Aiman Bin Ahmad Zaki", "designation": "IT Executive", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "nor.hisyam.mohamad.johan@aiu.edu.my", "name": "Nor Hisyam Bin Mohamad Johan", "designation": "IT Programmer", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "mohd.ruhaifi.zainol@aiu.edu.my", "name": "Mohd Ruhaifi Bin Zainol", "designation": "IT Programmer", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "nurul.afiqah.salihuddin@aiu.edu.my", "name": "Nurul Afiqah Binti Salihuddin @ Salih Huding", "designation": "IT Programmer", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "mohamad.faris.fadzlan@aiu.edu.my", "name": "Mohamad Faris Fadzlan Bin Muhamad Shahidin", "designation": "IT Support Engineer", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "muhammad.firdaus.hamdzah@aiu.edu.my", "name": "Muhammad Firdaus Bin Hamdzah", "designation": "IT Support", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "wan.mohd.syafiq@aiu.edu.my", "name": "Wan Mohd Syafiq Bin Wan Hamzainudin Helmy", "designation": "IT Assistant", "center": "ICT", "unit": "ICT-ADMIN"},
    {"email": "mohamad.amirul.arifin@aiu.edu.my", "name": "Mohamad Amirul Bin Mohd Arifin", "designation": "IT Support Executive", "center": "ICT", "unit": "ICT-ADMIN"},

    # COR-ADMIN
    {"email": "syuhada.ali@aiu.edu.my", "name": "Syuhada Binti Ali", "designation": "Chief Librarian", "center": "COR", "unit": "COR-ADMIN"},
    {"email": "nurul.izzati.sabri@aiu.edu.my", "name": "Nurul Izzati Binti Sabri", "designation": "Librarian", "center": "COR", "unit": "COR-ADMIN"},
    {"email": "mohd.dzairil.azhar@aiu.edu.my", "name": "Mohd Dzairil Azhar Bin Che Darus", "designation": "Librarian", "center": "COR", "unit": "COR-ADMIN"},
    {"email": "rabiatul.adawiyah@aiu.edu.my", "name": "Rabiatul Adawiyah Binti Zulkifli", "designation": "Librarian", "center": "COR", "unit": "COR-ADMIN"},
    {"email": "muhammad.rosmaizul@aiu.edu.my", "name": "Muhammad Rosmaizul Bin Maidin", "designation": "Assistant Librarian", "center": "COR", "unit": "COR-ADMIN"},
    {"email": "ernadia.wahida@aiu.edu.my", "name": "Ernadia Wahida Binti Cluny", "designation": "Assistant Librarian", "center": "COR", "unit": "COR-ADMIN"},
    {"email": "muhammad.farhan.fadzil@aiu.edu.my", "name": "Muhammad Farhan Bin Fadzil", "designation": "Assistant Librarian", "center": "COR", "unit": "COR-ADMIN"},

    # CQAA-ADMIN
    {"email": "najihah.mahmud@aiu.edu.my", "name": "Najihah Binti Mahmud", "designation": "Executive", "center": "CQAA", "unit": "CQAA-ADMIN"},
    {"email": "sahariatul.akmam@aiu.edu.my", "name": "Sahariatul Akmam Binti Harun", "designation": "Executive", "center": "CQAA", "unit": "CQAA-ADMIN"},

    # Additional: Registry (REG) top management
    {"email": "norpisah.mat.isa@aiu.edu.my", "name": "Norpisah Binti Mat Isa", "designation": "Registrar", "department": "REG", "unit": "REG-ADMIN"},

    # Additional: CPR - Centre of Reference management
    {"email": "mohamad.kamal.dasuki@aiu.edu.my", "name": "Dr. Mohamad Kamal Bin Mohamad Dasuki", "designation": "Senior Executive, Centre for Quality Assurance", "center": "CQAA", "unit": "CQAA-ADMIN"},
]


ADMINS = [
    {"email": "mohd.saleh.jaafar@aiu.edu.my", "name": "Professor Dato' Ir. Dr. Mohd Saleh Bin Jaafar", "designation": "Vice Chancellor and President", "department": "VCO", "unit": "VCO-ADMIN"},
    {"email": "mohamad.abdullah.hemdi@aiu.edu.my", "name": "Professor Dr. Hj. Mohamad Abdullah Bin Hemdi", "designation": "Deputy Vice Chancellor (Academic)", "department": "DVCA", "unit": "DVCA-ADMIN"},
    {"email": "abdul.shakur@aiu.edu.my", "name": "Abdul Shakur Bin Abdullah", "designation": "Deputy Registrar / Director, Centre for Corporate Planning and Communication", "department": "REG", "unit": "REG-ADMIN"},
]


LEGACY_PROGRAM_CODES = {
    "CDAE-P01",
    "CDAE-P02",
    "CFGS-P01",
    "CFGS-P02",
    "CGS-P01",
    "CGS-P02",
    "CGS-P03",
    "CGS-P04",
    "CGS-PGA",
    "CGS-RS",
    "LC-P01",
    "LC-P02",
    "LC-P03",
    "LC-P04",
    "CSAA-P01",
    "CSAA-P02",
    "ICT-P01",
    "CPC-P01",
    "COR-P01",
    "CQAA-P01",
    *{f"SBSS-P{index:02d}" for index in range(1, 12)},
    *{f"SEHS-P{index:02d}" for index in range(1, 6)},
    *{f"SCI-P{index:02d}" for index in range(1, 4)},
}


class Command(BaseCommand):
    help = (
        "Seed the current AIU organisation structure, programmes, teachers, "
        "executives, and admin person records from the official website data."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        schools = self.seed_schools()
        centers = self.seed_centers()
        departments = self.seed_departments()
        units = self.seed_units(schools, centers, departments)
        programmes = self.seed_programmes(schools, centers)
        teachers = self.seed_teachers(schools, centers)
        executives = self.seed_executives(schools, centers, departments, units)
        admins = self.seed_admins(departments, units)

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded AIU organisation: "
                f"{len(schools)} schools, {len(centers)} centres, "
                f"{len(departments)} departments, {len(units)} units, "
                f"{programmes} programmes, "
                f"{len(teachers)} teachers, {len(executives)} executives, "
                f"{len(admins)} admins."
                f"{len(executives)} Executives."
                f"{len(teachers)} Teachers."
            )
        )

    def seed_schools(self):
        schools = {}
        for item in SCHOOLS:
            programmes = [row[1] for row in SCHOOL_PROGRAMMES[item["code"]]]
            school, _ = models.School.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "slug": item["slug"],
                    "description": item["description"],
                    "about": item["about"],
                    "vision": item["vision"],
                    "mission": item["mission"],
                    "programmes": programmes,
                    "is_active": True,
                },
            )
            schools[school.code] = school
        return schools

    def seed_centers(self):
        centers = {}
        for item in CENTERS:
            center, _ = models.Center.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "slug": item["slug"],
                    "description": item["description"],
                    "about": item["about"],
                    "offerings": item["offerings"],
                    "is_active": True,
                },
            )
            centers[center.code] = center
        return centers

    def seed_departments(self):
        departments = {}
        for item in DEPARTMENTS:
            department, _ = models.Department.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "school": None,
                    "center": None,
                    "description": item["description"],
                    "is_active": True,
                },
            )
            departments[department.code] = department
        return departments

    def seed_units(self, schools, centers, departments):
        units = {}
        for item in UNITS:
            unit, _ = models.Unit.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "unit_type": item["unit_type"],
                    "school": schools.get(item.get("school")),
                    "center": centers.get(item.get("center")),
                    "department": departments.get(item.get("department")),
                    "description": item["description"],
                    "is_active": True,
                },
            )
            units[unit.code] = unit
        return units

    def seed_programmes(self, schools, centers):
        models.Program.objects.filter(code__in=LEGACY_PROGRAM_CODES).delete()
        count = 0
        for school_code, programmes in SCHOOL_PROGRAMMES.items():
            for code, name, level, duration_years in programmes:
                models.Program.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "school": schools[school_code],
                        "center": None,
                        "department": None,
                        "program_type": models.Program.PROGRAM_ACADEMIC,
                        "level": level,
                        "duration_years": duration_years,
                        "description": f"{level} programme offered by {schools[school_code].name}.",
                        "is_active": True,
                    },
                )
                count += 1

        for center_code, programmes in CENTER_PROGRAMMES.items():
            for code, name, program_type in programmes:
                is_foundation = center_code == "CFGS"
                models.Program.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "school": None,
                        "center": centers[center_code],
                        "department": None,
                        "program_type": program_type,
                        "level": "Foundation" if is_foundation else "",
                        "duration_years": 1 if is_foundation else None,
                        "description": f"Programme or service offered by {centers[center_code].name}.",
                        "is_active": True,
                    },
                )
                count += 1
        return count

    def _make_username(self, email):
        return email.split("@")[0].replace(".", "_").lower()

    def _get_or_create_user(self, email, name):
        username = self._make_username(email)
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": name,
                "is_active": True,
            },
        )
        if created:
            user.set_unusable_password()
            user.save()
        return user

    def seed_teachers(self, schools, centers):
        results = []
        for item in TEACHERS:
            user = self._get_or_create_user(item["email"], item["name"])
            school = schools.get(item.get("school"))
            center = centers.get(item.get("center"))
            profile, _ = models.Profile.objects.update_or_create(
                user=user,
                defaults={
                    "role": models.Profile.ROLE_TEACHER,
                    "school": school,
                    "center": center,
                    "department": None,
                    "unit": None,
                    "designation": item["designation"],
                    "is_active": True,
                },
            )
            Teacher.objects.update_or_create(
                profile=profile,
                defaults={
                    "teacher_id": profile.staff_id or self._make_username(item["email"]).upper(),
                    "designation": item["designation"],
                    "school": school,
                    "center": center,
                    "is_active": True,
                },
            )
            results.append(str(profile.user))
        return results

    def seed_executives(self, schools, centers, departments, units):
        results = []
        for item in EXECUTIVES:
            user = self._get_or_create_user(item["email"], item["name"])
            unit = units.get(item.get("unit"))
            profile, _ = models.Profile.objects.update_or_create(
                user=user,
                defaults={
                    "role": models.Profile.ROLE_EXECUTIVE,
                    "school": schools.get(item.get("school")),
                    "center": centers.get(item.get("center")),
                    "department": departments.get(item.get("department")),
                    "unit": unit,
                    "designation": item["designation"],
                    "is_active": True,
                },
            )
            Executive.objects.update_or_create(
                profile=profile,
                defaults={
                    "executive_id": profile.staff_id or self._make_username(item["email"]).upper(),
                    "designation": item["designation"],
                    "school": schools.get(item.get("school")),
                    "center": centers.get(item.get("center")),
                    "department": departments.get(item.get("department")),
                    "unit": unit,
                    "is_active": True,
                },
            )
            results.append(str(profile.user))
        return results

    def seed_admins(self, departments, units):
        results = []
        for item in ADMINS:
            user = self._get_or_create_user(item["email"], item["name"])
            profile, _ = models.Profile.objects.update_or_create(
                user=user,
                defaults={
                    "role": models.Profile.ROLE_ADMIN,
                    "school": None,
                    "center": None,
                    "department": departments.get(item.get("department")),
                    "unit": units.get(item.get("unit")),
                    "designation": item["designation"],
                    "is_active": True,
                },
            )
            models.Admin.objects.update_or_create(
                profile=profile,
                defaults={
                    "admin_id": profile.staff_id or self._make_username(item["email"]).upper(),
                    "designation": item["designation"],
                    "department": departments.get(item.get("department")),
                    "unit": units.get(item.get("unit")),
                    "is_active": True,
                },
            )
            results.append(str(profile.user))
        return results
