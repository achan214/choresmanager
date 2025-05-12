from fastapi import APIRouter, Depends, HTTPException, status 
from pydantic import BaseModel
from datetime import datetime
import sqlalchemy
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/chores",
    tags=["chores"],
    dependencies=[Depends(auth.get_api_key)],
)

class ChoreCreate(BaseModel):
    group_id: int
    chore_name: str
    description: str  
    due_date: datetime
    assignees: list[int]
    recurring: str | None = None

class ChoreCreatedResponse(BaseModel):
    chore_id: int
    message: str

@router.post("/", response_model=ChoreCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_chore(chore: ChoreCreate):
    user = auth.get_current_user()

    if not chore.chore_name or not chore.due_date or not chore.description:
        raise HTTPException(status_code=400, detail="Chore name, description, and due date are required.")

    with db.engine.begin() as conn:
        # insert the chore
        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO chores (name, description, group_id, due_date, is_recurring, recurrence_pattern, created_by, completed)
                VALUES (:name, :description, :group_id, :due_date, :is_recurring, :recurrence_pattern, :created_by, false)
                RETURNING id
            """),
            {
                "name": chore.chore_name,
                "description": chore.description,
                "group_id": chore.group_id,
                "due_date": chore.due_date,
                "is_recurring": chore.recurring is not None,
                "recurrence_pattern": chore.recurring,
                "created_by": user["id"]
            }
        ).mappings().fetchone()

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create chore.")

        chore_id = result["id"]

        # assign the chores to users
        for user_id in chore.assignees:
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO assignments (chore_id, user_id, assigned_at)
                    VALUES (:chore_id, :user_id, :assigned_at)
                """),
                {
                    "chore_id": chore_id,
                    "user_id": user_id,
                    "assigned_at": datetime.now()
                }
            )

    return {"chore_id": chore_id, "message": "Chore created."}

@router.patch("/{chore_id}/complete")
def mark_chore_complete(chore_id: int):
    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                UPDATE chores
                SET completed = true
                WHERE id = :chore_id
                RETURNING id
            """),
            {"chore_id": chore_id}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Chore not found.")

    return {"message": "Chore marked as complete."}
