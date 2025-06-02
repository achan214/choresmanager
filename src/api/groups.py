from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import sqlalchemy
from src.api import auth
from enum import Enum
from typing import List, Optional
from src import database as db
from datetime import datetime, timedelta
from fastapi import Query


router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    dependencies=[Depends(auth.get_api_key)],
)

class Group(BaseModel):
    id: int
    group_name: str = Field(..., min_length=1, max_length=50)
    invite_code: str = Field(..., min_length=1, max_length=10)

class GroupResponse(BaseModel):
    id: int
    name: str

@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group: Group, user=Depends(auth.get_current_user)):
    """
    Create a new group and automatically assign the creator to it.
    """
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO groups (group_name, created_at, invite_code)
                VALUES (:name, NOW(), :invite_code)
                RETURNING id, group_name
                """
            ),
            {"name": group.group_name, "invite_code": group.invite_code},
        ).mappings().fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create group",
            )

        # Assign the creator to the group
        connection.execute(
            sqlalchemy.text("""
                UPDATE users
                SET group_id = :group_id
                WHERE id = :user_id
            """),
            {"group_id": result["id"], "user_id": user["id"]}
        )

    return GroupResponse(
        id=result["id"],
        name=result["group_name"],
    )


# join a group
@router.post("/join", response_model=GroupResponse, status_code=status.HTTP_200_OK)
def join_group(group_name: str, invite_code: str, user=Depends(auth.get_current_user)):
    """
    Join a group with the given ID and invite code.
    """
    
    with db.engine.begin() as connection:
        # Step 1: Retrieve the invite code for the specified group
        group = connection.execute(
            sqlalchemy.text(
                """
                SELECT invite_code, group_name
                FROM groups
                WHERE group_name = :group_name
                """
            ),
            {"group_name": group_name},
        ).mappings().fetchone()

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )

        # Step 2: Compare the invite codes
        if group["invite_code"] != invite_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invite code",
            )

        # Step 3: Update the user's group_id using the group name and username that are unique
        group_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id
                FROM groups
                WHERE group_name = :group_name
                """
            ),
            {"group_name": group_name},
        ).scalar()
        if not group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )

        # Update the user's group_id
        user_result = connection.execute(
            sqlalchemy.text(
                """
                UPDATE users
                SET group_id = :group_id
                WHERE id = :user_id
                RETURNING id, username
                """
            ),
            {"group_id": group_id, "user_id": user["id"]},
        ).mappings().fetchone()

        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to join group",
            )

    return GroupResponse(
        id=user_result["id"],
        name=group["group_name"],  # Return the group's name
    )

@router.get("/{group_id}/chores")
def get_group_chores(group_id: int):
    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT name AS chore_name, completed
                FROM chores
                WHERE group_id = :group_id
            """),
            {"group_id": group_id}
        ).mappings().all()

    return list(result)

@router.get("/{group_id}/stats")
def get_group_stats(group_id: int):
    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                SELECT u.id AS user_id, u.username, COUNT(*) AS completed_count
                FROM users u
                JOIN assignments a ON u.id = a.user_id
                JOIN chores c ON a.chore_id = c.id
                WHERE c.group_id = :group_id AND c.completed = true
                GROUP BY u.id, u.username
            """),
            {"group_id": group_id}
        ).mappings().all()

    return [
        {
            "user_id": row["user_id"],
            "username": row["username"],
            "completed_count": row["completed_count"]
        }
        for row in result
    ]


@router.post("/leave")
def leave_group(user=Depends(auth.get_current_user)):
    """
    Allows a user to leave their current group by setting group_id = NULL.
    """
    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.text("""
                UPDATE users
                SET group_id = NULL
                WHERE id = :id
                RETURNING id
            """),
            {"id": user["id"]}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found.")

    return {"message": "You have left the group."}

@router.get("/{group_id}/members")
def get_group_members(group_id: int, user=Depends(auth.get_current_user)):
    """
    Returns all members of the given group (id and username).
    Only accessible if the requesting user is in the group.
    """
    with db.engine.begin() as conn:
        # Ensure the user is part of the group they’re requesting
        user_group_id = conn.execute(
            sqlalchemy.text("SELECT group_id FROM users WHERE id = :user_id"),
            {"user_id": user["id"]}
        ).scalar()

        if user_group_id != group_id:
            raise HTTPException(status_code=403, detail="Access denied: not your group.")

        # Retrieve all users in the group
        members = conn.execute(
            sqlalchemy.text("""
                SELECT id, username FROM users
                WHERE group_id = :group_id
            """),
            {"group_id": group_id}
        ).mappings().all()

    return list(members)

@router.get("/{group_id}/summary")
def get_group_summary(
    group_id: int,
    period: Optional[str] = Query("week", regex="^(week|month)$"),
    user=Depends(auth.get_current_user)
):
    # Time window calculation
    now = datetime.now()
    start_date = now - timedelta(days=7) if period == "week" else now - timedelta(days=30)

    with db.engine.begin() as conn:
        # Confirm user belongs to group
        user_group = conn.execute(
            sqlalchemy.text("SELECT group_id FROM users WHERE id = :user_id"),
            {"user_id": user["id"]}
        ).scalar()

        if user_group != group_id:
            raise HTTPException(status_code=403, detail="Unauthorized for this group.")

        # Total chores created
        total_created = conn.execute(sqlalchemy.text("""
            SELECT COUNT(*) FROM chores
            WHERE group_id = :group_id AND created_at >= :start
        """), {"group_id": group_id, "start": start_date}).scalar()

        # Total chores completed
        total_completed = conn.execute(sqlalchemy.text("""
            SELECT COUNT(*) FROM chores
            WHERE group_id = :group_id AND completed = true AND completed_at >= :start
        """), {"group_id": group_id, "start": start_date}).scalar()

        # Chores completed late
        completed_late = conn.execute(sqlalchemy.text("""
            SELECT COUNT(*) FROM chores
            WHERE group_id = :group_id AND completed = true AND completed_at > due_date AND completed_at >= :start
        """), {"group_id": group_id, "start": start_date}).scalar()

        # Chores not completed
        not_completed = conn.execute(sqlalchemy.text("""
            SELECT COUNT(*) FROM chores
            WHERE group_id = :group_id AND completed = false AND due_date < :now
        """), {"group_id": group_id, "now": now}).scalar()

        # Per-user completion count
        user_stats = conn.execute(sqlalchemy.text("""
            SELECT u.id AS user_id, u.username, COUNT(c.id) AS completed_count
            FROM users u
            JOIN assignments a ON u.id = a.user_id
            JOIN chores c ON a.chore_id = c.id
            WHERE c.group_id = :group_id AND c.completed = true AND c.completed_at >= :start
            GROUP BY u.id, u.username
        """), {"group_id": group_id, "start": start_date}).mappings().all()

    # Compute top and lowest contributor
    top_user = max(user_stats, key=lambda x: x["completed_count"], default=None)
    low_user = min(user_stats, key=lambda x: x["completed_count"], default=None)

    return {
        "period": period,
        "total_chores_created": total_created,
        "total_chores_completed": total_completed,
        "completed_late": completed_late,
        "not_completed": not_completed,
        "user_stats": user_stats,
        "top_contributor": top_user,
        "lowest_contributor": low_user
    }


