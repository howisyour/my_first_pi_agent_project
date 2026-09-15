from taskapp.schemas.base import Schema


class CommentOut(Schema):
    fields = ("id", "task_id", "author_id", "body")
