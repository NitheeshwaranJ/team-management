
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from projects.models import ProjectMembership
from tasks.forms import TaskForm
from projects.models import Project
from .models import Task
from datetime import date
User = get_user_model()


class TaskFeatureTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="projectowner",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="outsider",
            password="testpass123",
        )

        self.project = Project.objects.create(
            name="Interview Project",
            description="Testing Django features",
            owner=self.owner,
        )

    def test_owner_can_create_task(self):
        self.client.login(
            username="projectowner",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "task_create",
                kwargs={"project_id": self.project.id},
            ),
            {
                "title": "Write automated tests",
                "description": "Test task creation",
                "priority": Task.Priority.HIGH,
                "due_date": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "project_detail",
                kwargs={"project_id": self.project.id},
            ),
        )

        self.assertTrue(
            Task.objects.filter(
                project=self.project,
                title="Write automated tests",
            ).exists()
        )

    def test_user_without_access_cannot_create_task(self):
        self.client.login(
            username="outsider",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "task_create",
                kwargs={"project_id": self.project.id},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_update_task_status(self):
        task = Task.objects.create(
            project=self.project,
            title="Complete Django tests",
        )

        self.client.login(
            username="projectowner",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "task_update_status",
                kwargs={
                    "project_id": self.project.id,
                    "task_id": task.id,
                },
            ),
            {"status": Task.Status.DONE},
        )

        self.assertRedirects(
            response,
            reverse(
                "project_detail",
                kwargs={"project_id": self.project.id},
            ),
        )

        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)
class TaskRolePermissionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
        )
        self.manager = User.objects.create_user(
            username="manager",
            password="testpass123",
        )
        self.member = User.objects.create_user(
            username="member",
            password="testpass123",
        )
        self.outsider = User.objects.create_user(
            username="outsider",
            password="testpass123",
        )

        self.project = Project.objects.create(
            name="Test Project",
            description="Permission testing",
            owner=self.owner,
        )

        ProjectMembership.objects.create(
            project=self.project,
            user=self.manager,
            role=ProjectMembership.Role.MANAGER,
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

    def create_task(self):
        return Task.objects.create(
            project=self.project,
            title="Test Task",
            priority=Task.Priority.MEDIUM,
        )

    def test_owner_can_create_task(self):
        self.client.login(
            username="owner",
            password="testpass123",
        )

        response = self.client.post(
            reverse("task_create", args=[self.project.id]),
            {
                "title": "Owner Task",
                "description": "Created by owner",
                "priority": "MEDIUM",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Task.objects.filter(
                project=self.project,
                title="Owner Task",
            ).exists()
        )

    def test_manager_can_create_task(self):
        self.client.login(
            username="manager",
            password="testpass123",
        )

        response = self.client.post(
            reverse("task_create", args=[self.project.id]),
            {
                "title": "Manager Task",
                "description": "Created by manager",
                "priority": "HIGH",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Task.objects.filter(
                project=self.project,
                title="Manager Task",
            ).exists()
        )

    def test_member_cannot_create_task(self):
        self.client.login(
            username="member",
            password="testpass123",
        )

        response = self.client.post(
            reverse("task_create", args=[self.project.id]),
            {
                "title": "Unauthorized Task",
                "description": "",
                "priority": "MEDIUM",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Task.objects.filter(
                project=self.project,
                title="Unauthorized Task",
            ).exists()
        )

    def test_member_can_update_task_status(self):
        task = self.create_task()

        self.client.login(
            username="member",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "task_update_status",
                args=[self.project.id, task.id],
            ),
            {"status": "DONE"},
        )

        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)

    def test_non_member_cannot_update_task_status(self):
        task = self.create_task()

        self.client.login(
            username="outsider",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "task_update_status",
                args=[self.project.id, task.id],
            ),
            {"status": "DONE"},
        )

        self.assertEqual(response.status_code, 404)

        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)
    
    def test_assignee_choices_include_owner_and_members(self):
      form = TaskForm(project=self.project)

      assignee_ids = set(
        form.fields["assignee"].queryset.values_list(
            "id", flat=True
        )
    )

      self.assertIn(self.owner.id, assignee_ids)
      self.assertIn(self.manager.id, assignee_ids)
      self.assertIn(self.member.id, assignee_ids)
      self.assertNotIn(self.outsider.id, assignee_ids)


    def test_owner_can_assign_task_to_project_member(self):
      self.client.login(
        username="owner",
        password="testpass123",
    )

      response = self.client.post(
        reverse("task_create", args=[self.project.id]),
        {
            "title": "Assigned Task",
            "description": "Task assigned to a member",
            "priority": "HIGH",
            "assignee": self.member.id,
        },
    )

      self.assertEqual(response.status_code, 302)

      task = Task.objects.get(
        project=self.project,
        title="Assigned Task",
    )
      self.assertEqual(task.assignee_id, self.member.id)
    
    def test_owner_can_create_task_with_due_date(self):
      self.client.login(
        username="owner",
        password="testpass123",
    )

      response = self.client.post(
        reverse("task_create", args=[self.project.id]),
        {
            "title": "Deadline Task",
            "description": "Test due date saving",
            "priority": "HIGH",
            "due_date": "2026-11-15",
        },
    )

      self.assertEqual(response.status_code, 302)

      task = Task.objects.get(
        project=self.project,
        title="Deadline Task",
    )

      self.assertEqual(
        task.due_date,
        date(2026, 11, 15),
    )
    def test_task_is_overdue_when_due_date_is_past(self):
      task = Task.objects.create(
        project=self.project,
        title="Overdue Task",
        due_date=date(2020, 1, 1),
        status=Task.Status.TODO,
    )
      self.assertTrue(task.is_overdue)


    def test_completed_task_is_not_overdue(self):
      task = Task.objects.create(
        project=self.project,
        title="Completed Task",
        due_date=date(2020, 1, 1),
        status=Task.Status.DONE,
    )
      self.assertFalse(task.is_overdue)
