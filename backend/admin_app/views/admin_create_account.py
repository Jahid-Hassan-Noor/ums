import csv
import io
import logging
import re
import secrets
import string
import zipfile
from xml.etree import ElementTree as ET

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsAdminRole
from admin_app import models
from admin_app.serializers import CenterSerializer, ProgramSerializer, SchoolSerializer, UnitSerializer
from auth_app.serializers import RegisterSerializer, UserSerializer
from core.common.errors import first_error as _first_error


logger = logging.getLogger(__name__)
TEMPORARY_PASSWORD_LENGTH = 8
TEMPORARY_PASSWORD_ALPHABET = string.ascii_letters + string.digits
MAX_IMPORT_ROWS = 500
MAX_IMPORT_FILE_SIZE = 5 * 1024 * 1024
XLSX_MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
XLSX_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
XLSX_PACKAGE_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


CREATE_ACCOUNT_ROLES = {
    "student": {
        "title": "Create Student",
        "label": "Student",
        "id_label": "Student ID",
    },
    "teacher": {
        "title": "Create Teacher",
        "label": "Teacher",
        "id_label": "Staff ID",
    },
    "executive": {
        "title": "Create Executive",
        "label": "Executive",
        "id_label": "Staff ID",
    },
    "librarian": {
        "title": "Create Librarian",
        "label": "Librarian",
        "id_label": "Staff ID",
    },
    "caterer": {
        "title": "Create Caterer",
        "label": "Caterer",
        "id_label": "Staff ID",
    },
    "technician": {
        "title": "Create Technician",
        "label": "Technician",
        "id_label": "Staff ID",
    },
    "accountant": {
        "title": "Create Accountant",
        "label": "Accountant",
        "id_label": "Staff ID",
    },
    "hr": {
        "title": "Create HR",
        "label": "Human Resources",
        "id_label": "Staff ID",
    },
}


def _generate_temporary_password():
    characters = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    characters.extend(
        secrets.choice(TEMPORARY_PASSWORD_ALPHABET)
        for _ in range(TEMPORARY_PASSWORD_LENGTH - len(characters))
    )
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)


def _build_account_email(*, full_name, username, email, role_label, temporary_password):
    frontend_base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
    login_url = f"{frontend_base_url}/login" if frontend_base_url else ""
    reset_url = f"{frontend_base_url}/forgot-password" if frontend_base_url else ""

    message_lines = [
        f"Hello {full_name},",
        "",
        f"An AIU Portal {role_label.lower()} account has been created for you.",
        "",
        f"Full name: {full_name}",
        f"Username: {username}",
        f"Email: {email}",
        f"Temporary password: {temporary_password}",
    ]
    if login_url:
        message_lines.extend(["", f"Login: {login_url}"])
    if reset_url:
        message_lines.append(f"Reset password: {reset_url}")
    message_lines.extend(
        [
            "",
            "For security, sign in and replace the temporary password as soon as possible.",
            "Do not share these credentials with anyone.",
        ]
    )

    send_mail(
        subject="Your AIU Portal account credentials",
        message="\n".join(message_lines),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )


def _send_account_credentials(*, user, role_label, temporary_password):
    _build_account_email(
        full_name=user.get_full_name().strip() or user.username,
        username=user.username,
        email=user.email,
        role_label=role_label,
        temporary_password=temporary_password,
    )


class AccountValidationError(Exception):
    def __init__(self, detail, errors=None):
        self.detail = detail
        self.errors = errors or {}
        super().__init__(detail)


class AccountEmailError(Exception):
    pass


class SheetImportError(Exception):
    pass


HEADER_ALIASES = {
    "temporary_password": "password",
    "temp_password": "password",
    "student_id": "ums_id",
    "staff_id": "ums_id",
    "phone": "phone_number",
    "mobile": "phone_number",
    "centre_id": "center_id",
    "centre_code": "center_code",
    "programme_id": "program_id",
    "programme_code": "program_code",
}


def _normalize_header(value):
    key = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return HEADER_ALIASES.get(key, key)


def _clean_cell_value(value):
    if value is None:
        return ""
    cleaned = str(value).strip()
    if re.fullmatch(r"-?\d+\.0", cleaned):
        return cleaned[:-2]
    return cleaned


def _tabular_rows_to_dicts(rows):
    header = None
    header_row_number = 0
    for row_number, row in rows:
        if any(_clean_cell_value(cell) for cell in row):
            header = [_normalize_header(cell) for cell in row]
            header_row_number = row_number
            break

    if not header:
        raise SheetImportError("The uploaded sheet does not contain a header row.")

    records = []
    for row_number, row in rows:
        if row_number <= header_row_number:
            continue
        if not any(_clean_cell_value(cell) for cell in row):
            continue
        record = {}
        for index, column in enumerate(header):
            if not column:
                continue
            value = _clean_cell_value(row[index] if index < len(row) else "")
            record[column] = value
        records.append({"row": row_number, "data": record})
        if len(records) > MAX_IMPORT_ROWS:
            raise SheetImportError(
                f"Import files can contain at most {MAX_IMPORT_ROWS} account rows."
            )

    if not records:
        raise SheetImportError("The uploaded sheet does not contain any account rows.")
    return records


def _parse_csv_rows(content):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    reader = csv.reader(io.StringIO(text))
    return _tabular_rows_to_dicts(
        (row_number, row) for row_number, row in enumerate(reader, start=1)
    )


def _xlsx_texts(element):
    return "".join(
        node.text or "" for node in element.iter() if node.tag == f"{XLSX_MAIN_NS}t"
    )


def _xlsx_shared_strings(workbook):
    try:
        xml = workbook.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(xml)
    return [_xlsx_texts(item) for item in root.findall(f"{XLSX_MAIN_NS}si")]


def _xlsx_first_sheet_path(workbook):
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    first_sheet = workbook_root.find(f"{XLSX_MAIN_NS}sheets/{XLSX_MAIN_NS}sheet")
    if first_sheet is None:
        raise SheetImportError("The uploaded workbook does not contain a worksheet.")
    relationship_id = first_sheet.attrib.get(f"{XLSX_REL_NS}id")
    if not relationship_id:
        return "xl/worksheets/sheet1.xml"

    rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    for relationship in rels_root.findall(f"{XLSX_PACKAGE_REL_NS}Relationship"):
        if relationship.attrib.get("Id") == relationship_id:
            target = relationship.attrib.get("Target", "")
            if target.startswith("/"):
                return target.lstrip("/")
            if target.startswith("xl/"):
                return target
            return f"xl/{target}"
    raise SheetImportError("The workbook's first worksheet could not be located.")


def _xlsx_column_index(cell_reference):
    match = re.match(r"([A-Z]+)", (cell_reference or "").upper())
    if not match:
        return None
    index = 0
    for character in match.group(1):
        index = index * 26 + (ord(character) - ord("A") + 1)
    return index - 1


def _xlsx_cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        inline = cell.find(f"{XLSX_MAIN_NS}is")
        return _xlsx_texts(inline) if inline is not None else ""

    value_node = cell.find(f"{XLSX_MAIN_NS}v")
    raw_value = value_node.text if value_node is not None else ""
    if cell_type == "s" and raw_value:
        try:
            return shared_strings[int(raw_value)]
        except (IndexError, ValueError):
            return ""
    if cell_type == "b":
        return "TRUE" if raw_value == "1" else "FALSE"
    return raw_value or ""


def _parse_xlsx_rows(content):
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as workbook:
            shared_strings = _xlsx_shared_strings(workbook)
            sheet_path = _xlsx_first_sheet_path(workbook)
            sheet_root = ET.fromstring(workbook.read(sheet_path))
    except (KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise SheetImportError("The uploaded .xlsx file could not be read.") from exc

    parsed_rows = []
    for row in sheet_root.findall(f".//{XLSX_MAIN_NS}sheetData/{XLSX_MAIN_NS}row"):
        row_number = int(row.attrib.get("r") or len(parsed_rows) + 1)
        cells = []
        next_index = 0
        for cell in row.findall(f"{XLSX_MAIN_NS}c"):
            cell_index = _xlsx_column_index(cell.attrib.get("r")) or next_index
            while len(cells) < cell_index:
                cells.append("")
            cells.append(_xlsx_cell_value(cell, shared_strings))
            next_index = cell_index + 1
        parsed_rows.append((row_number, cells))
    return _tabular_rows_to_dicts(parsed_rows)


def _extract_import_rows(uploaded_file):
    if uploaded_file.size > MAX_IMPORT_FILE_SIZE:
        raise SheetImportError("Upload a .csv or .xlsx file that is 5 MB or smaller.")

    file_name = (uploaded_file.name or "").lower()
    content = uploaded_file.read()
    if file_name.endswith(".csv"):
        return _parse_csv_rows(content)
    if file_name.endswith(".xlsx"):
        return _parse_xlsx_rows(content)
    raise SheetImportError("Upload a .csv or .xlsx file. Save .xls files as .xlsx first.")


def _lookup_active_code(model, code, label):
    matches = list(
        model.objects.filter(code__iexact=code, is_active=True).values_list("id", flat=True)[:2]
    )
    if not matches:
        raise SheetImportError(f"No active {label} exists with code '{code}'.")
    if len(matches) > 1:
        raise SheetImportError(
            f"More than one active {label} uses code '{code}'. Use the numeric id column."
        )
    return str(matches[0])


def _scope_id_from_row(data, *, id_key, code_key, model, label):
    explicit_id = data.get(id_key, "")
    if explicit_id:
        return explicit_id
    code = data.get(code_key, "")
    if code:
        return _lookup_active_code(model, code, label)
    return ""


def _scope_id_from_token(kind, identifier):
    if not identifier:
        raise SheetImportError("Teacher assignment entries must include an id or code.")
    if kind not in {"school", "center"}:
        raise SheetImportError("Teacher assignments must use school or center.")
    if identifier.isdigit():
        return identifier
    if kind == "school":
        return _lookup_active_code(models.School, identifier, "school")
    return _lookup_active_code(models.Center, identifier, "centre")


def _parse_teacher_assignments(value):
    assignments = []
    for chunk in re.split(r"[;|]", value):
        token = chunk.strip()
        if not token:
            continue
        if ":" in token:
            raw_kind, identifier = token.split(":", 1)
        elif "=" in token:
            raw_kind, identifier = token.split("=", 1)
        else:
            raise SheetImportError(
                "Teacher assignments must look like school:SAS;center:ACE."
            )
        kind = raw_kind.strip().lower()
        if kind == "centre":
            kind = "center"
        identifier = identifier.strip()
        object_id = _scope_id_from_token(kind, identifier)
        assignments.append({f"{kind}_id": object_id})
    if not assignments:
        raise SheetImportError("Teacher assignments cannot be blank.")
    return assignments


def _sheet_row_payload(data, role):
    payload = {"role": role}
    for field in ("username", "email", "first_name", "last_name", "ums_id", "phone_number", "password"):
        if field in data:
            payload[field] = data[field]

    if role == "student":
        if "room" in data:
            payload["room"] = data["room"]
        school_id = _scope_id_from_row(
            data,
            id_key="school_id",
            code_key="school_code",
            model=models.School,
            label="school",
        )
        center_id = _scope_id_from_row(
            data,
            id_key="center_id",
            code_key="center_code",
            model=models.Center,
            label="centre",
        )
        program_id = _scope_id_from_row(
            data,
            id_key="program_id",
            code_key="program_code",
            model=models.Program,
            label="program",
        )
        if school_id:
            payload["school_id"] = school_id
        if center_id:
            payload["center_id"] = center_id
        if program_id:
            payload["program_id"] = program_id

    if role == "teacher":
        if "designation" in data:
            payload["designation"] = data["designation"]
        if data.get("teacher_assignments"):
            payload["teacher_assignments"] = _parse_teacher_assignments(
                data["teacher_assignments"]
            )
        else:
            school_id = _scope_id_from_row(
                data,
                id_key="school_id",
                code_key="school_code",
                model=models.School,
                label="school",
            )
            center_id = _scope_id_from_row(
                data,
                id_key="center_id",
                code_key="center_code",
                model=models.Center,
                label="centre",
            )
            if school_id:
                payload["school_id"] = school_id
            if center_id:
                payload["center_id"] = center_id

    if role == "executive":
        school_id = _scope_id_from_row(
            data,
            id_key="school_id",
            code_key="school_code",
            model=models.School,
            label="school",
        )
        center_id = _scope_id_from_row(
            data,
            id_key="center_id",
            code_key="center_code",
            model=models.Center,
            label="centre",
        )
        unit_id = _scope_id_from_row(
            data,
            id_key="unit_id",
            code_key="unit_code",
            model=models.Unit,
            label="unit",
        )
        if school_id:
            payload["school_id"] = school_id
        if center_id:
            payload["center_id"] = center_id
        if unit_id:
            payload["unit_id"] = unit_id

    return payload


def _payload_with_temporary_password(payload):
    account_payload = dict(payload)
    supplied_password = account_payload.get("password", "")
    if not isinstance(supplied_password, str) or not supplied_password.strip():
        temporary_password = _generate_temporary_password()
        account_payload["password"] = temporary_password
    else:
        temporary_password = supplied_password
    return account_payload, temporary_password


def _create_account_from_payload(payload, config):
    account_payload, temporary_password = _payload_with_temporary_password(payload)
    serializer = RegisterSerializer(data=account_payload)
    if not serializer.is_valid():
        raise AccountValidationError(
            _first_error(serializer.errors, default="Unable to create account."),
            serializer.errors,
        )

    full_name = (
        f"{serializer.validated_data.get('first_name', '')} "
        f"{serializer.validated_data.get('last_name', '')}"
    ).strip() or serializer.validated_data.get("username", "")
    email = serializer.validated_data.get("email", "")
    username = serializer.validated_data.get("username", "")

    try:
        _build_account_email(
            full_name=full_name,
            username=username,
            email=email,
            role_label=config["label"],
            temporary_password=temporary_password,
        )
    except Exception as exc:
        raise AccountEmailError from exc

    try:
        return serializer.save()
    except IntegrityError as exc:
        raise AccountValidationError("Account could not be saved. Check for duplicate values.") from exc


class AdminCreateAccount(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "title": "Create Account",
                "section": "admin",
                "roles": [
                    {"role": role, **config}
                    for role, config in CREATE_ACCOUNT_ROLES.items()
                ],
            },
            status=status.HTTP_200_OK,
        )


class AdminCreateAccountRole(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, role):
        config = CREATE_ACCOUNT_ROLES.get(role)
        if not config:
            return Response(
                {"detail": "Unsupported account role."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {"role": role, "section": "admin", **config}

        schools = models.School.objects.filter(is_active=True).order_by("name")
        centers = models.Center.objects.filter(is_active=True).order_by("name")
        programs = models.Program.objects.filter(is_active=True).order_by("name")

        if role == "executive":
            payload["schools"] = SchoolSerializer(schools, many=True).data
            payload["centers"] = CenterSerializer(centers, many=True).data
            payload["units"] = UnitSerializer(
                models.Unit.objects.filter(is_active=True).order_by("name"),
                many=True,
            ).data

        if role in {"student", "teacher"}:
            payload["schools"] = SchoolSerializer(schools, many=True).data
            payload["centers"] = CenterSerializer(
                centers.filter(center_type=models.Center.CENTER_ACADEMIC)
                if role == "student"
                else centers,
                many=True,
            ).data
        if role == "student":
            payload["programs"] = ProgramSerializer(programs, many=True).data

        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request, role):
        config = CREATE_ACCOUNT_ROLES.get(role)
        if not config:
            return Response(
                {"detail": "Unsupported account role."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {**request.data, "role": role}
        try:
            user = _create_account_from_payload(payload, config)
        except AccountValidationError as exc:
            return Response(
                {
                    "detail": exc.detail,
                    "errors": exc.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AccountEmailError:
            email = payload.get("email", "")
            full_name = f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip()
            logger.exception(
                "Unable to send account credentials email for %s <%s>.",
                full_name,
                email,
            )
            return Response(
                {
                    "detail": (
                        f"{config['label']} account could not be created because the "
                        "credentials email could not be sent. Check the SMTP "
                        "configuration and try again."
                    ),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "message": (
                    f"{config['label']} account created successfully. "
                    f"Credentials were sent to {user.email}."
                ),
                "email_sent": True,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminCreateAccountRoleImport(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, role):
        config = CREATE_ACCOUNT_ROLES.get(role)
        if not config:
            return Response(
                {"detail": "Unsupported account role."},
                status=status.HTTP_404_NOT_FOUND,
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "Upload a .csv or .xlsx file named file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rows = _extract_import_rows(uploaded_file)
        except SheetImportError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        created_count = 0
        for item in rows:
            row_number = item["row"]
            try:
                payload = _sheet_row_payload(item["data"], role)
                user = _create_account_from_payload(payload, config)
            except SheetImportError as exc:
                results.append(
                    {"row": row_number, "status": "error", "detail": str(exc)}
                )
            except AccountValidationError as exc:
                results.append(
                    {
                        "row": row_number,
                        "status": "error",
                        "detail": exc.detail,
                        "errors": exc.errors,
                    }
                )
            except AccountEmailError:
                logger.exception(
                    "Unable to send account credentials email while importing %s row %s.",
                    role,
                    row_number,
                )
                results.append(
                    {
                        "row": row_number,
                        "status": "error",
                        "detail": (
                            "Credentials email could not be sent. Check the SMTP "
                            "configuration and import this row again."
                        ),
                    }
                )
            else:
                created_count += 1
                results.append(
                    {
                        "row": row_number,
                        "status": "created",
                        "username": user.username,
                        "email": user.email,
                        "email_sent": True,
                    }
                )

        failed_count = len(results) - created_count
        if created_count and failed_count:
            response_status = status.HTTP_200_OK
        elif created_count:
            response_status = status.HTTP_201_CREATED
        else:
            response_status = status.HTTP_200_OK

        return Response(
            {
                "message": (
                    f"Imported {created_count} {config['label'].lower()} account"
                    f"{'' if created_count == 1 else 's'}."
                    + (
                        f" {failed_count} row{'' if failed_count == 1 else 's'} need attention."
                        if failed_count
                        else ""
                    )
                ),
                "created_count": created_count,
                "failed_count": failed_count,
                "total_rows": len(rows),
                "results": results,
            },
            status=response_status,
        )
