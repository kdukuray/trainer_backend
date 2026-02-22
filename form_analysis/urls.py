from django.urls import path

from . import views

urlpatterns = [
    path("exercises/", views.list_exercises, name="list_exercises"),
    path("analyze/", views.analyze_form, name="analyze_form"),
    path("analyses/", views.list_analyses, name="list_analyses"),
    path("analyses/<int:analysis_id>/", views.get_analysis_detail, name="get_analysis_detail"),
]
