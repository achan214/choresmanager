from src import config, database as db
from fastapi import Security, HTTPException, status, Header, Depends
from fastapi.security.api_key import APIKeyHeader
import sqlalchemy

# get api key from .env
api_key = config.get_settings().API_KEY
api_key_header = APIKeyHeader(name="access_token", auto_error=False)

# check the api key from headers
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == api_key:
        return api_key_header
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")

# get the current user from x-user-id header
def get_current_user(x_user_id: str = Header(..., alias="X-User-Id")):
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid user ID")

    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("SELECT id, username, email FROM users WHERE id = :id"),
            {"id": user_id}
        ).mappings().fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="user not found")

        return dict(result)
