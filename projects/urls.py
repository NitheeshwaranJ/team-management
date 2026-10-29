from django.urls import path
from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("create/", views.project_create, name="project_create"),
    path("<int:project_id>/", views.project_detail, name="project_detail"),
    path(
        "<int:project_id>/members/",
        views.project_members,
        name="project_members",
    ),
    path(
        "<int:project_id>/members/<int:membership_id>/role/",
        views.member_update_role,
        name="member_update_role",
    ),
    path(
        "<int:project_id>/members/<int:membership_id>/remove/",
        views.member_remove,
        name="member_remove",
    ),
]