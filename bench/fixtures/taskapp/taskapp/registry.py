"""Route registry. A route is reachable only if it is listed in ROUTE_REGISTRY."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    handler: str
    schema: str


ROUTE_REGISTRY: list[Route] = [
    Route("GET", "/health", "taskapp.routes.health:health", "HealthOut"),
    Route("GET", "/projects", "taskapp.routes.projects:list_projects", "ProjectOut"),
    Route("POST", "/projects", "taskapp.routes.projects:create_project", "ProjectOut"),
    Route("GET", "/projects/{project_id}", "taskapp.routes.projects:get_project", "ProjectOut"),
    Route("POST", "/projects/{project_id}/archive", "taskapp.routes.projects:archive_project", "ProjectOut"),
    Route("GET", "/projects/{project_id}/tasks", "taskapp.routes.tasks:list_tasks", "TaskOut"),
    Route("POST", "/projects/{project_id}/tasks", "taskapp.routes.tasks:create_task", "TaskOut"),
    Route("GET", "/tasks/search", "taskapp.routes.tasks:search_tasks", "TaskOut"),
    Route("PATCH", "/tasks/{task_id}", "taskapp.routes.tasks:update_task", "TaskOut"),
    Route("GET", "/tasks/{task_id}/comments", "taskapp.routes.comments:list_comments", "CommentOut"),
    Route("POST", "/tasks/{task_id}/comments", "taskapp.routes.comments:add_comment", "CommentOut"),
    Route("GET", "/users", "taskapp.routes.users:list_users", "UserOut"),
    Route("GET", "/users/{user_id}", "taskapp.routes.users:get_user", "UserOut"),
]
