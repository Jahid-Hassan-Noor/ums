import hashlib
import json
import re
from dataclasses import dataclass, field

from django.utils import timezone

from admin_app.models import (
    Center,
    Course,
    Department,
    Program,
    School,
    Unit,
    Venue,
)
from chatbot_app.models import SearchDocument
from chatbot_app.search_permissions import FORBIDDEN_DOCUMENT_TYPES, FORBIDDEN_DOMAINS
from home_app.models import (
    OfficialLink,
    PublicAnnouncement,
    PublicDirectoryEntry,
    PublicEvent,
    PublicNews,
    PublicPage,
)
from librarian_app.models import Book
from teacher_app.models import Assignment, CourseResource


@dataclass
class IndexedDocument:
    source_key: str
    title: str
    domain: str
    document_type: str
    summary: str = ""
    body: str = ""
    keywords: str = ""
    source_label: str = ""
    source_url: str = ""
    source_app_label: str = ""
    source_model: str = ""
    source_object_id: str = ""
    icon: str = ""
    breadcrumbs: list[str] = field(default_factory=list)
    visibility: str = SearchDocument.VISIBILITY_PUBLIC
    allowed_roles: list[str] = field(default_factory=list)
    owner_user_id: int | None = None
    course_id: int | None = None
    course_offering_id: int | None = None
    semester_id: int | None = None
    school_id: int | None = None
    center_id: int | None = None
    department_id: int | None = None
    unit_id: int | None = None
    program_id: int | None = None
    scope_metadata: dict = field(default_factory=dict)
    safe_metadata: dict = field(default_factory=dict)
    source_updated_at: object | None = None


def clean_text(value, limit=None):
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = " ".join(text.split())
    return text[:limit].rstrip() if limit else text


def json_words(value):
    if not value:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(item) for item in value)
    return str(value)


def source_ref(instance):
    meta = instance._meta
    return {
        "source_key": f"{meta.app_label}.{meta.model_name}:{instance.pk}",
        "source_app_label": meta.app_label,
        "source_model": meta.model_name,
        "source_object_id": str(instance.pk),
    }


def document_hash(payload):
    values = {
        key: getattr(payload, key)
        for key in (
            "title",
            "summary",
            "body",
            "keywords",
            "source_label",
            "source_url",
            "domain",
            "document_type",
            "visibility",
            "allowed_roles",
            "course_id",
            "course_offering_id",
            "semester_id",
            "school_id",
            "center_id",
            "department_id",
            "unit_id",
            "program_id",
            "scope_metadata",
            "safe_metadata",
        )
    }
    raw = json.dumps(values, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_safe_payload(payload):
    metadata = payload.safe_metadata or {}
    return not (
        payload.domain in FORBIDDEN_DOMAINS
        or payload.document_type in FORBIDDEN_DOCUMENT_TYPES
        or metadata.get("sensitive") is True
    )


def _upsert(payload, *, dry_run=False):
    if not is_safe_payload(payload):
        return "skipped_sensitive"
    if dry_run:
        return "dry_run"

    content_hash = document_hash(payload)
    values = {
        "source_app_label": payload.source_app_label,
        "source_model": payload.source_model,
        "source_object_id": payload.source_object_id,
        "title": payload.title,
        "summary": payload.summary,
        "body": payload.body,
        "keywords": payload.keywords,
        "source_label": payload.source_label,
        "source_url": payload.source_url,
        "domain": payload.domain,
        "document_type": payload.document_type,
        "icon": payload.icon,
        "breadcrumbs": payload.breadcrumbs,
        "visibility": payload.visibility,
        "allowed_roles": payload.allowed_roles,
        "owner_user_id": payload.owner_user_id,
        "course_id": payload.course_id,
        "course_offering_id": payload.course_offering_id,
        "semester_id": payload.semester_id,
        "school_id": payload.school_id,
        "center_id": payload.center_id,
        "department_id": payload.department_id,
        "unit_id": payload.unit_id,
        "program_id": payload.program_id,
        "scope_metadata": payload.scope_metadata,
        "safe_metadata": payload.safe_metadata,
        "content_hash": content_hash,
        "source_updated_at": payload.source_updated_at,
        "last_indexed_at": timezone.now(),
        "is_active": True,
    }
    existing = SearchDocument.objects.filter(source_key=payload.source_key).first()
    if not existing:
        SearchDocument.objects.create(source_key=payload.source_key, **values)
        return "created"
    if existing.content_hash == content_hash and existing.is_active:
        return "unchanged"
    for key, value in values.items():
        setattr(existing, key, value)
    existing.save()
    return "updated"


def _role_visibility(role):
    if role == "public":
        return SearchDocument.VISIBILITY_PUBLIC, []
    if role == "authenticated":
        return SearchDocument.VISIBILITY_AUTHENTICATED, []
    if role == "admin":
        return SearchDocument.VISIBILITY_ADMIN_ONLY, ["admin"]
    return SearchDocument.VISIBILITY_ROLE_BASED, [role]


def public_documents():
    for page in PublicPage.objects.filter(status=PublicPage.STATUS_PUBLISHED):
        route = page.route_path or f"/{page.slug}"
        yield IndexedDocument(
            **source_ref(page),
            title=page.title,
            summary=clean_text(page.summary, 360),
            body=clean_text(page.body),
            keywords=f"{page.section} {page.slug}",
            source_label="Public page",
            source_url=route,
            domain="public",
            document_type="page",
            icon="file-text",
            breadcrumbs=["Public", page.get_section_display()],
            source_updated_at=page.updated_at,
        )

    for item in PublicNews.objects.filter(status=PublicNews.STATUS_PUBLISHED):
        yield IndexedDocument(
            **source_ref(item),
            title=item.title,
            summary=clean_text(item.summary or item.body, 360),
            body=clean_text(item.body),
            keywords=item.slug,
            source_label="News",
            source_url=f"/news/{item.slug}",
            domain="public",
            document_type="news",
            icon="newspaper",
            breadcrumbs=["Public", "News"],
            source_updated_at=item.updated_at,
        )

    for item in PublicEvent.objects.filter(status=PublicEvent.STATUS_PUBLISHED):
        event_date = timezone.localtime(item.starts_at).strftime("%d %b %Y %H:%M")
        yield IndexedDocument(
            **source_ref(item),
            title=item.title,
            summary=clean_text(f"{event_date} {item.location} {item.description}", 360),
            body=clean_text(item.description),
            keywords=item.location,
            source_label="Event",
            source_url=f"/events/{item.slug}",
            domain="public",
            document_type="event",
            icon="calendar-days",
            breadcrumbs=["Public", "Events"],
            safe_metadata={"location": item.location},
            source_updated_at=item.updated_at,
        )

    for item in PublicAnnouncement.objects.filter(is_published=True):
        visibility, roles = _role_visibility(
            {
                PublicAnnouncement.AUDIENCE_PUBLIC: "public",
                PublicAnnouncement.AUDIENCE_AUTHENTICATED: "authenticated",
                PublicAnnouncement.AUDIENCE_STUDENTS: "student",
                PublicAnnouncement.AUDIENCE_TEACHERS: "teacher",
                PublicAnnouncement.AUDIENCE_EXECUTIVES: "executive",
                PublicAnnouncement.AUDIENCE_ADMINS: "admin",
            }.get(item.audience, "public")
        )
        yield IndexedDocument(
            **source_ref(item),
            title=item.title,
            summary=clean_text(item.body, 360),
            body=clean_text(item.body),
            source_label="Announcement",
            source_url="/news",
            domain="public",
            document_type="announcement",
            icon="megaphone",
            breadcrumbs=["Public", "Announcements"],
            visibility=visibility,
            allowed_roles=roles,
            source_updated_at=item.updated_at,
        )

    for item in OfficialLink.objects.filter(is_active=True):
        visibility, roles = _role_visibility(item.audience)
        yield IndexedDocument(
            **source_ref(item),
            title=item.title,
            summary=clean_text(item.description or item.url, 360),
            keywords=item.category,
            source_label="Official link",
            source_url=item.url,
            domain="public",
            document_type="official_link",
            icon="external-link",
            breadcrumbs=["Public", "Official links"],
            visibility=visibility,
            allowed_roles=roles,
            safe_metadata={"category": item.category},
            source_updated_at=item.updated_at,
        )

    for item in PublicDirectoryEntry.objects.filter(is_active=True):
        body = " ".join(
            part
            for part in (item.description, item.email, item.url)
            if part
        )
        yield IndexedDocument(
            **source_ref(item),
            title=item.name,
            summary=clean_text(body, 360),
            body=clean_text(body),
            keywords=f"{item.code} {item.entry_type}",
            source_label="Public directory",
            source_url=item.url or "/directories",
            domain="public",
            document_type="directory",
            icon="building-2",
            breadcrumbs=["Public", "Directory"],
            school_id=item.school_id,
            center_id=item.center_id,
            safe_metadata={"category": item.get_entry_type_display()},
            source_updated_at=item.updated_at,
        )


def academic_documents():
    for school in School.objects.filter(is_active=True):
        yield IndexedDocument(
            **source_ref(school),
            title=school.name,
            summary=clean_text(school.description or school.about, 360),
            body=clean_text(f"{school.description} {school.about} {json_words(school.programmes)}"),
            keywords=school.code,
            source_label="School",
            source_url="/schools",
            domain="academic",
            document_type="school",
            icon="school",
            breadcrumbs=["Academics", "Schools"],
            school_id=school.id,
        )

    for center in Center.objects.filter(is_active=True):
        yield IndexedDocument(
            **source_ref(center),
            title=center.name,
            summary=clean_text(center.description or center.about, 360),
            body=clean_text(f"{center.description} {center.about} {json_words(center.offerings)}"),
            keywords=f"{center.code} {center.center_type}",
            source_label="Centre",
            source_url="/centres",
            domain="academic",
            document_type="centre",
            icon="building-2",
            breadcrumbs=["Academics", "Centres"],
            center_id=center.id,
        )

    for department in Department.objects.select_related("school", "center").filter(is_active=True):
        yield IndexedDocument(
            **source_ref(department),
            title=department.name,
            summary=clean_text(department.description, 360),
            body=clean_text(department.description),
            keywords=department.code,
            source_label="Department",
            source_url="/directories",
            domain="academic",
            document_type="department",
            icon="building-2",
            breadcrumbs=["Academics", "Departments"],
            school_id=department.school_id,
            center_id=department.center_id,
            department_id=department.id,
        )

    for unit in Unit.objects.select_related("school", "center", "department").filter(is_active=True):
        yield IndexedDocument(
            **source_ref(unit),
            title=unit.name,
            summary=clean_text(unit.description, 360),
            body=clean_text(unit.description),
            keywords=f"{unit.code} {unit.unit_type}",
            source_label="Unit",
            source_url="/directories",
            domain="academic",
            document_type="unit",
            icon="building-2",
            breadcrumbs=["Academics", "Units"],
            school_id=unit.school_id,
            center_id=unit.center_id,
            department_id=unit.department_id,
            unit_id=unit.id,
        )

    for program in Program.objects.select_related("school", "center", "department").filter(is_active=True):
        yield IndexedDocument(
            **source_ref(program),
            title=program.name,
            summary=clean_text(program.description, 360),
            body=clean_text(program.description),
            keywords=f"{program.code} {program.level} {program.program_type}",
            source_label="Programme",
            source_url="/programmes",
            domain="academic",
            document_type="programme",
            icon="graduation-cap",
            breadcrumbs=["Academics", "Programmes"],
            school_id=program.school_id,
            center_id=program.center_id,
            department_id=program.department_id,
            program_id=program.id,
            safe_metadata={"category": program.level},
        )

    for course in Course.objects.select_related("school", "center", "department", "program").filter(is_active=True):
        yield IndexedDocument(
            **source_ref(course),
            title=f"{course.code} - {course.title}",
            summary=clean_text(course.description, 360),
            body=clean_text(course.description),
            keywords=f"{course.code} {course.title}",
            source_label="Course",
            source_url="/programmes",
            domain="academic",
            document_type="course",
            icon="book-open",
            breadcrumbs=["Academics", "Courses"],
            course_id=course.id,
            school_id=course.school_id,
            center_id=course.center_id,
            department_id=course.department_id,
            program_id=course.program_id,
            safe_metadata={"course_code": course.code, "course_title": course.title},
        )


def library_documents():
    for book in Book.objects.filter(is_active=True):
        yield IndexedDocument(
            **source_ref(book),
            title=book.title,
            summary=clean_text(f"{book.author}. {book.description}", 360),
            body=clean_text(f"{book.author} {book.publisher} {book.edition} {book.category} {book.description}"),
            keywords=f"{book.isbn} {book.category}",
            source_label="Library catalogue",
            source_url="/student/library/books",
            domain="library",
            document_type="book",
            icon="library",
            breadcrumbs=["Library", "Books"],
            visibility=SearchDocument.VISIBILITY_AUTHENTICATED,
            safe_metadata={"category": book.category},
            source_updated_at=book.updated_at,
        )


def venue_documents():
    for venue in Venue.objects.select_related("building").filter(is_active=True, building__is_active=True):
        summary = f"{venue.building.name}, floor {venue.floor}, capacity {venue.capacity or 'not set'}"
        yield IndexedDocument(
            **source_ref(venue),
            title=venue.name,
            summary=clean_text(summary, 360),
            body=clean_text(f"{venue.code} {venue.building.name} {venue.floor} {venue.capacity}"),
            keywords=venue.code,
            source_label="Venue",
            source_url="/student/venue-bookings",
            domain="venues",
            document_type="venue",
            icon="map-pin",
            breadcrumbs=["Venues"],
            visibility=SearchDocument.VISIBILITY_AUTHENTICATED,
            safe_metadata={"location": venue.building.name},
            source_updated_at=venue.updated_at,
        )


def course_material_documents():
    resources = CourseResource.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
    ).filter(is_published=True)
    now = timezone.now()
    for resource in resources:
        if resource.visible_from and resource.visible_from > now:
            continue
        body = resource.content if resource.resource_type == CourseResource.TYPE_PAGE else ""
        yield IndexedDocument(
            **source_ref(resource),
            title=resource.title,
            summary=clean_text(resource.description or body, 360),
            body=clean_text(body),
            keywords=f"{resource.offering.course.code} {resource.resource_type}",
            source_label="Course resource",
            source_url=f"/student/courses/{resource.offering_id}",
            domain="course_materials",
            document_type="course_resource",
            icon="file-text",
            breadcrumbs=["Courses", resource.offering.course.code, "Resources"],
            visibility=SearchDocument.VISIBILITY_COURSE_MEMBER,
            allowed_roles=["student", "teacher"],
            course_id=resource.offering.course_id,
            course_offering_id=resource.offering_id,
            semester_id=resource.offering.semester_id,
            safe_metadata={
                "course_code": resource.offering.course.code,
                "course_title": resource.offering.course.title,
                "section": resource.offering.section,
                "semester": resource.offering.semester.name,
            },
            source_updated_at=resource.updated_at,
        )


def assignment_documents():
    assignments = Assignment.objects.select_related(
        "offering",
        "offering__course",
        "offering__semester",
    ).filter(status__in=[Assignment.STATUS_PUBLISHED, Assignment.STATUS_CLOSED])
    for assignment in assignments:
        body = " ".join(
            part
            for part in (
                assignment.description,
                assignment.instructions,
                assignment.file_instructions,
                assignment.group_rules,
            )
            if part
        )
        yield IndexedDocument(
            **source_ref(assignment),
            title=assignment.title,
            summary=clean_text(assignment.description or assignment.instructions, 360),
            body=clean_text(body),
            keywords=f"{assignment.offering.course.code} assignment instruction",
            source_label="Assignment instructions",
            source_url=f"/student/assignments/{assignment.id}",
            domain="assignments",
            document_type="assignment_instruction",
            icon="clipboard-list",
            breadcrumbs=["Assignments", assignment.offering.course.code],
            visibility=SearchDocument.VISIBILITY_COURSE_MEMBER,
            allowed_roles=["student", "teacher"],
            course_id=assignment.offering.course_id,
            course_offering_id=assignment.offering_id,
            semester_id=assignment.offering.semester_id,
            safe_metadata={
                "course_code": assignment.offering.course.code,
                "course_title": assignment.offering.course.title,
                "section": assignment.offering.section,
                "semester": assignment.offering.semester.name,
            },
            source_updated_at=assignment.updated_at,
        )


DOMAIN_INDEXERS = {
    "public": public_documents,
    "academic": academic_documents,
    "library": library_documents,
    "venues": venue_documents,
    "course_materials": course_material_documents,
    "assignments": assignment_documents,
}


def rebuild_search_index(*, domains=None, clear=False, dry_run=False):
    selected_domains = list(domains or DOMAIN_INDEXERS.keys())
    report = {}
    for domain in selected_domains:
        indexer = DOMAIN_INDEXERS.get(domain)
        if not indexer:
            report[domain] = {"error": "unknown domain"}
            continue
        if clear and not dry_run:
            SearchDocument.objects.filter(domain=domain).delete()

        seen_keys = []
        counts = {
            "seen": 0,
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "dry_run": 0,
            "skipped_sensitive": 0,
            "hidden_stale": 0,
        }
        for payload in indexer():
            counts["seen"] += 1
            seen_keys.append(payload.source_key)
            status = _upsert(payload, dry_run=dry_run)
            counts[status] = counts.get(status, 0) + 1

        if not dry_run and not clear:
            stale = (
                SearchDocument.objects.filter(domain=domain, is_active=True)
                .exclude(source_key__in=seen_keys)
                .update(is_active=False)
            )
            counts["hidden_stale"] = stale

        report[domain] = counts
    return report
