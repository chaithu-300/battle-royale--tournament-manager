from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime

import functions

app = FastAPI(title="BGMI Tournament Manager")


# Request models
class CreateOrganizer(BaseModel):
    username: str
    email: str
    password: str


class CreateTournament(BaseModel):
    tournament_name: str
    description: str
    map_name: str
    registration_start: datetime
    registration_end: datetime
    max_squads: int


class UpdateTournament(BaseModel):
    tournament_name: str = None
    description: str = None
    map_name: str = None
    registration_start: datetime = None
    registration_end: datetime = None
    max_squads: int = None
    status: str = None


class CreateSquad(BaseModel):
    squad_name: str


@app.get("/")
def home():
    return {"message": "BGMI Tournament Manager API is running"}


# E1 – Create organizer
@app.post("/admin/organizers")
def add_organizer(data: CreateOrganizer, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create organizers")

    result = functions.create_organizer(
        data.username,
        data.email,
        data.password
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Email already exists")

    return result


# E2 – Create tournament
@app.post("/tournaments")
def add_tournament(data: CreateTournament, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can create tournaments")

    result = functions.create_tournament(
        user.user_id,
        data.tournament_name,
        data.description,
        data.map_name,
        data.registration_start,
        data.registration_end,
        data.max_squads
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Invalid tournament details")

    return result


# E3 – Get all available tournaments
@app.get("/tournaments")
def all_tournaments():

    result = functions.get_tournaments()

    return result


