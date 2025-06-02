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
    Checks that the chore and user both exist.
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

        # Create assignment
        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, completed, completed_at)
                VALUES (:chore_id, :user_id, false, NULL)
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
    Mark a specific assignment as complete.
    Sets the `completed` flag and updates the `completed_at` timestamp.
    """
    with db.engine.begin() as conn:
        assignment = conn.execute(
            sqlalchemy.text("SELECT id FROM assignments WHERE id = :id"),
            {"id": assignment_id}
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found.")

        now = datetime.utcnow().isoformat()

        conn.execute(
            sqlalchemy.text("""
                UPDATE assignments
                SET completed = true,
                    completed_at = :completed_at
                WHERE id = :id
            """),
            {"id": assignment_id, "completed_at": now}
        )

    return CompleteAssignmentResponse(
        message="Assignment marked as complete.",
        completed_at=now
    )
def assign_users_to_chore(conn, chore_id: int, assignee_ids: list[int]):
    """
    Helper function to assign multiple users to a chore.
    Used internally by the chores module.
    """
    for user_id in assignee_ids:
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore_id, :user_id, NOW())
            """),
            {"chore_id": chore_id, "user_id": user_id}
        )
