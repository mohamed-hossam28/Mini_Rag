## Run Alembic Migrations

For Alembic to work properly, you need to have a `schemas` (or `models`) folder that contains all of your database table schemas.

First, navigate to your database directory:

```bash
cd src/models/DBSchemas/mini_rag
```

### Initialization

If you are setting up Alembic for the first time in your current module, initialize the environment:

```bash
alembic init alembic
```

### Configuration

- Open the `alembic.ini` file.
- Update the `sqlalchemy.url` line with your actual database credentials.
  _(Example: `sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/minirag`)_

### Create a New Migration

Whenever you create or modify your table schemas, generate a new migration script. Replace `"Add ..."` with a brief description of what changed:

```bash
alembic revision --autogenerate -m "Add ..."
```

### Upgrade the Database

To apply the pending migrations and update your actual database schema, run:

```bash
alembic upgrade head
```
