from fastapi import APIRouter, Depends, HTTPException
import sqlalchemy
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/{user_id}/chores")
def get_user_chores(user_id: int):
    """
    Get all chores assigned to a specific user.
    Returns the chore name and due date.
    """
    with db.engine.begin() as conn:
        results = conn.execute(
            sqlalchemy.text("""
                SELECT c.name AS chore_name, c.due_date
                FROM chores c
                JOIN assignments a ON c.id = a.chore_id
                WHERE a.user_id = :user_id
            """),
            {"user_id": user_id}
        ).mappings().all()

    if not results:
        return []  # Optionally, return a message like: {"message": "No chores assigned."}

    return list(results)
