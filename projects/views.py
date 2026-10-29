from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProjectForm
from .models import Project, ProjectMembership
from tasks.models import Task
from .forms import ProjectForm
from .models import Project, ProjectMembership


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
        },
    )
