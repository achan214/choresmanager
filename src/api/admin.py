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

@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_database(user=Depends(require_admin)):
    """
    Admin-only. Resets the database by truncating all key tables.
    Removes all data but keeps the schema intact.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE assignments, chores, users, groups RESTART IDENTITY CASCADE"
        ))

@router.delete("/remove_user/{user_id}", status_code=200)
def remove_user(user_id: int, user=Depends(require_admin)):
    """
    Admin-only. Permanently deletes a user and related assignments.
    """
    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("DELETE FROM users WHERE id = :user_id RETURNING id"),
            {"user_id": user_id}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} deleted."}
