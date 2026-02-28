# checkpointers.py
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver
from psycopg import Connection
from typing import Union

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