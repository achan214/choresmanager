from fastapi import APIRouter, Depends, HTTPException, status
import sqlalchemy
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

def require_admin(user=Depends(auth.get_current_user)):
    """
    Checks if the current user is an admin. Raises 403 if not.
    """
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return user

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_database(user=Depends(require_admin)):
    """
    Admin-only. Resets the database by truncating all key tables.
    Removes all data but keeps the schema intact.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE assignments, chores, users, groups RESTART IDENTITY CASCADE"
        ))

    return {"message": "Database reset successfully."}

@router.delete("/remove_user/{user_id}", status_code=200)
def remove_user(username: str, user=Depends(require_admin)):
    """
    Admin-only. Permanently deletes a user and related assignments.
    """
    with db.engine.begin() as conn:
        # Delete assignments for this user first
        conn.execute(
            sqlalchemy.text("DELETE FROM assignments WHERE user_id = (SELECT id FROM users WHERE username = :username)"),
            {"username": username}
        )
        # Now delete the user
        result = conn.execute(
            sqlalchemy.text("DELETE FROM users WHERE username = :username RETURNING username"),
            {"username": username}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {username} deleted."}
