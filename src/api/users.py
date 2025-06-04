from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Union
import sqlalchemy
from pydantic import BaseModel
from src import database as db
from src.api import auth
from datetime import datetime

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth.get_api_key)],
)

class CreateUserResponse(BaseModel):
    user_id: int
    message: str

class ChoreInfo(BaseModel):
    chore_name: str
    due_date: Optional[datetime]
    completed: bool

class NoChoresResponse(BaseModel):
    message: str

@router.post("/", response_model=CreateUserResponse, status_code=201)
def create_user(username: str, email: str):
    """
    Create a new user if the email is not already taken.

    Returns:
        user_id: int - ID of the created user
        message: str - Success confirmation
    Raises:
        400 - if username or email is missing
        409 - if email is already in use
    """
    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email are required.")

    with db.engine.begin() as connection:
        existing_user = connection.execute(
            sqlalchemy.text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        ).first()

        if existing_user:
            raise HTTPException(status_code=409, detail="Email already in use.")

        result = connection.execute(
            sqlalchemy.text("""
                INSERT INTO users (username, email, is_admin)
                VALUES (:username, :email, false)
                RETURNING id
            """),
            {"username": username, "email": email}
        ).mappings().fetchone()

    return CreateUserResponse(user_id=result["id"], message="User created successfully.")

@router.get("/{user_id}/chores", response_model=Union[List[ChoreInfo], NoChoresResponse])
def get_user_chores(
    username: str,
    completed: Optional[bool] = Query(None)
):
    """
    Get all chores assigned to a specific user.
    Returns the chore name and due date.

    Supports filtering by:
        - completion status (`completed`)
    """
    with db.engine.begin() as connection:
        user_id = connection.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        ).scalar()
        user_exists = connection.execute(
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

        chores = connection.execute(sqlalchemy.text(query), params).mappings().all()

    if chores:
        return [ChoreInfo(**row) for row in chores]
    return NoChoresResponse(message="No chores assigned.")
