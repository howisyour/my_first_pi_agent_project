# Data migrations

Every model change ships as a numbered migration. Follow all steps.

1. Edit `schema/models.json`: add or change the field and increase the top-level `version` by one.
   A new field must have a `default` so existing records stay valid.
2. Regenerate the models: `python scripts/gen_models.py`. Never edit `taskapp/models_generated.py` by hand.
3. Create `migrations/NNNN_<slug>.py`, where `NNNN` is the new schema version padded to four digits
   and `<slug>` is a short snake_case description. The module defines:
   - `VERSION = <new schema version>`
   - `up(store)`: backfill the field with its default on every existing record of the affected table
     (records that do not have the attribute yet).
   - `down(store)`: remove the attribute from those records.
4. Append the migration name (file name without `.py`) as the new last line of `migrations/INDEX`.
5. If the field is visible in the API, add it to the matching schema's `fields` in `taskapp/schemas/`.
6. Run `python scripts/check.py`.

`migrations/0002_add_task_priority.py` is a complete example. Table names are `users`, `projects`,
`tasks` and `comments`.
