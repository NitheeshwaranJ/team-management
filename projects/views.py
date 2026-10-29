from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from tasks.models import Task

from .forms import AddMemberForm, ProjectForm
from .models import Project, ProjectMembership
from .permissions import can_manage_project, can_view_project


@login_required
def project_list(request):
    projects = Project.objects.filter(
        Q(owner=request.user)
        | Q(memberships__user=request.user)
    ).distinct().order_by("-created_at")

    return render(
        request,
        "projects/project_list.html",
        {"projects": projects},
    )


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                project = form.save(commit=False)
                project.owner = request.user
                project.save()

                ProjectMembership.objects.create(
                    project=project,
                    user=request.user,
                    role=ProjectMembership.Role.MANAGER,
                )

            return redirect("project_list")
    else:
        form = ProjectForm()

    return render(
        request,
        "projects/project_form.html",
        {"form": form},
    )


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.filter(
            Q(owner=request.user)
            | Q(memberships__user=request.user)
        ).distinct(),
        pk=project_id,
    )
    status_filter = request.GET.get("status", "")
    priority_filter = request.GET.get("priority", "")

    tasks = Task.objects.filter(
        project=project
    ).select_related("assignee").order_by("due_date", "created_at")

    if status_filter in Task.Status.values:
        tasks = tasks.filter(status=status_filter)

    if priority_filter in Task.Priority.values:
        tasks = tasks.filter(priority=priority_filter)

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "tasks": tasks,
            "status_filter": status_filter,
            "priority_filter": priority_filter,
            "status_choices": Task.Status.choices,
            "priority_choices": Task.Priority.choices,
            "can_manage": can_manage_project(request.user, project),
        },
    )


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------

def _get_manageable_project(request, project_id):
    """
    Return the project if the current user may manage it.

    Outsiders get a 404 (we don't reveal that the project exists).
    Regular members get a 403 (they can see it but cannot manage it).
    """
    project = get_object_or_404(Project, pk=project_id)

    if not can_view_project(request.user, project):
        raise Http404("Project not found.")

    if not can_manage_project(request.user, project):
        raise PermissionDenied(
            "Only the project owner or a Manager can manage members."
        )

    return project


@login_required
def project_members(request, project_id):
    """List members (everyone with access) and add members (managers only)."""
    project = get_object_or_404(Project, pk=project_id)

    if not can_view_project(request.user, project):
        raise Http404("Project not found.")

    can_manage = can_manage_project(request.user, project)
    form = None

    if request.method == "POST":
        if not can_manage:
            raise PermissionDenied(
                "Only the project owner or a Manager can manage members."
            )

        form = AddMemberForm(request.POST, project=project)

        if form.is_valid():
            user = form.user_to_add
            try:
                with transaction.atomic():
                    ProjectMembership.objects.create(
                        project=project,
                        user=user,
                        role=form.cleaned_data["role"],
                    )
            except IntegrityError:
                # Someone added the same user at the same moment.
                messages.error(
                    request,
                    "This user is already part of the project.",
                )
            else:
                messages.success(
                    request,
                    f"{user.username} was added to the project.",
                )
            return redirect("project_members", project_id=project.id)
    elif can_manage:
        form = AddMemberForm(project=project)

    memberships = list(
        project.memberships.select_related("user").order_by("user__username")
    )
    for membership in memberships:
        membership.is_owner = membership.user_id == project.owner_id

    return render(
        request,
        "projects/project_members.html",
        {
            "project": project,
            "memberships": memberships,
            "form": form,
            "can_manage": can_manage,
            "role_choices": ProjectMembership.Role.choices,
        },
    )


@login_required
@require_POST
def member_update_role(request, project_id, membership_id):
    project = _get_manageable_project(request, project_id)
    # Filtering by project prevents editing another project's membership
    # by guessing its id.
    membership = get_object_or_404(
        ProjectMembership.objects.select_related("user"),
        pk=membership_id,
        project=project,
    )

    if membership.user_id == project.owner_id:
        messages.error(request, "The project owner's role cannot be changed.")
        return redirect("project_members", project_id=project.id)

    new_role = request.POST.get("role")

    if new_role not in ProjectMembership.Role.values:
        messages.error(request, "Invalid role.")
    else:
        membership.role = new_role
        membership.save(update_fields=["role"])
        messages.success(
            request,
            f"{membership.user.username} is now a "
            f"{membership.get_role_display()}.",
        )

    return redirect("project_members", project_id=project.id)


@login_required
@require_POST
def member_remove(request, project_id, membership_id):
    project = _get_manageable_project(request, project_id)
    membership = get_object_or_404(
        ProjectMembership.objects.select_related("user"),
        pk=membership_id,
        project=project,
    )

    if membership.user_id == project.owner_id:
        messages.error(request, "The project owner cannot be removed.")
        return redirect("project_members", project_id=project.id)

    removed_user = membership.user

    with transaction.atomic():
        # Don't leave tasks assigned to someone who no longer has access.
        Task.objects.filter(
            project=project,
            assignee=removed_user,
        ).update(assignee=None)
        membership.delete()

    messages.success(
        request,
        f"{removed_user.username} was removed from the project.",
    )

    if removed_user.pk == request.user.pk:
        # The user removed themselves; they can no longer open this project.
        return redirect("project_list")

    return redirect("project_members", project_id=project.id)