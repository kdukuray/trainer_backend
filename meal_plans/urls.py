from django.urls import path

from . import views

urlpatterns = [
    path("generate/", views.generate_meal_plan, name="generate_meal_plan"),
    path("", views.list_meal_plans, name="list_meal_plans"),
    path("<int:plan_id>/", views.get_meal_plan_detail, name="get_meal_plan_detail"),
]
