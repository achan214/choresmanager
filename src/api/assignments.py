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
    username: str

class AssignmentResponse(BaseModel):
    message: str
    assignment_id: int

class CompleteAssignmentResponse(BaseModel):
    message: str
    completed_by: str

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
        user_row = conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": assignment.username}
        ).mappings().fetchone()
        # user_exists = conn.execute(
        #     sqlalchemy.text("SELECT 1 FROM users WHERE id = :id"),
        #     {"id": assignment.user_id}
        # ).first()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found.")

        user_id = user_row["id"]

        # Create assignment with assigned_at
        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore_id, :user_id, NOW())
                RETURNING id
            """),
            {"chore_id": assignment.chore_id, "user_id": user_id}
        ).mappings().fetchone()

    return AssignmentResponse(
        message="Assignment created successfully.",
        assignment_id=result["id"]
    )

@router.patch("/{assignment_id}/complete", response_model=CompleteAssignmentResponse)
def mark_assignment_complete(
    assignment_id: int,
    username: str,
    api_key: str = Depends(auth.get_api_key)
):

    with db.engine.begin() as conn:
        # Ensure assignment exists
        assignment = conn.execute(
            sqlalchemy.text("SELECT * FROM assignments WHERE id = :id"),
            {"id": assignment_id}
        ).mappings().fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found.")

        # Ensure user matches the assignment
        if assignment["user_id"] != conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        ).scalar():
            raise HTTPException(status_code=403, detail="User does not own this assignment.")

        user_id = conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        ).scalar()

        if not user_id:
            raise HTTPException(status_code=404, detail="User not found.")

        # Mark as complete
        conn.execute(
            sqlalchemy.text("""
                UPDATE assignments SET completed_by = :user_id
                WHERE id = :id
            """),
            {"id": assignment_id, "user_id": user_id}
        )

        # Get the chore_id for this assignment
        chore_id = conn.execute(
            sqlalchemy.text("SELECT chore_id FROM assignments WHERE id = :assignment_id"),
            {"assignment_id": assignment_id}
        ).scalar()

        # Check if all assignments for this chore are completed
        all_completed = conn.execute(
            sqlalchemy.text("""
                SELECT COUNT(*) = SUM(CASE WHEN completed_by IS NOT NULL THEN 1 ELSE 0 END)
                FROM assignments
                WHERE chore_id = :chore_id
            """),
            {"chore_id": chore_id}
        ).scalar()

        # If all are complete, mark the chore as completed
        if all_completed:
            conn.execute(
                sqlalchemy.text("""
                    UPDATE chores SET completed = TRUE WHERE id = :chore_id
                """),
                {"chore_id": chore_id}
            )
    return CompleteAssignmentResponse(
        message="Marked assignment as complete.",
        completed_by=username
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
