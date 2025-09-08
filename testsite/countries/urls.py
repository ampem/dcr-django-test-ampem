from django.urls import path

from . import views

urlpatterns = [
    path("stats/", views.stats),
    path("id:<country_id>/", views.detail),
    path("name:<country_name>/", views.detail),
]
