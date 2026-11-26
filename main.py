
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from datetime import datetime

import functions

app = FastAPI(title="BGMI Tournament Manager")


# --------------------------------------------------
# PYDANTIC MODELS
# --------------------------------------------------


class CreateAdmin(BaseModel):
    username: str
    email: str
    password: str


class RegisterData(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginData(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


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
    tournament_name: str = None    #pyright:ignore
    description: str = None    #pyright:ignore
    map_name: str = None   #pyright:ignore
    registration_start: datetime = None   #pyright:ignore
    registration_end: datetime = None    #pyright:ignore
    max_squads: int = None    #pyright:ignore
    status: str = None   #pyright:ignore


class CreateSquad(BaseModel):
    squad_name: str


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


class InvitePlayerData(BaseModel):
    squad_id: int
    invited_player_id: int


class InvitationResponseData(BaseModel):
    invitation_id: int
    response: str = Field(min_length=1)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {"message": "BGMI Tournament Manager API is running"}


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

# 1. Register player

@app.post("/auth/register")
def register(data: RegisterData):

    response = functions.register_user(
        username=data.username,
        email=data.email,
        password=data.password
    )

    if not response:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    return {"message": "User registered successfully"}


# 2. Login

@app.post("/auth/login")
def login(data: LoginData):

    tokens = functions.verify_login(
        email=data.email,
        password=data.password
    )

    if not tokens:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    return tokens


# 3. Refresh token

@app.post("/auth/refresh")
def refresh(refresh_token: str = Header(None)):

    response = functions.refresh_access_token(refresh_token)

    if not response:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    return response


# --------------------------------------------------
# E1 - CREATE ORGANIZER
# Only admin
# --------------------------------------------------

@app.post("/admin/organizers")
def add_organizer(data: CreateOrganizer, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    if user.role != "admin":     #pyright:ignore
        raise HTTPException(
            status_code=403,
            detail="Only admin can create organizers"
        )

    result = functions.create_organizer(
        data.username,
        data.email,
        data.password
    )

    if result is False:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    return result


# --------------------------------------------------
# E2 - CREATE TOURNAMENT
# Only organizer
# --------------------------------------------------

@app.post("/tournaments")
def add_tournament(data: CreateTournament, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "organizer":    #pyright:ignore
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


# --------------------------------------------------
# E3 - GET ALL AVAILABLE TOURNAMENTS
# Public
# --------------------------------------------------

@app.get("/tournaments")
def all_tournaments():

    result = functions.get_tournaments()

    return result


# --------------------------------------------------
# E4 - GET TOURNAMENT BY ID
# Public
# --------------------------------------------------

@app.get("/tournaments/{tournament_id}")
def tournament_details(tournament_id: int):

    result = functions.get_tournament_by_id(tournament_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return result


# --------------------------------------------------
# E5 - UPDATE TOURNAMENT
# Only organizer
# --------------------------------------------------

@app.patch("/tournaments/{tournament_id}")
def edit_tournament(
    tournament_id: int,
    data: UpdateTournament,
    token: str = Header(None)
):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "organizer":    #pyright:ignore
        raise HTTPException(status_code=403, detail="Only organizers can update tournaments")

    result = functions.update_tournament(
        tournament_id,
        user.user_id,
        data.tournament_name,
        data.description,
        data.map_name,
        data.registration_start,
        data.registration_end,
        data.max_squads,
        data.status
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Tournament could not be updated")

    return result


# --------------------------------------------------
# E6 - CREATE SQUAD
# Only player
# --------------------------------------------------

@app.post("/squads")
def add_squad(data: CreateSquad, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "player":    #pyright:ignore
        raise HTTPException(status_code=403, detail="Only players can create squads")

    result = functions.create_squad(
        user.user_id,
        data.squad_name
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Invalid squad name")

    return result


# --------------------------------------------------
# E7 - GET MY SQUADS
# Only player
# --------------------------------------------------

@app.get("/squads/me")
def get_my_squads(token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "player":    #pyright:ignore
        raise HTTPException(status_code=403, detail="Only players can access this endpoint")

    response = functions.get_player_squads(user.user_id)

    return {"squads": response}


# --------------------------------------------------
# E8 - INVITE PLAYER TO SQUAD
# Only player and squad captain
# --------------------------------------------------

@app.post("/squads/invite")
def invite_player(data: InvitePlayerData, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "player":   #pyright:ignore
        raise HTTPException(status_code=403, detail="Only players can invite squad members")

    response = functions.invite_player_to_squad(
        user.user_id,
        data.squad_id,
        data.invited_player_id
    )

    if "error" in response:

        if response["error"] in ["Squad not found", "Player not found"]:
            raise HTTPException(status_code=404, detail=response["error"])

        raise HTTPException(status_code=400, detail=response["error"])

    return response


# --------------------------------------------------
# E9 - ACCEPT OR REJECT SQUAD INVITATION
# Only player
# --------------------------------------------------


# E9 - Player accepts or rejects a squad invitation

@app.post("/squads/invitations/respond")
def respond_to_invitation(data: InvitationResponseData, token: str = Header(None)):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "player":  #pyright:ignore
        raise HTTPException(status_code=403, detail="Only players can respond to invitations")

    response = functions.respond_to_squad_invitation(
        user.user_id,
        data.invitation_id,
        data.response.lower()
    )

    if "error" in response:
        if response["error"] == "Invitation not found" or response["error"] == "Squad not found":
            raise HTTPException(status_code=404, detail=response["error"])

        if response["error"] == "You are not allowed to respond to this invitation":
            raise HTTPException(status_code=403, detail=response["error"])

        raise HTTPException(status_code=400, detail=response["error"])

    return response



# --------------------------------------------------
# E10 - UPDATE SQUAD DETAILS
# Only player and squad captain
# --------------------------------------------------

@app.patch("/squads/{squad_id}")
def update_squad_details(
    data: UpdateSquad,
    squad_id: int,
    token: str = Header(None)
):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "player":   #pyright:ignore
        raise HTTPException(status_code=403, detail="Only players can update squads")

    result = functions.update_squad(
        squad_id,
        user.user_id,
        data.squad_name
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to update squad")

    return {"message": "Squad updated successfully"}


# --------------------------------------------------
# E11 - REGISTER SQUAD FOR TOURNAMENT
# Only player and squad captain
# --------------------------------------------------


# E11 - Register squad for tournament

@app.post("/tournaments/{tournament_id}/register")
def register_tournament_squad(
    tournament_id: int,
    data: RegisterSquad,
    token: str = Header(None)
):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    if user.role != "player":  #pyright:ignore
        raise HTTPException(
            status_code=403,
            detail="Only players can register squads"
        )

    result = functions.register_squad(
        tournament_id,
        data.squad_id,
        user.user_id
    )

    if result is False:
        raise HTTPException(
            status_code=400,
            detail="Unable to register squad. Check tournament and squad requirements."
        )

    return result



# --------------------------------------------------
# E12 - WITHDRAW SQUAD FROM TOURNAMENT
# Only player and squad captain
# --------------------------------------------------

@app.delete("/tournaments/{tournament_id}/squads/{squad_id}")
def withdraw_tournament_squad(
    tournament_id: int,
    squad_id: int,
    token: str = Header(None)
):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "player":   #pyright:ignore
        raise HTTPException(status_code=403, detail="Only players can withdraw squads")

    result = functions.withdraw_squad(
        tournament_id,
        squad_id,
        user.user_id
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to withdraw squad")

    return result


# --------------------------------------------------
# E13 - SCHEDULE TOURNAMENT MATCH
# Only organizer
# --------------------------------------------------

@app.post("/tournaments/{tournament_id}/matches")
def create_tournament_match(
    tournament_id: int,
    data: ScheduleMatch,
    token: str = Header(None)
):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "organizer":   #pyright:ignore
        raise HTTPException(status_code=403, detail="Only organizers can schedule matches")

    result = functions.schedule_match(
        tournament_id,
        user.user_id,
        data.match_number,
        data.match_date,
        data.map_name
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to schedule match")

    return result


# --------------------------------------------------
# E14 - SUBMIT MATCH RESULTS
# Only organizer
# --------------------------------------------------

@app.post("/matches/{match_id}/results")
def create_match_result(
    match_id: int,
    data: SubmitMatchResult,
    token: str = Header(None)
):

    user = functions.get_current_user(token)

    if user is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if user.role != "organizer":   #pyright:ignore
        raise HTTPException(status_code=403, detail="Only organizers can submit match results")

    result = functions.submit_match_result(
        match_id,
        user.user_id,
        data.squad_id,
        data.placement,
        data.kills
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to submit match result")

    return result


# --------------------------------------------------
# E15 - GET TOURNAMENT LEADERBOARD
# Public
# --------------------------------------------------

@app.get("/tournaments/{tournament_id}/leaderboard")
def tournament_leaderboard(tournament_id: int):

    result = functions.get_tournament_leaderboard(tournament_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return result




@app.post("/setup/create-admin")
def create_admin(data: CreateAdmin):

    result = functions.create_first_admin(
        data.username,
        data.email,
        data.password
    )

    if result is False:
        raise HTTPException(
            status_code=400,
            detail="Admin already exists or email is already registered"
        )

    return {"message": "First admin account created successfully"}

