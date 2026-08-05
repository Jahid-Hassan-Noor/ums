from auth_app.auth_tokens import issue_ums_refresh
from auth_app.models import Profile
from applicant_app import models
from applicant_app.admissions_setup import admissions_setup, detail_field_label
from applicant_app.serializers import ApplicantSerializer
from core.media_access import public_profile_picture_url


def profile_for_user(user):
    return Profile.objects.filter(user=user, is_active=True).first()


def applicant_for_user(user):
    return models.Applicant.objects.filter(profile__user=user, is_active=True).first()


def auth_payload(user):
    refresh = issue_ums_refresh(user)
    applicant = applicant_for_user(user)
    profile = profile_for_user(user)
    user_payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": Profile.ROLE_APPLICANT,
        "ums_id": None,
        "phone_number": applicant.phone if applicant else None,
        "profile_picture": public_profile_picture_url(profile),
        "is_email_verified": bool(user.email),
        "is_account_banned": not user.is_active or bool(applicant and not applicant.is_active),
    }
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": user_payload,
        "applicant": ApplicantSerializer(applicant).data if applicant else None,
    }


def required_submission_gaps(application):
    gaps = []
    setup = admissions_setup()
    preferences = application.programme_preferences or []
    if len([item for item in preferences if item]) < 4:
        gaps.append("Select four different programme preferences.")

    personal = application.personal_information or {}
    academic = application.academic_information or {}

    for field_name in setup["required_detail_fields"]:
        section, key = field_name.split(".", 1)
        source = personal if section == "personal" else academic
        if not source.get(key):
            gaps.append(f"{detail_field_label(field_name)} is required.")

    answers = personal.get("question_responses") or {}
    for question in setup["custom_questions"]:
        if question.get("required") and not str(answers.get(question["id"], "")).strip():
            gaps.append(f"{question['label']} is required.")

    if application.scholarship_requested:
        scholarship = application.scholarship_information or {}
        if not scholarship.get("personal_statement"):
            gaps.append("Scholarship personal statement is required.")

    uploaded_document_types = set(application.documents.values_list("document_type", flat=True))
    document_labels = {
        item["value"]: item["label"]
        for item in setup["document_types"]
    }
    for document_type in setup["required_documents"]:
        if document_type not in uploaded_document_types:
            gaps.append(f"{document_labels.get(document_type, document_type)} must be uploaded.")

    if not application.statement_accepted:
        gaps.append("Statement of truth must be accepted.")

    return gaps
