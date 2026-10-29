
from django.urls import path
from . import views

urlpatterns = [
    path(
        "projects/<int:project_id>/tasks/create/",
        views.task_create,
        name="task_create",
    ),
    path(
    "projects/<int:project_id>/tasks/<int:task_id>/status/",
    views.task_update_status,
    name="task_update_status",
),
]
