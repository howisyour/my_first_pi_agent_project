from taskapp.schemas.base import Schema


class TaskOut(Schema):
    fields = ("id", "project_id", "title", "status", "priority", "assignee_id")
