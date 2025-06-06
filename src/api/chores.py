from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlalchemy
from src import database as db
from src.api import auth
from src.api.assignments import assign_users_to_chore
from typing import Optional
from datetime import datetime

router = APIRouter(
    prefix="/chores",
    tags=["chores"],
    dependencies=[Depends(auth.get_api_key)],
)

class ChoreCreate(BaseModel):
    username: str
    group_name: str
    chore_name: str
    description: str  
    due_date: datetime
    assignees: list[str]  
    recurring: str | None = None

class ChoreCreatedResponse(BaseModel):
    chore_id: int
    message: str

@router.post("/", response_model=ChoreCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_chore(
    chore: ChoreCreate,
):
    if not chore.chore_name or not chore.due_date or not chore.description:
        raise HTTPException(status_code=400, detail="chore name, description, and due date are required")

    if not chore.assignees:
        raise HTTPException(status_code=400, detail="at least one assignee must be specified")

    with db.engine.begin() as conn:
        user_id = conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": chore.username}
        ).scalar()

        if not user_id:
            raise HTTPException(status_code=404, detail="user not found")

        group_id = conn.execute(
            sqlalchemy.text("SELECT id FROM groups WHERE group_name = :group_name"),
            {"group_name": chore.group_name}
        ).scalar()

        if not group_id:
            raise HTTPException(status_code=404, detail="group not found")

        assignee_ids = conn.execute(
            sqlalchemy.text("""
                SELECT id FROM users 
                WHERE username = ANY(:usernames) AND group_id = :group_id
            """),
            {"usernames": chore.assignees, "group_id": group_id}
        ).scalars().all()

        if not assignee_ids or len(assignee_ids) != len(chore.assignees):
            raise HTTPException(status_code=400, detail="One or more assignees not found in group")

        result = conn.execute(
            sqlalchemy.text("""
                INSERT INTO chores (name, description, group_id, due_date, is_recurring, recurrence_pattern, created_by, completed, created_at)
                VALUES (:name, :description, :group_id, :due_date, :is_recurring, :recurrence_pattern, :created_by, false, NOW())
                RETURNING id
            """),
            {
                "name": chore.chore_name,
                "description": chore.description,
                "group_id": group_id,
                "due_date": chore.due_date,
                "is_recurring": chore.recurring is not None,
                "recurrence_pattern": chore.recurring,
                "created_by": user_id
            }
        ).mappings().fetchone()

        chore_id = result["id"]
        assign_users_to_chore(conn, chore_id, assignee_ids)

    return {"chore_id": chore_id, "message": "chore created"}


@router.post("/assign-balanced")
def assign_chore_balanced(chore: ChoreCreate):
    with db.engine.begin() as conn:
        group_id = conn.execute(
            sqlalchemy.text("SELECT id FROM groups WHERE group_name = :group_name"),
            {"group_name": chore.group_name}
        ).scalar()

        if not group_id:
            raise HTTPException(status_code=404, detail="group not found")

        members = conn.execute(sqlalchemy.text("""
            SELECT u.id, COUNT(a.chore_id) as chore_count
            FROM users u
            LEFT JOIN assignments a ON u.id = a.user_id
            LEFT JOIN chores c ON a.chore_id = c.id AND c.completed = false AND c.archived = false
            WHERE u.group_id = :group_id
            GROUP BY u.id
            ORDER BY chore_count ASC
        """), {"group_id": group_id}).mappings().all()

        if not members:
            raise HTTPException(status_code=404, detail="no users found in group")

        selected = [m["id"] for m in members[:len(chore.assignees)]]


        user_id = conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": chore.username}
        ).scalar()

        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

        result = conn.execute(sqlalchemy.text("""
            INSERT INTO chores (name, description, group_id, due_date, is_recurring, recurrence_pattern, created_by, completed, created_at)
            VALUES (:name, :description, :group_id, :due_date, :is_recurring, :recurrence_pattern, :created_by, false, NOW())
            RETURNING id
        """), {
            "name": chore.chore_name,
            "description": chore.description,
            "group_id": group_id,
            "due_date": chore.due_date,
            "is_recurring": chore.recurring is not None,
            "recurrence_pattern": chore.recurring,
            "created_by": user_id
        }).mappings().fetchone()

        chore_id = result["id"]
        assign_users_to_chore(conn, chore_id, selected)

    return {"chore_id": chore_id, "assigned_to": selected, "message": "chore assigned fairly"}


@router.post("/reminders/send")
def send_reminders(group_name: str = Body(...), timeframe_hours: int = Body(default=48)):
    now = datetime.now()
    deadline = now + timedelta(hours=timeframe_hours)

    with db.engine.begin() as conn:
        group_id = conn.execute(
            sqlalchemy.text("SELECT id FROM groups WHERE group_name = :group_name"),
            {"group_name": group_name}
        ).scalar()

        if not group_id:
            raise HTTPException(status_code=404, detail="group not found")

        results = conn.execute(sqlalchemy.text("""
            SELECT u.id as user_id, u.username, c.id as chore_id, c.name, c.due_date
            FROM chores c
            JOIN assignments a ON c.id = a.chore_id
            JOIN users u ON a.user_id = u.id
            WHERE c.group_id = :group_id AND c.completed = false AND c.archived = false AND c.due_date BETWEEN :now AND :deadline
        """), {"group_id": group_id, "now": now, "deadline": deadline}).mappings().all()

        if not results:
            return {"message": "no upcoming chores found"}

        reminders_sent = []
        for r in results:
            reminders_sent.append({
                "user_id": r["user_id"],
                "chore_id": r["chore_id"],
                "message": f"reminder: '{r['name']}' is due by {r['due_date']}"
            })

        return {"reminders_sent": reminders_sent}


@router.patch("/{chore_id}/archive")
def archive_chore(chore_id: int, user=Depends(auth.get_current_user)):
    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                UPDATE chores
                SET archived = true
                WHERE id = :chore_id
                RETURNING id
            """),
            {"chore_id": chore_id}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="chore not found")

    return {"message": "chore archived"}

class ChoreDuplicateRequest(BaseModel):
    new_due_date: Optional[datetime] = None
    assignees: Optional[list[str]] = None
    recurring: Optional[str] = None

@router.post("/{chore_id}/duplicate", response_model=ChoreCreatedResponse)
def duplicate_chore(
    chore_id: int,
    request: ChoreDuplicateRequest,
    username: str
):
    with db.engine.begin() as conn:
        chore = conn.execute(sqlalchemy.text("""
            SELECT * FROM chores WHERE id = :id
        """), {"id": chore_id}).mappings().fetchone()

        if not chore:
            raise HTTPException(status_code=404, detail="Original chore not found")

        user_id = conn.execute(
            sqlalchemy.text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        ).scalar()

        group_check = conn.execute(
            sqlalchemy.text("SELECT group_id FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).scalar()

        if group_check != chore["group_id"]:
            raise HTTPException(status_code=403, detail="Not authorized to duplicate this chore")

        new_due_date = request.new_due_date or chore["due_date"]
        new_recurrence = request.recurring if request.recurring is not None else chore["recurrence_pattern"]

        result = conn.execute(sqlalchemy.text("""
            INSERT INTO chores (name, description, group_id, due_date, is_recurring, recurrence_pattern, created_by, completed, created_at)
            VALUES (:name, :description, :group_id, :due_date, :is_recurring, :recurrence_pattern, :created_by, false, NOW())
            RETURNING id
        """), {
            "name": chore["name"],
            "description": chore["description"],
            "group_id": chore["group_id"],
            "due_date": new_due_date,
            "is_recurring": new_recurrence is not None,
            "recurrence_pattern": new_recurrence,
            "created_by": user_id
        }).mappings().fetchone()

        new_chore_id = result["id"]

        if request.assignees:
            assignee_ids = conn.execute(
                sqlalchemy.text("""
                    SELECT id FROM users 
                    WHERE username = ANY(:usernames) AND group_id = :group_id
                """),
                {"usernames": request.assignees, "group_id": chore["group_id"]}
            ).scalars().all()
        else:
            assignee_ids = conn.execute(sqlalchemy.text("""
                SELECT user_id FROM assignments WHERE chore_id = :chore_id
            """), {"chore_id": chore_id}).scalars().all()

        if not assignee_ids:
            raise HTTPException(status_code=400, detail="No assignees provided or found on original chore")

        assign_users_to_chore(conn, new_chore_id, assignee_ids)

    return {"chore_id": new_chore_id, "message": "Chore duplicated successfully"}

