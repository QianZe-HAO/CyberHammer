# config.py
import os
from urllib.parse import quote_plus

# -----------------------------------------------------
# PostgreSQL Configuration
POSTGRESQL_DB_USER = os.getenv("POSTGRESQL_DB_USER")
POSTGRESQL_DB_PASSWORD = os.getenv("POSTGRESQL_DB_PASSWORD")
POSTGRESQL_DB_HOST = os.getenv("POSTGRESQL_DB_HOST")
POSTGRESQL_DB_PORT = os.getenv("POSTGRESQL_DB_PORT", "5432")
POSTGRESQL_DB_NAME = os.getenv("POSTGRESQL_DB_NAME")

# Validate required fields
if not all(
    [
        POSTGRESQL_DB_USER,
        POSTGRESQL_DB_PASSWORD,
        POSTGRESQL_DB_HOST,
        POSTGRESQL_DB_PORT,
        POSTGRESQL_DB_NAME,
    ]
):
    raise EnvironmentError(
        "Missing one or more required environment variables for PostgreSQL: "
        "DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME"
    )

# URL-encode password for safe use in connection string
pg_password_encoded = quote_plus(POSTGRESQL_DB_PASSWORD)
POSTGRESQL_DATABASE_URL = (
    f"postgresql://{POSTGRESQL_DB_USER}:{pg_password_encoded}@"
    f"{POSTGRESQL_DB_HOST}:{POSTGRESQL_DB_PORT}/{POSTGRESQL_DB_NAME}"
)
