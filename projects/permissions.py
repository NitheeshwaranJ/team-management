
from .models import ProjectMembership


def can_view_project(user, project):
    """The owner and project members can view the project."""
    if not user.is_authenticated:
        return False

    return (
        project.owner_id == user.pk
        or ProjectMembership.objects.filter(
            project=project,
            user=user,
        ).exists()
    )


def can_manage_project(user, project):
    """Only the owner and Managers can manage the project."""
    if not user.is_authenticated:
        return False

    return (
        project.owner_id == user.pk
        or ProjectMembership.objects.filter(
            project=project,
            user=user,
            role=ProjectMembership.Role.MANAGER,
        ).exists()
    )


def can_update_task_status(user, project):
    """Any authorized project
      user can update task status."""
    return can_view_project(user, project)
