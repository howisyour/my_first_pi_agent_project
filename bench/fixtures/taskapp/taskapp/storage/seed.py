"""Demo data used by contract tests."""

from taskapp.constants import TASK_STATUSES
from taskapp.models_generated import Comment, Project, Task, User
from taskapp.storage.repository import get_repo

SEED_TASKS_PER_PROJECT = (30, 6)


def seed_demo_data(store) -> None:
    users = get_repo(store, "users")
    users.add(lambda i: User(id=i, username="ada", display_name="Ada"))
    users.add(lambda i: User(id=i, username="linus", display_name="Linus"))

    projects = get_repo(store, "projects")
    tasks = get_repo(store, "tasks")
    for owner_id, task_count in enumerate(SEED_TASKS_PER_PROJECT, start=1):
        project = projects.add(lambda i, o=owner_id: Project(id=i, name=f"Project {i}", owner_id=o))
        for n in range(task_count):
            status = TASK_STATUSES[n % len(TASK_STATUSES)]
            tasks.add(
                lambda i, p=project.id, n=n, s=status: Task(
                    id=i, project_id=p, title=f"Task {n + 1} of project {p}", status=s
                )
            )

    comments = get_repo(store, "comments")
    comments.add(lambda i: Comment(id=i, task_id=1, author_id=1, body="Looks good"))
