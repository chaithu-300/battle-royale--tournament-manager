
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import jwt

from functions import (
    get_db,
    User,
    update_squad,
    register_squad,
    withdraw_squad,
    schedule_match,
    submit_match_result,
    get_tournament_leaderboard,
    SECRET_KEY,
    ALGORITHM
)


app = FastAPI(title="BGMI Tournament Manager")


# --------------------------------------------------
# PYDANTIC MODELS
# --------------------------------------------------

# E10 - UPDATE SQUAD

class UpdateSquad(BaseModel):
    squad_name: str


# E11 - REGISTER SQUAD

class RegisterSquad(BaseModel):
    squad_id: int


# E13 - SCHEDULE MATCH

class ScheduleMatch(BaseModel):
    match_number: int = Field(ge=1)
    match_date: datetime
    map_name: str


# E14 - SUBMIT MATCH RESULT

class SubmitMatchResult(BaseModel):
    squad_id: int
    placement: int = Field(ge=1)
    kills: int = Field(ge=0)


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def get_current_user(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db)
):

    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization token is required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use Bearer token"
        )

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("user_id", payload.get("sub"))

    if user_id is None or not str(user_id).isdigit():
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(
        User.user_id == int(user_id)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# PLAYER ROLE CHECK

def get_current_player(
    user: User = Depends(get_current_user)
):

    if user.role != "player":  #pyright:ignore
        raise HTTPException(
            status_code=403,
            detail="Only players can access this endpoint"
        )

    return user


# ORGANIZER ROLE CHECK

def get_current_organizer(
    user: User = Depends(get_current_user)
):

    if user.role != "organizer":  #pyright:ignore
        raise HTTPException(
            status_code=403,
            detail="Only organizers can access this endpoint"
        )

    return user


# --------------------------------------------------
# COMMON FUNCTION RESPONSE HANDLER
# --------------------------------------------------

def handle_response(result):

    success, message, data = result

    if success is False:

        if "not found" in message.lower():
            status_code = 404

        elif "only" in message.lower() or "not the organizer" in message.lower():
            status_code = 403

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=message
        )

    return {
        "message": message,
        "data": data
    }


# --------------------------------------------------
# E10: UPDATE SQUAD DETAILS
# PATCH /squads/{squad_id}
# --------------------------------------------------

@app.patch("/squads/{squad_id}")
def update_squad_details(
    squad_id: int,
    request: UpdateSquad,
    user: User = Depends(get_current_player),
    db: Session = Depends(get_db)
):

    result = update_squad(
        db,
        squad_id,
        user.user_id,  #pyright:ignore
        request.squad_name
    )

    return handle_response(result)


# --------------------------------------------------
# E11: REGISTER SQUAD FOR TOURNAMENT
# POST /tournaments/{tournament_id}/register
# --------------------------------------------------

@app.post("/tournaments/{tournament_id}/register")
def register_tournament_squad(
    tournament_id: int,
    request: RegisterSquad,
    user: User = Depends(get_current_player),
    db: Session = Depends(get_db)
):

    result = register_squad(
        db,
        tournament_id,
        request.squad_id,
        user.user_id   #pyright:ignore
    )

    return handle_response(result)


# --------------------------------------------------
# E12: WITHDRAW SQUAD FROM TOURNAMENT
# DELETE /tournaments/{tournament_id}/squads/{squad_id}
# --------------------------------------------------

@app.delete("/tournaments/{tournament_id}/squads/{squad_id}")
def withdraw_tournament_squad(
    tournament_id: int,
    squad_id: int,
    user: User = Depends(get_current_player),
    db: Session = Depends(get_db)
):

    result = withdraw_squad(
        db,
        tournament_id,
        squad_id, 
        user.user_id   #pyright:ignore
    )

    return handle_response(result)


# --------------------------------------------------
# E13: SCHEDULE TOURNAMENT MATCH
# POST /tournaments/{tournament_id}/matches
# --------------------------------------------------

@app.post("/tournaments/{tournament_id}/matches")
def create_tournament_match(
    tournament_id: int,
    request: ScheduleMatch,
    user: User = Depends(get_current_organizer),
    db: Session = Depends(get_db)
):

    result = schedule_match(
        db,
        tournament_id,
        user.user_id,   #pyright:ignore
        request.match_number,
        request.match_date,
        request.map_name
    )

    return handle_response(result)


# --------------------------------------------------
# E14: SUBMIT MATCH RESULTS
# POST /matches/{match_id}/results
# --------------------------------------------------

@app.post("/matches/{match_id}/results")
def create_match_result(
    match_id: int,
    request: SubmitMatchResult,
    user: User = Depends(get_current_organizer),
    db: Session = Depends(get_db)
):

    result = submit_match_result(
        db,
        match_id,
        user.user_id,  #pyright:ignore
        request.squad_id,
        request.placement,
        request.kills
    )

    return handle_response(result)


# --------------------------------------------------
# E15: GET TOURNAMENT LEADERBOARD
# GET /tournaments/{tournament_id}/leaderboard
# --------------------------------------------------

@app.get("/tournaments/{tournament_id}/leaderboard")
def tournament_leaderboard(
    tournament_id: int,
    db: Session = Depends(get_db)
):

    result = get_tournament_leaderboard(
        db,
        tournament_id
    )

    return handle_response(result)
