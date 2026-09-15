---
name: taskapp-migration
description: Required procedure for any change to taskapp data models (adding or changing a field on User, Project, Task or Comment) - schema version bump, model regeneration, numbered migration file, INDEX entry and API schema. Use whenever a task changes a taskapp model or asks for a data migration.
---

# taskapp model change and migration

Do every step, in order.

1. **schema/models.json** – add the field with a `"default"` and increase the top-level `"version"` by 1.
2. **Regenerate** – run `python scripts/gen_models.py`. It rewrites `taskapp/models_generated.py` and
   `schema/models.lock`. Never edit the generated file by hand.
3. **Migration file** – create `migrations/NNNN_<slug>.py`, where `NNNN` is the new version padded to 4 digits:

   ```python
   """Add Task.<field> (schema version N)."""

   VERSION = N
   TABLE = "tasks"
   FIELD = "<field>"


   def up(store) -> None:
       for record in store.table(TABLE).values():
           if FIELD not in vars(record):
               setattr(record, FIELD, <default>)


   def down(store) -> None:
       for record in store.table(TABLE).values():
           if FIELD in vars(record):
               delattr(record, FIELD)
   ```

   Table names: `users`, `projects`, `tasks`, `comments`.
4. **INDEX** – append the migration name (file name without `.py`) as the new last line of `migrations/INDEX`.
5. **API schema** – if the API returns the model, add the field to `fields` in `taskapp/schemas/<model>.py`.
6. **Verify** – `python scripts/check.py` must exit 0.
