from fastapi import APIRouter, Depends, HTTPException, status 
from pydantic import BaseModel
from datetime import datetime
import sqlalchemy
from src import database as db
from src.api import auth
from fastapi import Body
from datetime import timedelta

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

@router.post("/assign-balanced")
def assign_chore_balanced(chore: ChoreCreate):
    user = auth.get_current_user()

    with db.engine.begin() as conn:
        # Get group members and chore counts
        members = conn.execute(sqlalchemy.text("""
            SELECT u.id, COUNT(a.chore_id) as chore_count
            FROM users u
            LEFT JOIN assignments a ON u.id = a.user_id
            LEFT JOIN chores c ON a.chore_id = c.id AND c.completed = false
            WHERE u.group_id = :group_id
            GROUP BY u.id
            ORDER BY chore_count ASC
        """), {"group_id": chore.group_id}).mappings().all()

        if not members:
            raise HTTPException(status_code=404, detail="No users found in group.")

        # Choose N least busy members (or all if fewer than requested)
        selected = [m["id"] for m in members[:len(chore.assignees)]]

        result = conn.execute(sqlalchemy.text("""
            INSERT INTO chores (name, description, group_id, due_date, is_recurring, recurrence_pattern, created_by, completed)
            VALUES (:name, :description, :group_id, :due_date, :is_recurring, :recurrence_pattern, :created_by, false)
            RETURNING id
        """), {
            "name": chore.chore_name,
            "description": chore.description,
            "group_id": chore.group_id,
            "due_date": chore.due_date,
            "is_recurring": chore.recurring is not None,
            "recurrence_pattern": chore.recurring,
            "created_by": user["id"]
        }).mappings().fetchone()

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create chore.")

        chore_id = result["id"]

        for uid in selected:
            conn.execute(sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore_id, :user_id, NOW())
            """), {"chore_id": chore_id, "user_id": uid})

    return {"chore_id": chore_id, "assigned_to": selected, "message": "Chore assigned fairly."}

@router.post("/reminders/send")
def send_reminders(group_id: int = Body(...), timeframe_hours: int = Body(default=48)):
    now = datetime.now()
    deadline = now + timedelta(hours=timeframe_hours)

    with db.engine.begin() as conn:
        results = conn.execute(sqlalchemy.text("""
            SELECT u.id as user_id, u.username, c.id as chore_id, c.name, c.due_date
            FROM chores c
            JOIN assignments a ON c.id = a.chore_id
            JOIN users u ON a.user_id = u.id
            WHERE c.group_id = :group_id AND c.completed = false AND c.due_date BETWEEN :now AND :deadline
        """), {"group_id": group_id, "now": now, "deadline": deadline}).mappings().all()

        if not results:
            return {"message": "No upcoming chores found."}

        reminders_sent = []
        for r in results:
            reminders_sent.append({
                "user_id": r["user_id"],
                "chore_id": r["chore_id"],
                "message": f"Reminder: '{r['name']}' is due by {r['due_date']}"
            })

        return {"reminders_sent": reminders_sent}

