from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sqlalchemy
from datetime import datetime
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
    dependencies=[Depends(auth.get_api_key)],
)

class AssignmentCreate(BaseModel):
    chore_id: int
    user_id: int

class AssignmentResponse(BaseModel):
    message: str
    assignment_id: int

class CompleteAssignmentResponse(BaseModel):
    message: str
    completed_at: str

@router.post("/", response_model=AssignmentResponse)
def create_assignment(
    assignment: AssignmentCreate,
    api_key: str = Depends(auth.get_api_key)
):
    """
    Create a new assignment by linking a user to a chore.
    """
    with db.engine.begin() as conn:
        # Ensure chore exists
        chore_exists = conn.execute(
            sqlalchemy.text("SELECT 1 FROM chores WHERE id = :id"),
            {"id": assignment.chore_id}
        ).first()
        if not chore_exists:
            raise HTTPException(status_code=404, detail="Chore not found.")

        # Ensure user exists
        user_exists = conn.execute(
            sqlalchemy.text("SELECT 1 FROM users WHERE id = :id"),
            {"id": assignment.user_id}
        ).first()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found.")

        # Create assignment with assigned_at
        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore_id, :user_id, NOW())
                RETURNING id
            """),
            {"chore_id": assignment.chore_id, "user_id": assignment.user_id}
        ).mappings().fetchone()

    return AssignmentResponse(
        message="Assignment created successfully.",
        assignment_id=result["id"]
    )

@router.patch("/{assignment_id}/complete", response_model=CompleteAssignmentResponse)
def mark_assignment_complete(
    assignment_id: int,
    api_key: str = Depends(auth.get_api_key)
):
    """
    Acknowledge assignment completion — placeholder for systems without `completed_at`.
    """
    now = datetime.utcnow().isoformat()

    return CompleteAssignmentResponse(
        message="This database does not support assignment completion tracking.",
        completed_at=now
    )

def assign_users_to_chore(conn, chore_id: int, assignee_ids: list[int]):
    """
    Helper function to assign multiple users to a chore.
    """
    for user_id in assignee_ids:
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore_id, :user_id, NOW())
            """),
            {"chore_id": chore_id, "user_id": user_id}
        )
