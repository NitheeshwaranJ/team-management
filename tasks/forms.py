
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Task
from projects.models import ProjectMembership

User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "priority",
            "assignee",
            "due_date",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Enter task title"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show members of this project in the assignee dropdown.
        if project is not None:
          member_ids = ProjectMembership.objects.filter(project=project).values_list("user_id", flat=True)

          self.fields["assignee"].queryset = (User.objects.filter(
            Q(pk__in=member_ids) | Q(pk=project.owner_id)
        )
        .distinct()
        .order_by("username")
    )
