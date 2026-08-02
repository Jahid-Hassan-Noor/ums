from django.contrib import admin

from quiz_app.models import (
    Question,
    QuestionAttempt,
    QuestionAttemptStep,
    QuestionBank,
    QuestionCategory,
    QuestionChoice,
    QuestionVersion,
    Quiz,
    QuizAccessOverride,
    QuizAttempt,
    QuizGrade,
    QuizQuestionSlot,
    QuizRandomRule,
    QuizSection,
)


admin.site.register(QuestionBank)
admin.site.register(QuestionCategory)
admin.site.register(Question)
admin.site.register(QuestionVersion)
admin.site.register(QuestionChoice)
admin.site.register(Quiz)
admin.site.register(QuizSection)
admin.site.register(QuizQuestionSlot)
admin.site.register(QuizRandomRule)
admin.site.register(QuizAccessOverride)
admin.site.register(QuizAttempt)
admin.site.register(QuestionAttempt)
admin.site.register(QuestionAttemptStep)
admin.site.register(QuizGrade)
