# Testing

There are two suites:

- `tests/unit/` – pure functions. `python -m pytest` runs only this suite.
- `tests/contract/` – API behaviour through `taskapp.app.Client`. These tests need the fixtures in
  `taskapp_testing/plugin.py`, which is not auto-loaded.

## Quality gate

CI runs:

```
python scripts/check.py
```

It runs ruff, both test suites (with the plugin enabled), the generated-code checksum, a scan for
bare built-in exceptions and inline numbers in routes/services, and a registry consistency check.
A change is done only when this command exits 0.
