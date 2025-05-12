from fastapi import FastAPI
from src.api import chores, groups, users, auth, server, admin, assignments
from starlette.middleware.cors import CORSMiddleware

description = """
Chores Manager API helps you manage your chores and tasks effectively.
"""
tags_metadata = [
    {"name": "groups", "description": "Manage groups and group memberships."}  # Add groups metadata
]

app = FastAPI(
    title="Chores Manager",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Amanda Chan",
        "email": "achan214@calpoly.edu",
    },
    openapi_tags=tags_metadata,
)

# origins = ["https://potion-exchange.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(groups.router)
app.include_router(chores.router)
app.include_router(assignments.router)
app.include_router(users.router)



@app.get("/")
async def root():
    return {"message": "Welcome to Chores Management API!"}
