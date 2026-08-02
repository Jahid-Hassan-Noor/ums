from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsStudentRole, IsTeacherRole
from quiz_app.models import QuestionAttempt, QuizAttempt
from quiz_app.services import (
    QuizWorkflowError,
    add_question_to_quiz,
    add_random_rule_to_quiz,
    answer_attempt_question,
    attempt_for_student,
    attempt_for_teacher,
    attempt_payload,
    create_quiz_from_payload,
    create_bank_question,
    create_new_question_version,
    create_question_category,
    get_client_ip,
    get_student_profile,
    get_teacher_profile,
    manually_grade_question,
    quiz_for_student,
    quiz_for_teacher,
    quiz_payload,
    question_bank_options_payload,
    question_payload,
    start_quiz_attempt,
    student_access_payload,
    teacher_question_bank_payload,
    student_quiz_queryset,
    submit_attempt,
    teacher_options_payload,
    teacher_quiz_queryset,
    update_quiz_from_payload,
)


def get_safe_exam_browser_key(request):
    return (
        request.headers.get("X-Safe-Exam-Browser-Config-Key-Hash")
        or request.headers.get("X-Safe-Exam-Browser-Config-Key")
        or ""
    )


def workflow_error_response(exc):
    return Response({"detail": str(exc)}, status=getattr(exc, "status_code", 400))


class TeacherQuizList(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        teacher = get_teacher_profile(request.user)
        quizzes = teacher_quiz_queryset(teacher)
        return Response(
            {
                "title": "Quizzes",
                "section": "teacher",
                "options": teacher_options_payload(teacher),
                "quizzes": [quiz_payload(quiz, include_teacher=True) for quiz in quizzes],
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        teacher = get_teacher_profile(request.user)
        try:
            quiz = create_quiz_from_payload(teacher, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Quiz saved.",
                "quiz": quiz_payload(quiz, include_detail=True, include_teacher=True),
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherQuizDetail(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request, quiz_id):
        teacher = get_teacher_profile(request.user)
        quiz = quiz_for_teacher(teacher, quiz_id)
        if not quiz:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "title": quiz.title,
                "section": "teacher",
                "quiz": quiz_payload(quiz, include_detail=True, include_teacher=True),
                "options": question_bank_options_payload(teacher, offering=quiz.offering),
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, quiz_id):
        teacher = get_teacher_profile(request.user)
        quiz = quiz_for_teacher(teacher, quiz_id)
        if not quiz:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            quiz = update_quiz_from_payload(quiz, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Quiz updated.",
                "quiz": quiz_payload(quiz, include_detail=True, include_teacher=True),
                "options": question_bank_options_payload(teacher, offering=quiz.offering),
            },
            status=status.HTTP_200_OK,
        )


class TeacherQuestionBankView(APIView):
    permission_classes = [IsTeacherRole]

    def get(self, request):
        teacher = get_teacher_profile(request.user)
        return Response(
            {
                "title": "Question Bank",
                "section": "teacher",
                **teacher_question_bank_payload(teacher),
            },
            status=status.HTTP_200_OK,
        )


class TeacherQuestionBankCategoryCreate(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request):
        teacher = get_teacher_profile(request.user)
        try:
            category = create_question_category(teacher, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Category saved.",
                "category": {
                    "id": category.id,
                    "bank_id": category.bank_id,
                    "parent_id": category.parent_id,
                    "title": category.title,
                    "description": category.description,
                    "sort_order": category.sort_order,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherQuestionBankQuestionCreate(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request):
        teacher = get_teacher_profile(request.user)
        try:
            question, _version = create_bank_question(teacher, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Question saved.",
                "question": question_payload(question, include_versions=True),
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherQuestionVersionCreate(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request, question_id):
        teacher = get_teacher_profile(request.user)
        try:
            version = create_new_question_version(teacher, question_id, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Question version saved.",
                "version": {
                    **question_payload(version.question, include_versions=True),
                    "latest_version_id": version.id,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherQuizQuestionCreate(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request, quiz_id):
        teacher = get_teacher_profile(request.user)
        quiz = quiz_for_teacher(teacher, quiz_id)
        if not quiz:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            add_question_to_quiz(quiz, teacher, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        quiz.refresh_from_db()
        return Response(
            {
                "message": "Question added.",
                "quiz": quiz_payload(quiz, include_detail=True, include_teacher=True),
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherQuizRandomRuleCreate(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request, quiz_id):
        teacher = get_teacher_profile(request.user)
        quiz = quiz_for_teacher(teacher, quiz_id)
        if not quiz:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            add_random_rule_to_quiz(quiz, request.data)
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        quiz.refresh_from_db()
        return Response(
            {
                "message": "Random rule added.",
                "quiz": quiz_payload(quiz, include_detail=True, include_teacher=True),
            },
            status=status.HTTP_201_CREATED,
        )


class TeacherQuizAttemptGrade(APIView):
    permission_classes = [IsTeacherRole]

    def post(self, request, quiz_id, attempt_id):
        teacher = get_teacher_profile(request.user)
        attempt = attempt_for_teacher(teacher, attempt_id)
        if not attempt or str(attempt.quiz_id) != str(quiz_id):
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)
        question_attempt = (
            QuestionAttempt.objects.select_related("attempt", "quiz")
            .filter(pk=request.data.get("question_attempt_id"), attempt=attempt)
            .first()
        )
        if not question_attempt:
            return Response({"detail": "Question attempt not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            manually_grade_question(
                question_attempt,
                teacher,
                awarded_mark=request.data.get("awarded_mark"),
                feedback=request.data.get("feedback", ""),
            )
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        attempt.refresh_from_db()
        return Response(
            {
                "message": "Question graded.",
                "attempt": attempt_payload(attempt, include_questions=True, teacher=True, review=True),
            },
            status=status.HTTP_200_OK,
        )


class StudentQuizList(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request):
        student = get_student_profile(request.user)
        ip_address = get_client_ip(request)
        safe_exam_browser_key = get_safe_exam_browser_key(request)
        quizzes = student_quiz_queryset(student)
        return Response(
            {
                "title": "Quizzes",
                "section": "student",
                "quizzes": [
                    {
                        **quiz_payload(quiz, student=student),
                        "access": student_access_payload(
                            quiz,
                            student,
                            ip_address=ip_address,
                            safe_exam_browser_key=safe_exam_browser_key,
                        ),
                    }
                    for quiz in quizzes
                ],
            },
            status=status.HTTP_200_OK,
        )


class StudentQuizDetail(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request, quiz_id):
        student = get_student_profile(request.user)
        quiz = quiz_for_student(student, quiz_id)
        if not quiz:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "title": quiz.title,
                "section": "student",
                "quiz": {
                    **quiz_payload(quiz, include_detail=False, student=student),
                    "access": student_access_payload(
                        quiz,
                        student,
                        ip_address=get_client_ip(request),
                        safe_exam_browser_key=get_safe_exam_browser_key(request),
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class StudentQuizStart(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, quiz_id):
        student = get_student_profile(request.user)
        quiz = quiz_for_student(student, quiz_id)
        if not quiz:
            return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            attempt = start_quiz_attempt(
                quiz,
                student,
                password=request.data.get("password", ""),
                ip_address=get_client_ip(request),
                safe_exam_browser_key=get_safe_exam_browser_key(request),
            )
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Quiz attempt started.",
                "attempt": attempt_payload(attempt, include_questions=True),
            },
            status=status.HTTP_201_CREATED,
        )


class StudentQuizAttemptDetail(APIView):
    permission_classes = [IsStudentRole]

    def get(self, request, attempt_id):
        student = get_student_profile(request.user)
        attempt = attempt_for_student(student, attempt_id)
        if not attempt:
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)
        review = request.query_params.get("review") == "1"
        if review and not attempt.quiz.review_show_attempt:
            return Response({"detail": "Review is not available for this quiz."}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "title": attempt.quiz.title,
                "section": "student",
                "attempt": attempt_payload(
                    attempt,
                    include_questions=True,
                    review=review,
                    teacher=False,
                ),
            },
            status=status.HTTP_200_OK,
        )


class StudentQuizAttemptAnswer(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, attempt_id):
        student = get_student_profile(request.user)
        attempt = attempt_for_student(student, attempt_id)
        if not attempt:
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            answer_attempt_question(
                attempt,
                request.data.get("question_attempt_id"),
                request.data.get("response") or {},
                actor=student,
                ip_address=get_client_ip(request),
            )
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        attempt.refresh_from_db()
        return Response(
            {
                "message": "Answer saved.",
                "attempt": attempt_payload(attempt, include_questions=True),
            },
            status=status.HTTP_200_OK,
        )


class StudentQuizAttemptSubmit(APIView):
    permission_classes = [IsStudentRole]

    def post(self, request, attempt_id):
        student = get_student_profile(request.user)
        attempt = attempt_for_student(student, attempt_id)
        if not attempt:
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            attempt = submit_attempt(
                attempt,
                actor=student,
                ip_address=get_client_ip(request),
                responses=request.data.get("responses") or {},
            )
        except QuizWorkflowError as exc:
            return workflow_error_response(exc)
        return Response(
            {
                "message": "Quiz submitted.",
                "attempt": attempt_payload(attempt, include_questions=True, review=True),
            },
            status=status.HTTP_200_OK,
        )
