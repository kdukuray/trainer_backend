from django.urls import path

from . import views

urlpatterns = [
    path("quiz/", views.get_quiz_questions, name="get_quiz_questions"),
    path("quiz/submit/", views.submit_quiz, name="submit_quiz"),
    path("flashcards/", views.get_flashcards, name="get_flashcards"),
]
