from fastapi import Depends, HTTPException, Header
from fastapi.security import APIKeyHeader
import os
import sqlalchemy
from src import database as db

# Extract API key from request headers
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    """
    Validates the API key against the expected key in environment variables.
    Raises 403 if invalid or missing.
    """
    expected_key = os.getenv("API_KEY")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    return api_key


def get_current_user(x_user_id: str = Header(..., alias="X-User-Id")):
    """
    Retrieves user information based on user ID passed via header.
    Raises:
        400 - if user_id is not an integer
        404 - if no user is found
    Returns:
        dict - {id, username, email, group_id}
    """
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("""
                SELECT id, username, email, group_id
                FROM users
                WHERE id = :id
            """),
            {"id": user_id}
        ).mappings().fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(result)
