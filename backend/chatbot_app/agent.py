import re

from admin_app.models import Profile
from chatbot_app.llm import generate_chat_answer
from chatbot_app.search_services import retrieve_for_chatbot
from chatbot_app import tools


PRIVATE_INTENTS = {
    "self_profile",
    "next_class",
    "today_classes",
    "weekly_timetable",
    "next_deadline",
    "upcoming_assignments",
    "current_courses",
    "attendance_status",
    "exam_schedule",
}

RETRIEVAL_INTENTS = {
    "public_or_policy_knowledge",
    "portal_navigation_search",
    "course_resource_or_assignment_instruction",
}

SENSITIVE_PERSONAL_TERMS = {
    "passport",
    "identity",
    "ic number",
    "phone",
    "mobile",
    "address",
    "grade",
    "grades",
    "gpa",
    "marks",
    "medical",
    "payment details",
    "payment secret",
    "payment secrets",
    "payment gateway",
    "visa",
    "student id",
    "staff id",
    "aiu id",
}


SYSTEM_PROMPT = """
You are the AIU Unified Portal assistant.
Answer only from the provided context.
Never invent class times, venues, deadlines, personal data, marks, or identifiers.
For personal timetable, deadline, course, attendance, or exam questions, the backend tool result is the source of truth.
Keep the answer concise and useful.
""".strip()


def classify_intent(question):
    q = question.lower()
    if "email" in q and not any(term in q for term in ("my email", "my e-mail")):
        return "directory_email"
    if (
        "who am i" in q
        or "whoami" in q
        or "my profile" in q
        or "my account" in q
        or "what is my name" in q
        or "which account" in q
    ):
        return "self_profile"
    if "next class" in q or "when is my class" in q or "upcoming class" in q:
        return "next_class"
    if "today" in q and ("class" in q or "timetable" in q or "schedule" in q):
        return "today_classes"
    if "timetable" in q or "weekly schedule" in q or "calendar" in q:
        return "weekly_timetable"
    if "deadline" in q or "due" in q:
        return "next_deadline"
    if "assignment" in q or "lab activity" in q:
        if any(term in q for term in ("instruction", "explain", "guide", "rubric", "resource", "material")):
            return "course_resource_or_assignment_instruction"
        return "upcoming_assignments"
    if "current course" in q or "my course" in q or "enrolled course" in q:
        return "current_courses"
    if "attendance" in q:
        if any(term in q for term in ("policy", "rule", "requirement", "guide")):
            return "public_or_policy_knowledge"
        return "attendance_status"
    if "exam" in q:
        return "exam_schedule"
    if any(term in q for term in ("where is", "find", "search", "open", "page", "link", "navigate")):
        return "portal_navigation_search"
    if any(
        term in q
        for term in (
            "policy",
            "rule",
            "rules",
            "handbook",
            "guideline",
            "library",
            "venue",
            "course registration",
            "programme",
            "program",
            "admission",
            "service",
            "helpdesk",
            "news",
            "event",
            "announcement",
            "official link",
        )
    ):
        return "public_or_policy_knowledge"
    return "public_or_policy_knowledge"


def _mentions_other_person(question):
    q = question.lower()
    if re.search(r"\b(my|me|mine|i)\b", q):
        return False
    if re.search(r"\b(of|for|about)\s+[a-z][a-z.'-]{2,}", q):
        return True
    return bool(re.search(r"[a-z][a-z.'-]{2,}'s\b", q))


def _privacy_refusal(intent, question):
    q = question.lower()
    if intent == "directory_email":
        return None
    if any(term in q for term in SENSITIVE_PERSONAL_TERMS):
        return (
            "I cannot disclose private identifiers, phone numbers, grades, attendance, "
            "medical, passport, or visa information through a public lookup."
        )
    if intent in PRIVATE_INTENTS and _mentions_other_person(question):
        return "I can only answer private timetable, course, deadline, attendance, and exam questions for your own account."
    return None


def _base_payload(answer, *, intent, scope, requires_auth=False, data=None, sources=None, model=None):
    return {
        "answer": answer,
        "intent": intent,
        "scope": scope,
        "requires_auth": requires_auth,
        "data": data,
        "sources": sources or [],
        "model": model or "deterministic",
    }


def _login_required(intent):
    return _base_payload(
        "Please log in first so I can answer using only your own portal account data.",
        intent=intent,
        scope="private",
        requires_auth=True,
        sources=[],
    )


def _role_not_supported(intent):
    return _base_payload(
        "This personal chatbot tool is currently available for student and teacher accounts.",
        intent=intent,
        scope="private",
    )


def _private_tool_answer(user, intent):
    role = tools.current_role(user)
    if intent == "self_profile":
        result = tools.get_self_profile_for_user(user)
        return _base_payload(
            result["answer"],
            intent=intent,
            scope="private",
            data=result.get("data"),
        )

    if intent in {"next_class", "today_classes", "weekly_timetable", "next_deadline", "upcoming_assignments", "current_courses"}:
        if role not in {Profile.ROLE_STUDENT, Profile.ROLE_TEACHER}:
            return _role_not_supported(intent)

    if intent == "next_class":
        result = tools.get_next_class_for_user(user)
    elif intent == "today_classes":
        result = tools.get_today_classes_for_user(user)
    elif intent == "weekly_timetable":
        result = tools.get_weekly_timetable_for_user(user)
    elif intent == "next_deadline":
        result = tools.get_next_deadline_for_user(user)
    elif intent == "upcoming_assignments":
        result = tools.get_upcoming_assignments_for_user(user)
    elif intent == "current_courses":
        result = tools.get_current_courses_for_user(user)
    elif intent == "attendance_status":
        return _base_payload(
            "Attendance summaries are private. Please open your attendance dashboard for the official record; chatbot attendance summaries can be added through the existing attendance service next.",
            intent=intent,
            scope="private",
        )
    elif intent == "exam_schedule":
        result = tools.get_weekly_timetable_for_user(user)
    else:
        result = {"answer": "I do not have a tool for that request yet.", "data": None}

    return _base_payload(
        result["answer"],
        intent=intent,
        scope="private",
        data=result.get("data"),
    )


def _public_answer(question, intent):
    if intent == "directory_email":
        result = tools.public_directory_email_answer(question)
        return _base_payload(
            result["answer"],
            intent=intent,
            scope="public",
            data=result.get("data"),
            sources=result.get("sources"),
        )

    context = tools.public_context_for_question(question)
    snippets = context["snippets"]
    sources = context["sources"]
    if snippets:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Question:\n"
                    f"{question}\n\n"
                    "Public context:\n"
                    + "\n".join(f"- {item}" for item in snippets)
                ),
            },
        ]
        model_answer, model = generate_chat_answer(messages)
        if model_answer:
            return _base_payload(
                model_answer,
                intent=intent,
                scope="public",
                sources=sources,
                model=model,
            )
        return _base_payload(
            " ".join(snippets),
            intent=intent,
            scope="public",
            sources=sources,
        )

    return _base_payload(
        (
            "I can help with public AIU information such as admissions, programmes, "
            "schools, services, news, events, official links, and public directory emails. "
            "For personal schedules, assignments, attendance, or exams, please log in first."
        ),
        intent=intent,
        scope="public",
    )


def _retrieval_answer(user, question, intent):
    payload = retrieve_for_chatbot(user, question)
    results = payload["results"]
    if not results:
        return _base_payload(
            "I could not find an approved portal source for that question.",
            intent=intent,
            scope="retrieval",
            sources=[],
        )

    context_lines = [
        f"{index}. {item['title']}: {item['summary']}"
        for index, item in enumerate(results, start=1)
    ]
    sources = [
        {
            "title": item["source_label"] or item["title"],
            "type": item["type"],
            "url": item.get("url", ""),
        }
        for item in results
    ]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Question:\n"
                f"{question}\n\n"
                "Approved retrieved sources:\n"
                + "\n".join(context_lines)
            ),
        },
    ]
    model_answer, model = generate_chat_answer(messages)
    if model_answer:
        return _base_payload(
            model_answer,
            intent=intent,
            scope="retrieval",
            sources=sources,
            model=model,
            data={"results": results},
        )

    answer = "I found this in approved portal sources:\n" + "\n".join(
        f"- {item['title']}: {item['summary']}" for item in results[:3]
    )
    return _base_payload(
        answer,
        intent=intent,
        scope="retrieval",
        sources=sources,
        data={"results": results},
    )


def answer_question(user, question):
    intent = classify_intent(question)
    refusal = _privacy_refusal(intent, question)
    if refusal:
        return _base_payload(refusal, intent=intent, scope="privacy")

    if intent in PRIVATE_INTENTS:
        if not user or not user.is_authenticated:
            return _login_required(intent)
        return _private_tool_answer(user, intent)

    if intent in RETRIEVAL_INTENTS:
        return _retrieval_answer(user, question, intent)

    return _public_answer(question, intent)
