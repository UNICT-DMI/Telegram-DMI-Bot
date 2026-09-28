# Telegram-DMI-Bot

Telegram bot [@DMI_Bot](https://t.me/DMI_Bot) giving UNICT DMI students info on professors, lessons, exams and offices. Python with python-telegram-bot 13 (sync API), plus a FastAPI + Parcel webapp in `webapp/`. Code must run on Python 3.9 (CI tests 3.9 and 3.10).

## Commands

Setup: `pip install -r requirements.txt -r requirements_dev.txt`, then copy `config/settings.yaml.dist` to `config/settings.yaml` and `data/DMI_DB.db.dist` to `data/DMI_DB.db`.

- Run: `python3 main.py` (needs a bot token in `config/settings.yaml`)
- Unit tests: `pytest tests/unit/`
- Lint (CI, must pass):
  - `pylint`, `mypy`, `black --check`, `isort --check-only`, each on `$(git ls-files '*.py')`
  - `flake8 . --select=E9,F63,F7,F82`

## Structure

- Commands live in `module/commands/<name>.py`; every handler is registered in `add_handlers()` in `main.py`.
- Callback queries are routed by `callback_data` prefix (`CallbackQueryHandler` patterns in `main.py`). `sm_<func>` calls `<func>` via `globals()` in `module/callback_handlers.py`, so `<func>` must be imported there.
- User-facing texts: `data/translations/{it,en}.yaml`, keyed by `TEXT_IDS` (`module/data/vars.py`); add each new text to both files, `it` is the fallback.
- `tests/e2e/` needs a real Telegram account (see README); CI runs only `tests/unit/`.

## Docs

- [README.md](README.md): read when setting up a local instance, Docker, Google Drive, or e2e tests.
- [CONTRIBUTING.md](CONTRIBUTING.md): read before committing or opening a PR (conventional commits).
- [.agents/docs/agents-setup.md](.agents/docs/agents-setup.md): read when wiring up an agent, or adding an agent doc or skill.

## Plans

Save planning docs (plans, requirements, investigations) in `.agents/plans/<task-slug>/`; the dir is gitignored.
