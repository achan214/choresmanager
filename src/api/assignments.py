from fastapi import APIRouter, Depends, HTTPException, Request
import sqlalchemy
from datetime import datetime
from src import database as db
from src.api import auth

router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
    dependencies=[Depends(auth.get_api_key)],
)

# assign a user to a chore
@router.post("/assign")
def assign_user_to_chore(request: Request, chore_id: int, user_id: int):
    user = auth.get_current_user(request)

    with db.engine.begin() as conn:
        # check if chore exists
        chore = conn.execute(
            sqlalchemy.text("SELECT group_id FROM chores WHERE id = :chore_id"),
            {"chore_id": chore_id}
        ).mappings().fetchone()

        if not chore:
            raise HTTPException(status_code=404, detail="chore not found")

        # check if user is in the same group
        if chore["group_id"] != user["group_id"]:
            raise HTTPException(status_code=403, detail="not authorized to assign in this group")

        # insert assignment
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO assignments (chore_id, user_id, assigned_at)
                VALUES (:chore_id, :user_id, :assigned_at)
            """),
            {"chore_id": chore_id, "user_id": user_id, "assigned_at": datetime.now()}
        )

    return {"message": "user assigned to chore"}

# mark an assignment complete
@router.patch("/{chore_id}/complete/{user_id}")
def complete_assignment(request: Request, chore_id: int, user_id: int):
    current_user = auth.get_current_user(request)

    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="cannot complete assignment for another user")

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
            raise HTTPException(status_code=404, detail="chore not found")

    return {"message": "assignment marked complete"}
