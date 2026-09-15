from taskapp.schemas.base import Schema


class HealthOut(Schema):
    fields = ("status", "version")
