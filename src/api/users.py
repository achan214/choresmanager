from fastapi import APIRouter, Depends, HTTPException
import sqlalchemy
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth.get_api_key)],
)

# create a user
@router.post("/", status_code=201)
def create_user(username: str, email: str):
    """
    Create a new user with the given username.
    """
    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    with db.engine.begin() as conn:
        # id, username, email, is_admin
        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO users (username, email, is_admin)
                VALUES (:username, :email, false)
                RETURNING id
            """),
            {"username": username, "email": email}
        ).mappings().fetchone()

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create user.")

    return {"user_id": result["id"], "message": "User created successfully."}

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
