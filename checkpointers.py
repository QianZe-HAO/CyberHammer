# checkpointers.py
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver
from psycopg import Connection, AsyncConnection
from typing import Union
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


# Import from config instead of main
from config import POSTGRESQL_DATABASE_URL

Checkpointer = Union[InMemorySaver, PostgresSaver]


def get_checkpointer(use_postgres: bool = True) -> Checkpointer:
    """
    Returns a configured checkpointer instance.

    Args:
        use_postgres: If True, returns PostgresSaver; otherwise, returns InMemorySaver.

    Returns:
        Configured checkpointer.
    """
    if not use_postgres:
        return InMemorySaver()

    conn = Connection.connect(conninfo=POSTGRESQL_DATABASE_URL, autocommit=True)
    checkpointer = PostgresSaver(conn=conn)
    checkpointer.setup()  # Creates required tables if they don't exist
    return checkpointer


async def get_async_checkpointer(use_postgres: bool = True):
    if not use_postgres:
        return InMemorySaver()
    # conn = Connection.connect(conninfo=POSTGRESQL_DATABASE_URL, autocommit=True)
    conn = await AsyncConnection.connect(conninfo=POSTGRESQL_DATABASE_URL, autocommit=True)
    checkpointer = AsyncPostgresSaver(conn=conn)
    await checkpointer.setup()
    return checkpointer
