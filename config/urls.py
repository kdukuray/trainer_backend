"""
Root URL configuration for the trainr backend.

All API endpoints are namespaced under ``/api/<app>/``.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/calories/", include("calories.urls")),
    path("api/education/", include("education.urls")),
    path("api/meal-plans/", include("meal_plans.urls")),
    path("api/form/", include("form_analysis.urls")),
]
