from django.urls import path

from . import views

urlpatterns = [
    path("analyze/", views.analyze_meal_image, name="analyze_meal_image"),
    path("logs/", views.list_meal_logs, name="list_meal_logs"),
    path("logs/<int:log_id>/", views.get_meal_log_detail, name="get_meal_log_detail"),
]
