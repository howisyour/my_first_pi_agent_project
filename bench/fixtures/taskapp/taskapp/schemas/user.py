from taskapp.schemas.base import Schema


class UserOut(Schema):
    fields = ("id", "username", "display_name")
