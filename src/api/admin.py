from fastapi import APIRouter, Depends, status
import sqlalchemy
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset():
    """
    Reset the database, remove all data (no groups, users, chores, etc.) within the tables but keep the tables empty
    """

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "TRUNCATE TABLE assignments, chores, users, groups RESTART IDENTITY CASCADE"
        ))
        

