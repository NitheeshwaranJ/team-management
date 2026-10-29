from django import forms
from django.contrib.auth import get_user_model

from .models import Project, ProjectMembership

User = get_user_model()


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]


class AddMemberForm(forms.Form):
    """Add an existing user to a project by username."""

    username = forms.CharField(max_length=150)
    role = forms.ChoiceField(
        choices=ProjectMembership.Role.choices,
        initial=ProjectMembership.Role.MEMBER,
    )

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user_to_add = None

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            raise forms.ValidationError("No user with that username exists.")

        already_in_project = (
            user.pk == self.project.owner_id
            or ProjectMembership.objects.filter(
                project=self.project,
                user=user,
            ).exists()
        )
        if already_in_project:
            raise forms.ValidationError(
                "This user is already part of the project."
            )

        self.user_to_add = user
        return username