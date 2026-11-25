from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime

import functions

app = FastAPI(title="BGMI Tournament Manager")


# Request models

class UpdateSquad(BaseModel):
    squad_name: str


class RegisterSquad(BaseModel):
    squad_id: int


class ScheduleMatch(BaseModel):
    match_number: int
    match_date: datetime
    map_name: str


class SubmitMatchResult(BaseModel):
    squad_id: int
    placement: int
    kills: int

@app.get("/")
def home():
    return {"message": "BGMI Tournament Manager API is running"}


# E10 - Update squad details

@app.patch("/squads/{squad_id}")
def update_squad_details(data: UpdateSquad, squad_id: int, token: str = Header(None)):

    user_id = functions.get_current_user(token)

    result = functions.update_squad(squad_id, user_id, data.squad_name)

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to update squad")

    return {"message": "Squad updated successfully"}


# E11 - Register squad for tournament

@app.post("/tournaments/{tournament_id}/register")
def register_tournament_squad(tournament_id: int, data: RegisterSquad, token: str = Header(None)):

    user_id = functions.get_current_user(token)

    result = functions.register_squad(tournament_id, data.squad_id, user_id)

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to register squad")

    return result


# E12 - Withdraw squad from tournament

@app.delete("/tournaments/{tournament_id}/squads/{squad_id}")
def withdraw_tournament_squad(tournament_id: int, squad_id: int, token: str = Header(None)):

    user_id = functions.get_current_user(token)

    result = functions.withdraw_squad(tournament_id, squad_id, user_id)

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to withdraw squad")

    return result


# E13 - Schedule tournament match

@app.post("/tournaments/{tournament_id}/matches")
def create_tournament_match(tournament_id: int, data: ScheduleMatch, token: str = Header(None)):

    user_id = functions.get_current_user(token)

    result = functions.schedule_match(
        tournament_id,
        user_id,
        data.match_number,
        data.match_date,
        data.map_name
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to schedule match")

    return result


# E14 - Submit match results

@app.post("/matches/{match_id}/results")
def create_match_result(match_id: int, data: SubmitMatchResult, token: str = Header(None)):

    user_id = functions.get_current_user(token)

    result = functions.submit_match_result(
        match_id,
        user_id,
        data.squad_id,
        data.placement,
        data.kills
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to submit match result")

    return result


# E15 - Get tournament leaderboard

@app.get("/tournaments/{tournament_id}/leaderboard")
def tournament_leaderboard(tournament_id: int):

    result = functions.get_tournament_leaderboard(tournament_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return result
