from taskapp.schemas.base import Schema


class ProjectOut(Schema):
    fields = ("id", "name", "owner_id", "archived")
