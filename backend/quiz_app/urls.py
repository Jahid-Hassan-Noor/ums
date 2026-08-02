from django.urls import path

from quiz_app.views import (
    StudentQuizAttemptAnswer,
    StudentQuizAttemptDetail,
    StudentQuizAttemptSubmit,
    StudentQuizDetail,
    StudentQuizList,
    StudentQuizStart,
    TeacherQuestionBankCategoryCreate,
    TeacherQuestionBankQuestionCreate,
    TeacherQuestionBankView,
    TeacherQuestionVersionCreate,
    TeacherQuizAttemptGrade,
    TeacherQuizDetail,
    TeacherQuizList,
    TeacherQuizQuestionCreate,
    TeacherQuizRandomRuleCreate,
)


urlpatterns = [
    path("teacher/quizzes", TeacherQuizList.as_view()),
    path("teacher/question-bank", TeacherQuestionBankView.as_view()),
    path("teacher/question-bank/categories", TeacherQuestionBankCategoryCreate.as_view()),
    path("teacher/question-bank/questions", TeacherQuestionBankQuestionCreate.as_view()),
    path("teacher/question-bank/questions/<int:question_id>/versions", TeacherQuestionVersionCreate.as_view()),
    path("teacher/quizzes/<int:quiz_id>", TeacherQuizDetail.as_view()),
    path("teacher/quizzes/<int:quiz_id>/questions", TeacherQuizQuestionCreate.as_view()),
    path("teacher/quizzes/<int:quiz_id>/random-rules", TeacherQuizRandomRuleCreate.as_view()),
    path("teacher/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/grade", TeacherQuizAttemptGrade.as_view()),
    path("student/quizzes", StudentQuizList.as_view()),
    path("student/quizzes/<int:quiz_id>", StudentQuizDetail.as_view()),
    path("student/quizzes/<int:quiz_id>/start", StudentQuizStart.as_view()),
    path("student/attempts/<int:attempt_id>", StudentQuizAttemptDetail.as_view()),
    path("student/attempts/<int:attempt_id>/answer", StudentQuizAttemptAnswer.as_view()),
    path("student/attempts/<int:attempt_id>/submit", StudentQuizAttemptSubmit.as_view()),
]
