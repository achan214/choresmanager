from fastapi import APIRouter, Depends, HTTPException, status
import sqlalchemy
from src import database as db
from src.api import auth
from pydantic import BaseModel
from typing import Optional

class Group(BaseModel):
    group_name: str
    invite_code: Optional[str] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    invite_code: Optional[str] = None


router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group: Group, user=Depends(auth.get_current_user)):
    """
    Create a new group and assign the requesting user to it.
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
                detail="Group creation failed."
            )

        connection.execute(
            sqlalchemy.text("""
                UPDATE users
                SET group_id = :group_id
                WHERE id = :user_id
            """),
            {"group_id": result["id"], "user_id": user["id"]}
        )

    return {"id": result["id"], "name": result["group_name"]}


@router.post("/join", response_model=GroupResponse, status_code=status.HTTP_200_OK)
def join_group(group_name: str, invite_code: str, user=Depends(auth.get_current_user)):
    """
    Join a group using the group name and invite code.
    """
    with db.engine.begin() as connection:
        group = connection.execute(
            sqlalchemy.text(
                """
                SELECT id, group_name, invite_code
                FROM groups
                WHERE group_name = :group_name
                """
            ),
            {"group_name": group_name},
        ).mappings().fetchone()

        if not group:
            raise HTTPException(status_code=404, detail="Group not found.")

        if group["invite_code"] != invite_code:
            raise HTTPException(status_code=400, detail="Invalid invite code.")

        updated = connection.execute(
            sqlalchemy.text(
                """
                UPDATE users
                SET group_id = :group_id
                WHERE id = :user_id
                RETURNING id
                """
            ),
            {"group_id": group["id"], "user_id": user["id"]},
        ).fetchone()

        if not updated:
            raise HTTPException(status_code=400, detail="Group join failed.")

    return {"id": group["id"], "name": group["group_name"]}


@router.post("/leave")
def leave_group(user=Depends(auth.get_current_user)):
    """
    Remove the user from their current group.
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
