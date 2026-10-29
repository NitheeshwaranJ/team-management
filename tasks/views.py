
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from projects.models import Project
from .forms import TaskForm
from .models import Task
from projects.models import Project
from projects.permissions import (
    can_manage_project,
    can_view_project,
)
from django.http import Http404
@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if not can_view_project(request.user, project):
        from django.http import Http404
        raise Http404("Project not found.")

    if not can_manage_project(request.user, project):
        raise PermissionDenied(
            "Only the project owner or a Manager can create tasks."
        )

    if request.method == "POST":
        form = TaskForm(request.POST, project=project)

        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()

            return redirect(
                "project_detail",
                project_id=project.id,
            )
    else:
        form = TaskForm(project=project)

    return render(
        request,
        "tasks/task_form.html",
        {"form": form, "project": project},
    )


@login_required
@require_POST
def task_update_status(request, project_id, task_id):
    project = get_object_or_404(Project, pk=project_id)

    if not can_view_project(request.user, project):
        from django.http import Http404
        raise Http404("Project not found.")

    task = get_object_or_404(
        Task,
        pk=task_id,
        project=project,
    )

    new_status = request.POST.get("status")

    if new_status in Task.Status.values:
        task.status = new_status
        task.save(update_fields=["status"])

    return redirect(
        "project_detail",
        project_id=project.id,
    )
