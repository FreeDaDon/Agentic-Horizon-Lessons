"""
psql invocation helper for the orchestrator_db scripts.

The password is moved out of the connection URL into PGPASSWORD so it never
appears in the process list, and ON_ERROR_STOP makes psql exit non-zero on the
first failing statement instead of reporting success.
"""

import os
from typing import Dict, List, Tuple
from urllib.parse import unquote, urlsplit, urlunsplit


def psql_invocation(database_url: str, *args: str) -> Tuple[List[str], Dict[str, str]]:
    """Return (argv, env) for running psql against database_url with extra args."""
    parts = urlsplit(database_url)
    env = dict(os.environ)
    if parts.password is not None:
        env["PGPASSWORD"] = unquote(parts.password)
        host = parts.netloc.rsplit("@", 1)[1]
        user = parts.username or ""
        netloc = f"{user}@{host}" if user else host
        database_url = urlunsplit(parts._replace(netloc=netloc))
    return ["psql", "-v", "ON_ERROR_STOP=1", database_url, *args], env
