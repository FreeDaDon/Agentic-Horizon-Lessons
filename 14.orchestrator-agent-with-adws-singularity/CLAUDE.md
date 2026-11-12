# Engineering rules for our Multi-Agent Orchestration System

## Do not mock tests

- Use real database connections
- Use real Claude Agent SDK agents
- IMPORTANT: The trick with database connection is to make sure your tests are ephemeral, it should start and end the database in the exact same state. Create the test data you need for the test, then clean it up after the test.

## Keep models.py in sync with the migrations

Be sure we keep our apps/orchestrator_db/models.py in sync with the migrations in apps/orchestrator_db/migrations/*.py.

If we request a change to a migration file be absolutely sure to update the models.py file to reflect the changes.

## Use .env file when needed and expose with python-dotenv

- Use python-dotenv to load environment variables from .env file
- Copy the root level .env into the respective apps/*/.env if you need it locally

## IMPORTANT: Actually read the file

- IMPORTANT: When asked to read a file, read all of it - don't just read the first N lines.
- Read the file in chunks. If that's too large, cut in half and try again, then iterate to the next chunk.
- This is VERY IMPORTANT for understanding the codebase.
- Even if the file is large, read all of it in chunks.
- IMPORTANT: Use `wc -l <filename>` to get line counts if needed. So you can properly divide your Read tool in the right chunks.

## Use Astral UV, never raw python

- We're using Astral UV to manage our python projects.
- Always use uv to run commands, never raw python.

## Python rich panels

- Always full width panels with rich.

## Git Commits

- IMPORTANT: Do NOT commit any changes to the git repository unless you are explicitly asked to do so.

## Avoid dict and prefer pydantic models

- Prefer pydantic models over dicts.
- For every database model use the backend's `modules/orch_database_models.py` to parse and manage the data. It is a copy of `apps/orchestrator_db/models.py`: when you change `models.py`, copy it over (`cp apps/orchestrator_db/models.py apps/orchestrator_3_stream/backend/modules/orch_database_models.py`).