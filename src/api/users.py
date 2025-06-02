from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import sqlalchemy
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth.get_api_key)],
)

# create a new user and check for duplicate email
@router.post("/", status_code=201)
def create_user(username: str, email: str):
    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email are required.")

    with db.engine.begin() as conn:
        duplicate = conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        ).first()

        if duplicate:
            raise HTTPException(status_code=409, detail="Email already in use.")

        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO users (username, email, is_admin)
                VALUES (:username, :email, false)
                RETURNING id
            """),
            {"username": username, "email": email}
        ).mappings().fetchone()

    return {"user_id": result["id"], "message": "User created successfully."}


# get all chores assigned to a user if the user exists, with optional completion filter
@router.get("/{user_id}/chores")
def get_user_chores(
    user_id: int,
    completed: Optional[bool] = Query(None),
    sort_by_due: Optional[str] = Query(None, regex="^(asc|desc)?$")
):
    with db.engine.begin() as conn:
        user_exists = conn.execute(
            sqlalchemy.text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).first()

        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found.")

        query = """
            SELECT c.name AS chore_name, c.due_date, c.completed
            FROM chores c
            JOIN assignments a ON c.id = a.chore_id
            WHERE a.user_id = :user_id
        """
        params = {"user_id": user_id}

        if completed is not None:
            query += " AND c.completed = :completed"
            params["completed"] = completed

        if sort_by_due:
            query += f" ORDER BY c.due_date {sort_by_due.upper()}"

        results = conn.execute(sqlalchemy.text(query), params).mappings().all()

    return list(results) if results else {"message": "No chores assigned."}
