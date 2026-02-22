from django.contrib import admin

from .models import FlashCard, QuizQuestion, UserQuizResult

admin.site.register(QuizQuestion)
admin.site.register(FlashCard)
admin.site.register(UserQuizResult)
