from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import sqlalchemy
from src.api import auth
from enum import Enum
from typing import List, Optional
from src import database as db

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    dependencies=[Depends(auth.get_api_key)],
)

class Group(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=50)
    invite_code: str = Field(..., min_length=1, max_length=10)

class GroupResponse(BaseModel):
    id: int
    name: str

@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group: Group):
    """
    Create a new group with the given name and invite code.
    """
    
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO groups (name, created_at, invite_code)
                VALUES (:name, NOW(), :invite_code)
                RETURNING id, name, created_at, invite_code
                """
            ),
            {"name": group.name, "invite_code": group.invite_code},
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create group",
            )

    return GroupResponse(
        id=result.id,
        name=result.name,
    )

# join a group
@router.post("/join", response_model=GroupResponse, status_code=status.HTTP_200_OK)
def join_group(group_id: int, invite_code: str):
    """
    Join a group with the given ID and invite code.
    """
    
    with db.engine.begin() as connection:
        # Step 1: Retrieve the invite code for the specified group
        group = connection.execute(
            sqlalchemy.text(
                """
                SELECT invite_code, name
                FROM groups
                WHERE id = :group_id
                """
            ),
            {"group_id": group_id},
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

        # Step 3: Update the user's group_id
        user_result = connection.execute(
            sqlalchemy.text(
                """
                UPDATE users
                SET group_id = :group_id
                WHERE id = :user_id
                RETURNING id, name
                """
            ),
            {"group_id": group_id, "user_id": auth.get_current_user()["id"]},
        ).mappings().fetchone()

        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to join group",
            )

    return GroupResponse(
        id=user_result["id"],
        name=group["name"],  # Return the group's name
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
                SELECT u.name, COUNT(*) AS completed_count
                FROM users u
                JOIN assignments a ON u.id = a.user_id
                JOIN chores c ON a.chore_id = c.id
                WHERE c.group_id = :group_id AND c.completed = true
                GROUP BY u.name
            """),
            {"group_id": group_id}
        ).mappings().all()

    return {row["name"]: row["completed_count"] for row in result}
