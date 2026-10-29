from django.contrib import admin
from .models import Project, ProjectMembership


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "role")
    list_filter = ("role",)
    search_fields = ("project__name", "user__username")