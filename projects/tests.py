from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task

from .models import Project, ProjectMembership

User = get_user_model()
PASSWORD = "testpass123"


class MemberManagementTestCase(TestCase):
    """Shared fixtures: an owner, a manager, a member, and an outsider."""

    def setUp(self):
        self.owner = User.objects.create_user("owner", password=PASSWORD)
        self.manager = User.objects.create_user("manager", password=PASSWORD)
        self.member = User.objects.create_user("member", password=PASSWORD)
        self.outsider = User.objects.create_user("outsider", password=PASSWORD)
        self.newcomer = User.objects.create_user("newcomer", password=PASSWORD)

        self.project = Project.objects.create(name="Alpha", owner=self.owner)
        ProjectMembership.objects.create(
            project=self.project,
            user=self.owner,
            role=ProjectMembership.Role.MANAGER,
        )
        self.manager_membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.manager,
            role=ProjectMembership.Role.MANAGER,
        )
        self.member_membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.member,
            role=ProjectMembership.Role.MEMBER,
        )

        self.members_url = reverse(
            "project_members", kwargs={"project_id": self.project.id}
        )

    def login(self, user):
        self.client.login(username=user.username, password=PASSWORD)

    def update_role_url(self, membership):
        return reverse(
            "member_update_role",
            kwargs={
                "project_id": membership.project_id,
                "membership_id": membership.id,
            },
        )

    def remove_url(self, membership):
        return reverse(
            "member_remove",
            kwargs={
                "project_id": membership.project_id,
                "membership_id": membership.id,
            },
        )


class MemberListTests(MemberManagementTestCase):
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.members_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_outsider_gets_404(self):
        self.login(self.outsider)
        self.assertEqual(self.client.get(self.members_url).status_code, 404)

    def test_member_can_view_list_but_not_the_add_form(self):
        self.login(self.member)
        response = self.client.get(self.members_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "manager")
        self.assertNotContains(response, "Add a member")

    def test_manager_sees_the_add_form(self):
        self.login(self.manager)
        response = self.client.get(self.members_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add a member")


class AddMemberTests(MemberManagementTestCase):
    def test_manager_can_add_member(self):
        self.login(self.manager)
        response = self.client.post(
            self.members_url,
            {"username": "newcomer", "role": ProjectMembership.Role.MEMBER},
        )

        self.assertRedirects(response, self.members_url)
        self.assertTrue(
            ProjectMembership.objects.filter(
                project=self.project,
                user=self.newcomer,
                role=ProjectMembership.Role.MEMBER,
            ).exists()
        )

    def test_owner_can_add_manager(self):
        self.login(self.owner)
        self.client.post(
            self.members_url,
            {"username": "newcomer", "role": ProjectMembership.Role.MANAGER},
        )

        membership = ProjectMembership.objects.get(
            project=self.project, user=self.newcomer
        )
        self.assertEqual(membership.role, ProjectMembership.Role.MANAGER)

    def test_regular_member_cannot_add_member(self):
        self.login(self.member)
        response = self.client.post(
            self.members_url,
            {"username": "newcomer", "role": ProjectMembership.Role.MEMBER},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            ProjectMembership.objects.filter(
                project=self.project, user=self.newcomer
            ).exists()
        )

    def test_outsider_cannot_add_member(self):
        self.login(self.outsider)
        response = self.client.post(
            self.members_url,
            {"username": "newcomer", "role": ProjectMembership.Role.MEMBER},
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_username_is_rejected(self):
        self.login(self.manager)
        response = self.client.post(
            self.members_url,
            {"username": "ghost", "role": ProjectMembership.Role.MEMBER},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No user with that username exists.")
        self.assertEqual(self.project.memberships.count(), 3)

    def test_duplicate_member_is_rejected(self):
        self.login(self.manager)
        response = self.client.post(
            self.members_url,
            {"username": "member", "role": ProjectMembership.Role.MEMBER},
        )

        self.assertContains(response, "already part of the project")
        self.assertEqual(self.project.memberships.count(), 3)

    def test_owner_cannot_be_added_again(self):
        self.login(self.manager)
        response = self.client.post(
            self.members_url,
            {"username": "owner", "role": ProjectMembership.Role.MEMBER},
        )
        self.assertContains(response, "already part of the project")

    def test_invalid_role_is_rejected(self):
        self.login(self.manager)
        response = self.client.post(
            self.members_url,
            {"username": "newcomer", "role": "SUPERUSER"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            ProjectMembership.objects.filter(
                project=self.project, user=self.newcomer
            ).exists()
        )

    def test_inactive_user_cannot_be_added(self):
        self.newcomer.is_active = False
        self.newcomer.save()

        self.login(self.manager)
        response = self.client.post(
            self.members_url,
            {"username": "newcomer", "role": ProjectMembership.Role.MEMBER},
        )
        self.assertContains(response, "No user with that username exists.")


class UpdateRoleTests(MemberManagementTestCase):
    def test_manager_can_promote_member(self):
        self.login(self.manager)
        response = self.client.post(
            self.update_role_url(self.member_membership),
            {"role": ProjectMembership.Role.MANAGER},
        )

        self.assertRedirects(response, self.members_url)
        self.member_membership.refresh_from_db()
        self.assertEqual(
            self.member_membership.role, ProjectMembership.Role.MANAGER
        )

    def test_invalid_role_is_ignored(self):
        self.login(self.manager)
        self.client.post(
            self.update_role_url(self.member_membership),
            {"role": "SUPERUSER"},
        )

        self.member_membership.refresh_from_db()
        self.assertEqual(
            self.member_membership.role, ProjectMembership.Role.MEMBER
        )

    def test_owner_role_cannot_be_changed(self):
        owner_membership = ProjectMembership.objects.get(
            project=self.project, user=self.owner
        )
        self.login(self.manager)
        self.client.post(
            self.update_role_url(owner_membership),
            {"role": ProjectMembership.Role.MEMBER},
        )

        owner_membership.refresh_from_db()
        self.assertEqual(owner_membership.role, ProjectMembership.Role.MANAGER)

    def test_regular_member_cannot_change_roles(self):
        self.login(self.member)
        response = self.client.post(
            self.update_role_url(self.member_membership),
            {"role": ProjectMembership.Role.MANAGER},
        )

        self.assertEqual(response.status_code, 403)
        self.member_membership.refresh_from_db()
        self.assertEqual(
            self.member_membership.role, ProjectMembership.Role.MEMBER
        )

    def test_get_is_not_allowed(self):
        self.login(self.manager)
        response = self.client.get(self.update_role_url(self.member_membership))
        self.assertEqual(response.status_code, 405)

    def test_cannot_edit_membership_of_another_project(self):
        other_owner = User.objects.create_user("other", password=PASSWORD)
        other_project = Project.objects.create(name="Beta", owner=other_owner)
        other_membership = ProjectMembership.objects.create(
            project=other_project,
            user=self.newcomer,
            role=ProjectMembership.Role.MEMBER,
        )

        self.login(self.manager)
        # Manager of Alpha tries to edit a membership that belongs to Beta,
        # but through Alpha's URL.
        url = reverse(
            "member_update_role",
            kwargs={
                "project_id": self.project.id,
                "membership_id": other_membership.id,
            },
        )
        response = self.client.post(
            url, {"role": ProjectMembership.Role.MANAGER}
        )

        self.assertEqual(response.status_code, 404)
        other_membership.refresh_from_db()
        self.assertEqual(other_membership.role, ProjectMembership.Role.MEMBER)


class RemoveMemberTests(MemberManagementTestCase):
    def test_manager_can_remove_member(self):
        self.login(self.manager)
        response = self.client.post(self.remove_url(self.member_membership))

        self.assertRedirects(response, self.members_url)
        self.assertFalse(
            ProjectMembership.objects.filter(
                pk=self.member_membership.pk
            ).exists()
        )

    def test_removed_member_tasks_become_unassigned(self):
        task = Task.objects.create(
            project=self.project,
            title="Write docs",
            assignee=self.member,
        )

        self.login(self.manager)
        self.client.post(self.remove_url(self.member_membership))

        task.refresh_from_db()
        self.assertIsNone(task.assignee)

    def test_removal_only_unassigns_tasks_in_this_project(self):
        other_project = Project.objects.create(name="Beta", owner=self.member)
        other_task = Task.objects.create(
            project=other_project,
            title="Unrelated",
            assignee=self.member,
        )

        self.login(self.manager)
        self.client.post(self.remove_url(self.member_membership))

        other_task.refresh_from_db()
        self.assertEqual(other_task.assignee, self.member)

    def test_owner_cannot_be_removed(self):
        owner_membership = ProjectMembership.objects.get(
            project=self.project, user=self.owner
        )
        self.login(self.manager)
        self.client.post(self.remove_url(owner_membership))

        self.assertTrue(
            ProjectMembership.objects.filter(pk=owner_membership.pk).exists()
        )

    def test_regular_member_cannot_remove_anyone(self):
        self.login(self.member)
        response = self.client.post(self.remove_url(self.manager_membership))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            ProjectMembership.objects.filter(
                pk=self.manager_membership.pk
            ).exists()
        )

    def test_outsider_gets_404(self):
        self.login(self.outsider)
        response = self.client.post(self.remove_url(self.member_membership))
        self.assertEqual(response.status_code, 404)

    def test_get_is_not_allowed(self):
        self.login(self.manager)
        response = self.client.get(self.remove_url(self.member_membership))
        self.assertEqual(response.status_code, 405)

    def test_manager_removing_themselves_loses_access(self):
        self.login(self.manager)
        response = self.client.post(self.remove_url(self.manager_membership))

        self.assertRedirects(response, reverse("project_list"))
        detail = self.client.get(
            reverse("project_detail", kwargs={"project_id": self.project.id})
        )
        self.assertEqual(detail.status_code, 404)


class ProjectDetailLinksTests(MemberManagementTestCase):
    def detail(self):
        return self.client.get(
            reverse("project_detail", kwargs={"project_id": self.project.id})
        )

    def test_manager_sees_create_task_and_members_links(self):
        self.login(self.manager)
        response = self.detail()

        self.assertContains(response, "+ Create Task")
        self.assertContains(response, self.members_url)

    def test_regular_member_sees_members_link_but_not_create_task(self):
        self.login(self.member)
        response = self.detail()

        self.assertNotContains(response, "+ Create Task")
        self.assertContains(response, self.members_url)