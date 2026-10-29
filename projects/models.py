from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        MEMBER = "MEMBER", "Member"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.project} ({self.role})"