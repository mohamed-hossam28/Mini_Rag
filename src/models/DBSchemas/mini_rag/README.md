## Run Alembic Migrations

### Configuration

For Intialization on current modules

```bash
alembic init alembic
```

- Update the `alembic.ini` with your database credentials (`sqlalchemy.url`)

### (Optional) Create a new migration

```bash
alembic revision --autogenerate -m "Add ..."
```

### Upgrade the database

```bash
alembic upgrade head
```
