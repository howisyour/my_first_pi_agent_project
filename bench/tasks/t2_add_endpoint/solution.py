from bench.runner.edits import append_text, replace_once


def apply(workdir):
    replace_once(
        workdir / "taskapp/services/projects.py",
        "from taskapp.errors import NotFoundError\n",
        "from taskapp.constants import TASK_STATUSES\nfrom taskapp.errors import NotFoundError\n",
    )
    append_text(
        workdir / "taskapp/services/projects.py",
        "\n\ndef project_stats(store, project_id: int) -> dict:\n"
        "    get_project_or_404(store, project_id)\n"
        "    tasks = [task for task in get_repo(store, \"tasks\").all() if task.project_id == project_id]\n"
        "    by_status = {status: 0 for status in TASK_STATUSES}\n"
        "    for task in tasks:\n"
        "        by_status[task.status] += 1\n"
        "    return {\"project_id\": project_id, \"total\": len(tasks), \"by_status\": by_status}\n",
    )
    append_text(
        workdir / "taskapp/routes/projects.py",
        "\n\ndef project_stats(store, request, project_id):\n"
        "    return HTTP_OK, project_service.project_stats(store, parse_id(project_id, field=\"project_id\"))\n",
    )
    append_text(
        workdir / "taskapp/schemas/project.py",
        "\n\nclass ProjectStatsOut(Schema):\n    fields = (\"project_id\", \"total\", \"by_status\")\n",
    )
    replace_once(
        workdir / "taskapp/schemas/__init__.py",
        "from taskapp.schemas.project import ProjectOut\n",
        "from taskapp.schemas.project import ProjectOut, ProjectStatsOut\n",
    )
    replace_once(workdir / "taskapp/schemas/__init__.py", '"ProjectOut", ', '"ProjectOut", "ProjectStatsOut", ')
    replace_once(
        workdir / "taskapp/registry.py",
        '    Route("GET", "/projects/{project_id}/tasks",',
        '    Route("GET", "/projects/{project_id}/stats", "taskapp.routes.projects:project_stats", "ProjectStatsOut"),\n'
        '    Route("GET", "/projects/{project_id}/tasks",',
    )
